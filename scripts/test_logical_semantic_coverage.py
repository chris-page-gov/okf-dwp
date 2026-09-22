"""Coverage-ledger integrity controls; no model or legal-quality assertions."""
import copy
from pathlib import Path
import tempfile
import unittest

from build_semantic_coverage import canonical_obligations, observed_staff_rows, write_outputs


class SemanticCoverageTests(unittest.TestCase):
    def test_repeated_authored_ids_keep_distinct_canonical_case_identities(self):
        row = {'id': 'source-requirement-1', 'category': 'evidence_closure_unverified',
               'label': 'Source passage still needs review', 'status': 'candidate-evidence-only'}
        outputs = []
        for case in ('staff-001', 'staff-002'):
            expected = 'https://chris-page-gov.github.io/okf-dwp/id/obligation/staff/' + case + '/' + row['category'] + '/' + row['id']
            result = canonical_obligations(case, [row], [expected, 'https://example.org/source'])
            self.assertEqual(result[0]['id'], expected)
            self.assertEqual(result[0]['authored_id'], row['id'])
            self.assertEqual({k: result[0][k] for k in row if k != 'id'},
                             {k: row[k] for k in row if k != 'id'})
            outputs.append(result[0]['id'])
        self.assertNotEqual(*outputs)

    def test_obligation_ids_must_match_the_complete_prior_required_set(self):
        row = {'id': 'source-requirement-1', 'category': 'evidence_closure_unverified'}
        prefix = 'https://chris-page-gov.github.io/okf-dwp/id/obligation/staff/staff-001/'
        expected = prefix + row['category'] + '/' + row['id']
        for required in ([], [expected.replace('staff-001', 'staff-002')],
                         [expected, prefix + 'legal_version_unreconciled/legal-version']):
            with self.subTest(required=required), self.assertRaisesRegex(ValueError, 'recorded required set'):
                canonical_obligations('staff-001', [row], required)
        with self.assertRaisesRegex(ValueError, 'Duplicate canonical'):
            canonical_obligations('staff-001', [row, row], [expected])

    def rows(self):
        return {'rows': [{'case_id': case, 'stage': 'units', 'max_bytes': budget}
                         for case in ('a', 'b') for budget in (32768, 524288)]}

    def test_requires_both_observed_budgets_for_every_case(self):
        summary = self.rows()
        self.assertEqual(len(observed_staff_rows(summary, {'a', 'b'})), 4)
        summary['rows'].pop()
        with self.assertRaisesRegex(ValueError, 'Incomplete retained'):
            observed_staff_rows(summary, {'a', 'b'})

    def test_duplicate_observation_cannot_overwrite_a_case(self):
        summary = self.rows()
        summary['rows'].append(copy.deepcopy(summary['rows'][0]))
        with self.assertRaisesRegex(ValueError, 'Duplicate observed'):
            observed_staff_rows(summary, {'a', 'b'})

    def test_page_results_cannot_stand_in_for_unit_results(self):
        summary = self.rows()
        summary['rows'][0]['stage'] = 'pages'
        with self.assertRaisesRegex(ValueError, 'Incomplete retained'):
            observed_staff_rows(summary, {'a', 'b'})

    def test_writer_preserves_an_existing_observation(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'recorded'
            original = {'audit.json': b'{"value":1}\n', 'audit.md': b'Recorded\n'}
            write_outputs(path, original)
            with self.assertRaises(FileExistsError):
                write_outputs(path, {'audit.json': b'changed'})
            self.assertEqual((path / 'audit.json').read_bytes(), original['audit.json'])
            write_outputs(path, original, check=True)

    def test_check_rejects_drift_and_unlisted_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'recorded'
            original = {'audit.json': b'{}\n', 'audit.md': b'Recorded\n'}
            write_outputs(path, original)
            (path / 'audit.md').write_bytes(b'Changed\n')
            with self.assertRaisesRegex(ValueError, 'output differs'):
                write_outputs(path, original, check=True)
            (path / 'audit.md').write_bytes(original['audit.md'])
            (path / 'unlisted').write_bytes(b'extra')
            with self.assertRaisesRegex(ValueError, 'census differs'):
                write_outputs(path, original, check=True)

    def test_check_refuses_a_symlinked_record(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'recorded'
            original = {'audit.json': b'{}\n'}
            write_outputs(path, original)
            outside = Path(temporary) / 'outside.json'
            outside.write_bytes(original['audit.json'])
            (path / 'audit.json').unlink()
            (path / 'audit.json').symlink_to(outside)
            with self.assertRaisesRegex(ValueError, 'output differs'):
                write_outputs(path, original, check=True)


if __name__ == '__main__':
    unittest.main()
