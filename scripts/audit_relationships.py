#!/usr/bin/env python3
"""Audit authored-to-generated relationship preservation without claiming legal completeness."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import gzip
import json
from pathlib import Path

from build_bundle import ROOT, canonical, digest, load_yaml

OUTPUT = 'evaluation/relationship-audit.json'
CONTAINMENT = 'http://purl.org/dc/terms/isPartOf'
REFERENCES = 'http://purl.org/dc/terms/references'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def audit(root=ROOT):
    inputs = {}

    def raw(path):
        data = (root / path).read_bytes()
        inputs[path] = {'path': path, 'sha256': digest(data), 'bytes': len(data)}
        return data

    def read(path):
        data = raw(path)
        return json.loads(gzip.decompress(data) if path.endswith('.gz') else data)

    raw('scripts/audit_relationships.py')
    raw('scripts/build_bundle.py')
    raw('scripts/semantic_authoring.py')
    semantic = read('full-dmg/data/semantic/manifest.json')
    manifest = read('full-dmg/data/manifest.json')
    nodes = {}
    assertions = {}
    runtime = {}
    records = {}
    for group, target, key in [('nodes', nodes, '@id'), ('assertions', assertions, '@id')]:
        for shard in semantic[group]:
            for row in read('full-dmg/' + shard['path'])['@graph']:
                require(row[key] not in target, 'Duplicate semantic identity')
                target[row[key]] = row
    for group, target, key in [('datasets', records, 'route'), ('relationships', runtime, 'id')]:
        for shard in manifest['chunks'][group]:
            for row in read('full-dmg/' + shard):
                require(row[key] not in target, 'Duplicate runtime identity')
                target[row[key]] = row
    labels = {row['route']: row for row in read('full-dmg/data/endpoint-labels.json.gz')['entries']}
    adjacency_manifest = read('full-dmg/data/adjacency/manifest.json')
    adjacency = {}
    for path in adjacency_manifest['buckets'].values():
        for route, rows in read('full-dmg/' + path).items():
            require(route not in adjacency, 'Duplicate adjacency route')
            adjacency[route] = rows
    triples = defaultdict(list)
    for row in assertions.values():
        triples[(row['source_route'], row['predicate'], row['target_route'])].append(row)
    authored, references, explicit = [], [], []
    for path in sorted((root / 'knowledge').rglob('*.yamlld')):
        relative = path.relative_to(root).as_posix()
        raw(relative)
        document = load_yaml(path)
        explicit.extend(document.get('assertions', []))
        for node in document.get('@graph', []):
            for position, spec in enumerate(node.get('semantic_relations', [])):
                triple = (node['route'], spec['predicate'], spec['target'])
                authored.append({'path': relative, 'triple': triple})
                matches = triples[triple]
                require(len(matches) == 1, 'Authored semantic relation missing or duplicated: ' + str(triple))
                evidence = matches[0]['evidence']
                authored_evidence = [item for item in evidence if item.get('source_artifact') == relative and item.get('source_field') == f"{node['route']}.semantic_relations[{position}]"]
                require(len(authored_evidence) == 1, 'Authored relation provenance differs')
                require(authored_evidence[0]['source_sha256'] == inputs[relative]['sha256'], 'Authored relation source hash differs')
                require(json.loads(authored_evidence[0]['source_value']) == spec, 'Authored relation literal differs')
                for item in spec['evidence']:
                    require(any(row.get('source_page_route') == item['page'] and row.get('source_value') == item['quote'] and row.get('locator') == item['locator'] for row in evidence), 'Supporting passage differs')
            for target in node.get('references', []):
                triple = (node['route'], REFERENCES, target)
                references.append(triple)
                require(len(triples[triple]) == 1, 'Authored navigation missing or duplicated: ' + str(triple))
    for assertion in explicit:
        require(assertions.get(assertion['@id']) == assertion, 'Explicit assertion differs')
    require(set(assertions) == set(runtime), 'Semantic/runtime assertion identities differ')
    expected_incident = defaultdict(set)
    for identity, assertion in assertions.items():
        row = runtime[identity]
        for field, value in assertion.items():
            if field not in ['source', 'target']:
                require(row.get(field) == value, 'Runtime assertion value differs: ' + field)
        for endpoint in ['source', 'target']:
            route, iri = assertion[endpoint + '_route'], assertion[endpoint]
            require(row[endpoint] == route and row[endpoint + '_iri'] == iri, 'Runtime endpoint changed')
            require(route in records and route in labels and iri in nodes, 'Unresolved endpoint')
            require(records[route]['id'] == iri and labels[route]['iri'] == iri, 'Endpoint IRI differs')
            expected_incident[route].add(identity)
        predicate = assertion['predicate']
        compact = {REFERENCES: 'dcterms:references', CONTAINMENT: 'dcterms:isPartOf'}.get(predicate, predicate)
        values = nodes[assertion['source']].get(compact, nodes[assertion['source']].get(predicate, []))
        values = values if isinstance(values, list) else [values]
        require(any((value.get('@id') if isinstance(value, dict) else value) == assertion['target'] for value in values), 'Missing direct triple')
    require(set(adjacency) == set(expected_incident), 'Incident route sets differ')
    for route, rows in adjacency.items():
        require(len(rows) == len(expected_incident[route]) and {row['id'] for row in rows} == expected_incident[route], 'Incoming/outgoing incident rows differ')
        require(all(row == runtime[row['id']] for row in rows), 'Adjacency assertion values differ')
    concepts = [node for node in nodes.values() if node.get('type') == 'Concept']
    pages = {node['route'] for node in nodes.values() if node.get('type') == 'Source PDF page'}
    non_containment_routes = {row[role] for row in runtime.values() if row['predicate'] != CONTAINMENT for role in ['source', 'target']}
    supporting_pages = {item['source_page_route'] for row in assertions.values() for item in row.get('evidence', []) if item.get('source_page_route')}
    dependencies = read('evaluation/full-dmg-dependencies/index.json')
    over_limit = []
    for route, rows in sorted(adjacency.items()):
        if len(rows) <= 120:
            continue
        omitted = rows[120:]
        over_limit.append({'route': route, 'incident_count': len(rows), 'after_first_120': len(omitted),
                           'non_containment_after_first_120': [{'id': row['id'], 'source': row['source'], 'predicate': row['predicate'], 'target': row['target']} for row in omitted if row['predicate'] != CONTAINMENT]})
    return {'schema': 'okf-dwp-relationship-audit.v1', 'snapshot': semantic['snapshot'], 'status': 'passed-authored-preservation-and-projection-integrity',
            'inputs': sorted(inputs.values(), key=lambda row: row['path']),
            'checks': {'authored_semantic_relations': len(authored), 'authored_relation_files': len({row['path'] for row in authored}),
                       'authored_references': len(references), 'explicit_authored_assertions': len(explicit),
                       'missing_authored_relations': 0, 'changed_supporting_passages': 0,
                       'semantic_nodes': len(nodes), 'runtime_records': len(records), 'semantic_assertions': len(assertions),
                       'runtime_relationships': len(runtime), 'all_assertion_values_preserved': True, 'all_endpoints_resolved': True,
                       'all_direct_triples_present': True, 'exact_incoming_outgoing_adjacency': True,
                       'adjacency_routes': len(adjacency), 'incident_rows': sum(map(len, adjacency.values())),
                       'duplicate_triples': sum(len(rows) > 1 for rows in triples.values())},
            'coverage': {'concepts': len(concepts), 'source_pages': len(pages), 'pages_with_non_containment_edge': len(pages & non_containment_routes),
                         'pages_in_supporting_evidence': len(pages & supporting_pages),
                         'pages_with_reference_or_support': len(pages & (non_containment_routes | supporting_pages)),
                         'pages_only_containment': len(pages - non_containment_routes),
                         'predicate_counts': dict(sorted(Counter(row['predicate'] for row in assertions.values()).items())),
                         'assertion_status_counts': dict(sorted(Counter(row['assertion_status'] for row in assertions.values()).items())),
                         'dependency_candidates': {'citation_count': dependencies['citation_count'], 'states': dependencies['states'],
                                                   'status': 'Separate mechanical candidate index; not automatically promoted to graph assertions'}},
            'bounded_display_diagnostics': {'policy_examined': 'first 120 incident rows, before grouping', 'routes_over_120': len(over_limit), 'routes': over_limit,
                                            'relationships_with_dataset_prefix_source': sum(row['source'].startswith('dataset/') for row in runtime.values()),
                                            'meaning': 'Data diagnosis for the prior Explorer graph/Links implementation; not a requirement to retain its display defects.'},
            'limitations': ['No claim that implicit domain relationships are completely modelled.',
                            'No specialist legal review, current applicability or complete answerability established.',
                            'This check verifies publication bytes and authoring preservation, not a live browser rendering.',
                            'Known UI omissions are described separately; a passing data audit does not certify the UI.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Check the committed receipt without writing files')
    args = parser.parse_args()
    report = audit()
    rendered = canonical(report)
    if args.check:
        require((ROOT / OUTPUT).read_bytes() == rendered, 'Relationship audit receipt is stale; regenerate and review')
    else:
        (ROOT / OUTPUT).write_bytes(rendered)
    print(json.dumps({'status': report['status'], **report['checks'], **{key: report['coverage'][key] for key in ['pages_with_non_containment_edge', 'pages_only_containment']}, 'receipt': OUTPUT}))


if __name__ == '__main__':
    main()
