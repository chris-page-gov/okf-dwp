#!/usr/bin/env python3
"""Run small retrieval controls and bind returned citations to frozen pages."""
import json
from pathlib import Path
from query import ROOT, search

cases = [
    ('capital disregarded', 84), ('part-week payments', 79),
    ('self-employed earner', 86), ('assessed income periods', 83),
    ('notional income', 85), ('mixed-age couples', 77),
]
inventory = json.loads((ROOT / 'source/inventory.json').read_text())
documents = {d['id']: d for d in inventory['documents']}
results = []
for query, chapter in cases:
    result = search(query, limit=10)
    assert any(r['chapter'] == chapter for r in result['results']), query
    for hit in result['results']:
        doc = documents[hit['document_id']]
        page = json.loads((ROOT / doc['pages_path']).read_text())['pages'][hit['page'] - 1]
        assert hit['source_url'] == page['url']
        assert hit['source_sha256'] == doc['sha256']
        assert hit['extract'] in page['text']
        assert hit['role'] == 'substantive'
    results.append({'query': query, 'expected_chapter_present': chapter, 'status': 'passed', 'output': result})
assert search('unfindablepensionkeywordxyz')['results'] == []
assert search('the and')['results'] == []
receipt = {'schema': 'okf-dwp-retrieval-evaluation.v1', 'status': 'passed',
           'positive_cases': len(cases), 'negative_cases': 2, 'results': results,
           'scope': 'Deterministic retrieval and citation integrity only; no claim of legal-answer accuracy or expert review.'}
out = ROOT / 'validation/retrieval.json'
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'status': 'passed', 'positive_cases': len(cases), 'negative_cases': 2, 'output': str(out)}))
