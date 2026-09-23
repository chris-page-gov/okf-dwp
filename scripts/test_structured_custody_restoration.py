"""Exact source/profile translation checks; not legal or model-answer scoring."""
from copy import deepcopy
import gzip
import json
from pathlib import Path
import unittest

from build_bundle import BASE, REPO, canonical, digest
from structured_custody_restoration import AUTHORING, compile_restoration, project
from build_logical_units import Inputs

ROOT=Path(__file__).resolve().parents[1]
CUSTODY=BASE+'id/term/common-imprisonment-payability'


def fixture():
    author=json.loads((ROOT/AUTHORING).read_bytes())
    old=json.loads((ROOT/'full-dmg/context/assembly-index.json').read_bytes())
    # Stable pre-restoration input, rather than this producer's eventual output.
    manifest=json.loads((ROOT/'logical-context/manifest.json').read_bytes())
    raw=(ROOT/'logical-context'/manifest['base_index']['path']).read_bytes()
    assert digest(raw)==manifest['base_index']['sha256']
    semantic=json.loads(raw)
    manifest=json.loads((ROOT/'structured-units/manifest.json').read_bytes())
    wanted={r['id'] for r in author['source_units']}; records=[]; units={}
    for ref in manifest['records']['shards']:
        if not any(ref['first_id']<=i<=ref['last_id'] for i in wanted):continue
        raw=(ROOT/'structured-units'/ref['path']).read_bytes();assert digest(raw)==ref['sha256']
        records.extend(r for r in json.loads(gzip.decompress(raw))['records'] if r['id'] in wanted)
    docs={tuple(i.removeprefix(BASE+'id/unit/').split('/')[:2]) for i in wanted}
    for family,doc in docs:
        raw=(ROOT/'structured-units/documents'/family/(doc+'.json.gz')).read_bytes()
        for u in json.loads(gzip.decompress(raw))['units']:
            if u['id'] in wanted:units[u['id']]=u
    pages={}
    for record in records:
        for span in record['evidence_unit']['spans']:
            path=span['extraction_url'].removeprefix(REPO+'/blob/main/')
            pages[span['extraction_sha256']]=(ROOT/path).read_bytes()
    return author,semantic,records,units,old,pages


class CustodyRestorationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.args=fixture();cls.result,cls.ledger=compile_restoration(*cls.args)

    def test_original_requirements_and_inherited_meanings_are_exact(self):
        result={r['id']:r for r in self.result['records']}
        for r in self.args[1]['records']:self.assertEqual(r,result[r['id']])
        req={r['id']:r for r in self.result['requirements']}
        for r in self.args[4]['requirements']:self.assertEqual(r,req[r['id']])
        self.assertEqual(self.args[4]['requirements'],self.ledger['original_requirements'])
        self.assertEqual(0,self.ledger['original_obligations_closed'])

    def test_location_mapping_is_separate_from_narrower_read_selection(self):
        self.assertEqual(33,len(self.ledger['page_mappings']))
        mapped={u for m in self.ledger['page_mappings'] for u in m['unit_ids']}
        selected={u for p in self.ledger['profiles'] for u in p['unit_ids']}
        self.assertEqual(137,len(mapped));self.assertEqual(53,len(selected))
        self.assertLess(len(selected),len(mapped))
        self.assertTrue(all(p['mapped_but_not_selected_unit_ids'] for p in self.ledger['profiles']))
        self.assertEqual(7,len(self.ledger['unresolved_selectors']))

    def test_benefit_mentions_without_custody_do_not_activate_or_traverse(self):
        profiles=[p for p in self.result['requirements'] if '/requirement/custody-units/' in p['id']]
        benefits={BASE+'id/'+v for v in ['staff-domain/jsa','staff-domain/income-support','staff-domain/esa','term/pension-credit']}
        self.assertFalse(any(set(p['when_all'])<=benefits for p in profiles))
        emitted=[e for e in self.result['assertions'] if '/assertion/custody-restoration/' in e['id']]
        self.assertTrue(all(CUSTODY in e['context_guard']['when_all'] for e in emitted))
        self.assertFalse(any(set(e['context_guard']['when_all'])<=benefits for e in emitted))

    def test_all_new_profiles_keep_open_obligations_and_whole_units(self):
        known={r['id'] for r in self.result['records']+self.args[2]}
        for profile in self.ledger['profiles']:
            self.assertEqual(4,len(profile['open_obligation_ids']))
            self.assertFalse(set(profile['open_obligation_ids'])&known)
        before=deepcopy(self.args);compile_restoration(*self.args);self.assertEqual(before,self.args)

    def test_literal_chapter_paths_do_not_fan_out_to_all_chapter_units(self):
        edges={r['id']:r for r in self.result['assertions']}
        for p in self.ledger['profiles']:
            for path in p['required_paths']:
                self.assertEqual(len(path['records']),len(path['assertions'])+1)
                for n,aid in enumerate(path['assertions']):
                    self.assertEqual([edges[aid]['source'],edges[aid]['target']],path['records'][n:n+2])
            self.assertTrue(any(len(path['assertions'])==2 for path in p['required_paths']))
        chapters={r['target'] for r in self.ledger['chapter_routes']}
        self.assertEqual(4,len(chapters))
        self.assertFalse(any(e['source'] in chapters and '/id/unit/' in e['target'] for e in edges.values()))

    def test_catalogue_observations_have_separate_scope_ids_and_exact_text(self):
        old={r['id']:r for r in self.args[4]['records']};new={r['id']:r for r in self.result['records']}
        for row in self.args[0]['scope_records']:
            if row['mode']!='dated-catalogue-observation':continue
            self.assertNotEqual(row['original_id'],row['id'])
            self.assertEqual(old[row['original_id']]['text'],new[row['id']]['text'])
            self.assertEqual('scope',new[row['id']]['kind'])
            self.assertIn('later corpus',new[row['id']]['scope'])

    def test_changed_whole_record_rejected(self):
        args=deepcopy(self.args);args[2][0]['text']+=' altered'
        with self.assertRaisesRegex(ValueError,'whole-unit identity'):compile_restoration(*args)

    def test_wrong_original_page_mapping_rejected(self):
        args=deepcopy(self.args);args[0]['page_mappings'][0]['unit_ids']=args[0]['page_mappings'][3]['unit_ids']
        with self.assertRaisesRegex(ValueError,'page/unit source'):compile_restoration(*args)

    def test_unknown_scope_or_unrelated_selection_rejected(self):
        args=deepcopy(self.args);args[0]['profiles'][0]['selected_unit_ids'].append(args[0]['source_units'][0]['id'])
        with self.assertRaisesRegex(ValueError,'explicitly scoped'):compile_restoration(*args)
        args=deepcopy(self.args);args[0]['@context']='https://example.invalid/context'
        with self.assertRaisesRegex(ValueError,'context differs'):compile_restoration(*args)

    def test_duplicate_application_and_closed_obligation_rejected(self):
        args=list(self.args);args[1]=self.result
        with self.assertRaisesRegex(ValueError,'already applied'):compile_restoration(*args)
        args=deepcopy(self.args);args[0]['profiles'][0]['missing_obligations'][0]['status']='resolved'
        with self.assertRaisesRegex(ValueError,'obligation closed'):compile_restoration(*args)

    def test_fabricated_chapter_literal_rejected(self):
        args=deepcopy(self.args);args[0]['chapter_routes'][0]['literal']='DMG Chapter 999'
        with self.assertRaisesRegex(ValueError,'lacks source support'):compile_restoration(*args)

    def test_registered_inputs_and_projection_are_bound(self):
        result,ledger=project(Inputs(ROOT),*self.args[1:4])
        self.assertEqual(result,self.result);self.assertEqual(ledger,self.ledger)

    def test_duplicate_scopes_and_guards_rejected(self):
        args=deepcopy(self.args);args[0]['scope_records'].append(args[0]['scope_records'][0])
        with self.assertRaisesRegex(ValueError,'Duplicate custody scope'):compile_restoration(*args)
        for field in ('dependencies','chapter_routes'):
            args=deepcopy(self.args);args[0][field][0]['when_all']*=2
            with self.assertRaisesRegex(ValueError,'duplicate custody'):compile_restoration(*args)

    def test_source_selection_caveat_is_visible_to_consumer(self):
        requirements={r['id']:r for r in self.result['requirements']}
        edges={r['id']:r for r in self.result['assertions']}
        for profile in self.args[0]['profiles']:
            requirement=requirements[profile['id']]
            self.assertIn(profile['source_read_note'],requirement['scope'])
            for path in requirement['required_paths']:
                self.assertIn(profile['source_read_note'],edges[path['assertions'][0]]['scope'])

    def test_paired_metadata_hash_rewrite_cannot_change_source_text(self):
        args=deepcopy(self.args);record=args[2][0];record['text']+=' forged'
        sha=digest(canonical(record));args[3][record['id']]['record_sha256']=sha
        next(r for r in args[0]['source_units'] if r['id']==record['id'])['record_sha256']=sha
        with self.assertRaisesRegex(ValueError,'text differs from catalogue'):compile_restoration(*args)
        args[3][record['id']]['text']=record['text']
        with self.assertRaisesRegex(ValueError,'differs from original source spans'):compile_restoration(*args)

    def test_changed_extraction_bytes_rejected(self):
        args=deepcopy(self.args);sha=next(iter(args[5]));args[5][sha]+=b' '
        with self.assertRaisesRegex(ValueError,'extraction bytes differ'):compile_restoration(*args)


if __name__=='__main__':unittest.main()
