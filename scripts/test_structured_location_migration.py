"""Location migration is navigation, never a silently satisfied requirement."""
from copy import deepcopy
import gzip
import json
from pathlib import Path
import unittest

from build_bundle import BASE, canonical, digest
from build_logical_units import Inputs
from structured_location_migration import AUTHORING, compile_migration, decode_profiles, project

ROOT=Path(__file__).resolve().parents[1]


def fixture():
    policy=json.loads((ROOT/AUTHORING).read_text())
    legacy=json.loads((ROOT/policy['legacy_index']['path']).read_text())
    profiles=decode_profiles((ROOT/policy['legacy_profiles']['path']).read_bytes())
    candidates={r['id']:json.loads((ROOT/r['path']).read_text()) for r in policy['candidates']}
    pages={k:json.loads((ROOT/c['provenance']['pages_path']).read_text()) for k,c in candidates.items()}
    source_locations={}
    for c in candidates.values(): source_locations.setdefault(c['document_id'],set()).add(c['provenance']['page'])
    manifest=json.loads((ROOT/'structured-units/manifest.json').read_text())
    units={}
    for ref in manifest['documents']:
        if ref['document_id'] not in source_locations:continue
        raw=(ROOT/'structured-units'/ref['path']).read_bytes();assert digest(raw)==ref['sha256']
        decoded=gzip.decompress(raw);assert digest(decoded)==ref['decoded_sha256']
        for unit in json.loads(decoded)['units']:
            if any(s['page'] in source_locations[ref['document_id']] for s in unit['spans']):units[unit['id']]=unit
    rows=[]
    for ref in manifest['records']['shards']:
        if not any(ref['first_id']<=i<=ref['last_id'] for i in units):continue
        raw=(ROOT/'structured-units'/ref['path']).read_bytes();assert digest(raw)==ref['sha256']
        decoded=gzip.decompress(raw);assert digest(decoded)==ref['decoded_sha256']
        rows.extend(r for r in json.loads(decoded)['records'] if r['id'] in units)
    # The earlier logical projection is frozen and carries its complete
    # inherited graph. The v3 base alone deliberately has no assertions.
    frozen=json.loads((ROOT/'logical-context/manifest.json').read_text())
    raw=(ROOT/'logical-context'/frozen['base_index']['path']).read_bytes()
    assert digest(raw)==frozen['base_index']['sha256']
    semantic=json.loads(raw)
    return policy,semantic,legacy,profiles,candidates,pages,rows,units


class LocationMigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.args=fixture();cls.result,cls.ledger=compile_migration(*cls.args)

    def test_exact_old_requirements_and203_obligations_stay_unclosed(self):
        before=self.args[1];legacy=self.args[2]
        self.assertEqual(self.result['requirements'][:len(before['requirements'])],before['requirements'])
        self.assertEqual(self.result['requirements'][len(before['requirements']):],legacy['requirements'])
        obligations=[i for r in legacy['requirements'] for i in r['required'] if '/obligation/staff/' in i]
        self.assertEqual(len(set(obligations)),203)
        self.assertFalse(set(obligations).intersection(r['id'] for r in self.result['records']+self.args[6]))
        self.assertEqual(self.ledger['counts']['requirements_closed_by_migration'],0)

    def test_old_required_path_ids_are_never_replaced_with_new_navigation(self):
        old={i for r in self.args[2]['requirements'] for p in r['required_paths'] for i in p['assertions']}
        new={e['id'] for e in self.result['assertions'] if '/assertion/location-migration/' in e['id']}
        self.assertTrue(old.isdisjoint(new))
        self.assertFalse(any(i.startswith(BASE+'id/unit/') for r in self.args[2]['requirements'] for i in r['required']))

    def test_full_unit_cross_page_example_retained_separately_from_old_excerpt(self):
        mapping=next(r for r in self.ledger['source_maps'] if r['candidate_id']=='source-c002')
        self.assertEqual(mapping['status'],'location-fully-mapped')
        self.assertEqual(len(mapping['new_units']),1)
        unit=mapping['new_units'][0]
        self.assertEqual({s['page'] for s in unit['spans']},{8,9})
        record=next(r for r in self.args[6] if r['id']==unit['id'])
        self.assertIn('Nicola',record['text'])
        self.assertEqual(unit['boundary_status'],'author-declared')
        self.assertEqual(mapping['requirement_support'],'not-established')

    def test_unicode_offsets_are_converted_without_changing_source_bytes(self):
        for m in self.ledger['source_maps']:
            c=self.args[4][m['candidate_id']];p=self.args[5][m['candidate_id']]
            text=next(r['text'] for r in p['pages'] if r['page']==c['provenance']['page'])
            extent=m['utf8_location']
            self.assertEqual(text.encode()[extent['start_utf8']:extent['end_utf8']],c['excerpt']['text'].encode())
            self.assertEqual(m['mapped_bytes']+sum(s['end_utf8']-s['start_utf8'] for s in m['unmapped_spans']),m['location_bytes'])
        partial=[m for m in self.ledger['source_maps'] if m['status']!='location-fully-mapped']
        self.assertEqual({m['candidate_id'] for m in partial},{'source-c011','source-c031','source-c041'})
        self.assertTrue(all(s['whitespace_only'] for m in partial for s in m['unmapped_spans']))

    def test_guards_bind_each_original_scope_without_adding_seeds(self):
        rows={r['requirement_id']:r for r in self.ledger['profiles']}
        edges={r['id']:r for r in self.result['assertions']}
        for req in self.args[2]['requirements']:
            for nav in rows[req['id']]['navigation_routes']:
                edge=edges[nav['assertion_id']]
                self.assertEqual(edge['context_guard'],{'when_all':req['when_all']})
                self.assertIn(nav['seed'],req['when_all'])
                self.assertEqual(edge['source'],nav['records'][-2])
                self.assertEqual(edge['assertion_status'],'model-derived')
                self.assertEqual(edge['authority']['class'],'model-assisted')
                self.assertIn('neither semantic equivalence nor applicability',edge['scope'])
                self.assertEqual(nav['support_status'],'navigation-only')

    def test_missing_old_routes_stay_visible_alongside_inferred_navigation(self):
        missing=[m for r in self.ledger['profiles'] for m in r['missing_original_routes']]
        self.assertEqual(len(missing),28)
        self.assertTrue(all(m['status']=='no-original-profile-route' for m in missing))
        routes=[n for r in self.ledger['profiles'] for n in r['navigation_routes']]
        inferred=[n for n in routes if n['derivation']=='inferred-profile-candidate-route']
        self.assertTrue(inferred)
        self.assertTrue(all(n['original_assertion_ids']==[] and n['support_status']=='navigation-only' for n in inferred))
        self.assertTrue(any(n['derivation']=='restored-original-route' and len(n['records'])>2 for n in routes))

    def test_absent_original_prefix_is_reported_and_not_claimed_as_restored(self):
        args=list(self.args);args[1]=deepcopy(args[1]);args[1]['assertions']=[]
        result,ledger=compile_migration(*args)
        self.assertEqual(ledger['counts']['unresolved_original_prefixes'],25)
        self.assertTrue(all(len(n['records'])==2 for p in ledger['profiles'] for n in p['navigation_routes']))
        self.assertTrue(all(not p['route_emitted'] for r in ledger['profiles'] for p in r['unresolved_original_prefixes']))
        self.assertEqual(result['requirements'][-40:],self.args[2]['requirements'])

    def test_missing_source_unit_is_visible_without_deleting_old_requirement(self):
        args=list(self.args);args[6]=[];args[7]={}
        result,ledger=compile_migration(*args)
        self.assertEqual(ledger['counts']['locations_unresolved_or_partial'],42)
        self.assertEqual(ledger['counts']['location_navigation_assertions'],0)
        self.assertEqual(result['requirements'][-40:],self.args[2]['requirements'])

    def test_changed_source_hash_excerpt_and_record_are_rejected(self):
        for variant in ('pdf','excerpt','record','consistent-record-tamper','overlap','obligation'):
            args=list(self.args)
            if variant in ('pdf','excerpt'):
                args[4]=deepcopy(args[4]);c=args[4]['source-c002']
                if variant=='pdf':c['provenance']['source_sha256']='f'*64
                else:c['excerpt']['text']+='changed'
            elif variant=='record':
                args[6]=deepcopy(args[6]);args[6][0]['scope']+='changed'
            elif variant=='consistent-record-tamper':
                args[6]=deepcopy(args[6]);args[7]=deepcopy(args[7])
                record=next(r for r in args[6] if args[7][r['id']]['paragraph_labels']==['077001'])
                record['text']+=' invented text';args[7][record['id']]['record_sha256']=digest(canonical(record))
            elif variant=='overlap':
                args[7]=deepcopy(args[7]);r=next(r for r in args[7].values() if r['paragraph_labels']==['077001']);r['spans'][0]['end_utf8']-=1
            else:
                args[2]=deepcopy(args[2]);r=args[2]['requirements'][0];r['required']=[i for i in r['required'] if '/obligation/staff/' not in i]
            with self.subTest(variant=variant),self.assertRaises(ValueError):compile_migration(*args)

    def test_weakened_policy_cannot_promote_overlap_or_close_obligations(self):
        for key in ('substitute_old_required_ids','close_obligations','promote_boundary_review'):
            args=list(self.args);args[0]=deepcopy(args[0]);args[0]['controls'][key]=True
            with self.subTest(key=key),self.assertRaises(ValueError):compile_migration(*args)

    def test_duplicate_application_fails_instead_of_doubling_requirements(self):
        args=list(self.args);args[1]=self.result
        with self.assertRaises(ValueError):compile_migration(*args)

    def test_registered_wrapper_binds_all_consumed_sources(self):
        inputs=Inputs(ROOT)
        result,ledger=project(inputs,self.args[1],self.args[6],self.args[7])
        self.assertEqual(result,self.result);self.assertEqual(ledger,self.ledger)
        self.assertIn(AUTHORING,inputs.files)
        for c in self.args[4].values():
            self.assertIn(c['provenance']['pages_path'],inputs.files)
            self.assertIn('evaluation/staff-review/evidence/'+c['id']+'.json',inputs.files)


if __name__=='__main__':unittest.main()
