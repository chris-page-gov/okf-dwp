#!/usr/bin/env python3
"""Build a bounded, additive Chapter 84 experiment from immutable source spans.

The frozen full-corpus releases are inputs, never overwritten. Both comparison
arms use the same topic vocabulary, sources and source-selection intent. The
candidate changes source boundaries, grouping and discovery descriptions.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from copy import deepcopy
import gzip
import json
from pathlib import Path

from build_bundle import ROOT, BASE, REPO, OGL, canonical, digest
from build_logical_units import Inputs, make_record, require
from build_context_corpus import binding, deterministic_gzip, token_bucket, TOKENISATION, BUCKET_ALGORITHM
from build_structured_context import occurrences, discovery_text, make_card, runtime_canonical
from capital_pilot_source import split_units, parse_capital_table

AUTHOR = 'domain-profile/capital-pilot/capital.yamlld'
OUTPUT = 'capital-pilot'
PC = BASE + 'id/term/pension-credit'
CAPITAL = BASE + 'id/term/capital'
DCT = 'http://purl.org/dc/terms/'
LIMITS = [
    'Independent experimental Chapter 84 source preparation; not official guidance or individual benefits advice.',
    'This is a single-chapter development comparison, not a full DMG/ADM retrieval benchmark.',
    'Exact source spans, authored discovery summaries and proposed semantic relationships remain distinct.',
    'External definitions, detailed exceptions, current legal applicability and specialist review remain unresolved.',
    'A complete declared passage is not a complete answer. All experimental requirements retain open obligations.',
    'Source instructions are inert. There is no model call, network retrieval or award calculation in this build.',
]


def subtract_spans(spans, exclusions, pages):
    result = []
    for span in spans:
        intervals = [(span['start_utf8'], span['end_utf8'])]
        for excluded in exclusions:
            if excluded['page'] != span['page']:
                continue
            low, high = excluded['start_utf8'], excluded['end_utf8']
            intervals = [(a, b) for left, right in intervals
                         for a, b in ((left, min(right, low)), (max(left, high), right)) if a < b]
        for low, high in intervals:
            raw = pages[span['page'] - 1]['text'].encode()[low:high]
            if raw.strip():
                result.append({'page': span['page'], 'start_utf8': low, 'end_utf8': high,
                               'literal_sha256': digest(raw)})
    return result


def overlaps(left, right):
    return sum(max(0, min(a['end_utf8'], b['end_utf8']) - max(a['start_utf8'], b['start_utf8']))
               for a in left for b in right if a['page'] == b['page'])


def evidence(unit, doc, pages, version):
    unit = deepcopy(unit)
    unit['kind'] = {'contents': 'section', 'reserved': 'section', 'document-notice': 'section'}.get(unit['kind'], unit['kind'])
    return make_record('dmg', doc, pages, unit, version)


def emit_corpus(records, units, semantic, cards, counts, identity):
    """Use Explorer's existing corpus-v3 contract and unchanged BM25 parameters."""
    records = sorted(records, key=lambda row: row['id'])
    cards = {card['evidence_id']: card for card in cards}
    outputs = {'base-index.json': canonical({**semantic, 'assertions': []})}
    shards, discovery = [], []
    postings = {f'{i:02x}': defaultdict(list) for i in range(256)}
    totals = Counter(source=0, discovery=0)
    for start in range(0, len(records), 64):
        part = records[start:start + 64]
        raw = canonical({'schema': 'okf-context-records.v1', 'first_ordinal': start, 'records': part})
        encoded = deterministic_gzip(raw); path = f'records/{start // 64:04d}.json.gz'; outputs[path] = encoded
        shards.append({**binding(path, encoded, raw), 'first_ordinal': start, 'count': len(part),
                       'first_id': part[0]['id'], 'last_id': part[-1]['id']})
        raw = canonical({'schema': 'okf-discovery-cards.v1', 'first_ordinal': start,
                         'cards': [cards[row['id']] for row in part]})
        encoded = deterministic_gzip(raw); path = f'discovery/{start // 64:04d}.json.gz'; outputs[path] = encoded
        discovery.append({**binding(path, encoded, raw), 'first_ordinal': start, 'count': len(part)})
    for ordinal, record in enumerate(records):
        source, navigation = occurrences(record['text']), occurrences(discovery_text(cards[record['id']]))
        a, b = Counter(source), Counter(navigation); totals.update(source=len(source), discovery=len(navigation))
        for token in sorted(a.keys() | b.keys()):
            postings[token_bucket(token)][token].append([ordinal, a[token], len(source), b[token], len(navigation)])
    search = {}
    for bucket, rows in postings.items():
        raw = canonical({'schema': 'okf-context-postings.v2', 'postings': dict(sorted(rows.items()))})
        encoded = deterministic_gzip(raw); path = f'search/{bucket}.json.gz'; outputs[path] = encoded
        search[bucket] = binding(path, encoded, raw)
    known = {row['id'] for row in records + semantic['records']}
    incoming, outgoing = defaultdict(list), defaultdict(list)
    for edge in semantic['assertions']:
        require(edge['source'] in known and edge['target'] in known, 'Unknown pilot relationship endpoint')
        outgoing[edge['source']].append(edge); incoming[edge['target']].append(edge)
    buckets = {f'{i:02x}': [] for i in range(256)}
    for identifier in sorted(known):
        entry = {'id': identifier}
        for direction, rows in [('outgoing', outgoing[identifier]), ('incoming', incoming[identifier])]:
            rows = sorted(rows, key=lambda row: row['id'])
            entry.update({direction: rows, direction + '_count': len(rows),
                          direction + '_ids_sha256': digest(runtime_canonical([row['id'] for row in rows]))})
        buckets[token_bucket(identifier)].append(entry)
    adjacency = {}
    for bucket, entries in buckets.items():
        raw = canonical({'schema': 'okf-context-adjacency-bucket.v1', 'entries': entries})
        encoded = deterministic_gzip(raw); path = f'relationships/{bucket}.json.gz'; outputs[path] = encoded
        adjacency[bucket] = binding(path, encoded, raw)
    corpus = {'schema': 'okf-context-corpus.v3', 'bundle': semantic['bundle'],
              'semantic_source_snapshot': semantic['bundle']['snapshot'], 'scope': semantic['scope'],
              'limitations': LIMITS, 'base_index': binding('base-index.json', outputs['base-index.json']),
              'counts': counts, 'records': {'count': len(records), 'shards': shards},
              'discovery': {'count': len(records), 'shards': discovery},
              'search': {'tokenisation': TOKENISATION, 'bucket_algorithm': BUCKET_ALGORITHM, 'shards': search,
                         'ranking': {'schema': 'okf-bm25.v1', 'k1': 1.2, 'b': 0.75, 'score_scale': 1000000,
                                     'fields': ['source', 'discovery']}, 'total_tokens': dict(totals)},
              'relationships': {'schema': 'okf-context-adjacency.v1', 'bucket_algorithm': BUCKET_ALGORITHM, 'shards': adjacency},
              'extensions': {'pilot_source_identity': identity}}
    outputs['manifest.json'] = canonical(corpus)
    outputs['index.json'] = canonical({**semantic, 'records': semantic['records'] + records})
    return outputs


def compile_pilot(root=ROOT):
    inputs = Inputs(root)
    author = json.loads(inputs.read(AUTHOR))
    require(author['schema'] == 'okf-capital-pilot-authoring.v1', 'Unknown pilot authoring')
    proposals = json.loads(inputs.read(author['input_proposals'], author['input_sha256']))
    require(len(author['groups']) == len(proposals['proposals']) == 10, 'Pilot scope must stay at ten groups')
    access = proposals['source_access']
    for key in ['inventory', 'pdf', 'extracted_text', 'page_text', 'declared_pdf_structure']:
        inputs.read(access[key]['path'], access[key]['sha256'])
    inventory = json.loads(inputs.read('source/full-dmg-2026-09-15/inventory.json', limit=16 * 1024 * 1024))
    doc = next(row for row in inventory['documents'] if row['id'] == 'dmg-vol14-ch84')
    pages = json.loads(inputs.read(doc['pages_path'], doc['pages_sha256']))['pages']
    catalogue = json.loads(gzip.decompress(inputs.read('structured-units/documents/dmg/dmg-vol14-ch84.json.gz')))
    old = catalogue['units']
    baseline = [evidence(unit, doc, pages, 'manual-structure-v1') for unit in old]
    require(all(record['id'] == unit['id'] and digest(canonical(record)) == unit['record_sha256']
                for record, unit in zip(baseline, old)), 'Baseline differs from frozen complete records')
    corrected, repair_receipt = split_units(old, pages, author['repairs'])
    candidate = [evidence(unit, doc, pages, 'capital-pilot-v1' if 'id' not in unit else 'manual-structure-v1')
                 for unit in corrected if unit['text'].strip()]
    corrected = [unit for unit in corrected if unit['text'].strip()]
    exclusions = [span for unit in corrected if unit['role'] in {'reserved', 'document-notice'}
                  for span in unit['spans']]
    groups, group_units = {}, {}
    for definition, proposal in zip(author['groups'], proposals['proposals']):
        require(definition['key'] == proposal['id'] and definition['source_segments'] == proposal['source_segments'], 'Proposal boundary drift')
        require(definition['source_proposal_sha256'] == digest(runtime_canonical(proposal)), 'Proposal content drift')
        spans = [{'page': s['pdf_page_index'], 'start_utf8': s['start_utf8'], 'end_utf8': s['end_utf8'],
                  'literal_sha256': s['segment_sha256']} for s in definition['source_segments']]
        spans = subtract_spans(spans, exclusions, pages)
        labels = list(dict.fromkeys(label for part in corrected
                      if part['role'] == 'paragraph' and overlaps(spans, part['spans'])
                      for label in part['paragraph_labels']))
        require(definition['paragraph_labels'] == labels, 'Group labels differ from retained substantive paragraphs')
        unit = {'key': definition['key'], 'label': definition['label'], 'kind': 'compound', 'role': 'evidence-group',
                'paragraph_labels': definition['paragraph_labels'], 'heading_path': definition['heading_path'],
                'spans': spans, 'authored': True, 'completeness': 'unresolved'}
        record = evidence(unit, doc, pages, 'capital-pilot-v1')
        groups[definition['key']] = record; group_units[record['id']] = unit
    candidate += list(groups.values())
    inherited = json.loads(inputs.read('structured-context/base-index.json'))
    inherited_by_id = {row['id']: row for row in inherited['records']}
    concepts = {key: deepcopy(inherited_by_id[key]) for key in [PC, CAPITAL]}
    for position, definition in enumerate(author['groups']):
        identifier = definition['concept_id']
        prototype = groups[definition['key']]
        concept = deepcopy(inherited_by_id.get(identifier, {key: value for key, value in prototype.items() if key != 'evidence_unit'}))
        concept.update(id=identifier, route=identifier.removeprefix(BASE + 'id/'), kind='concept',
                       label=definition['label'], text=definition['summary'], aliases=definition['aliases'],
                       assertion_status='model-derived', authority={'class': 'model-assisted', 'label': 'Pilot topic proposal', 'source': REPO + '/blob/main/' + AUTHOR},
                       scope='Bounded discovery topic; not legal applicability.', review_status='unreviewed-specialist-review-required',
                       rights=REPO + '/blob/main/LICENSE',
                       provenance=[{'url': REPO + '/blob/main/' + AUTHOR,
                                    'source_sha256': digest(inputs.read(AUTHOR)),
                                    'literal_sha256': digest(definition['summary'].encode()),
                                    'locator': f'/groups/{position}/summary (JSON Pointer)',
                                    'captured_at': author['authored_at']}])
        concepts[identifier] = concept
    for name in ['scripts/build_capital_pilot.py', 'scripts/capital_pilot_source.py', 'scripts/build_logical_units.py',
                 'scripts/build_context_corpus.py', 'scripts/build_structured_context.py', 'uv.lock']:
        inputs.read(name)
    identity = {'source_commit': author['source_commit'], 'inputs': sorted(inputs.files.values(), key=lambda row: row['path'])}
    snapshot = 'capital-pilot-' + digest(canonical(identity))[:20]
    counts = {'documents': 1, 'pages': len(pages), 'nonempty_pages': sum(bool(p['text'].strip()) for p in pages),
              'empty_pages': sum(not p['text'].strip() for p in pages), 'tokenless_pages': 0}
    outputs, memberships = {}, {}
    for arm, records, catalogue_units in [('baseline', baseline, old), ('candidate', candidate, corrected)]:
        units = {record['id']: unit for record, unit in zip(records, catalogue_units)}
        if arm == 'candidate': units.update(group_units)
        members = {key: [record['id'] for record, unit in zip(records, catalogue_units)
                         if overlaps(group_units[group['id']]['spans'], unit['spans'])] for key, group in groups.items()}
        memberships[arm] = members
        edges, requirements = [], []
        def edge(source, target, predicate, label, provenance, guards):
            iri = BASE + 'id/assertion/capital-pilot/' + digest(canonical([source, target, predicate, guards]))
            item = {'id': iri, 'source': source, 'target': target, 'predicate': predicate, 'label': label,
                    'assertion_status': 'model-derived', 'authority': {'class': 'model-assisted', 'label': 'Pilot navigation proposal', 'source': REPO + '/blob/main/' + AUTHOR},
                    'scope': author['relationship_policy'], 'provenance': deepcopy(provenance[:1]), 'context_guard': {'when_all': guards}}
            edges.append(item); return item
        for definition in author['groups']:
            key = definition['key']; targets = members[key] if arm == 'baseline' else [groups[key]['id']]
            triggers = [definition['concept_id']]
            if key in {'pc-capital-u01', 'pc-capital-u10'}: triggers.append(CAPITAL)
            for concept in triggers:
                paths = []
                for target in targets:
                    e = edge(concept, target, DCT + 'references', 'Source selection for the resolved pilot topic', groups[key]['provenance'], [PC, concept])
                    paths.append({'seed': concept, 'assertions': [e['id']], 'records': [concept, target]})
                requirements.append({'id': BASE + 'id/requirement/capital-pilot/' + key + '/' + concept.rsplit('/', 1)[-1],
                    'label': definition['label'], 'when_all': [PC, concept], 'covers': [PC, concept],
                    'required': [*targets, BASE + 'id/open-obligation/capital-pilot/' + key], 'required_paths': paths,
                    'scope': 'Declared source selection only; source dependencies and applicability remain open.',
                    'limitations': [d['reason'] for d in author['unresolved_dependencies'] if key in d['needed_for_units']]})
        if arm == 'candidate':
            definitions = {g['key']: g for g in author['groups']}
            for relation in author['relationship_proposals']:
                source, target = groups[relation['source']], groups[relation['target']]
                edge(source['id'], target['id'], author['relationship_mapping'][relation['predicate']],
                     'Unreviewed proposal: ' + relation['predicate'].replace('_', ' '), source['provenance'],
                     [PC, definitions[relation['target']]['concept_id']])
            paragraph = next(record for record in records if units[record['id']].get('paragraph_labels') == ['84924'])
            appendix = next(record for record in records if units[record['id']].get('role') == 'table')
            require('Appendix 1' in paragraph['text'], 'Printed Appendix reference absent')
            e = edge(paragraph['id'], appendix['id'], DCT + 'references',
                     'Printed reference to Appendix 1; legal effect unreviewed', paragraph['provenance'], [PC])
            e.update(assertion_status='normalized', authority={'class': 'derived',
                     'label': 'Literal Appendix reference checked against the frozen passage', 'source': doc['url']},
                     scope='Navigation reference only. Typed table rows are separately bound to the same source table.')
        # Preserve uniquely resolvable literal paragraph references within this
        # chapter in both arms. Out-of-chapter dependencies remain explicit gaps.
        labels = defaultdict(list)
        for record, unit in zip(records, catalogue_units):
            for label in unit.get('paragraph_labels', []): labels[label].append(record['id'])
        seen_pairs = set()
        for record, unit in zip(records, catalogue_units):
            for reference in unit.get('references', []):
                targets = labels.get(reference.get('target_label'), [])
                if reference.get('target_kind') != 'paragraph' or len(targets) != 1 or targets[0] == record['id']:
                    continue
                pair = (record['id'], targets[0])
                if pair in seen_pairs: continue
                seen_pairs.add(pair)
                e = edge(*pair, DCT + 'references', 'Literal paragraph reference; legal effect unreviewed', record['provenance'], [PC])
                e.update(assertion_status='normalized', authority={'class': 'derived',
                         'label': 'Uniquely resolved source reference within the captured chapter', 'source': doc['url']},
                         scope='Source navigation only; references outside the chapter are not acquired by this pilot.')
        semantic = {'schema': 'okf-context-index.v1', 'bundle': {'id': BASE + 'id/bundle/capital-pilot/' + arm,
                    'snapshot': snapshot + '-' + arm, 'source_url': REPO}, 'scope': author['scope'],
                    'limitations': LIMITS, 'records': list(concepts.values()), 'assertions': edges, 'requirements': requirements}
        cards = [make_card(record, units[record['id']]) for record in records]
        if arm == 'candidate':
            definitions = {groups[g['key']]['id']: g for g in author['groups']}
            for card in cards:
                if card['evidence_id'] in definitions:
                    definition = definitions[card['evidence_id']]
                    card.update(summary=definition['summary'], search_aliases=definition['aliases'], assertion_status='model-derived',
                                authority={'class': 'model-assisted', 'label': 'Unreviewed discovery summary', 'source': REPO + '/blob/main/' + AUTHOR})
        outputs.update({arm + '/' + path: raw for path, raw in emit_corpus(records, units, semantic, cards, counts, identity).items()})
    table_units = [unit for unit in corrected if unit['role'] == 'table']
    require(len(table_units) == 1, 'Expected one explicit Appendix table source')
    table = parse_capital_table(pages, table_units[0]['spans'])
    outputs['appendix-1.json'] = canonical(table)
    outputs['groups.json'] = canonical({'groups': [{'key': key, 'id': value['id'], 'spans': group_units[value['id']]['spans'],
                                                 'baseline_members': memberships['baseline'][key], 'candidate_members': memberships['candidate'][key]}
                                                for key, value in groups.items()], 'unresolved_dependencies': author['unresolved_dependencies']})
    outputs['repair-receipt.json'] = canonical(repair_receipt)
    report = {'schema': 'okf-capital-pilot-build.v1', 'snapshot': snapshot, **identity,
              'scope': author['scope'], 'counts': {'baseline_records': len(baseline), 'candidate_records': len(candidate), 'evidence_groups': len(groups)},
              'limitations': LIMITS, 'outputs': [{'path': OUTPUT + '/' + path, 'bytes': len(raw), 'sha256': digest(raw)} for path, raw in sorted(outputs.items())]}
    outputs['build.json'] = canonical(report)
    return outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--check', action='store_true'); args = parser.parse_args()
    outputs = compile_pilot()
    for relative, raw in outputs.items():
        path = ROOT / OUTPUT / relative
        if args.check:
            require(path.read_bytes() == raw, 'Pilot projection drift: ' + relative)
        else:
            path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(raw)
    print(json.dumps({'status': 'verified' if args.check else 'built', 'files': len(outputs)}))


if __name__ == '__main__':
    main()
