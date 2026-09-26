#!/usr/bin/env python3
"""Validate this review package against the original attached ZIP, without network access.

Usage:
  python verify-pilot.py --source-pack /path/to/okf-dwp-ch60-reading-help.zip \
      --output-dir /path/to/ch60-reading-help --reextract-pdfs

Requires Python 3.10+. Optional PDF re-extraction requires the local pdftotext executable.
The source pack is read only as data; no source-provided code or links are executed.
This validates technical provenance and coverage, not meanings, counts or legal correctness.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import zipfile
from collections import Counter


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source-pack', required=True, type=Path)
    ap.add_argument('--output-dir', default=Path(__file__).resolve().parent, type=Path)
    ap.add_argument('--reextract-pdfs', action='store_true')
    args = ap.parse_args()
    out = args.output_dir
    errors: list[str] = []
    checks: dict = {}

    def check(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    def jl(name: str) -> list:
        return [json.loads(s) for s in (out / name).read_text(encoding='utf-8').splitlines() if s]

    with zipfile.ZipFile(args.source_pack) as z:
        # Manifest is the first member content read.
        manifest_bytes = z.read('manifest.json')
        manifest = json.loads(manifest_bytes)
        meta = {s['id']: s for s in manifest['sources']}
        check(z.testzip() is None, 'ZIP CRC failure')
        listed = []
        for f in manifest['files']:
            data = z.read(f['path'])
            ok = digest(data) == f['sha256'] and len(data) == f['bytes']
            check(ok, 'Source hash/length mismatch: ' + f['path'])
            listed.append({'path': f['path'], 'hash_and_length_match': ok})
        checks['listed_files'] = listed
        checks['manifest_sha256_computed_not_independently_authenticated'] = digest(manifest_bytes)
        checks['source_archive_sha256'] = digest(args.source_pack.read_bytes())
        pages = {sid: {p['page']: p['text'] for p in json.loads(z.read(f'sources/{sid}/pages.json'))['pages']} for sid in meta}
        rows = list(csv.DictReader(io.StringIO(z.read('DWP_Chapter_60_recurring_terms.csv').decode('utf-8-sig'))))
        if args.reextract_pdfs:
            exe = shutil.which('pdftotext')
            if not exe:
                raise RuntimeError('--reextract-pdfs requested, but local pdftotext is unavailable')
            comparisons = []
            with tempfile.TemporaryDirectory(prefix='ch60-verify-') as td:
                for i, sid in enumerate(meta):
                    pdf = Path(td) / f'source-{i}.pdf'
                    pdf.write_bytes(z.read(f'sources/{sid}/pdf.pdf'))
                    fresh = subprocess.run([exe, '-layout', '-enc', 'UTF-8', str(pdf), '-'], check=True, capture_output=True, timeout=30).stdout
                    text_match = fresh == z.read(f'sources/{sid}/text.txt')
                    check(text_match, f'Re-extracted text.txt mismatch: {sid}')
                    chunks = fresh.decode('utf-8').split('\f')
                    if chunks and not chunks[-1].strip():
                        chunks.pop()
                    check(len(chunks) == len(pages[sid]), f'Page count mismatch: {sid}')
                    page_checks = []
                    for p, text in pages[sid].items():
                        ok = p <= len(chunks) and chunks[p-1].strip() == text.strip()
                        check(ok, f'Page text mismatch: {sid} p{p}')
                        page_checks.append({'pdf_page': p, 'matches_after_outer_whitespace_trim': ok})
                    comparisons.append({'source_id': sid, 'whole_text_byte_identical': text_match, 'pages': page_checks})
            checks['independent_pdf_reextraction'] = comparisons
        else:
            checks['independent_pdf_reextraction'] = 'not rerun; use --reextract-pdfs to reproduce'

    vocab, cites = jl('vocabulary-proposals.jsonl'), jl('citation-proposals.jsonl')
    coverage = json.loads((out / 'coverage.json').read_text(encoding='utf-8'))
    ids = [v['candidate_id'] for v in vocab]
    check(len(ids) == len(set(ids)), 'Duplicate candidate_id')
    required_vocab = {'candidate_id', 'exact_term', 'aliases', 'manual_scope', 'benefit_scope', 'expansion', 'source_definition', 'proposed_plain_english', 'assertion_status', 'sources', 'unresolved_questions', 'review_status'}
    for v in vocab:
        check(required_vocab <= set(v), f'Missing vocabulary fields: {v.get("candidate_id")}')
        check(v['proposed_plain_english'].get('status') == 'model_authored_unreviewed', f'Explanation not marked unreviewed: {v["candidate_id"]}')
        check(bool(v['sources']), f'No source: {v["candidate_id"]}')
        check('unreviewed' in v['review_status'], f'Review status not unreviewed: {v["candidate_id"]}')

    ledger = coverage['rows']
    check(len(rows) == len(ledger) == 219, 'Inventory/ledger row count mismatch')
    check([r['original_row_number'] for r in ledger] == list(range(1, 220)), 'Missing or reordered original rows')
    for original, record in zip(rows, ledger):
        n = record['original_row_number']
        check(record['original_csv_row'] == original, f'Original CSV values changed: row {n}')
        check(record['exact_original_phrase'] == original['term'], f'Original phrase changed: row {n}')
        check(record['csv_record_number_including_header'] == n+1, f'CSV record index mismatch: row {n}')
        check(bool(record['candidate_ids']) and all(x in ids for x in record['candidate_ids']), f'Broken candidate link: row {n}')
        check(record['source_occurrence_check']['status'] == 'one_occurrence_independently_located_not_recounted', f'Unlocated row {n}')
        for field, value in record['counts'].items():
            check(value['original_value'] == original[field] and value['status'] == 'unverified_not_recomputed', f'Count changed or overstated: row {n}, {field}')
    check(coverage['run_status']['next_unprocessed_row'] is None, 'Unexpected next-row state')
    check(coverage['inventory_summary']['dispositions'] == dict(Counter(r['disposition'] for r in ledger)), 'Disposition summary mismatch')

    quote_checks = []
    def walk(obj: object, location: str) -> None:
        if isinstance(obj, dict):
            if 'source_id' in obj and 'exact_quote' in obj:
                sid, page, quote = obj['source_id'], obj.get('pdf_page'), obj['exact_quote']
                ok = sid in meta and obj.get('source_sha256') == meta[sid]['sha256'] and page in pages[sid] and isinstance(quote, str) and bool(quote) and quote in pages[sid][page]
                check(ok, f'Invalid exact quote/provenance: {location}')
                check(bool(obj.get('locator')), f'Missing source locator: {location}')
                quote_checks.append(ok)
            for key, val in obj.items():
                walk(val, location + '.' + key)
        elif isinstance(obj, list):
            for i, val in enumerate(obj):
                walk(val, location + f'[{i}]')
    walk(vocab, 'vocabulary'); walk(cites, 'citations'); walk(coverage, 'coverage')

    required_cite = {'paragraph_id', 'marker', 'source_pages', 'anchor_quote', 'raw_reference', 'proposed_expanded_reference', 'reference_kind', 'supporting_source', 'confidence_basis', 'unresolved_questions'}
    for c in cites:
        check(required_cite <= set(c), f'Missing citation fields: {c.get("proposal_id")}')
        for key in ['anchor_quote', 'raw_reference']:
            value = c[key]
            if value is not None:
                check(any(value in pages[s['source_id']][s['pdf_page']] for s in c['supporting_source']), f'Citation {key} is not source-exact: {c.get("proposal_id")}')
    body = [c for c in cites if c.get('marker_type') == 'superscript_source_reference']
    check(len(body) == 20, 'Expected 20 body marker records')
    for para, num in [('60025',7), ('60033',13)]:
        check(sorted(int(c['marker']) for c in body if c['paragraph_id']==para) == list(range(1,num+1)), f'Missing target markers: {para}')
    conflicts = [c for c in cites if c.get('marker_type') == 'duplicate_reference_list_label_without_unique_body_anchor']
    check(len(conflicts)==1 and conflicts[0]['marker']=='2' and conflicts[0]['anchor_quote'] is None, 'Extra conflicting 2 was lost or forcibly anchored')
    ref12 = next(c for c in body if c['paragraph_id']=='60033' and c['marker']=='12')
    check(ref12['proposed_expanded_reference'] is None, 'Unresolved reference 12 was silently expanded')

    example_text = (out / 'reading-help-examples.md').read_text(encoding='utf-8')
    blocks = re.findall(r'```text\n(.*?)\n```', example_text, re.S)
    expected = [x['exact_quote'] for x in coverage['example_quote_provenance']]
    check(blocks == expected, 'Markdown exact-source blocks differ from source provenance ledger')
    for term in ['GB', 'FTE', 'WDisP', 'Prescribed', 'SS CB Act 92', 's:', 'reg', 'Sch', 'para', 'AP']:
        check(term in example_text, 'Missing requested reading example: ' + term)

    checks.update({'vocabulary_objects':len(vocab), 'citation_objects':len(cites), 'inventory_rows':len(ledger), 'exact_source_objects_checked_including_repetitions':len(quote_checks), 'all_exact_source_objects_pass':all(quote_checks), 'markdown_source_blocks':len(blocks), 'body_marker_mappings':len(body), 'unresolved_extra_reference_entries':len(conflicts)})
    checks['artefact_hashes'] = {p.name:digest(p.read_bytes()) for p in sorted(out.iterdir()) if p.is_file() and p.name not in ['validation.json', '_ledger-temporary.json']}
    result = {'validation_status':'pass' if not errors else 'fail', 'checks':checks, 'errors':errors,
      'limits':['No occurrence frequency or classification partition has been independently validated.','No semantic, legal, current-applicability or specialist-acceptance claim is made.','Visual interpretation and model-authored explanations still require human review.','Successful source hashes prove agreement with the supplied manifest, not publisher authentication.']}
    (out / 'validation.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'validation_status':result['validation_status'], 'errors':errors, 'counts':{k:checks[k] for k in ['vocabulary_objects','citation_objects','inventory_rows','exact_source_objects_checked_including_repetitions','markdown_source_blocks']}}, indent=2))
    if errors:
        raise SystemExit(1)

if __name__ == '__main__':
    main()
