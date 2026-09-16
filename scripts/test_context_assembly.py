"""Focused producer checks: source bytes and graph dependencies, not legal grading."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from jsonschema import Draft202012Validator

from build_bundle import BASE, canonical, digest, yaml_bytes
from context_assembly import augment_context_graph, project_context_index


class ContextProducerTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)
        self.path = self.root / 'knowledge/full-dmg/example.yamlld'
        self.path.parent.mkdir(parents=True)
        (self.root / 'source').mkdir()
        self.text = '12003 A complete frozen passage.\n  Exact trailing spaces.  \n'
        pdf = b'frozen source test bytes'
        pages = canonical({'pages': [{'page': 1, 'url': 'https://example.org/source.pdf#page=1', 'text': self.text}]})
        (self.root / 'source/test.pdf').write_bytes(pdf)
        (self.root / 'source/pages.json').write_bytes(pages)
        self.when = '2026-09-16T00:00:00Z'
        self.doc = {'id': 'test', 'sha256': digest(pdf), 'pdf_path': 'source/test.pdf',
                    'pages_path': 'source/pages.json', 'pages_sha256': digest(pages),
                    'url': 'https://example.org/source.pdf', 'observed_at': self.when}
        self.nodes = {
            'term/test': {'@id': BASE+'id/term/test', 'route': 'term/test', 'title': 'Test concept', 'generated': {'at': self.when}},
            'page/test/0001': {'@id': BASE+'id/page/test/0001', 'route': 'page/test/0001', 'title': 'Source page',
                               'type': 'Source PDF page', 'source_sha256': self.doc['sha256'], 'page_number': 1,
                               'source': 'https://example.org/source.pdf#page=1', 'generated': {'at': self.when}}
        }
        self.input = {'context_profile': {'schema': 'okf-dwp-context-authoring.v1', 'scope': 'Fixture only', 'authored_at': self.when, 'limitations': ['Not legal evidence']},
                      'context_overlays': [
                          {'route': 'term/test', 'context_assembly': {'kind': 'concept', 'scope': 'Fixture', 'text': 'An authored concept',
                             'aliases': [{'label': 'IS', 'case_sensitive': True}],
                             'relations': [{'target': 'page/test/0001', 'predicate': 'http://purl.org/dc/terms/requires',
                                            'rationale': 'Requires the source', 'evidence': ['page/test/0001']}]}},
                          {'route': 'page/test/0001', 'context_assembly': {'kind': 'evidence', 'scope': 'Fixture',
                             'source_page': 'page/test/0001', 'locator': 'DMG 12003, PDF page 1', 'paragraphs': ['12003']}}],
                      'context_requirements': [{'id': BASE+'id/context-requirement/test-v1', 'label': 'Test v1', 'scope': 'Fixture',
                           'when_all': [BASE+'id/term/test'], 'required': [BASE+'id/page/test/0001']}]}

    def build(self):
        self.path.write_bytes(yaml_bytes(self.input))
        nodes, edges = deepcopy(self.nodes), []
        plan = augment_context_graph(self.root, nodes, edges, [self.doc])
        return nodes, edges, project_context_index(plan, edges, 'fixture-snapshot')

    def test_exact_page_and_graph_identity(self):
        nodes, edges, index = self.build()
        schema = json.loads((Path(__file__).resolve().parents[1] / 'profiles/bundle-wiki/v1/semantic-assertion.schema.json').read_bytes())
        Draft202012Validator(schema).validate(edges[0])
        evidence = next(x for x in index['records'] if x['kind'] == 'evidence')
        self.assertEqual(evidence['text'], self.text)
        self.assertEqual(evidence['provenance'][0]['literal_sha256'], digest(self.text.encode()))
        self.assertEqual(index['assertions'][0]['original_assertion_id'], edges[0]['@id'])
        self.assertEqual(nodes['term/test']['http://purl.org/dc/terms/requires'], [{'@id': BASE+'id/page/test/0001'}])
        self.assertEqual(index['records'][1]['aliases'], [{'label': 'IS', 'case_sensitive': True}])
        self.assertEqual(edges[0]['evidence'][0]['retrieved_at'], self.when)

    def test_requirements_do_not_create_edges(self):
        self.input['context_overlays'][0]['context_assembly']['relations'] = []
        _, edges, index = self.build()
        self.assertEqual(edges, [])
        self.assertEqual(index['assertions'], [])
        self.assertEqual(len(index['requirements']), 1)

    def test_changed_pdf_is_rejected(self):
        (self.root / 'source/test.pdf').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'PDF hash differs'): self.build()

    def test_changed_page_extraction_is_rejected(self):
        (self.root / 'source/pages.json').write_bytes(b'{}')
        with self.assertRaisesRegex(ValueError, 'extraction hash differs'): self.build()

    def test_absent_paragraph_is_rejected(self):
        self.input['context_overlays'][1]['context_assembly']['paragraphs'] = ['12004']
        with self.assertRaisesRegex(ValueError, 'paragraph absent'): self.build()

    def test_unknown_evidence_endpoint_is_rejected(self):
        self.input['context_overlays'][0]['context_assembly']['relations'][0]['target'] = 'page/absent/0001'
        with self.assertRaisesRegex(ValueError, 'endpoint'): self.build()

    def test_requirement_cannot_cover_evidence_as_concept(self):
        self.input['context_requirements'][0]['covers'] = [BASE+'id/term/test', BASE+'id/page/test/0001']
        with self.assertRaisesRegex(ValueError, 'coverage must be concepts'): self.build()

    def test_undeclared_predicate_is_rejected(self):
        self.input['context_overlays'][0]['context_assembly']['relations'][0]['predicate'] = 'https://example.org/equivalent'
        with self.assertRaisesRegex(ValueError, 'endpoint/predicate'): self.build()

    def test_scope_and_alias_governance(self):
        self.input['context_overlays'][1]['context_assembly']['aliases'] = ['source']
        with self.assertRaisesRegex(ValueError, 'Only concepts'): self.build()

    def add_chapter_route(self):
        quote = '12015 For benefit specific guidance see DMG Chapter 24.'
        self.text += quote
        pages = canonical({'pages': [{'page': 1, 'url': self.nodes['page/test/0001']['source'], 'text': self.text}]})
        (self.root / 'source/pages.json').write_bytes(pages)
        self.doc.update(pages_sha256=digest(pages), title='Fixture chapter 24', chapter=24)
        path = self.root / 'source/full-dmg-2026-09-15/inventory.json'
        path.parent.mkdir(parents=True)
        path.write_bytes(canonical({'documents': [self.doc]}))
        self.nodes['document/test'] = {'@id': BASE+'id/document/test', 'route': 'document/test',
                                      'title': self.doc['title'], 'source': self.doc['url'], 'source_sha256': self.doc['sha256']}
        self.input['context_overlays'].append({'route': 'document/test', 'context_assembly': {
            'kind': 'scope', 'source_document': 'test', 'scope': 'Document identity only'}})
        self.input['context_overlays'][1]['context_assembly']['relations'] = [{
            'target': 'document/test', 'predicate': 'http://purl.org/dc/terms/references',
            'rationale': 'Literal chapter reference only', 'evidence': ['page/test/0001'],
            'literal_chapter_route': {'quote': quote}}]

    def test_literal_chapter_routing_has_separate_authority(self):
        self.add_chapter_route()
        _, edges, index = self.build()
        route = next(x for x in edges if x['target_route'] == 'document/test')
        self.assertEqual(route['assertion_status'], 'normalized')
        self.assertEqual(route['authority']['class'], 'derived')
        metadata = next(x for x in index['records'] if x['route'] == 'document/test')
        self.assertEqual(metadata['kind'], 'scope')
        self.assertEqual(metadata['provenance'][1]['literal_sha256'], digest(self.doc['title'].encode()))

    def test_chapter_route_cannot_normalise_an_invented_reference(self):
        self.add_chapter_route()
        self.input['context_overlays'][1]['context_assembly']['relations'][0]['literal_chapter_route']['quote'] = (
            '12015 For benefit specific guidance see DMG Chapter 99.')
        with self.assertRaisesRegex(ValueError, 'exact source passage'): self.build()

    def test_required_path_binds_real_assertion_direction(self):
        _, edges, _ = self.build()
        path = {'seed': BASE+'id/term/test', 'records': [BASE+'id/term/test', BASE+'id/page/test/0001'],
                'assertions': [edges[0]['@id']]}
        self.input['context_requirements'][0]['required_paths'] = [path]
        _, _, index = self.build()
        self.assertEqual(index['requirements'][0]['required_paths'], [path])
        path['seed'] = BASE+'id/page/test/0001'
        path['records'].reverse()
        with self.assertRaisesRegex(ValueError, 'actual directed'): self.build()


if __name__ == '__main__':
    unittest.main()
