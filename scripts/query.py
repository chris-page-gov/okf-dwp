#!/usr/bin/env python3
"""Find source pages, returning citation data without generating benefit advice."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STOP = set('a an and are as at be can do does for from how i in is it of on or should the to what when where which with'.split())


def search(query: str, limit: int = 5, include_history: bool = False) -> dict:
    terms = [t for t in re.findall(r"[a-z0-9]+", query.lower()) if t not in STOP]
    if not terms:
        return {'query': query, 'results': [], 'reason': 'No searchable terms supplied.'}
    inventory = json.loads((ROOT / 'source/inventory.json').read_text())
    results = []
    for doc in inventory['documents']:
        if not include_history and doc.get('role') != 'substantive':
            continue
        if not doc.get('pages_path'):
            continue
        pages = json.loads((ROOT / doc['pages_path']).read_text())['pages']
        for page in pages:
            content = page['text']
            words = content.lower()
            hits = [term for term in terms if term in words]
            if len(hits) != len(terms):
                continue
            phrase = query.lower() in words
            score = 12 * int(phrase) + sum(min(words.count(term), 6) for term in terms)
            # A contents page remains valid evidence for navigation, with a lower rank.
            if 'subpages' in words or ('contents' in words and page['page'] < 3):
                score -= 10
            first = min(words.find(term) for term in terms)
            start = max(0, first - 160)
            snippet = content[start:min(len(content), first + 740)].strip()
            results.append({
                'document_id': doc['id'], 'title': doc['title'],
                'chapter': doc.get('chapter'), 'role': doc['role'],
                'page': page['page'], 'source_url': page['url'],
                'source_sha256': doc['sha256'],
                'page_text_sha256': hashlib.sha256(content.encode()).hexdigest(),
                'observed_at': doc['observed_at'],
                'extract': snippet, 'score': score,
                'extraction_status': 'machine-extracted; inspect original and neighbouring pages',
            })
    results.sort(key=lambda r: (-r['score'], r['document_id'], r['page']))
    return {
        'query': query, 'scope': 'all acquired documents' if include_history else 'seven substantive chapter files',
        'total_matching_pages': len(results), 'results': results[:limit],
        'notice': 'Unofficial source retrieval. This does not determine entitlement or legal currency.',
        'limitations': ['Substring matching is not semantic reasoning.', 'PDF extraction can damage reading order and searchability.',
                        'Current-linked files can contain historical provisions; check effective dates and external memos.'],
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('query')
    parser.add_argument('--limit', type=int, default=5)
    parser.add_argument('--include-history', action='store_true')
    args = parser.parse_args()
    if not 1 <= args.limit <= 50:
        parser.error('--limit must be between 1 and 50')
    print(json.dumps(search(args.query, args.limit, args.include_history), ensure_ascii=False, indent=2))
