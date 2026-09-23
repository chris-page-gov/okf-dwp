"""Check scoped source selection, without deciding a person's entitlement."""
from copy import deepcopy
import unittest

from build_bundle import BASE
from structured_context_profiles import compile_selection
from test_structured_context_profiles import fixture, active

PATH = 'domain-profile/structured-units/state-pension-routing.yamlld'
SP = BASE + 'id/staff-domain/state-pension'
AGE = BASE + 'id/staff-domain/pension-age'
ELIGIBILITY = BASE + 'id/staff-domain/eligibility'


class StatePensionSelectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.args = fixture(PATH)
        cls.result = compile_selection(*cls.args, authoring_path=PATH)
        cls.units = {u['key']: next(r for r in cls.args[2] if r['id'] == u['id'])
                     for u in cls.args[0]['source_units']}

    def test_age_does_not_become_entitlement_or_an_award_calculation(self):
        self.assertEqual(len(active(self.result, [SP])), 1)
        profiles = active(self.result, [SP, AGE])
        self.assertEqual(len(profiles), 2)
        self.assertEqual(active(self.result, [AGE]), [])
        age = next(p for p in profiles if p['id'].endswith('/state-pension-age'))
        self.assertTrue(any(x.endswith('/entitlement-not-age') for x in age['required']))
        self.assertIn('Do not calculate an individual entitlement', age['scope'])
        self.assertEqual([s['source_url'].rsplit('#page=', 1)[-1]
                          for s in self.units['dmg-74022']['evidence_unit']['spans']], ['3', '4'])

    def test_appendix_keeps_cohort_and_end_of_month_qualification(self):
        text = self.units['dmg-74-appendix-3']['text']
        self.assertIn('6.4.60 to 5.3.61', text)
        self.assertIn('66 years and 2 months', text)
        self.assertIn('31.7.60 reaches pensionable age on 30.11.26', text)
        self.assertIn('Sch 4', text)
        profile = next(p for p in self.result['requirements'] if p['id'].endswith('/state-pension-age'))
        for i in range(1, 5):
            unit = self.units[f'dmg-74-appendix-{i}']
            self.assertIn(unit['id'], profile['required'])
            self.assertIn(f'Appendix {i}', unit['text'])

    def test_qualification_retains_branch_scope_and_referenced_exception(self):
        profiles = active(self.result, [SP, ELIGIBILITY])
        p = next(x for x in profiles if x['id'].endswith('/state-pension-qualification'))
        for key in ('dmg-74101', 'dmg-74151', 'dmg-74201', 'dmg-74406'):
            self.assertIn(self.units[key]['id'], p['required'])
        self.assertIn('no pre-commencement', self.units['dmg-74101']['text'])
        self.assertIn('no pre-commencement', self.units['dmg-74151']['text'])
        self.assertIn('reduced rate election', self.units['dmg-74406']['text'])
        self.assertTrue(any(x.endswith('/component-calculation') for x in p['required']))

    def test_ambiguous_sda_and_unnamed_benefit_do_not_acquire_state_pension(self):
        for terms in (['rates'], ['care-home', 'partner'], ['abroad'], ['pip', 'overlap']):
            concepts = [BASE + 'id/staff-domain/' + x for x in terms]
            self.assertEqual(active(self.result, concepts), [])
            self.assertFalse(any(e['source'] in concepts and
                                 set(e.get('context_guard', {}).get('when_all', [])) <= set(concepts)
                                 for e in self.result['assertions']
                                 if '/assertion/structured-selection/' in e['id']))

    def test_changed_table_source_fails_closed_and_inherited_semantics_unchanged(self):
        self.assertEqual(self.result['records'], self.args[1]['records'])
        self.assertEqual(self.result['requirements'][:len(self.args[1]['requirements'])],
                         self.args[1]['requirements'])
        args = deepcopy(self.args)
        table = next(r for r in args[2] if r['id'] == self.units['dmg-74-appendix-3']['id'])
        table['text'] = table['text'].replace('66 years and 2 months', '66 years')
        with self.assertRaises(ValueError):
            compile_selection(*args, authoring_path=PATH)

    def test_pip_comparison_reuses_exact_authored_units_without_upgrading_them(self):
        pip = BASE + 'id/staff-domain/pip'
        profiles = active(self.result, [SP, pip])
        comparison = next(p for p in profiles if p['id'].endswith('/state-pension-pip-scope'))
        self.assertTrue(any(x.endswith('/overlapping-payment') for x in comparison['required']))
        self.assertEqual(active(self.result, [pip]), [])
        for key in ('adm-p1011', 'adm-p1013', 'adm-p4076-4086'):
            source = self.units[key]
            self.assertIn(source['id'], comparison['required'])
            self.assertEqual(source['evidence_unit']['boundary_status'], 'author-declared')
            self.assertEqual(source['evidence_unit']['completeness'], 'complete-within-declared-boundary')
            self.assertEqual(source['authority']['class'], 'derived')
        self.assertIn('P4080 3.1 or 3.2', self.units['adm-p4076-4086']['text'])

    def test_paired_record_hash_changes_cannot_replace_source_text(self):
        from build_bundle import canonical, digest
        for replace_text_hash in (False, True):
            args = deepcopy(self.args)
            entry = next(x for x in args[0]['source_units'] if x['key'] == 'adm-p1013')
            record = next(x for x in args[2] if x['id'] == entry['id'])
            record['text'] = record['text'].replace('age 16 or over', 'age 18 or over')
            entry['record_sha256'] = digest(canonical(record))
            args[3][entry['id']]['record_sha256'] = entry['record_sha256']
            if replace_text_hash:
                args[3][entry['id']]['text'] = record['text']
                args[3][entry['id']]['text_sha256'] = digest(record['text'].encode())
            with self.subTest(replace_text_hash=replace_text_hash), self.assertRaises(ValueError):
                compile_selection(*args, authoring_path=PATH)

    def test_unbound_suffix_is_rejected_even_with_rehashed_catalogue_text(self):
        from build_bundle import canonical, digest
        args = deepcopy(self.args)
        entry = next(x for x in args[0]['source_units'] if x['key'] == 'adm-p1013')
        record = next(x for x in args[2] if x['id'] == entry['id'])
        record['text'] += 'Invented unbound conclusion.'
        entry['record_sha256'] = digest(canonical(record))
        unit = args[3][entry['id']]
        unit.update(record_sha256=entry['record_sha256'], text=record['text'],
                    text_sha256=digest(record['text'].encode()))
        with self.assertRaises(ValueError):
            compile_selection(*args, authoring_path=PATH)

    def test_source_selection_cannot_convert_an_authored_unit_to_machine_or_upgrade_a_boundary(self):
        for change in ('catalogue-origin', 'boundary', 'completeness'):
            args = deepcopy(self.args)
            entry = next(x for x in args[0]['source_units'] if x['key'] == 'adm-p1013')
            if change == 'catalogue-origin':
                args[3][entry['id']]['authored'] = False
            elif change == 'boundary':
                entry['boundary_status'] = 'machine-detected'
            else:
                entry['boundary_completeness'] = 'complete'
            with self.subTest(change=change), self.assertRaises(ValueError):
                compile_selection(*args, authoring_path=PATH)


if __name__ == '__main__':
    unittest.main()
