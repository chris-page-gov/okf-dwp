"""Source-bound selection admission controls, separate from answer quality."""
from copy import deepcopy
import gzip
import json
from pathlib import Path
import unittest

from build_bundle import BASE, canonical, digest
from structured_context_profiles import AUTHORING, compile_selection

ROOT = Path(__file__).resolve().parents[1]
PC = BASE + 'id/term/pension-credit'
CAPITAL = BASE + 'id/term/capital'
CALCULATION = BASE + 'id/staff-domain/calculation'
ELIGIBILITY = BASE + 'id/staff-domain/eligibility'
STATE_PENSION = BASE + 'id/staff-domain/state-pension'


def fixture(authoring_path=AUTHORING):
    author = json.loads((ROOT / authoring_path).read_text())
    manifest = json.loads((ROOT / 'structured-units/manifest.json').read_text())
    old_manifest=json.loads((ROOT/'logical-context/manifest.json').read_text())
    old_raw=(ROOT/'logical-context'/old_manifest['base_index']['path']).read_bytes()
    assert digest(old_raw)==old_manifest['base_index']['sha256']
    semantic=json.loads(old_raw)
    selected = {r['id'] for r in author['source_units']}
    records = []
    for binding in manifest['records']['shards']:
        if not any(binding['first_id'] <= identifier <= binding['last_id'] for identifier in selected):
            continue
        raw = (ROOT / 'structured-units' / binding['path']).read_bytes()
        if digest(raw) != binding['sha256']:
            raise ValueError('Source record shard identity differs')
        records.extend(r for r in json.loads(gzip.decompress(raw))['records'] if r['id'] in selected)
    catalogue = {}
    for entry in author['source_units']:
        key = entry['document_id']
        if not any(r['document_id'] == key for r in catalogue.values()):
            raw = (ROOT / 'structured-units/documents' / entry['family'] / (key + '.json.gz')).read_bytes()
            for row in json.loads(gzip.decompress(raw))['units']:
                if row['id'] in selected:
                    catalogue[row['id']] = {**row, 'document_id': key}
    return author, semantic, records, catalogue


def active(result, concepts):
    return [r for r in result['requirements'] if r['id'].startswith(BASE + 'id/requirement/structured/') and set(r['when_all']) <= set(concepts)]


class StructuredSelectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.args = fixture()
        cls.result = compile_selection(*cls.args)

    def test_inherited_concepts_requirements_and_source_units_are_unchanged(self):
        before = deepcopy(self.args)
        result = compile_selection(*self.args)
        self.assertEqual(before, self.args)
        self.assertEqual(result['records'], self.args[1]['records'])
        self.assertEqual(result['requirements'][:len(self.args[1]['requirements'])], self.args[1]['requirements'])
        self.assertEqual(result['assertions'][:len(self.args[1]['assertions'])], self.args[1]['assertions'])
        self.assertEqual(len([r for r in result['records'] if r['kind'] == 'concept']), 331)
        self.assertTrue(all(r['evidence_unit']['boundary_status'] == 'machine-detected' for r in self.args[2]))

    def test_pc_gateway_and_narrower_scopes_use_declared_concepts(self):
        self.assertEqual([r['label'] for r in active(self.result, [PC])], ['Pension Credit: introductory entitlement and component context'])
        for concept in (CAPITAL, CALCULATION, ELIGIBILITY, STATE_PENSION):
            profiles = active(self.result, [PC, concept])
            self.assertEqual(len(profiles), 2)
            self.assertTrue(any(r['when_all'] == [PC, concept] for r in profiles))

    def test_unrelated_benefits_do_not_activate_pc_requirements(self):
        for concepts in ([BASE+'id/staff-domain/universal-credit', CAPITAL], [BASE+'id/staff-domain/pip', CALCULATION], [STATE_PENSION], [ELIGIBILITY]):
            self.assertEqual(active(self.result, concepts), [])

    def test_pc_abroad_and_care_home_do_not_gain_task_specific_closure(self):
        for other in ('abroad', 'care-home'):
            profiles = active(self.result, [PC, BASE+'id/staff-domain/'+other])
            self.assertEqual(len(profiles), 1)
            profile = profiles[0]
            self.assertIn('does not cover its absence, care-home', profile['scope'])
            self.assertTrue(any('task-scope' in identifier for identifier in profile['required']))
            self.assertTrue(any('Foundation evidence never satisfies temporary absence' in text for text in profile['limitations']))

    def test_all_new_requirements_retain_absent_obligations(self):
        known = {r['id'] for r in self.args[2] + self.result['records']}
        for profile in self.result['requirements']:
            if '/requirement/structured/' not in profile['id']:
                continue
            missing = [r for r in profile['required'] if r not in known]
            self.assertGreaterEqual(len(missing), 5)
            self.assertTrue(all('/obligation/structured/' in r for r in missing))
            self.assertTrue(any('specialist' in r for r in missing))

    def test_required_paths_have_exact_derived_source_and_scoped_assertions(self):
        edges = {r['id']:r for r in self.result['assertions']}
        for profile in self.result['requirements']:
            if '/requirement/structured/' not in profile['id']:
                continue
            for path in profile['required_paths']:
                edge = edges[path['assertions'][0]]
                self.assertEqual(path['records'], [edge['source'], edge['target']])
                self.assertEqual(edge['source'], profile['when_all'][-1])
                self.assertEqual(edge['context_guard'], {'when_all': profile['when_all']})
                self.assertIn(profile['scope'], edge['scope'])
                self.assertEqual(edge['predicate'], 'http://purl.org/dc/terms/references')
                self.assertEqual(edge['assertion_status'], 'model-derived')
                self.assertEqual(edge['authority']['class'], 'model-assisted')
                source = next(r for r in self.args[2] if r['id'] == edge['target'])
                self.assertEqual(edge['provenance'], source['provenance'])
                self.assertIn('not a legal prerequisite', edge['scope'])

    def test_cross_benefit_routes_require_all_declared_concepts(self):
        # Producer assertion contract only: actual engine traversal has separate
        # guarded-path integration controls. A matching requirement alone never
        # makes the edge eligible.
        edges = [r for r in self.result['assertions'] if '/assertion/structured-selection/' in r['id']]
        for other in ([BASE+'id/staff-domain/universal-credit', CAPITAL],
                      [BASE+'id/staff-domain/pip', CALCULATION], [STATE_PENSION], [ELIGIBILITY]):
            self.assertFalse(any(e['source'] in other and set(e['context_guard']['when_all']) <= set(other) for e in edges))
        for topic in (CAPITAL, CALCULATION, ELIGIBILITY, STATE_PENSION):
            self.assertTrue(any(e['source'] == topic and set(e['context_guard']['when_all']) <= {PC,topic} for e in edges))

    def test_distinct_conjunctions_do_not_collapse_into_one_assertion(self):
        args = deepcopy(self.args)
        profile = deepcopy(args[0]['profiles'][2])
        profile['id'] += '-different-guard'
        profile['when_all'] = [PC, ELIGIBILITY, CAPITAL]
        profile['covers'] = [PC, CAPITAL]
        args[0]['profiles'].append(profile)
        result = compile_selection(*args)
        paths = result['requirements'][-1]['required_paths']
        old = next(r for r in result['requirements'] if r['id'].endswith('/pc-capital'))['required_paths']
        self.assertTrue(set(p['assertions'][0] for p in paths).isdisjoint(p['assertions'][0] for p in old))

    def test_same_trigger_and_unit_preserve_distinct_profile_scope(self):
        args = deepcopy(self.args)
        profile = deepcopy(args[0]['profiles'][2]); profile['id'] += '-different-scope'
        profile['scope'] = 'Separate research-selection scope; legal applicability not established.'
        args[0]['profiles'].append(profile)
        result = compile_selection(*args)
        edges = {r['id']:r for r in result['assertions']}
        old = next(r for r in result['requirements'] if r['id'].endswith('/pc-capital'))
        new = result['requirements'][-1]
        self.assertTrue(set(p['assertions'][0] for p in old['required_paths']).isdisjoint(p['assertions'][0] for p in new['required_paths']))
        self.assertTrue(all(profile['scope'] in edges[p['assertions'][0]]['scope'] for p in new['required_paths']))

    def test_local_context_and_authoring_identity_are_closed(self):
        for field,value in (('@context', {'@vocab':'https://example.invalid/'}), ('@id', BASE+'id/authoring/structured-units/other')):
            args=deepcopy(self.args);args[0][field]=value
            with self.assertRaises(ValueError):compile_selection(*args)

    def test_pc_seed_has_only_small_gateway_not_all_narrower_requirements(self):
        ids = {u['key']:u['id'] for u in self.args[0]['source_units']}
        edges = [r for r in self.result['assertions'] if '/assertion/structured-selection/' in r['id'] and r['source'] == PC]
        self.assertEqual({r['target'] for r in edges}, {ids[k] for k in ('dmg-77031','dmg-77300','dmg-77301','dmg-77350')})

    def test_changed_record_or_boundary_fails_closed(self):
        for change in ('record', 'source', 'span', 'label'):
            args = deepcopy(self.args)
            if change == 'record': args[2][0]['scope'] += ' altered'
            elif change == 'source': args[0]['source_units'][0]['source_sha256'] = 'f'*64
            elif change == 'span': args[0]['source_units'][0]['spans'][0]['end_utf8'] -= 1
            else: args[0]['source_units'][0]['paragraph_labels'] = ['99999']
            with self.subTest(change=change), self.assertRaises(ValueError):compile_selection(*args)

    def test_authority_boundary_or_answerability_upgrade_fails_closed(self):
        for mutate in (lambda a:a[0].update(assertion_status='official'),
                       lambda a:a[0]['source_units'][0].update(boundary_status='author-declared'),
                       lambda a:a[0]['profiles'][0].update(answerability='sufficient'),
                       lambda a:a[0]['profiles'][0].update(missing_obligations=[])):
            args=deepcopy(self.args);mutate(args)
            with self.assertRaises(ValueError):compile_selection(*args)

    def test_per_file_attribution_and_explicit_registration(self):
        from structured_context_profiles import project
        args = deepcopy(self.args)
        args[0]['@id'] = BASE + 'id/authoring/structured-units/another-slice'
        other = compile_selection(*args, authoring_path='domain-profile/structured-units/another-slice.yamlld')
        new_edges = [r for r in other['assertions'] if '/assertion/structured-selection/' in r['id']]
        self.assertTrue(all(r['authority']['source'].endswith('/another-slice.yamlld') for r in new_edges))
        for paths in ([], ['../private.yamlld'], [AUTHORING, AUTHORING]):
            with self.subTest(paths=paths), self.assertRaises(ValueError):
                project(None, self.args[1], self.args[2], self.args[3], paths)

    def test_explicit_default_registry_combines_pc_and_household_without_source_changes(self):
        from build_logical_units import Inputs
        from structured_context_profiles import AUTHORING_PATHS, project
        household=fixture(AUTHORING_PATHS[1])
        records={r['id']:r for r in self.args[2]+household[2]}
        units={**self.args[3],**household[3]}
        inputs=Inputs(ROOT)
        result=project(inputs,self.args[1],list(records.values()),units)
        self.assertEqual(len(result['requirements'])-len(self.args[1]['requirements']),7)
        self.assertEqual(result['records'],self.args[1]['records'])
        self.assertTrue(all(path in inputs.files for path in AUTHORING_PATHS))
        edges=[e for e in result['assertions'] if '/assertion/structured-selection/' in e['id']]
        self.assertEqual(len(edges),55)
        self.assertTrue(all(e['context_guard']['when_all'] for e in edges))

    def test_unknown_concept_duplicate_requirement_and_closed_obligation_fail(self):
        for mutate in (lambda a:a[0]['profiles'][0].update(when_all=['https://example.invalid/new-concept']),
                       lambda a:a[0]['profiles'].append(deepcopy(a[0]['profiles'][0])),
                       lambda a:a[0]['profiles'][0]['missing_obligations'][0].update(status='resolved')):
            args=deepcopy(self.args);mutate(args)
            with self.assertRaises(ValueError):compile_selection(*args)


if __name__ == '__main__':
    unittest.main()
