"""Offline contract controls for logical semantic and Reader projections.

Uses current hash-bound generated files. No browser, provider, network or source
mutation occurs. The fixture census is not a legal completeness measure.
"""
from copy import deepcopy
import json
import unittest

from build_bundle import ROOT, BASE, canonical, digest
from build_logical_units import Inputs
from build_logical_context import decode_shard
from build_full_dmg import bucket
from logical_context_profiles import project

PREFIX = 'domain-profile/logical-units/'
DCT = 'http://purl.org/dc/terms/'


class ReboundInputs:
    """Synthetic mutation of explicit authoring only; no repository writes."""
    def __init__(self, replacements):
        self.real = Inputs(ROOT)
        self.replacements = replacements
        self.files = {}

    def read(self, path, expected_sha=None, expected_size=None, **kw):
        if path not in self.replacements:
            return self.real.read(path, expected_sha, expected_size, **kw)
        raw = canonical(self.replacements[path])
        if expected_sha is not None and digest(raw) != expected_sha:
            raise ValueError('Input hash mismatch')
        if expected_size is not None and len(raw) != expected_size:
            raise ValueError('Input size mismatch')
        self.files[path] = {'path': path, 'bytes': len(raw), 'sha256': digest(raw)}
        return raw


class LogicalContextTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs = Inputs(ROOT)
        cls.manifest = json.loads(cls.inputs.read('logical-units/manifest.json'))
        cls.overrides = json.loads(cls.inputs.read(PREFIX + 'overrides.json'))
        cls.profile_author = json.loads(cls.inputs.read(PREFIX + 'profiles.json'))
        cls.refs = json.loads(cls.inputs.read(PREFIX + 'reference-review.json'))
        cls.catalogue = {}
        docrefs = {(d['family'], d['document_id']): d for d in cls.manifest['documents']}
        for d in cls.overrides['documents']:
            ref = docrefs[(d['family'], d['document_id'])]
            raw = cls.inputs.read('logical-units/' + ref['path'], ref['sha256'], ref['bytes'])
            catalogue = json.loads(decode_shard(raw, ref))
            keys = {u['key'] for u in d['units']}
            cls.catalogue.update({u['key']: u for u in catalogue['units'] if u['key'] in keys})
        wanted = {u['id'] for u in cls.catalogue.values()}
        rows = []
        for ref in cls.manifest['records']['shards']:
            if any(ref['first_id'] <= iri <= ref['last_id'] for iri in wanted):
                raw = cls.inputs.read('logical-units/' + ref['path'], ref['sha256'], ref['bytes'])
                rows.extend(r for r in json.loads(decode_shard(raw, ref))['records'] if r['id'] in wanted)
        if {r['id'] for r in rows} != wanted:
            raise ValueError('Incomplete current authored-unit fixture')
        cls.units = sorted(rows, key=lambda r: r['id'])
        cls.by_id = {r['id']: r for r in rows}
        cls.semantic, _ = project(cls.inputs, cls.manifest, cls.units)
        cls.edges = {(e['source'], e['target'], e['predicate']): e for e in cls.semantic['assertions']}
        cls.reader_manifest = json.loads(cls.inputs.read('logical-context/data/manifest.json'))
        cls.locator = json.loads(cls.inputs.read('logical-context/data/locator/manifest.json'))
        cls.adjacency = json.loads(cls.inputs.read('logical-context/data/adjacency/manifest.json'))
        cls.bound_reader = {s['path']: s for shards in cls.reader_manifest['shards'].values() for s in shards}
        cls.bound_reader.update({s['path']: s for s in cls.adjacency['shards']})
        cls.reader_cache = {}

    def id(self, key):
        return self.catalogue[key]['id']

    def edge(self, a, b, predicate=DCT + 'requires'):
        return self.edges[(self.id(a), self.id(b), predicate)]

    def compile_mutation(self, path, change):
        value = deepcopy(json.loads(self.inputs.read(PREFIX + path)))
        change(value)
        return project(ReboundInputs({PREFIX + path: value}), self.manifest, deepcopy(self.units))

    def reader_json(self, path, reference=None):
        if path not in self.reader_cache:
            ref = reference or self.bound_reader[path]
            raw = self.inputs.read('logical-context/' + path, ref['sha256'], ref['bytes'])
            if path.endswith('.gz'):
                # Reader shards declare the same gzip hash/size shape, at a
                # potentially larger bound than the 4 MiB Ask record shards.
                import gzip, io
                with gzip.GzipFile(fileobj=io.BytesIO(raw)) as f:
                    decoded = f.read(ref['decoded_bytes'] + 1)
                if len(decoded) != ref['decoded_bytes'] or digest(decoded) != ref['decoded_sha256']:
                    raise ValueError('Reader decoded identity differs')
            else:
                decoded = raw
            self.reader_cache[path] = json.loads(decoded)
        return self.reader_cache[path]

    def reader_record(self, key):
        unit = self.by_id[self.id(key)]
        route = unit['route']
        ref = self.locator['buckets'][bucket(route)]
        shard, slot = self.reader_json(ref['path'], ref)[route]
        return self.reader_json(self.locator['record_chunks'][shard])[slot]

    def test_all_authored_proposals_keep_reason_scope_and_conditional_scope(self):
        for d in self.overrides['documents']:
            for p in d['proposals']:
                edge = self.edge(p['source_unit_key'], p['target_unit_key'], p['predicate'])
                self.assertEqual(edge['assertion_status'], 'model-derived')
                for field in ('reason', 'assertion_scope', 'conditional_scope'):
                    if p.get(field):
                        self.assertIn(p[field], edge['scope'])
                self.assertEqual(edge['provenance'], self.by_id[self.id(p['source_unit_key'])]['provenance'])
        cross = self.edge('pip-transfer-p5093-5097', 'pip-p4021', DCT + 'references')
        self.assertIn('PIP transfer scenario', cross['scope'])
        conditional = self.edge('spc-077003', 'spc-qyp-077008-014', DCT + 'references')
        self.assertIn('do not require for every claimant', conditional['scope'])

    def test_unresolved_references_and_obligations_are_not_promoted_to_records(self):
        records = {r['id'] for r in self.semantic['records']} | set(self.by_id)
        for p in self.profile_author['profiles']:
            requirement = next(r for r in self.semantic['requirements'] if r['id'].endswith('/' + p['id']))
            for o in p['missing_obligations']:
                iri = BASE + 'id/obligation/logical/' + p['id'] + '/' + o['id']
                self.assertIn(iri, requirement['required'])
                self.assertNotIn(iri, records)
            for ref in self.refs['references']:
                if ref['source_unit_key'] in p['required_unit_keys']:
                    self.assertTrue(any(ref['literal_reference'] in text and ref['note'] in text for text in requirement['limitations']))

    def test_required_paths_retain_actual_direction_and_scope_seed(self):
        edges = {e['id']: e for e in self.semantic['assertions']}
        for requirement in self.semantic['requirements']:
            for path in requirement['required_paths']:
                self.assertIn(path['seed'], requirement['when_all'])
                self.assertEqual(path['records'][0], path['seed'])
                self.assertEqual(len(path['assertions']), len(path['records']) - 1)
                for i, identifier in enumerate(path['assertions']):
                    self.assertEqual((edges[identifier]['source'], edges[identifier]['target']), tuple(path['records'][i:i + 2]))

    def test_unknown_unit_key_and_changed_spans_reject(self):
        def unknown(x): x['documents'][0]['units'][0]['key'] = 'synthetic-missing-key'
        def changed(x): x['documents'][0]['units'][0]['spans'][0]['start_utf8'] += 1
        for mutation in (unknown, changed):
            with self.assertRaises(ValueError):
                self.compile_mutation('overrides.json', mutation)

    def test_changed_unit_text_or_record_identity_rejects(self):
        changed = deepcopy(self.units)
        changed[0]['text'] += '\nSynthetic changed qualifier'
        with self.assertRaisesRegex(ValueError, 'identity'):
            project(Inputs(ROOT), self.manifest, changed)

    def test_unsupported_predicate_changed_proposal_span_and_false_review_reject(self):
        def predicate(x): x['documents'][0]['proposals'][0]['predicate'] = 'https://example.invalid/grants-entitlement'
        def spans(x): x['documents'][0]['proposals'][0]['evidence_spans'][0]['end_utf8'] -= 1
        def authority(x): x['documents'][0]['proposals'][0]['assertion_status'] = 'official'
        for mutation in (predicate, spans, authority):
            with self.assertRaises(ValueError):
                self.compile_mutation('overrides.json', mutation)

    def test_declared_proposal_and_reference_documents_must_match_key_owner(self):
        def wrong_target(x):
            p = next(p for d in x['documents'] for p in d['proposals'] if p.get('target_document_id'))
            p['target_document_id'] = 'adm-chapter-c1'
        def wrong_source_owner(x):
            owner = next(d for d in x['documents'] if d['document_id'] == 'adm-chapter-p5')
            other = next(d for d in x['documents'] if d['document_id'] == 'adm-chapter-c1')
            other['proposals'].append(owner['proposals'].pop())
        def wrong_reference_owner(x):
            x['references'][0]['document_id'] = 'adm-chapter-p5'
        for filename, mutation in [('overrides.json', wrong_target),
                                   ('overrides.json', wrong_source_owner),
                                   ('reference-review.json', wrong_reference_owner)]:
            with self.subTest(filename=filename, mutation=mutation.__name__):
                with self.assertRaisesRegex(ValueError, '[Dd]ocument|owner'):
                    self.compile_mutation(filename, mutation)

    def test_source_backed_alias_addition_preserves_original_identity_and_meaning(self):
        declarations = json.loads(self.inputs.read(PREFIX + 'concepts.yamlld'))
        previous = json.loads(self.inputs.read('combined/context/corpus/base-index.json'))
        old = {r['id']: r for r in previous['records']}
        current = {r['id']: r for r in self.semantic['records']}
        self.assertEqual(len(declarations['alias_additions']), 1)
        for addition in declarations['alias_additions']:
            before, after = old[addition['id']], current[addition['id']]
            self.assertEqual(after['id'], before['id'])
            self.assertEqual(after['text'], before['text'])
            self.assertEqual(after['label'], before['label'])
            self.assertEqual(after['assertion_status'], before['assertion_status'])
            self.assertEqual(after['review_status'], before['review_status'])
            self.assertEqual(after['aliases'][:len(before['aliases'])], before['aliases'])
            self.assertTrue(set(addition['aliases']) <= set(after['aliases']))
            self.assertIn(addition['scope'], after['scope'])
            for key in addition['source_unit_keys']:
                for provenance in self.by_id[self.id(key)]['provenance']:
                    source = {k: v for k, v in provenance.items() if k != 'literal_sha256'}
                    self.assertIn(source, after['provenance'])
        self.assertIn('temporary care home residence', addition['aliases'])
        self.assertIn('do not establish permanent residence', addition['scope'])

    def test_alias_unknown_identity_source_unreviewed_scope_and_bounds_reject(self):
        def unknown(x): x['alias_additions'][0]['id'] = BASE + 'id/synthetic-missing-concept'
        def missing_source(x): x['alias_additions'][0]['source_unit_keys'] = ['synthetic-unknown-unit']
        def no_source(x): x['alias_additions'][0]['source_unit_keys'] = []
        def reviewed(x): x['alias_additions'][0]['review_status'] = 'specialist-accepted'
        def no_scope(x): x['alias_additions'][0]['scope'] = ' '
        def too_long(x): x['alias_additions'][0]['aliases'] = ['x' * 301]
        for mutation in (unknown, missing_source, no_source, reviewed, no_scope, too_long):
            with self.subTest(mutation=mutation.__name__):
                with self.assertRaises(ValueError):
                    self.compile_mutation('concepts.yamlld', mutation)

    def test_reader_locator_binds_same_source_spans_and_correct_record_class(self):
        for key in ('spc-077001', 'spc-077004', 'uc-c1988', 'state-pension-077028', 'spc-temporary-78086', 'pip-p4016', 'spc-deductions-2024'):
            row = self.reader_record(key)
            item = self.by_id[self.id(key)]
            self.assertEqual((row['id'], row['route']), (item['id'], item['route']))
            self.assertEqual(row['type'], 'Logical evidence unit')
            self.assertEqual(row['record_type'], 'Logical evidence unit')
            self.assertEqual(row['source_family'], row['route'].split('/')[1].upper())
            self.assertEqual(row['provenance']['evidence_unit'], item['evidence_unit'])
            self.assertEqual(row['provenance']['literal_sha256'], digest(item['text'].encode()))
            self.assertEqual(row['url'], item['provenance'][0]['url'])
            self.assertEqual(row['provenance']['date_roles']['captured_at'], item['provenance'][0]['captured_at'])
            self.assertEqual(row['timestamp'], '')
            self.assertEqual(row['provenance']['date_roles']['publication_date_status'], 'not-established-from-document-evidence')
            for s in item['evidence_unit']['spans']:
                self.assertIn(s['source_url'], row['narrative']['body'])
                self.assertIn(s['literal_sha256'], row['narrative']['body'])

    def test_pdf_resource_is_unique_per_document_including_empty_extraction(self):
        expected = {}
        for group in self.manifest['source_groups']:
            binding = group['inventory']
            source = json.loads(self.inputs.read(binding['repository_path'], binding['sha256']))
            for doc in source['documents']:
                key = (group['id'], doc['id'])
                self.assertNotIn(key, expected)
                expected[key] = doc
        resources = {}
        resource_documents = {}
        for ref in self.reader_manifest['shards']['resources']:
            for resource in self.reader_json(ref['path']):
                self.assertNotIn(resource['id'], resources)
                pieces = resource['dataset'].split('/')
                self.assertEqual(pieces[:2], ['document', 'logical'])
                key = tuple(pieces[2:4])
                self.assertIn(key, expected)
                self.assertNotIn(key, resource_documents)
                self.assertEqual(resource['url'], expected[key]['url'])
                self.assertEqual(resource['provenance']['source_sha256'], expected[key]['sha256'])
                self.assertEqual(resource['source_access']['url'], expected[key]['url'])
                self.assertNotIn('#page=', resource['url'])
                resources[resource['id']] = resource
                resource_documents[key] = resource['id']
        self.assertEqual(set(resource_documents), set(expected))
        self.assertEqual(len(resources), self.reader_manifest['counts']['source_documents'])
        self.assertEqual(len(resources), self.reader_manifest['counts']['resources'])
        # Entirely empty extraction still has an inspectable official document;
        # it must not acquire a fabricated logical evidence record.
        empty = {(d['family'], d['document_id']) for d in self.manifest['documents'] if d['counts']['records'] == 0}
        self.assertTrue(empty)
        self.assertTrue(empty <= set(resource_documents))
        seen_documents, routes, per_publisher = set(), set(), {}
        units_seen = 0
        import gzip, io
        for ref in self.reader_manifest['shards']['datasets']:
            raw = self.inputs.read('logical-context/' + ref['path'], ref['sha256'], ref['bytes'])
            self.assertLessEqual(ref['decoded_bytes'], 64 * 1024 * 1024)
            with gzip.GzipFile(fileobj=io.BytesIO(raw)) as stream:
                decoded = stream.read(ref['decoded_bytes'] + 1)
            self.assertEqual(len(decoded), ref['decoded_bytes'])
            self.assertEqual(digest(decoded), ref['decoded_sha256'])
            # Consume each full-text shard once without retaining the full corpus.
            for row in json.loads(decoded):
                self.assertNotIn(row['route'], routes)
                routes.add(row['route'])
                refs = row['resource_ids']
                self.assertEqual(len(refs), row['resource_count'])
                self.assertEqual(len(refs), len(set(refs)))
                self.assertTrue(set(refs) <= set(resources))
                per_publisher.setdefault(row['publisher'], set()).update(refs)
                if row['route'].startswith('document/logical/'):
                    key = tuple(row['route'].split('/')[2:4])
                    self.assertEqual(refs, [resource_documents[key]])
                    self.assertEqual(row['record_type'], 'Source document')
                    seen_documents.add(key)
                if row['record_type'] == 'Logical evidence unit':
                    key = (row['source_family'].lower(), row['document_id'])
                    self.assertNotIn(key, empty)
                    self.assertEqual(refs, [resource_documents[key]])
                    self.assertTrue(row['provenance']['evidence_unit']['spans'])
                    units_seen += 1
        self.assertEqual(seen_documents, set(expected))
        self.assertEqual(units_seen, self.manifest['records']['count'])
        self.assertEqual(len(routes), self.reader_manifest['counts']['records'])
        self.assertTrue(all(r['dataset'] in routes for r in resources.values()))
        publishers = json.loads(self.inputs.read('logical-context/data/publishers.json'))
        for publisher in publishers:
            self.assertEqual(publisher['resource_count'], len(per_publisher[publisher['name']]))

    def test_endpoint_catalogue_stays_within_consumer_count_bound(self):
        ref = self.reader_manifest['indexes']['endpoint_labels']
        raw = self.inputs.read('logical-context/' + ref['path'], ref['sha256'], ref['bytes'])
        import gzip, io
        cap = 64 * 1024 * 1024
        with gzip.GzipFile(fileobj=io.BytesIO(raw)) as stream:
            decoded = stream.read(cap + 1)
        self.assertLessEqual(len(decoded), cap)
        catalogue = json.loads(decoded)
        entries = catalogue['entries']
        self.assertEqual(catalogue['schema'], 'okf-explorer-endpoint-label-index.v1')
        self.assertEqual(catalogue['counts']['entries'], len(entries))
        self.assertLessEqual(len(entries), 100000)
        self.assertEqual(len({e['route'] for e in entries}), len(entries))
        self.assertEqual(catalogue['snapshot'], self.reader_manifest['snapshot'])
        for key in ('spc-077001', 'uc-c1988', 'pip-transfer-p5093-5097'):
            item = self.by_id[self.id(key)]
            entry = next(e for e in entries if e['route'] == item['route'])
            self.assertEqual(entry['iri'], item['id'])
            self.assertEqual(entry['type'], 'Logical evidence unit')

    def test_search_declares_actual_largest_posting_without_capping_census(self):
        import gzip, io
        search = json.loads(self.inputs.read('logical-context/data/search/manifest.json'))
        inventory = json.loads(self.inputs.read('logical-context/' + search['shard_metadata']))
        self.assertEqual(digest(canonical(inventory['shards'])), search['shard_manifest_sha256'])
        bindings = {r['path']: r for r in inventory['shards']['search']}
        def load(path):
            ref = bindings[path]
            raw = self.inputs.read('logical-context/' + path, ref['sha256'], ref['bytes'])
            cap = 4 * 1024 * 1024
            with gzip.GzipFile(fileobj=io.BytesIO(raw)) as stream:
                decoded = stream.read(cap + 1)
            self.assertLessEqual(len(decoded), cap)
            return json.loads(decoded)
        tokens, total, maximum = set(), 0, None
        posting_paths = set(search['entrypoints']['postings'])
        for path in search['entrypoints']['lexicon'].values():
            for entry in load(path):
                self.assertNotIn(entry['token'], tokens)
                tokens.add(entry['token'])
                self.assertIsInstance(entry['df'], int)
                self.assertGreater(entry['df'], 0)
                self.assertIn(entry['postings'], posting_paths)
                total += entry['df']
                if maximum is None or entry['df'] > maximum['df']:
                    maximum = entry
        self.assertIsNotNone(maximum)
        counts = search['counts']
        self.assertEqual(counts['documents'], self.reader_manifest['counts']['records'])
        self.assertEqual(counts['tokens'], len(tokens))
        self.assertEqual(counts['postings'], total)
        self.assertEqual(counts['uncapped_postings'], total)
        self.assertEqual(counts['max_postings_per_token'], maximum['df'])
        self.assertLessEqual(maximum['df'], 50000)
        # The largest lexicon count is also checked against its real posting
        # list, rather than trusting a summary to repeat another summary.
        postings = load(maximum['postings'])['tokens'][maximum['token']]
        self.assertEqual(len(postings), maximum['df'])
        ordinals = [r[0] for r in postings]
        self.assertEqual(len(set(ordinals)), len(ordinals))
        self.assertEqual(ordinals, sorted(ordinals))
        self.assertTrue(all(0 <= ordinal < counts['documents'] for ordinal in ordinals))

    def test_reader_relationship_available_at_both_endpoints_without_reversal(self):
        for a, b, predicate in [('spc-077003', 'spc-077004', DCT + 'requires'), ('pip-transfer-p5093-5097', 'pip-p4021', DCT + 'references')]:
            original = self.edge(a, b, predicate)
            for key in (a, b):
                route = self.by_id[self.id(key)]['route']
                paths = self.adjacency['buckets']
                records = self.reader_json(paths[bucket(route)])[route]
                projected = next(e for e in records if e['id'] == original['id'])
                self.assertEqual(projected['source_iri'], original['source'])
                self.assertEqual(projected['target_iri'], original['target'])
                self.assertEqual(projected['scope'], original['scope'])
                self.assertEqual(projected['predicate'], predicate)


if __name__ == '__main__':
    unittest.main()
