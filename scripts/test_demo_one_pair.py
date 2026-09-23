"""Offline source-view and fixed experiment controls; never invokes a provider."""
import copy
import unittest
import demo_one_pair as demo

class DemoOnePairTests(unittest.TestCase):
    def test_every_selected_record_and_source_byte_is_preserved(self):
        for case in demo.CASES:
            name, raw, package = demo.load_package(case)
            view = demo.view_of(package, name, raw)
            self.assertEqual(view['records'], [item['record'] for item in package['selected']])
            self.assertEqual(view['missing_evidence'], package['missing_evidence'])
            self.assertEqual(view['audit_package']['sha256'], demo.identity(raw)['sha256'])
            self.assertTrue(view['budget']['truncated'])
            self.assertTrue(view['retrieval_truncated'])
            self.assertEqual(view['evidence_status'], 'insufficient')
    def test_projection_does_not_mutate_audit(self):
        name, raw, package = demo.load_package('staff-012')
        before = copy.deepcopy(package)
        demo.view_of(package, name, raw)
        self.assertEqual(before, package)
    def test_frozen_scope_and_input_hashes(self):
        protocol = demo.check()
        self.assertEqual(len(protocol['cases']) * len(protocol['arms']), 4)
        self.assertEqual(protocol['tools'], [])
        self.assertEqual(protocol['max_turns'], 1)
    def test_tampering_changes_binding(self):
        name, raw, package = demo.load_package('staff-006')
        self.assertNotEqual(demo.identity(raw), demo.identity(raw + b' '))

if __name__ == '__main__': unittest.main()
