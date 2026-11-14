"""Compile a separate source-bound graph; preserve every frozen projection."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = 'domain-profile/retrieval-graph/policy.yamlld'
OUTPUT = 'retrieval-graph/graph.json'


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def build(root=ROOT):
    inputs = {}

    def read(relative, expected=None, limit=16 * 1024 * 1024):
        path = (root / relative).resolve()
        if not path.is_relative_to(root.resolve()) or not path.is_file() or path.stat().st_size > limit:
            raise ValueError('Unsafe or oversized graph input: ' + relative)
        raw = path.read_bytes()
        if expected and digest(raw) != expected:
            raise ValueError('Graph input drift: ' + relative)
        inputs[relative] = {'path': relative, 'bytes': len(raw), 'sha256': digest(raw)}
        return raw

    policy_raw = read(POLICY)
    policy = json.loads(policy_raw)
    if policy['schema'] != 'okf-dwp-evidence-route-policy.v1' or policy['review_status'] != 'unreviewed':
        raise ValueError('Unsupported evidence graph policy')
    if policy['limits'] != {'records': 5000, 'assertions': 12000, 'requirements': 500, 'path_depth': 16}:
        raise ValueError('Evidence graph hard ceilings cannot be raised by policy')
    bound = {x['path']: x['sha256'] for x in policy['inputs']}
    source_json = {name: json.loads(read(name, expected)) for name, expected in bound.items()}
    manifest = source_json['structured-context/evidence-connect-manifest.json']
    cache = {}

    def reference(ref):
        path = 'structured-context/' + ref['path']
        if path not in cache:
            raw = read(path, ref['sha256'])
            if len(raw) != ref['bytes']:
                raise ValueError('Graph source length drift')
            if ref.get('encoding'):
                if ref['encoding'] != 'gzip':
                    raise ValueError('Unsupported graph compression')
                raw = gzip.decompress(raw)
                if len(raw) != ref['decoded_bytes'] or digest(raw) != ref['decoded_sha256']:
                    raise ValueError('Graph decoded source drift')
            cache[path] = json.loads(raw)
        return cache[path]

    def bucket(identifier):
        value = 0x811c9dc5
        encoded = identifier.encode('utf-16-le')
        for start in range(0, len(encoded), 2):
            value = ((value ^ int.from_bytes(encoded[start:start + 2], 'little')) * 0x01000193) & 0xffffffff
        return f'{value >> 24:02x}'

    records, assertions, requirements = {}, {}, {}
    variants = []

    def insert(collection, row, origin):
        old = collection.get(row['id'])
        if old is not None and old != row:
            different = sorted(k for k in set(old) | set(row) if old.get(k) != row.get(k))
            concept_variant = collection is records and old['kind'] == 'concept' and row['kind'] == 'concept'
            scope_variant = collection is assertions and different == ['scope']
            if not (concept_variant or scope_variant):
                raise ValueError('Conflicting graph evidence or assertion: ' + row['id'])
            variants.append({'id': row['id'], 'origin': origin, 'retained_sha256': digest(canonical(old).encode()),
                             'variant_sha256': digest(canonical(row).encode()),
                             'different_fields': different})
            return
        collection[row['id']] = row

    source_names = ['combined/context/assembly-index.json', 'full-dmg/context/assembly-index.json',
                    'structured-context/evidence-connect/base-index.json']
    for name in source_names:
        index = source_json[name]
        for collection, field in [(records, 'records'), (assertions, 'assertions'), (requirements, 'requirements')]:
            for row in index[field]:
                insert(collection, row, name)

    recovery = source_json['domain-profile/context-recovery/policy.yamlld']
    unit_ids = {x for r in requirements.values() for x in r['required'] if '/id/unit/' in x}
    unit_ids.update(x['unit_id'] for x in recovery['source_support'])
    unit_ids.update(x for r in requirements.values() for p in r.get('required_paths', []) for x in p['records'] if '/id/unit/' in x)
    for identifier in sorted(unit_ids):
        ref = next((r for r in manifest['records']['shards'] if r['first_id'] <= identifier <= r['last_id']), None)
        if ref is None:
            raise ValueError('Declared source unit absent from inventory: ' + identifier)
        row = next((x for x in reference(ref)['records'] if x['id'] == identifier), None)
        if row is None:
            raise ValueError('Declared source unit absent from bound shard')
        insert(records, row, 'structured-context/' + ref['path'])
    for requirement in list(requirements.values()):
        for path in requirement.get('required_paths', []):
            for source_id, edge_id in zip(path['records'], path['assertions']):
                if edge_id in assertions:
                    continue
                ref = manifest['relationships']['shards'][bucket(source_id)]
                entry = next((x for x in reference(ref)['entries'] if x['id'] == source_id), None)
                edge = next((x for x in entry['outgoing'] if x['id'] == edge_id), None) if entry else None
                if edge is None:
                    raise ValueError('Declared directed edge absent from bound source: ' + edge_id)
                insert(assertions, edge, 'structured-context/' + ref['path'])

    rules = []
    for route in recovery['routes']:
        seed = 'https://chris-page-gov.github.io/okf-dwp/id/retrieval-intent/' + route['id']
        extra = [n for d in policy.get('route_dependencies', []) if d['route_id'] == route['id'] for n in d['source_support']]
        support = [recovery['source_support'][n] for n in dict.fromkeys(route['support'] + extra)]
        provenance = []
        for unit in support:
            record = records[unit['unit_id']]
            if digest(record['text'].encode()) != unit['text_sha256'] or unit['literal'] not in record['text']:
                raise ValueError('Recovery source support drift')
            if not any(p['source_sha256'] == unit['source_sha256'] for p in record['provenance']):
                raise ValueError('Recovery PDF binding drift')
            provenance.extend(record['provenance'])
        authority = {'class': 'model-derived', 'label': 'Unreviewed source-bound navigation hypothesis',
                     'source': 'https://github.com/chris-page-gov/okf-dwp/blob/main/' + POLICY}
        records[seed] = {'id': seed, 'route': 'retrieval-intent/' + route['id'], 'label': route['label'],
                         'kind': 'concept', 'text': 'Navigation hypothesis: ' + route['query'], 'aliases': [],
                         'assertion_status': 'model-derived', 'authority': authority, 'scope': policy['scope'],
                         'provenance': provenance, 'rights': 'MIT-original-navigation; original source rights retained',
                         'access': 'public', 'review_status': 'unreviewed'}
        paths = []
        for unit in support:
            identifier = seed.replace('/retrieval-intent/', '/assertion/retrieval-graph/') + '/' + digest(unit['unit_id'].encode())[:20]
            assertions[identifier] = {'id': identifier, 'source': seed, 'target': unit['unit_id'],
                'predicate': 'http://purl.org/dc/terms/references', 'label': 'Source-supported navigation candidate',
                'assertion_status': 'model-derived', 'authority': authority, 'scope': policy['scope'],
                'provenance': records[unit['unit_id']]['provenance'], 'context_guard': {'when_all': [seed]}}
            paths.append({'seed': seed, 'records': [seed, unit['unit_id']], 'assertions': [identifier]})
        identifier = seed.replace('/retrieval-intent/', '/requirement/retrieval-graph/')
        requirements[identifier] = {'id': identifier, 'label': route['label'], 'when_all': [seed], 'covers': [seed],
            'required': [x['unit_id'] for x in support], 'required_paths': paths, 'scope': policy['scope'],
            'limitations': ['applicability_unresolved: Navigation does not establish that a condition applies.',
                           'legal_version_unreconciled: Relevant legal versions remain unreviewed.',
                           'independent_review_pending: Specialist acceptance remains required.']}
        rules.append({'id': route['id'], 'seed': seed, 'all_of': route['all_of'], 'source_support': support})

    repairs = source_json['domain-profile/retrieval-graph/navigation-repairs.yamlld']
    if repairs['schema'] != 'okf-dwp-navigation-repairs.v1' or repairs['review_status'] != 'unreviewed':
        raise ValueError('Unsupported navigation repair policy')
    for repair in repairs['repairs']:
        requirement = requirements[repair['requirement_id']]
        record = records[repair['target']]
        if (repair['target'] not in requirement['required'] or repair['source'] not in requirement['when_all']
                or repair['when_all'] != requirement['when_all'] or record['kind'] != 'evidence'
                or digest(record['text'].encode()) != repair['text_sha256']
                or sorted(set(p['source_sha256'] for p in record['provenance'])) != repair['source_sha256']):
            raise ValueError('Unbound navigation repair')
        identifier = 'https://chris-page-gov.github.io/okf-dwp/id/assertion/retrieval-graph/repair/' + digest(canonical(repair).encode())
        assertions[identifier] = {'id': identifier, 'source': repair['source'], 'target': repair['target'],
            'predicate': 'http://purl.org/dc/terms/references', 'label': 'Declared source-navigation dependency',
            'assertion_status': 'model-derived', 'authority': {'class': 'model-derived',
            'label': 'Unreviewed source-bound navigation repair', 'source': 'https://github.com/chris-page-gov/okf-dwp/blob/main/domain-profile/retrieval-graph/navigation-repairs.yamlld'},
            'scope': repair['reason'], 'provenance': record['provenance'], 'context_guard': {'when_all': repair['when_all']}}

    bridges = source_json['domain-profile/retrieval-graph/concept-bridges.yamlld']
    if bridges['schema'] != 'okf-dwp-concept-bridges.v1' or bridges['review_status'] != 'unreviewed':
        raise ValueError('Unsupported concept bridge policy')
    for bridge in bridges['bridges']:
        if set(bridge['concepts']) != {x['concept_id'] for x in bridge['source_support']}:
            raise ValueError('Concept bridge support differs')
        for ref in bridge['source_support']:
            record = records[ref['concept_id']]
            if record['kind'] != 'concept' or digest(canonical(record).encode()) != ref['record_sha256']:
                raise ValueError('Concept bridge record binding drift')

    topics = source_json['domain-profile/retrieval-graph/topic-profiles.yamlld']
    if topics['schema'] != 'okf-dwp-topic-navigation-profiles.v1' or topics['review_status'] != 'unreviewed':
        raise ValueError('Unsupported topic navigation profile')
    for topic in topics['profiles']:
        seed = topic['concept_id']
        if records[seed]['kind'] != 'concept':
            raise ValueError('Topic root must be a source concept')
        paths = []
        for first in list(assertions.values()):
            if first['source'] != seed or first.get('context_guard', {}).get('when_all'):
                continue
            target = records.get(first['target'])
            if target and target['kind'] == 'evidence':
                paths.append({'seed': seed, 'records': [seed, target['id']], 'assertions': [first['id']]})
            elif first['target'] in topic['via_concepts']:
                for second in list(assertions.values()):
                    leaf = records.get(second['target'])
                    if second['source'] == first['target'] and leaf and leaf['kind'] == 'evidence' and not second.get('context_guard', {}).get('when_all'):
                        paths.append({'seed': seed, 'records': [seed, first['target'], leaf['id']], 'assertions': [first['id'], second['id']]})
        if not paths:
            raise ValueError('Topic profile has no observed source path')
        identifier = seed.replace('/id/', '/id/requirement/topic-navigation/')
        requirements[identifier] = {'id': identifier, 'label': records[seed]['label'] + ' source navigation',
            'when_all': [seed], 'covers': [seed], 'required': sorted({p['records'][-1] for p in paths}),
            'required_paths': paths, 'scope': topic['scope'], 'limitations': [
                'applicability_unresolved: Topic navigation does not establish the relevant benefit facts or legal scope.',
                'independent_review_pending: No specialist acceptance of this navigation or interpretation.',
                'legal_version_unreconciled: Referenced legal sources and versions require their own reconciliation.']}

    snapshot = 'dwp-route-graph-' + digest(canonical(inputs).encode())[:20]
    graph = {'schema': 'okf-dwp-evidence-route-graph.v1', 'snapshot': snapshot,
             'source_bindings': sorted(inputs.values(), key=lambda x: x['path']),
             'source_commit': policy['source_commit'], 'concept_variants': variants,
             'routing_rules': rules, 'concept_bridges': bridges['bridges'], 'index': {'schema': 'okf-context-index.v1',
             'bundle': {'id': policy['@id'], 'snapshot': snapshot, 'source_url': 'https://github.com/chris-page-gov/okf-dwp'},
             'scope': policy['scope'], 'limitations': policy['limitations'],
             'records': sorted(records.values(), key=lambda x: x['id']),
             'assertions': sorted(assertions.values(), key=lambda x: x['id']),
             'requirements': sorted(requirements.values(), key=lambda x: x['id'])}}
    if len(records) > 5000 or len(assertions) > 12000 or len(requirements) > 500:
        raise ValueError('Evidence graph exceeds its hard work ceiling')
    result = json.dumps(graph, ensure_ascii=False, indent=2) + '\n'
    if len(result.encode()) > 32 * 1024 * 1024:
        raise ValueError('Evidence graph exceeds its hard byte ceiling')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    expected = build()
    output = ROOT / OUTPUT
    if args.check:
        if output.read_text() != expected:
            raise SystemExit('Evidence route graph is stale')
    else:
        output.parent.mkdir(exist_ok=True)
        output.write_text(expected)
    graph = json.loads(expected)
    print(json.dumps({'schema': graph['schema'], 'records': len(graph['index']['records']),
        'assertions': len(graph['index']['assertions']), 'requirements': len(graph['index']['requirements']),
        'bytes': len(expected.encode()), 'sha256': digest(expected.encode()), 'network_calls': 0, 'model_calls': 0}))


if __name__ == '__main__':
    main()
