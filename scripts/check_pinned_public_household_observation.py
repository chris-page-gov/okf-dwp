#!/usr/bin/env python3
"""Verify approved retained public Reader observations offline; never execute them."""
import argparse
import copy
import gzip
import hashlib
import io
import json
from pathlib import Path
import re
import stat
import subprocess

from check_household_reader_observations import bounded_read, checked_directory

ROOT = Path(__file__).resolve().parents[1]
RELEASE = '7f9feb96-c4f2de0a'
BASE = ROOT / 'validation/household-reader-public' / RELEASE
MAX_MANIFEST = 128 * 1024
MAX_MEMBER = 10 * 1024 * 1024
MAX_GIT_BLOB = 8 * 1024 * 1024
MAX_SOURCE_TOTAL = 64 * 1024 * 1024
MAX_DECODED_TOTAL = 64 * 1024 * 1024
APP_ROOT = 'https://chris-page-gov.github.io/okf-explorer/'
SOURCE_ROOT = 'https://raw.githubusercontent.com/chris-page-gov/okf-dwp/'
ATTEMPT = 'attempt-01-chrome'
FILES = frozenset({'observation.json', 'executed-harness.mjs', 'app-manifest.json',
    'care-home-context.json', 'sda-context.json', 'care-home-ask.png',
    'sda-alternatives.png', 'statutory-reader.png', 'statutory-source-timeline.png',
    'statutory-graph.png', 'concept-facet.png'})
METADATA = frozenset({'README.md', 'approval-manifest.json', 'artifact-manifest.json'})
# Reviewed admission lives outside the observation's self-reported identities.
# A different release requires an explicit new entry, not a caller URL or script.
APPROVED = {
    RELEASE: {
        'source_commit': '7f9feb9634e3d94004853b838462aca132c505a5',
        'engine_commit': 'c4f2de0a99b7bc2f8b8c8a06a3c715fb56b66d8e',
        'app_manifest_sha256': '9fc8cb1bbf10e4e5182efd69d56f2b5ed39a2e6ecf942dce64357c4a529d1ce8',
        'observation_sha256': 'ccafcf36f5b43281a99b4a58879f53cb487e999f7687f1c058a59806375d40ac',
        'harness_sha256': 'ea694325984cb8ba1a746e8be2c3ff97b196a19288f70fb522138494308b1366',
        'context_sha256': {
            'care-home': '456ca892797f55096ff9a5600e3cda77073949d2540d34ff9363f4f102525a2e',
            'sda': 'ba25e547d7a473c2192ac7bfb27be15aec5997894f58ec8b56f6c066047a771f'},
    }
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(raw): return hashlib.sha256(raw).hexdigest()
def canonical(value): return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
def encoded(value): return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()


def parse(raw):
    def pairs(rows):
        result = {}
        for key, value in rows:
            require(key not in result, 'Duplicate JSON key')
            result[key] = value
        return result
    def invalid(_): raise ValueError('Non-finite JSON number')
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid)


def safe_path(value):
    return (isinstance(value, str) and re.fullmatch(r'[A-Za-z0-9_-][A-Za-z0-9_.-]*(?:/[A-Za-z0-9_-][A-Za-z0-9_.-]*)*', value) is not None)


def valid_reference(row):
    return (isinstance(row, dict) and safe_path(row.get('path'))
        and type(row.get('bytes')) is int and 0 < row['bytes'] <= MAX_GIT_BLOB
        and isinstance(row.get('sha256'), str) and re.fullmatch('[a-f0-9]{64}', row['sha256']))


def source_path(value):
    require(safe_path(value) and (value.startswith('combined/') or value in {
        'domain-profile/legal-bodies/context-overlay.json', 'evaluation/staff-questions/cases.json'}), 'Unsafe or unapproved source path')


def git_blob(commit, relative, root=ROOT):
    require(re.fullmatch('[a-f0-9]{40}', commit or '') is not None, 'Immutable Git commit required')
    source_path(relative)
    ref = commit + ':' + relative
    size_raw = subprocess.check_output(['git', 'cat-file', '-s', ref], cwd=root, timeout=10, stderr=subprocess.DEVNULL)
    require(len(size_raw) <= 24 and size_raw.strip().isdigit(), 'Invalid Git blob size')
    size = int(size_raw)
    require(0 < size <= MAX_GIT_BLOB, 'Git blob exceeds byte limit')
    proc = subprocess.Popen(['git', 'cat-file', 'blob', ref], cwd=root, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    try:
        raw = proc.stdout.read(MAX_GIT_BLOB + 1)
        require(len(raw) <= MAX_GIT_BLOB, 'Git capture exceeds byte limit')
        require(proc.wait(timeout=10) == 0 and len(raw) == size, 'Git capture size or result differs')
        return raw
    finally:
        if proc.poll() is None:
            proc.kill(); proc.wait(timeout=5)
        proc.stdout.close()


def inventory(base):
    base = checked_directory(base)
    require({p.name for p in base.iterdir()} <= METADATA | {ATTEMPT}, 'Unexpected observation directory entry')
    for path in base.iterdir():
        require(stat.S_ISDIR(path.lstat().st_mode) if path.name == ATTEMPT else stat.S_ISREG(path.lstat().st_mode), 'Metadata and attempt types differ; symlinks forbidden')
    directory = checked_directory(base / ATTEMPT)
    require({p.name for p in directory.iterdir()} == FILES, 'Observation inventory differs')
    rows = []
    for name in sorted(FILES):
        raw = bounded_read(directory / name, MAX_MEMBER)
        if name.endswith('.png'):
            require(raw.startswith(b'\x89PNG\r\n\x1a\n'), 'Invalid screenshot encoding')
        rows.append({'path': ATTEMPT + '/' + name, 'bytes': len(raw), 'sha256': sha(raw)})
    require(sum(row['bytes'] for row in rows) <= 32 * 1024 * 1024, 'Observation aggregate byte limit exceeded')
    return rows


def verify_app(app_raw, observation, approval):
    app = parse(app_raw)
    require(sha(app_raw) == approval['app_manifest_sha256'] == observation['expected_app_manifest_sha256']
        == observation['app']['manifest_sha256'], 'Application manifest differs from approval')
    require(app['schema'] == 'okf-explorer-app-build-manifest.v1' and app['algorithm'] == 'sha256-canonical-json-materials-v1', 'Unknown application manifest')
    rows = app['materials']
    require(isinstance(rows, list) and 0 < len(rows) <= 64 and app['file_count'] == len(rows), 'Application material bound differs')
    require(all(valid_reference(row) and set(row) == {'path', 'bytes', 'sha256'} for row in rows), 'Invalid application material')
    paths = [row['path'] for row in rows]
    require(paths == sorted(set(paths)) and 'index.html' in paths, 'Application material paths repeated or unordered')
    tree = (json.dumps([{'path': r['path'], 'bytes': r['bytes'], 'sha256': r['sha256']} for r in rows], ensure_ascii=False, separators=(',', ':')) + '\n').encode()
    require(sha(tree) == app['tree_sha256'] == observation['app']['tree_sha256'], 'Application tree differs')
    require(observation['app']['manifest_url'] == APP_ROOT + 'okf-explorer-build-manifest.json', 'Application manifest URL differs')
    expected = {APP_ROOT + row['path']: row for row in rows}
    verified = observation['app']['verified_materials']
    require(len(verified) == len(expected) and {row['url'] for row in verified} == set(expected), 'Complete unique application material verification absent')
    loaded = observation['browser_loaded_app_materials']
    require(0 < len(loaded) <= len(expected) and len({r['url'] for r in loaded}) == len(loaded), 'Loaded application materials repeated or absent')
    for row in verified + loaded:
        require(row['url'] in expected and row['status'] == 200 and all(row[k] == expected[row['url']][k] for k in ['bytes', 'sha256']), 'Application response differs')
    require(any(row['url'].endswith('.js') for row in loaded), 'No observed loaded application script')
    return len(expected)


def verify_sources(observation, commit, reader):
    rows = observation['inputs']
    require(isinstance(rows, list) and 0 < len(rows) <= 512 and all(valid_reference(row) for row in rows), 'Invalid source inventory')
    require(len({r['path'] for r in rows}) == len(rows), 'Repeated source input')
    require(sum(r['bytes'] for r in rows) <= MAX_SOURCE_TOTAL, 'Source inventory exceeds aggregate byte bound')
    cache = {}
    for row in rows:
        source_path(row['path'])
        raw = reader(commit, row['path'])
        require(len(raw) == row['bytes'] and sha(raw) == row['sha256'], 'Source input differs: ' + row['path'])
        cache[row['path']] = raw
    requests = observation['corpus_requests']
    require(isinstance(requests, list) and 0 < len(requests) <= 512 and len({r['path'] for r in requests}) == len(requests), 'Invalid or repeated corpus response')
    for row in requests:
        require(valid_reference(row) and row['status'] == 200 and row['url'] == SOURCE_ROOT + commit + '/combined/' + row['path'], 'Non-canonical corpus response')
        raw = cache.get('combined/' + row['path'])
        require(raw is not None and len(raw) == row['bytes'] and sha(raw) == row['sha256'], 'Corpus response/source differs')
    require(len(requests) <= observation['corpus_response_count'] <= 1024, 'Response count differs')
    require(sum(r['bytes'] for r in requests) <= observation['corpus_response_bytes'] <= 64 * 1024 * 1024, 'Response byte census differs')
    return cache


def decode_gzip(raw, size):
    require(type(size) is int and 0 < size <= MAX_GIT_BLOB, 'Decoded file bound invalid')
    with gzip.GzipFile(fileobj=io.BytesIO(raw)) as stream:
        value = stream.read(size + 1)
    require(len(value) == size, 'Decoded source size differs')
    return value


def source_records(cache, manifest):
    prefix = 'combined/context/corpus/'
    ref = manifest['base_index']; require(valid_reference(ref), 'Invalid corpus base reference')
    raw = cache[prefix + ref['path']]
    require(len(raw) == ref['bytes'] and sha(raw) == ref['sha256'] and raw == cache['combined/context/assembly-index.json'], 'Base index binding differs')
    base = parse(raw)
    require(base['bundle']['snapshot'] == manifest['semantic_source_snapshot'], 'Semantic snapshot differs')
    records = {}
    def add(row):
        require(isinstance(row, dict) and isinstance(row.get('id'), str), 'Invalid source record')
        require(row['id'] not in records or records[row['id']] == row, 'Conflicting source record')
        records[row['id']] = row
    for row in base['records']: add(row)
    total = len(raw)
    references = manifest['records']['shards']
    require(len(references) <= 1024 and len({r['path'] for r in references}) == len(references), 'Invalid record-shard inventory')
    for ref in references:
        require(valid_reference(ref), 'Invalid record shard')
        raw = cache.get(prefix + ref['path'])
        if raw is None: continue
        require(len(raw) == ref['bytes'] and sha(raw) == ref['sha256'], 'Record-shard transfer differs')
        size = ref.get('decoded_bytes', ref['bytes']); total += size
        require(total <= MAX_DECODED_TOTAL, 'Decoded source aggregate bound exceeded')
        decoded = decode_gzip(raw, size) if ref.get('encoding') == 'gzip' else raw
        require(sha(decoded) == ref.get('decoded_sha256', ref['sha256']), 'Decoded source digest differs')
        value = parse(decoded)
        require(value['schema'] == 'okf-context-records.v1' and value['first_ordinal'] == ref['first_ordinal'] and len(value['records']) == ref['count'], 'Record-shard structure differs')
        for row in value['records']: add(row)
    return base, records


def verify_context(context, observed, manifest, binding, records, assertions, question):
    require(context['schema'] == 'okf-governed-context.v1' and context['engine'] == 'okf-context-assembly.v1', 'Unknown package contract')
    require(context['question'] == question and context['bundle'] == manifest['bundle'] and context['binding'] == binding, 'Package source or question differs')
    require(context['scope'] == manifest['scope'] and context['evidence_status'] == observed['evidence_status'] == 'insufficient'
        and context['ai_answer'] is None and observed['ai_answer'] is None, 'Package authority or answer boundary differs')
    require(context['context_id'] == observed['context_id'] and context['bundle']['snapshot'] == observed['snapshot'], 'Observed package identity differs')
    basis = copy.deepcopy(context); basis.pop('context_id'); basis['budget'].pop('used_bytes')
    require(context['context_id'] == 'urn:sha256:' + sha(canonical(basis)), 'Complete context identity differs')
    budget = context['budget']; selected = context['selected']; edges = context['relationships']
    require(budget == observed['budget'] and budget['truncated'] is True, 'Observed budget differs')
    for field, maximum in [('max_nodes', 200), ('max_relationships', 400), ('max_depth', 8), ('max_bytes', 524288)]:
        require(type(budget[field]) is int and 0 < budget[field] <= maximum, 'Unsafe package budget')
    size = len(json.dumps(context, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode())
    require(size == budget['used_bytes'] == observed['compact_json_bytes'] <= budget['max_bytes'], 'Complete package byte count differs')
    require(len(selected) == len({x['record']['id'] for x in selected}) == budget['used_nodes'] == observed['selected_records'] <= budget['max_nodes'], 'Selected record census differs')
    require(len(edges) == len({x['id'] for x in edges}) == budget['used_relationships'] == observed['relationships'] <= budget['max_relationships'], 'Relationship census differs')
    require(0 <= budget['reached_depth'] <= budget['max_depth'], 'Traversal depth exceeds budget')
    evidence = []
    for item in selected:
        row = item['record']
        require(records.get(row['id']) == row, 'Selected record differs from complete immutable source')
        if row['kind'] == 'evidence':
            literal = sha(row['text'].encode())
            refs = [p for p in row['provenance'] if 'literal_sha256' in p]
            require(refs and all(p['literal_sha256'] == literal for p in refs), 'Complete evidence literal digest differs')
            evidence.append({'record_id': row['id'], 'text_sha256': literal})
        for path in item['paths']:
            require(path['records'][0] == path['seed'] and path['records'][-1] == row['id'] and len(path['records']) == len(path['assertions']) + 1
                and len(path['assertions']) <= budget['max_depth'], 'Selected path shape or depth differs')
            for i, aid in enumerate(path['assertions']):
                edge = assertions.get(aid)
                require(edge is not None and edge['source'] == path['records'][i] and edge['target'] == path['records'][i+1], 'Selected directed path differs from source')
    selected_ids = {item['record']['id'] for item in selected}
    omitted_ids = {rid for issue in budget['omissions'] for rid in issue.get('ids', [])}
    omitted_targets = []
    for edge in edges:
        require(assertions.get(edge['id']) == edge and edge['source'] in selected_ids and edge['target'] in records,
            'Relationship or declared endpoints differ from immutable source')
        # The frozen assembler records an edge before attempting its target.
        # An omitted target is not evidence selected into this context.
        if edge['target'] not in selected_ids:
            require(edge['target'] in omitted_ids, 'Unselected relationship target lacks a budget omission')
            omitted_targets.append(edge['target'])
    edge_ids = {edge['id'] for edge in edges}
    selected_paths = [path for item in selected for path in item['paths']]
    required_paths = [path for requirement in context['requirements'] for path in requirement.get('required_paths', [])]
    def fully_retained(path):
        return set(path['records']) <= selected_ids and set(path['assertions']) <= edge_ids
    return {'context_id': context['context_id'], 'canonical_package_sha256': sha(canonical(context)),
        'selected_records': len(selected), 'relationships': len(edges), 'compact_bytes': size,
        'relationships_with_unselected_targets': len(omitted_targets), 'unselected_target_ids': sorted(set(omitted_targets)),
        'selected_path_references': len(selected_paths), 'selected_paths_fully_retained': sum(map(fully_retained, selected_paths)),
        'returned_required_path_occurrences': len(required_paths), 'returned_required_paths_fully_retained': sum(map(fully_retained, required_paths)),
        'evidence_literal_digests': evidence, 'evidence_status': 'insufficient', 'ai_answer': None}


def validate(base=BASE, approval=None, reader=git_blob):
    approval = APPROVED[RELEASE] if approval is None else approval
    inventory(base)
    directory = base / ATTEMPT
    raw = bounded_read(directory / 'observation.json', MAX_MEMBER)
    require(sha(raw) == approval['observation_sha256'], 'Observation differs from approved retained bytes')
    observed = parse(raw); commit = approval['source_commit']
    require(observed['schema'] == 'okf-public-household-reader.v1' and observed['status'] == 'passed'
        and observed['environment'] == 'published-browser-observation' and observed['network_mode'] == 'real-https-no-interception'
        and observed['browser'] == 'chrome' and observed['content_commit'] == commit, 'Observation status or source differs')
    require(observed['app_url'] == APP_ROOT + 'explore/' and observed['bundle_url'] == SOURCE_ROOT + commit + '/combined/okf-explorer.json', 'Observation URLs differ')
    require(observed['console_errors'] == [] and observed['network_errors'] == [], 'Passing observation contains errors')
    require(sha(bounded_read(directory / 'executed-harness.mjs', MAX_MEMBER)) == observed['harness_sha256'] == approval['harness_sha256'], 'Executed harness differs')
    app_count = verify_app(bounded_read(directory / 'app-manifest.json', MAX_MANIFEST), observed, approval)
    cache = verify_sources(observed, commit, reader)
    descriptor_raw = cache['combined/okf-explorer.json']; descriptor = parse(descriptor_raw)
    require(sha(descriptor_raw) == observed['descriptor']['sha256'] and descriptor['snapshot'] == observed['descriptor']['snapshot']
        and descriptor['counts']['records'] == observed['descriptor']['records'], 'Descriptor binding differs')
    manifest_raw = cache['combined/context/corpus/manifest.json']; manifest = parse(manifest_raw)
    require(manifest['semantic_source_snapshot'] == descriptor['snapshot'], 'Reader and context source differ')
    binding = {'index_url': SOURCE_ROOT + commit + '/combined/context/corpus/manifest.json', 'index_sha256': sha(manifest_raw)}
    base_index, records = source_records(cache, manifest)
    assertions = {r['id']: r for r in base_index['assertions']}
    require(len(assertions) == len(base_index['assertions']), 'Repeated source assertion')
    questions = {r['id']: r['question'] for r in parse(cache['evaluation/staff-questions/cases.json'])['cases']}
    checks = observed['checks']; cases = {}
    for filename, key, case_id in [('care-home', 'care_home', 'staff-012'), ('sda', 'sda', 'staff-008')]:
        raw = bounded_read(directory / (filename + '-context.json'), MAX_MEMBER)
        require(sha(raw) == approval['context_sha256'][filename], 'Retained context bytes differ')
        context = parse(raw)
        cases[key] = verify_context(context, checks[key], manifest, binding, records, assertions, questions[case_id])
        if key == 'care_home':
            heading = checks[key]['controlling_heading']
            require(heading['selected'] is True and heading['visible'] is True, 'Controlling heading not observed')
            record = next((x['record'] for x in context['selected'] if x['record']['id'] == heading['record_id']), None)
            require(record is not None and 'Claimants who have no partner' in record['text'] and '78088' in record['text'], 'Controlling source heading absent')
        else:
            ambiguity = next((x for x in context['ambiguities'] if x['phrase'] == 'SDA'), None)
            require(ambiguity is not None and len(set(ambiguity['candidates'])) == 2 and set(ambiguity['candidates']).isdisjoint(r['id'] for r in context['resolved_concepts']), 'SDA ambiguity lost')
            require(all(any(any(p['seed'] == candidate for p in x['paths']) for x in context['selected']) for candidate in ambiguity['candidates'])
                and len(checks[key]['alternative_labels']) >= 2, 'SDA alternative paths absent')
    facets = parse(cache['combined/data/facets.json'])
    for check, field in [('concept_facet', 'concept'), ('source_family_and_timeline', 'source_family')]:
        row = checks[check]
        require(any(x['value'] == row['value'] and x['count'] == row['count'] for x in facets[field]), 'Observed conceptual facet differs from source')
    time = checks['source_family_and_timeline']
    require(time['reader_graph_timeline_parity'] is True and time['source_series'] == 0 and time['audit_series'] == time['count']
        and time['requested_source_version_is_publication'] is False, 'Timeline provenance boundary differs')
    literal = checks['statutory_literal']; legal = parse(cache['domain-profile/legal-bodies/context-overlay.json'])['records']
    row = next((x for x in legal if x['route'] == literal['route']), None)
    require(row is not None and literal['exact_visible_literal'] is True and sha(row['text'].encode()) == literal['literal_sha256'], 'Observed statutory literal differs')
    require(any(p['url'] == literal['source_url'] for p in row['provenance']) and literal['requested_source_version'] in literal['source_url'], 'Statutory source version differs')
    require(checks['statutory_graph']['focus'] == literal['route'] and checks['statutory_graph']['incoming_and_outgoing_visible'] is True, 'Statutory graph observation differs')
    return {'scope': 'Offline integrity of one retained actual public Chrome observation; no new browser, network, model or current-availability check.',
        'source_commit': commit, 'app_manifest_sha256': approval['app_manifest_sha256'], 'observed_at': observed['observed_at'],
        'source_files_verified_against_git': len(cache), 'source_bytes': sum(len(x) for x in cache.values()),
        'app_material_observations_verified': app_count, 'cases': cases,
        'source_authority_or_completeness_upgraded': False, 'new_network_or_model_calls': 0}


def approval_manifest():
    return {'schema': 'okf-pinned-public-reader-approval.v1', 'release': RELEASE, 'binding': APPROVED[RELEASE],
        'boundary': 'Post-observation integrity admission of these exact retained bytes. The checker neither ran the browser nor establishes legal correctness.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write-manifest', action='store_true'); args = parser.parse_args()
    checked_directory(BASE)
    if not args.write_manifest:
        require(parse(bounded_read(BASE / 'approval-manifest.json', MAX_MANIFEST)) == approval_manifest(), 'Approval manifest differs')
        previous = parse(bounded_read(BASE / 'artifact-manifest.json', MAX_MANIFEST))
        require(previous['files'] == inventory(BASE), 'Retained artefact inventory differs')
    result = validate()
    manifest = {'schema': 'okf-pinned-public-reader-artefacts.v1', 'approval_sha256': sha(encoded(approval_manifest())),
        'checker_sources': {name: sha(bounded_read(ROOT / name, MAX_MEMBER)) for name in [
            'scripts/check_pinned_public_household_observation.py', 'scripts/check_household_reader_observations.py']},
        'files': inventory(BASE), 'integrity': result}
    for name, value in [('approval-manifest.json', approval_manifest()), ('artifact-manifest.json', manifest)]:
        raw = encoded(value); require(len(raw) <= MAX_MANIFEST, 'Metadata exceeds bound'); target = BASE / name
        if args.write_manifest and not target.exists():
            with target.open('xb') as stream: stream.write(raw)
        else:
            require(bounded_read(target, MAX_MANIFEST) == raw, 'Existing metadata differs; preserve it before replacement')
    print(json.dumps({'status': 'verified', 'retained_files': len(FILES), 'source_files': result['source_files_verified_against_git'],
        'evidence_literals': {key: len(value['evidence_literal_digests']) for key, value in result['cases'].items()}, 'new_network_or_model_calls': 0}))


if __name__ == '__main__': main()
