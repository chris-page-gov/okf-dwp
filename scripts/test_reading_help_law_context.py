"""Admission must preserve frozen requirements and abstain on unsupported citations."""
import json
import unittest
from unittest.mock import patch
import build_reading_help_law_context as context

class AdmissionTests(unittest.TestCase):
    def test_preserves_baseline_records_requirements_and_territorial_variants(self):
        outputs=context.build();before=context.load(context.ROOT,context.BASELINE)
        index=json.loads(outputs[context.AUTHORING+'/assembly-index.json']);records={r['id']:r for r in index['records']}
        self.assertEqual(before['requirements'],index['requirements'])
        for row in before['records']:self.assertEqual(records[row['id']],row)
        variants=[r for r in index['records'] if '/reading-help-law/body/ukpga/1992/4/section/70/' in r['id']]
        self.assertEqual(len(variants),2);self.assertNotEqual(variants[0]['text'],variants[1]['text'])
        self.assertTrue(all(r['rights'] and r['review_status']=='unreviewed' for r in variants))
    def test_unsupported_and_malformed_references_stay_unresolved(self):
        outputs=context.build();h=json.loads(outputs['reading-help-ch60-law.json']);cards={c['id']:c for c in h['cards']}
        for key in ['60033-marker-9','60033-marker-10','60033-marker-11','60033-marker-12','60033-extra-2']:
            self.assertEqual(cards[key]['target']['status'],'unresolved')
        for c in cards.values():
            if c['target'].get('url'):self.assertIn('/2026-09-20#',c['target']['url'])
    def test_nonexistent_structural_target_is_rejected(self):
        original=context.load
        def changed(root,path):
            value=original(root,path)
            if path==context.AUTHORING+'/citation-admission.json':value['mappings'][0]['structural_id']='invented'
            return value
        with patch.object(context,'load',side_effect=changed):
            with self.assertRaisesRegex(ValueError,'No retained source target'):context.build()

if __name__=='__main__':unittest.main()
