#!/usr/bin/env python3
"""Resolve literal DMG references to candidate locations, without legal inference."""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import re

from build_bundle import ROOT, canonical, digest

OUTPUT = "evaluation/full-dmg-dependencies"


def paragraph_starts(text, chapter):
    """Candidate body starts only; contents ranges and bare numbers are excluded."""
    result = []
    for match in re.finditer(r"(?m)^[ \t]*(\d{5,6})[ \t]+(?=[A-Za-z\[])", text):
        value = match[1]
        # A wrapped cross-reference can begin a new extracted line. These
        # continuations identify references, not the cited paragraph's body.
        if re.match(r"(?:et\s+seq\b|for\s+guidance\b)", text[match.end():], re.IGNORECASE):
            continue
        if (len(value) == 6 and chapter == 7 and value.startswith('07')) or (len(value) == 5 and chapter != 7 and int(value[:2]) == chapter):
            result.append((value, match.start(1)))
    return result


def resolution(candidates):
    return "single-acquired-location-candidate" if len(candidates) == 1 else "ambiguous-acquired-locations" if candidates else "no-acquired-location-resolved"


def build(root=ROOT):
    inventory_path = "source/full-dmg-2026-09-15/inventory.json"
    inventory = json.loads((root / inventory_path).read_text())
    evidence_path = "evaluation/full-dmg-evidence/index.json"
    evidence = json.loads((root / evidence_path).read_text())
    documents = {doc['id']: doc for doc in inventory['documents']}
    paragraphs, memos = defaultdict(list), defaultdict(list)
    for doc in documents.values():
        if doc['kind'] == 'memo':
            match = re.search(r"(?i)\bmemo\s+(\d{1,2})[/\-](\d{2})\b", doc['title'])
            if match:
                memos[f'{int(match[1])}/{match[2]}'].append({'document_id':doc['id'], 'title':doc['title'], 'url':doc['url'], 'source_sha256':doc['sha256'], 'role':doc['role']})
        if doc['role'] != 'substantive':
            continue
        raw_pages = (root / doc['pages_path']).read_bytes()
        if digest(raw_pages) != doc['pages_sha256']:
            raise ValueError('Source page identity changed: ' + doc['id'])
        pages = json.loads(raw_pages)['pages']
        for page in pages:
            for label, offset in paragraph_starts(page['text'], doc['chapter']):
                paragraphs[label].append({'document_id':doc['id'], 'pdf_page':page['page'], 'url':page['url'], 'source_sha256':doc['sha256'], 'page_text_sha256':digest(page['text'].encode()), 'label_start':offset})
    outputs, rows, counts = {}, [], Counter()
    for entry in evidence['documents']:
        raw = (root / entry['path']).read_bytes()
        if digest(raw) != entry['sha256']:
            raise ValueError('Reference discovery input changed')
        source = json.loads(raw)
        doc = documents[source['document_id']]
        citations = []
        for candidate in source['candidates']:
            kind = candidate['kind']
            if kind not in ['dmg-paragraph-reference', 'dmg-memo-reference', 'dmg-unresolved-digit-reference', 'legal-reference-line-candidate']:
                continue
            item = {'evidence_id':candidate['id'], 'kind':kind, 'literal':candidate['quote'], 'source_pdf_page':candidate['pdf_page'],
                    'source_url':candidate['url'], 'source_page_text_sha256':candidate['page_text_sha256'],
                    'literal_sha256':candidate['quote_sha256'], 'source_start':candidate['start'], 'source_end':candidate['end']}
            if kind == 'dmg-paragraph-reference':
                targets = paragraphs.get(candidate['target_label'], [])
                item.update(target_label=candidate['target_label'], range_end=candidate.get('range_end'),
                            location_status=resolution(targets), target_candidates=targets)
                if candidate.get('range_end'):
                    item['range_end_candidates'] = paragraphs.get(candidate['range_end'], [])
                    item['range_policy'] = 'Only end points are located; intervening paragraphs and continuity are not inferred.'
            elif kind == 'dmg-memo-reference':
                first, year = candidate['target_label'].split('/')
                targets = memos.get(f'{int(first)}/{year}', [])
                item.update(target_label=candidate['target_label'], location_status=resolution(targets), target_candidates=targets)
            else:
                item.update(location_status='unresolved-identifier-and-version' if kind == 'legal-reference-line-candidate' else 'ambiguous-digit-run', target_candidates=[])
            item['legal_applicability'] = 'not-established'
            item['incorporation_status'] = 'not-established'
            counts[item['location_status']] += 1
            citations.append(item)
        path = OUTPUT + '/' + doc['id'] + '.json'
        payload = {'schema':'okf-dwp-source-dependencies.v1', 'document_id':doc['id'], 'source_sha256':doc['sha256'], 'source_role':doc['role'],
                   'evidence_artifact':entry['path'], 'evidence_sha256':entry['sha256'], 'citations':citations,
                   'status':'candidate-location-reconciliation; legal-identity-version-and-applicability-unreviewed'}
        outputs[path] = canonical(payload)
        rows.append({'document_id':doc['id'], 'path':path, 'sha256':digest(outputs[path]), 'citations':len(citations),
                     'states':dict(sorted(Counter(x['location_status'] for x in citations).items()))})
    inputs = [inventory_path,evidence_path,'scripts/reconcile_full_dmg_references.py']
    outputs[OUTPUT + '/index.json'] = canonical({'schema':'okf-dwp-dependency-index.v1',
        'inputs':[{'path':p,'sha256':digest((root/p).read_bytes())} for p in inputs],
        'documents':rows, 'document_count':len(rows), 'citation_count':sum(counts.values()), 'states':dict(sorted(counts.items())),
        'meaning':'Candidate navigation between acquired source locations; no asserted legal identity, equivalence, amendment incorporation or current applicability.',
        'limitations':['Paragraph-start recognition can miss line breaks and damaged extraction; no match is an unresolved location, not proof of absence.',
                       'Obvious wrapped references beginning et seq or for guidance are excluded from body-start candidates; other candidates still need contextual review.',
                       'Single location candidates are mechanical matches and require contextual review.',
                       'Statutes, regulations, tribunal decisions, ADM provisions and CPAG body text are not acquired by this reconciliation.',
                       'Source role and observation dates are not legal effective dates.']})
    return outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    files = build()
    for path,data in files.items():
        target = ROOT / path
        if args.check:
            if not target.is_file() or target.read_bytes() != data:
                raise SystemExit('Dependency register differs: ' + path)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
    index = json.loads(files[OUTPUT + '/index.json'])
    print(json.dumps({k:index[k] for k in ['document_count','citation_count','states']}))


if __name__ == '__main__':
    main()
