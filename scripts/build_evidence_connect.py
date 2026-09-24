#!/usr/bin/env python3
"""Build a small, hash-bound connect overlay over frozen full DMG and ADM units."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from copy import deepcopy
import gzip
import json
from pathlib import Path

from build_bundle import BASE, ROOT, REPO, canonical, digest
from build_context_corpus import binding, deterministic_gzip, token_bucket
from build_logical_units import require
from build_structured_context import discovery_text, make_card, occurrences, runtime_canonical

AUTHOR = 'domain-profile/evidence-connect/profile.json'
SOURCE = 'structured-context/manifest.json'
PILOT = 'capital-pilot/candidate/index.json'
OUTPUT = 'structured-context/evidence-connect-manifest.json'
PREFIX = 'evidence-connect/'
DCT = 'http://purl.org/dc/terms/'
RANKING = {'schema': 'okf-bm25-weighted.v2', 'k1': 1.2, 'b': 0.75,
           'score_scale': 1000000, 'fields': ['source', 'discovery'],
           'weights': {'source': 1, 'discovery': 2}}


def content(root: Path, relative: str) -> bytes:
    path = root / relative
    require(path.is_file() and not path.is_symlink(), 'Missing or linked input: ' + relative)
    return path.read_bytes()


def compile_connect(root: Path = ROOT) -> dict[str, bytes]:
    authored_raw, original_raw, pilot_raw = (content(root, name) for name in (AUTHOR, SOURCE, PILOT))
    authored, original, pilot = (json.loads(raw) for raw in (authored_raw, original_raw, pilot_raw))
    require(authored['schema'] == 'okf-evidence-connect-authoring.v1', 'Unknown authoring schema')
    require(authored['source_pilot'] == PILOT and authored['source_full_corpus'] == SOURCE
            and authored['source_groups'] == 'capital-pilot/groups.json', 'Declared source paths differ')
    require(original['schema'] == 'okf-context-corpus.v3', 'Expected full structured corpus')
    require(len(authored['groups']) == 10, 'Ten pilot groups required')
    pilot_groups = {row['id'].split('/')[-1].rsplit('-', 1)[0]: row for row in pilot['records']
                    if row['id'].split('/')[-1].startswith('pc-capital-u')}
    require(len(pilot_groups) == 10, 'Pilot source records missing')
    groups_raw = content(root, authored['source_groups'])
    capital_raw = content(root, 'domain-profile/capital-pilot/capital.yamlld')
    capital_author = json.loads(capital_raw)
    producer_files = {name: digest(content(root, name)) for name in (
        'scripts/build_evidence_connect.py', 'scripts/build_structured_context.py',
        'scripts/build_context_corpus.py', 'scripts/build_bundle.py')}
    pilot_group_rows = json.loads(groups_raw)['groups']
    require(len(pilot_group_rows) == 10 and {row['key']: row['id'] for row in pilot_group_rows}
            == {key: row['id'] for key, row in pilot_groups.items()}, 'Pilot group declaration drift')
    group_records, group_cards, by_key = [], [], {}
    for definition in authored['groups']:
        key = definition['key']
        require(key in pilot_groups, 'Unknown group: ' + key)
        source = pilot_groups[key]
        record = deepcopy(source)
        record['id'] = BASE + 'id/unit/zz-evidence-connect/' + key
        record['route'] = 'unit/zz-evidence-connect/' + key
        record['scope'] += ' This successor retains the source span and adds unreviewed navigation links.'
        group_records.append(record)
        by_key[key] = record['id']
        card = make_card(record, {'heading_path': [], 'paragraph_labels': []})
        card.update(summary=source['label'] + '. ' + next(g['summary'] for g in
                    capital_author['groups'] if g['key'] == key),
                    search_aliases=definition['search_aliases'], assertion_status='model-derived',
                    authority={'class': 'model-assisted', 'label': 'Source-led discovery wording; unreviewed',
                               'source': REPO + '/blob/main/' + AUTHOR},
                    scope=definition['alias_scope'], provenance=[{
                        'url': REPO + '/blob/main/' + AUTHOR, 'source_sha256': digest(authored_raw),
                        'literal_sha256': digest(canonical(definition)), 'locator': '/groups/' + key,
                        'captured_at': authored['authored_at']}])
        if definition.get('route_patterns'):
            card['route_patterns'] = definition['route_patterns']
        group_cards.append(card)
    require(group_records == sorted(group_records, key=lambda row: row['id']), 'Group record order')

    outputs: dict[str, bytes] = {}
    manifest = deepcopy(original)
    count = original['records']['count']
    records_raw = canonical({'schema': 'okf-context-records.v1', 'first_ordinal': count, 'records': group_records})
    records_zip = deterministic_gzip(records_raw)
    outputs[PREFIX + 'records.json.gz'] = records_zip
    manifest['records']['shards'].append({**binding(PREFIX + 'records.json.gz', records_zip, records_raw),
        'first_ordinal': count, 'count': len(group_records), 'first_id': group_records[0]['id'],
        'last_id': group_records[-1]['id']})
    cards_raw = canonical({'schema': 'okf-discovery-cards.v1', 'first_ordinal': count, 'cards': group_cards})
    cards_zip = deterministic_gzip(cards_raw)
    outputs[PREFIX + 'discovery.json.gz'] = cards_zip
    manifest['discovery']['shards'].append({**binding(PREFIX + 'discovery.json.gz', cards_zip, cards_raw),
                                           'first_ordinal': count, 'count': len(group_cards)})
    manifest['records']['count'] += len(group_records)
    manifest['discovery']['count'] += len(group_cards)

    updates = defaultdict(lambda: defaultdict(list))
    for offset, (record, card) in enumerate(zip(group_records, group_cards)):
        source, discovery = occurrences(record['text']), occurrences(discovery_text(card))
        manifest['search']['total_tokens']['source'] += len(source)
        manifest['search']['total_tokens']['discovery'] += len(discovery)
        a, b = Counter(source), Counter(discovery)
        for token in sorted(a.keys() | b.keys()):
            updates[token_bucket(token)][token].append([count + offset, a[token], len(source), b[token], len(discovery)])
    for bucket, rows in sorted(updates.items()):
        ref = original['search']['shards'][bucket]
        old = json.loads(gzip.decompress(content(root, 'structured-context/' + ref['path'])))
        require(old['schema'] == 'okf-context-postings.v2', 'Unexpected posting schema')
        for token, entries in rows.items(): old['postings'].setdefault(token, []).extend(entries)
        raw = canonical({'schema': old['schema'], 'postings': dict(sorted(old['postings'].items()))})
        packed = deterministic_gzip(raw)
        name = PREFIX + 'search/' + bucket + '.json.gz'
        outputs[name] = packed
        manifest['search']['shards'][bucket] = binding(name, packed, raw)
    manifest['search']['ranking'] = RANKING
    # Alias routes are a small, exact phrase index over the same hashed cards.
    # The engine verifies each matched phrase against its bound card on hydration.
    # A direct phrase route must carry an explicit benefit qualifier. Unscoped
    # wording stays in the scored card index but cannot bypass the shortlist.
    manifest['search']['alias_routes'] = sorted(
        [{'ordinal': count + offset, 'phrase': phrase}
         for offset, card in enumerate(group_cards) for phrase in card['search_aliases']
         if len(occurrences(phrase)) >= 2 and
         ('pension credit' in phrase.lower() or 'state pension credit' in phrase.lower())] +
        [{'ordinal': count + offset, 'pattern': pattern}
         for offset, card in enumerate(group_cards) for pattern in card.get('route_patterns', [])],
        key=lambda row: (row['ordinal'], row.get('phrase', row.get('pattern', {}).get('id', ''))))
    require(len(manifest['search']['alias_routes']) <= 2000, 'Too many alias routes')

    base_ref = original['base_index']
    base = json.loads(content(root, 'structured-context/' + base_ref['path']))
    known_concepts = {row['id'] for row in base['records']}
    pilot_base = json.loads(content(root, 'capital-pilot/candidate/base-index.json'))
    pilot_topics = {row['id']: row for row in pilot_base['records'] if row['kind'] == 'concept'}
    group_defs = {row['key']: row for row in capital_author['groups']}
    edges = []
    def edge(src, dst, label, guards, evidence):
        item = {'id': BASE + 'id/assertion/evidence-connect/' + digest(canonical([src, dst, label])),
                'source': src, 'target': dst, 'predicate': DCT + 'references', 'label': label,
                'assertion_status': 'model-derived',
                'authority': {'class': 'model-assisted', 'label': 'Unreviewed source navigation proposal',
                              'source': REPO + '/blob/main/' + AUTHOR},
                'scope': 'Navigation to captured source only; legal effect and applicability unreviewed.',
                'provenance': evidence}
        if guards:
            item['context_guard'] = {'when_all': guards}
        edges.append(item)
        return item
    pc = BASE + 'id/term/pension-credit'
    group_paths = {}
    for key, target in by_key.items():
        concept = group_defs[key]['concept_id']
        if concept not in known_concepts:
            require(concept in pilot_topics, 'Missing topic concept')
            base['records'].append(pilot_topics[concept]); known_concepts.add(concept)
        group_paths[key] = edge(concept, target, 'Source selection for the proposed capital topic', [pc, concept],
                                pilot_groups[key]['provenance'][:1])
    for proposal in capital_author['relationship_proposals']:
        edge(by_key[proposal['source']], by_key[proposal['target']],
             'Pilot relationship proposal: ' + proposal['predicate'].replace('_', ' '), [pc],
             pilot_groups[proposal['source']]['provenance'][:1])
    # A captured target is verified against the full record shard before linking.
    checked = set()
    for dependency in authored['linked_captured_dependencies']:
        for target in dependency['target_record_ids']:
            if target not in checked:
                shard = next((s for s in original['records']['shards'] if s['first_id'] <= target <= s['last_id']), None)
                require(shard is not None, 'Dependency target outside frozen corpus: ' + target)
                data = json.loads(gzip.decompress(content(root, 'structured-context/' + shard['path'])))
                require(any(r['id'] == target for r in data['records']), 'Dependency target absent: ' + target)
                checked.add(target)
            for key in dependency['needed_for_units']:
                edge(by_key[key], target, 'Captured source entry: ' + dependency['source_reference'], [],
                     pilot_groups[key]['provenance'][:1])
    base['bundle'] = {'id': BASE + 'id/bundle/evidence-connect',
                      'snapshot': 'evidence-connect-' + digest(canonical({
                          'profile': digest(authored_raw), 'full_corpus': digest(original_raw),
                          'pilot_index': digest(pilot_raw), 'pilot_groups': digest(groups_raw),
                          'pilot_author': digest(capital_raw), 'producer_files': producer_files}))[:20],
                      'source_url': REPO}
    base['scope'] += ' Additive capital discovery groups over the full DMG and ADM structured corpus.'
    base['limitations'] += authored['limitations']
    for key, target in by_key.items():
        concept = group_defs[key]['concept_id']
        path = group_paths[key]
        base['requirements'].append({
            'id': BASE + 'id/requirement/evidence-connect/' + key,
            'label': group_defs[key]['label'], 'when_all': [pc, concept],
            'covers': [pc, concept],
            'required': [target, BASE + 'id/open-obligation/evidence-connect/' + key],
            'required_paths': [{'seed': concept, 'assertions': [path['id']],
                                'records': [concept, target]}],
            'scope': 'Declared source selection only; source dependencies, dates and applicability remain open.',
            'limitations': [d['id'] + ': ' + d['prior_classification']
                            for d in authored['dependency_census']
                            if key in next((original['needed_for_units'] for original in
                                capital_author['unresolved_dependencies']
                                if original['id'] == d['id']), [])] or authored['limitations']})
    base_raw = canonical(base)
    outputs[PREFIX + 'base-index.json'] = base_raw
    manifest['base_index'] = binding(PREFIX + 'base-index.json', base_raw)
    manifest['bundle'] = base['bundle']
    manifest['scope'] = base['scope']
    manifest['limitations'] += authored['limitations']
    manifest['semantic_source_snapshot'] = base['bundle']['snapshot']

    changed = defaultdict(list)
    for item in edges:
        changed[token_bucket(item['source'])].append(item)
        changed[token_bucket(item['target'])].append(item)
    for bucket in sorted(changed):
        ref = original['relationships']['shards'][bucket]
        data = json.loads(gzip.decompress(content(root, 'structured-context/' + ref['path'])))
        entries = {row['id']: row for row in data['entries']}
        for item in changed[bucket]:
            for endpoint, direction in [(item['source'], 'outgoing'), (item['target'], 'incoming')]:
                if token_bucket(endpoint) != bucket: continue
                row = entries.setdefault(endpoint, {'id': endpoint, 'outgoing': [], 'incoming': []})
                row[direction].append(item)
        for row in entries.values():
            for direction in ('outgoing', 'incoming'):
                row[direction] = sorted({e['id']: e for e in row[direction]}.values(), key=lambda e: e['id'])
                row[direction + '_count'] = len(row[direction])
                row[direction + '_ids_sha256'] = digest(runtime_canonical([e['id'] for e in row[direction]]))
        raw = canonical({'schema': 'okf-context-adjacency-bucket.v1',
                         'entries': sorted(entries.values(), key=lambda row: row['id'])})
        packed = deterministic_gzip(raw)
        name = PREFIX + 'relationships/' + bucket + '.json.gz'
        outputs[name] = packed
        manifest['relationships']['shards'][bucket] = binding(name, packed, raw)
    manifest['extensions'] = {**manifest.get('extensions', {}), 'evidence_connect': {
        'authoring_path': AUTHOR, 'authoring_sha256': digest(authored_raw),
        'full_corpus_sha256': digest(original_raw), 'pilot_sha256': digest(pilot_raw),
        'pilot_groups_sha256': digest(groups_raw),
        'pilot_author_sha256': digest(capital_raw),
        'producer_files': producer_files,
        'new_group_count': 10, 'new_dependency_link_count': len(edges),
        'pilot_group_ids': {key: pilot_groups[key]['id'] for key in sorted(by_key)}}}
    outputs['evidence-connect-manifest.json'] = canonical(manifest)
    descriptor = json.loads(content(root, 'structured-context/okf-explorer.json'))
    descriptor['title'] = 'DWP guidance: source-led evidence connect research'
    descriptor['description'] = ('Independent experimental source navigation with additive capital groups '
                                 'over the frozen full DMG and ADM corpus; specialist review is open.')
    descriptor['snapshot'] = base['bundle']['snapshot']
    descriptor['snapshot_id'] = base['bundle']['snapshot']
    descriptor['generated_at'] = authored['projected_at']
    descriptor['entrypoints']['context_corpus'] = binding('evidence-connect-manifest.json',
                                                           outputs['evidence-connect-manifest.json'])
    descriptor['entrypoint_integrity']['context_corpus'] = descriptor['entrypoints']['context_corpus']
    descriptor['entrypoints']['context_assembly'] = binding(PREFIX + 'base-index.json', base_raw)
    descriptor['entrypoint_integrity']['context_assembly'] = descriptor['entrypoints']['context_assembly']
    descriptor['exploratory_publication']['snapshot_id'] = base['bundle']['snapshot']
    descriptor['exploratory_publication']['generated_at'] = authored['projected_at']
    descriptor['exploratory_publication']['limitations'] += authored['limitations']
    outputs['evidence-connect-explorer.json'] = canonical(descriptor)
    outputs[PREFIX + 'report.json'] = canonical({'schema': 'okf-evidence-connect-build.v1',
        'source_manifest_sha256': digest(original_raw), 'pilot_sha256': digest(pilot_raw),
        'pilot_groups_sha256': digest(groups_raw),
        'pilot_author_sha256': digest(capital_raw),
        'producer_files': producer_files,
        'authoring_sha256': digest(authored_raw), 'group_count': 10,
        'dependency_groups_linked': [d['id'] for d in authored['linked_captured_dependencies']],
        'not_closed': authored['not_closed'], 'dependency_census': authored['dependency_census'],
        'edges': len(edges),
        'reused_record_shards': len(original['records']['shards']),
        'new_files': sorted(outputs)})
    return outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    for name, raw in compile_connect().items():
        path = ROOT / 'structured-context' / name
        if args.check:
            require(path.read_bytes() == raw, 'Connect projection drift: ' + name)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
    print(json.dumps({'status': 'verified' if args.check else 'built'}))


if __name__ == '__main__': main()
