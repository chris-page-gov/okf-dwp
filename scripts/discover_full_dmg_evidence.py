#!/usr/bin/env python3
"""Index explicit date statements and reference candidates without deciding applicability."""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = Path('source/full-dmg-2026-09-15/inventory.json')
OUTPUT = Path('evaluation/full-dmg-evidence')
MONTHS = ('January February March April May June July August September October November December').split()
MONTH_PATTERN = '|'.join(m + '|' + m[:3] for m in MONTHS)
DATE = re.compile(r'\b(?:(\d{1,2})\s+)?(' + MONTH_PATTERN + r')\s+(19\d{2}|20\d{2})\b', re.I)
REVISION = re.compile(r'\b(?:Amendment\s+\d+\s*[–—-]?\s*|Amended Chapters for\s+)$', re.I)
DMG = re.compile(r'\bDMG\s+(?:(Memo)\s+)?(\d{1,2}/\d{2}(?!\d)|\d{5,})(?:\s*(?:–|-|to)\s*(\d{5,}))?(?!\d)', re.I)
LEGAL_LINE = re.compile(r'\b(?:Act\s+(?:\d{2}|(?:19|20)\d{2})|Regs?\b|Regulations\b|SI\s+(?:19|20)\d{2}/\d+)|\bR\([A-Z ]+\)\s*\d+/\d+', re.I)


def canonical(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()


def digest(value):
    return sha256(value).hexdigest()


def date_value(match, amendment_number=False):
    month = next(i for i, m in enumerate(MONTHS, 1) if m.lower().startswith(match[2].lower()))
    value = f'{match[3]}-{month:02d}'
    if match[1] and not amendment_number:
        from datetime import date
        try:
            return date(int(match[3]), month, int(match[1])).isoformat(), 'day'
        except ValueError:
            return None
    return value, 'month'


def page_candidates(text):
    """Return exact spans. A labelled revision is not a publication or effective date."""
    result = []
    for match in DATE.finditer(text):
        amendment_number = bool(match[1] and re.search(r'\bAmendment\s+$', text[:match.start()], re.I))
        normalised = date_value(match, amendment_number)
        if not normalised:
            continue
        start, end = text.rfind('\n', 0, match.start()) + 1, text.find('\n', match.end())
        end = len(text) if end < 0 else end
        line = text[start:end]
        label = REVISION.search(text[start:match.start(2) if amendment_number else match.start()])
        result.append({'kind': 'stated-revision-date' if label else 'date-mention',
                       'quote': line, 'start': start, 'end': end, 'matched_text': match[0],
                       'value': normalised[0], 'precision': normalised[1],
                       'status': 'normalised-source-statement' if label else 'unresolved-context',
                       'legal_effective_date_established': False,
                       'source_publication_date_established': False})
    for match in DMG.finditer(text):
        labels = [label for label in (match[2], match[3]) if label]
        is_memo = bool(match[1]) or '/' in match[2]
        # Chapter 7 uses six digits. Other long digit runs may contain a
        # flattened footnote marker; keep them intact and unresolved.
        ambiguous = not is_memo and any(not (len(label) == 5 or (len(label) == 6 and label.startswith('07'))) for label in labels)
        result.append({'kind': 'dmg-memo-reference' if is_memo else ('dmg-unresolved-digit-reference' if ambiguous else 'dmg-paragraph-reference'),
                       'quote': match[0], 'start': match.start(), 'end': match.end(),
                       'target_label': match[2], 'range_end': match[3],
                       'status': 'ambiguous-digit-run-no-identifier-assigned' if ambiguous else 'literal-reference-unresolved-applicability'})
    offset = 0
    for line in text.splitlines(keepends=True):
        quote = line.rstrip('\r\n')
        if LEGAL_LINE.search(quote):
            result.append({'kind': 'legal-reference-line-candidate', 'quote': quote,
                           'start': offset, 'end': offset + len(quote),
                           'status': 'unresolved-identifier-version-and-applicability'})
        offset += len(line)
    seen = set()
    unique = []
    for row in result:
        key = (row['kind'], row['start'], row['end'], row.get('value'))
        if key not in seen:
            assert text[row['start']:row['end']] == row['quote']
            row['quote_sha256'] = digest(row['quote'].encode())
            unique.append(row)
            seen.add(key)
    return unique


def build():
    raw = (ROOT / INVENTORY).read_bytes()
    inventory = json.loads(raw)
    files = {}
    summaries = []
    totals = Counter()
    for doc in inventory['documents']:
        if not doc.get('pages_path'):
            summaries.append({'id': doc['id'], 'status': 'source-not-acquired'})
            continue
        pages_raw = (ROOT / doc['pages_path']).read_bytes()
        pages = json.loads(pages_raw)
        if pages['source_sha256'] != doc['sha256'] or len(pages['pages']) != doc['pages']:
            raise ValueError(f"Page identity or denominator mismatch: {doc['id']}")
        records = []
        revision_values = set()
        counts = Counter()
        for page in pages['pages']:
            for row in page_candidates(page['text']):
                row.update({'pdf_page': page['page'], 'url': page['url'],
                            'page_text_sha256': digest(page['text'].encode())})
                row['id'] = digest(canonical([doc['sha256'], page['page'], row['kind'], row['start'], row['end']]))
                records.append(row)
                counts[row['kind']] += 1
                if row['kind'] == 'stated-revision-date':
                    revision_values.add(row['value'])
        # More than one statement is retained; never choose a latest date as a rule date.
        filename = f"{doc['id']}.json"
        report = {'schema': 'okf-dwp-source-evidence-candidates.v1', 'document_id': doc['id'],
                  'source_url': doc['url'], 'source_pdf_sha256': doc['sha256'],
                  'pages_artifact': doc['pages_path'], 'pages_artifact_sha256': digest(pages_raw),
                  'observed_at': doc['observed_at'], 'source_role': doc['role'],
                  'document_publication_date': None, 'legal_applicability_established': False,
                  'stated_revision_dates': sorted(revision_values), 'counts': dict(sorted(counts.items())),
                  'candidates': records}
        data = canonical(report)
        files[filename] = data
        totals.update(counts)
        summaries.append({'id': doc['id'], 'path': (OUTPUT / filename).as_posix(),
                          'sha256': digest(data), 'pages_examined': doc['pages'],
                          'counts': dict(sorted(counts.items())),
                          'stated_revision_dates': sorted(revision_values),
                          'document_publication_date': None,
                          'date_review_status': 'source-statements-present' if revision_values else 'publication-and-revision-not-established'})
    index = {'schema': 'okf-dwp-evidence-discovery-index.v1',
             'inventory': INVENTORY.as_posix(), 'inventory_sha256': digest(raw),
             'documents': summaries, 'counts': dict(sorted(totals.items())),
             'method': 'Deterministic pattern matching over every acquired extracted page; exact spans retained.',
             'limitations': ['Reference and date recognition is deliberately bounded and not exhaustive.',
                            'A date mention can concern an example, historical fact or effective provision; its role is unresolved.',
                            'An explicitly labelled amendment date is a source revision statement, not publication or commencement.',
                            'Legal reference lines require identifier, version and applicability reconciliation.',
                            'Machine text extraction defects can hide or damage references; no specialist review is claimed.']}
    files['index.json'] = canonical(index)
    return files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    files = build()
    output = ROOT / OUTPUT
    if args.check:
        actual = {p.name for p in output.glob('*.json')}
        if actual != set(files) or any((output / p).read_bytes() != b for p, b in files.items()):
            raise SystemExit('Source evidence discovery output differs from frozen input.')
    else:
        output.mkdir(parents=True, exist_ok=True)
        if any(p.name not in files for p in output.glob('*.json')):
            raise SystemExit('Unexpected prior outputs: inspect before replacing this snapshot.')
        for path, data in files.items():
            (output / path).write_bytes(data)
    print(json.dumps({'files': len(files), 'bytes': sum(map(len, files.values())), 'check': args.check}))


if __name__ == '__main__':
    main()
