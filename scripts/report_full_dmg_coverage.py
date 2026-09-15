#!/usr/bin/env python3
"""Report measured source and authored-evidence coverage without implying review."""
import argparse
from collections import defaultdict
import json
from pathlib import Path

from build_bundle import ROOT, digest, load_yaml, pretty

OUTPUT = 'evaluation/full-dmg-coverage.json'


def build():
    inventory_path = ROOT / 'source/full-dmg-2026-09-15/inventory.json'
    plan_path = ROOT / 'evaluation/full-dmg-coverage-plan.json'
    evidence_path = ROOT / 'evaluation/full-dmg-evidence/index.json'
    inventory, plan, evidence = [json.loads(p.read_text()) for p in (inventory_path, plan_path, evidence_path)]
    docs = {d['url']: d for d in inventory['documents']}
    by_id = {d['id']: d for d in inventory['documents']}
    evidence_docs = {d['id']: d for d in evidence['documents']}
    concepts, proposals = defaultdict(set), defaultdict(set)
    files = []
    for path in sorted((ROOT / 'knowledge').rglob('*.yamlld')):
        files.append({'path': path.relative_to(ROOT).as_posix(), 'sha256': digest(path.read_bytes())})
        for node in load_yaml(path).get('@graph', []):
            if node.get('type') != 'Concept':
                continue
            for source in node.get('sources', []):
                if source.get('id') in by_id:
                    concepts[source['id']].add(node['route'])
            for relation in node.get('semantic_relations', []):
                for item in relation.get('evidence', []):
                    route = item.get('page', '').split('/')
                    if len(route) != 3 or route[0] != 'page':
                        raise ValueError('Unexpected semantic evidence page route')
                    candidates = [by_id[route[1]]] if route[1] in by_id else [d for d in by_id.values() if str(d.get('chapter')) == route[1] and d.get('role') == 'substantive']
                    if len(candidates) != 1:
                        raise ValueError('Ambiguous or missing semantic source page')
                    doc = candidates[0]
                    text = json.loads((ROOT / doc['pages_path']).read_text())['pages'][int(route[2]) - 1]['text']
                    if not item.get('quote') or item['quote'] not in text:
                        raise ValueError('Coverage cannot count an unsupported quotation')
                    concepts[doc['id']].add(node['route'])
                    proposals[doc['id']].add((node['route'], relation['predicate'], relation['target']))
    rows = []
    for unit in plan['source_units']:
        doc = docs.get(unit['official_url'])
        if doc is None:
            raise ValueError('Census source unit missing from acquisition')
        dates = evidence_docs[doc['id']]['stated_revision_dates']
        rows.append({'source_unit': unit['id'], 'document_id': doc['id'], 'title': doc['title'],
                     'url': doc['url'], 'role': doc['role'], 'plan_classification': unit['classification'],
                     'pdf_sha256': doc['sha256'], 'measured_pages': doc['pages'],
                     'source_status': 'acquired-and-hash-verified',
                     'concept_routes_with_source_reference': sorted(concepts[doc['id']]),
                     'evidence_bearing_proposals': len(proposals[doc['id']]),
                     'semantic_status': 'proposals-present-further-research-and-specialist-review-required' if proposals[doc['id']] else 'systematic-semantic-authoring-pending',
                     'source_revision_statements': dates, 'source_publication_date': None,
                     'legal_applicability': 'not-established', 'specialist_acceptance': 'not-recorded'})
    chapters = [r for r in rows if r['role'] == 'substantive']
    return pretty({'schema': 'okf-dwp-full-coverage.v1',
                   'inputs': [{'path': p.relative_to(ROOT).as_posix(), 'sha256': digest(p.read_bytes())} for p in (inventory_path, plan_path, evidence_path)] + files,
                   'source_documents': len(rows), 'measured_pages': sum(r['measured_pages'] for r in rows),
                   'substantive_pdf_units': len(chapters),
                   'substantive_units_with_proposals': sum(bool(r['evidence_bearing_proposals']) for r in chapters),
                   'substantive_units_pending_proposals': sum(not r['evidence_bearing_proposals'] for r in chapters),
                   'specialist_accepted_units': 0, 'rows': rows,
                   'limitations': ['A referenced concept or a proposed relationship is not comprehensive chapter modelling.',
                                   'This measures source references and exact passage support, not correctness of interpretation.',
                                   'Title-derived workplan prompts remain prompts until source-backed authoring is completed.',
                                   'No specialist acceptance or legal applicability is established by this report.']})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    data = build()
    if args.check:
        if (ROOT / OUTPUT).read_bytes() != data:
            raise SystemExit('Full-DMG coverage report is stale.')
    else:
        (ROOT / OUTPUT).write_bytes(data)
    report = json.loads(data)
    print(json.dumps({k: report[k] for k in ['source_documents', 'measured_pages', 'substantive_pdf_units', 'substantive_units_with_proposals', 'substantive_units_pending_proposals', 'specialist_accepted_units']}))


if __name__ == '__main__':
    main()
