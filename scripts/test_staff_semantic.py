"""Control stale sources, fabricated governance, missing profiles and alias regressions."""
from copy import deepcopy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from build_bundle import ROOT, digest, load_yaml
from build_staff_semantic import AUTHORING, OUTPUT, BASE_INDEX, compile_staff_semantic


class StaffSemanticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.outputs=compile_staff_semantic()
        cls.index=json.loads(cls.outputs[OUTPUT+'assembly-index.json'])
        cls.catalogue=json.loads(cls.outputs[OUTPUT+'catalogue.json'])
        cls.profiles=json.loads(cls.outputs[OUTPUT+'profiles.json'])

    def test_reproducible_and_additive(self):
        for name,raw in self.outputs.items():self.assertEqual((ROOT/name).read_bytes(),raw)
        old=json.loads((ROOT/BASE_INDEX).read_bytes())
        self.assertLess(len(self.outputs[OUTPUT+'assembly-index.json']),4*1024*1024)
        self.assertTrue({r['id'] for r in old['records']} <= {r['id'] for r in self.index['records']})
        self.assertTrue({r['id'] for r in old['assertions']} <= {r['id'] for r in self.index['assertions']})
        old_evidence={r['id']:r for r in old['records'] if r['kind']=='evidence'}
        now={r['id']:r for r in self.index['records']}
        for key,row in old_evidence.items():self.assertEqual(row,now[key])

    def test_all_source_pages_bound_to_exact_pdf_and_text(self):
        records={r['id']:r for r in self.index['records']}
        self.assertIn('adm',{p['family'] for p in self.catalogue['source_pages']})
        for binding in self.catalogue['source_pages']:
            raw=(ROOT/binding['pages_path']).read_bytes()
            self.assertEqual(digest(raw),binding['pages_sha256'])
            page=json.loads(raw)['pages'][binding['page']-1]
            self.assertEqual(page['url'],binding['source_url'])
            self.assertEqual(records[binding['id']]['text'],page['text'])
            self.assertEqual(digest(page['text'].encode()),binding['literal_sha256'])
            self.assertEqual(records[binding['id']]['assertion_status'],'normalized')

    def test_every_occurrence_and_duplicate_preserved(self):
        registry=json.loads((ROOT/'evaluation/staff-questions/cases.json').read_bytes())
        self.assertEqual(len(self.profiles['profiles']),40)
        self.assertEqual(len({p['question'] for p in self.profiles['profiles']}),39)
        for case,profile in zip(registry['cases'],self.profiles['profiles']):
            for k in ('id','question','duplicate_of','candidate_ids','ambiguities','required_evidence'):
                self.assertEqual(case[k],profile[k])

    def test_obligations_are_labelled_absence_not_evidence(self):
        ids={r['id'] for r in self.index['records']}
        obligations={r['@id']:r for r in self.profiles['obligations']}
        for p in self.profiles['profiles']:
            self.assertEqual(p['evidence_status'],'insufficient')
            self.assertTrue(p['obligation_ids'])
            for iri in p['obligation_ids']:
                self.assertNotIn(iri,ids)
                self.assertFalse(obligations[iri]['is_source_evidence'])
                self.assertTrue(obligations[iri]['category'])
                self.assertTrue(obligations[iri]['resolution'])

    def test_source_backed_meanings_never_promoted(self):
        rows={r['id']:r for r in self.index['records']}
        assertions={r['id']:r for r in self.index['assertions']}
        for c in self.catalogue['concepts']:
            self.assertEqual(c['assertion_status'],'model-derived')
            self.assertTrue(c['evidence_ids'])
            self.assertTrue(all(rows[i]['kind']=='evidence' for i in c['evidence_ids']))
        for i in self.catalogue['new_assertion_ids']:
            self.assertEqual(assertions[i]['assertion_status'],'model-derived')
            self.assertEqual(assertions[i]['authority']['class'],'model-assisted')
            self.assertGreater(len(assertions[i]['provenance']),1)

    def test_legal_links_are_not_substantive_evidence(self):
        rows={r['id']:r for r in self.index['records']}
        self.assertEqual(len(self.catalogue['legal_reference_ids']),44)
        self.assertEqual(len(self.catalogue['legal_assertion_ids']),62)
        required={i for r in self.index['requirements'] for i in r['required']}
        for identifier in self.catalogue['legal_reference_ids']:
            self.assertEqual(rows[identifier]['kind'],'scope')
            self.assertEqual(rows[identifier]['review_status'],'reference-only-unreviewed')
            self.assertNotIn(identifier,required)
            self.assertIn('statutory text and applicability are not established',rows[identifier]['text'])

    def test_scope_compaction_preserves_specialised_scopes(self):
        old={r['id']:r for r in json.loads((ROOT/BASE_INDEX).read_bytes())['assertions']}
        current={r['id']:r for r in self.index['assertions']}
        compact=self.catalogue['scope_compaction']
        for identifier,row in old.items():
            if identifier in compact['assertion_ids']:
                self.assertEqual(row['scope'],compact['before'])
                expected=deepcopy(row);expected['scope']=compact['after']
                self.assertEqual(expected,current[identifier])
            else:self.assertEqual(row,current[identifier])

    def test_rejects_alias_reassignment_of_absent_phrase(self):
        self.mutate_authoring('concepts.yamlld',lambda d:d['alias_reassignments']['term/pc-prisoner-credit-rates'].append('invented phrase'),'Alias reassignment must exactly match')

    def mutate_authoring(self,filename,mutate,message):
        original=load_yaml
        def changed(path):
            result=deepcopy(original(path))
            if Path(path)==ROOT/AUTHORING/filename:mutate(result)
            return result
        with patch('build_staff_semantic.load_yaml',changed):
            with self.assertRaisesRegex(ValueError,message):compile_staff_semantic()

    def test_rejects_invented_source_anchor(self):
        self.mutate_authoring('concepts.yamlld',lambda d:next(x for x in d['@graph'] if x.get('additional_sources'))['additional_sources'][0].update(anchor='unrepresented invented anchor'),'Source anchor absent')

    def test_rejects_removed_case(self):
        self.mutate_authoring('profiles.yamlld',lambda d:d['profiles'].pop(),'cover all question')

    def test_rejects_unknown_trigger(self):
        self.mutate_authoring('profiles.yamlld',lambda d:d['profiles'][0]['when_all'].append('invented'),'Unknown/duplicate profile trigger')

    def test_rejects_fake_completed_review(self):
        self.mutate_authoring('profiles.yamlld',lambda d:d['profiles'][0]['obligations'][0].update(status='official-approved'),'Unknown or promoted obligation')

    def test_rejects_silent_review_gate_removal(self):
        self.mutate_authoring('profiles.yamlld',lambda d:d['profiles'][0].update(obligations=[o for o in d['profiles'][0]['obligations'] if o['category']!='independent_review_pending']),'silently close independent review')

    def test_rejects_official_authority(self):
        self.mutate_authoring('concepts.yamlld',lambda d:d.update(assertion_status='official'),'cannot acquire official authority')

    def test_rejects_changed_frozen_extraction(self):
        target=ROOT/self.catalogue['source_pages'][0]['pages_path'];original=Path.read_bytes
        def changed(path):
            raw=original(path)
            return raw+b' ' if path==target else raw
        with patch.object(Path,'read_bytes',changed):
            with self.assertRaisesRegex(ValueError,'Input digest mismatch'):compile_staff_semantic()


if __name__=='__main__':unittest.main()
