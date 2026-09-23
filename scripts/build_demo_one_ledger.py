#!/usr/bin/env python3
"""Generate a readable forty-question ledger from frozen cases and observations."""
import argparse
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def build():
    readiness=json.loads((ROOT/'evaluation/demo-1-freeze/readiness-2026-09-23.json').read_bytes())
    raw=(ROOT/readiness['cases_binding']['path']).read_bytes()
    assert hashlib.sha256(raw).hexdigest()==readiness['cases_binding']['sha256']
    cases=json.loads(raw)['cases']; rows=readiness['coverage'];assert len(cases)==len(rows)==40
    lines=['# Demo 1: all forty questions', '',
        'This ledger keeps the supplied question wording and repeated occurrences. Every',
        'result remains **insufficient**; every large package reports retrieval and assembly',
        'truncation. A retained source-selection path is a review lead, not a verified answer.',
        'Only staff-006 and staff-012 have new paired model responses in this freeze.', '',
        '[Freeze and demonstration](demo-one-freeze-2026-09-23.md) · [Four-answer results](demo-one-pair-results.md) · [Detailed source results](source-led-results.md)', '',
        '| Case | Exact question | Source-read profile | Source passages | Declared source-selection paths retained / required | Frozen audit |',
        '| --- | --- | --- | ---: | ---: | --- |']
    for c,r in zip(cases,rows):
        assert c['id']==r['id'] and hashlib.sha256(c['question'].encode()).hexdigest()==r['question_sha256']
        q=c['question'].replace('|','\\|').replace('\n',' ')
        paths=f"{r['source_selection_paths_retained']} / {r['source_selection_paths_required']}"
        active='Active' if r['source_read_profile_active'] else 'Scope unresolved'
        lines.append(f"| {c['id']} | {q} | {active} | {r['source_units']} | {paths} | [Package](../{r['archive']}) |")
    lines+=['', 'The audit links download gzip-compressed JSON. Decompress them to inspect the',
        'complete retained context. The machine-readable [readiness record](../evaluation/demo-1-freeze/readiness-2026-09-23.json)',
        'binds the brief, source report and exact question hashes. No source has been',
        'recaptured and no legal obligation is closed by this table.']
    return '\n'.join(lines)+'\n'

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args()
    out=ROOT/'docs/demo-one-question-ledger.md';value=build()
    if a.check: assert out.read_text()==value
    else: out.write_text(value)
    print('Forty-question ledger verified' if a.check else 'Forty-question ledger generated')
