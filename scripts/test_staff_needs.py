import copy
import json
from pathlib import Path
import unittest
from build_staff_needs import build

ROOT = Path(__file__).resolve().parents[1]


class StaffNeedsTests(unittest.TestCase):
    def setUp(self):
        self.spec = json.loads((ROOT / 'domain-profile/staff-needs/journeys.json').read_text())
        self.questions = json.loads((ROOT / 'evaluation/staff-questions/cases.json').read_text())

    def test_all_occurrences_keep_unreviewed_status(self):
        result = build(self.spec, self.questions)
        self.assertEqual(result['occurrences'], 40)
        self.assertEqual(result['unique_questions'], 39)
        self.assertTrue(all(c['user_validation'] == 'not-run' for c in result['cases']))

    def test_missing_question_is_rejected(self):
        self.spec['journeys'][0]['cases'].pop()
        with self.assertRaisesRegex(ValueError, 'no primary journey'):
            build(self.spec, self.questions)

    def test_duplicate_assignment_is_rejected(self):
        self.spec['journeys'][1]['cases'].append('staff-001')
        with self.assertRaisesRegex(ValueError, 'multiply assigned'):
            build(self.spec, self.questions)

    def test_duplicate_registry_identity_is_rejected(self):
        self.questions['cases'].append(copy.deepcopy(self.questions['cases'][0]))
        with self.assertRaisesRegex(ValueError, 'occurrence'):
            build(self.spec, self.questions)

    def test_unknown_cross_cutting_persona_is_rejected(self):
        self.spec['cross_cutting_journeys'][0]['personas'].append('persona/invented')
        with self.assertRaisesRegex(ValueError, 'Unknown journey persona'):
            build(self.spec, self.questions)

    def test_duplicate_persona_is_rejected(self):
        self.spec['personas'].append(copy.deepcopy(self.spec['personas'][0]))
        with self.assertRaisesRegex(ValueError, 'Duplicate persona'):
            build(self.spec, self.questions)

    def test_duplicate_journey_identity_is_rejected(self):
        self.spec['cross_cutting_journeys'][0]['id'] = self.spec['journeys'][0]['id']
        with self.assertRaisesRegex(ValueError, 'Duplicate journey'):
            build(self.spec, self.questions)

    def test_unknown_persona_is_rejected(self):
        self.spec['journeys'][0]['personas'].append('persona/invented')
        with self.assertRaisesRegex(ValueError, 'Unknown journey persona'):
            build(self.spec, self.questions)

    def test_changed_duplicate_question_is_rejected(self):
        q = next(c for c in self.questions['cases'] if c['duplicate_of'])
        q['question'] += ' changed'
        with self.assertRaises(ValueError):
            build(self.spec, self.questions)


if __name__ == '__main__':
    unittest.main()
