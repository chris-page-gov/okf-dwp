"""Admit additive source-read selection profiles without upgrading source units.

Profiles govern context selection, not legal applicability. All inherited
concepts, assertions and requirements remain byte-equivalent and every new
profile retains absent obligation IDs so it cannot claim complete answerability.
"""
from copy import deepcopy
import re

from build_bundle import BASE, REPO, canonical, digest
from build_logical_units import require, strict_json

AUTHORING = 'domain-profile/structured-units/pc-core.yamlld'
AUTHORING_PATHS = (AUTHORING, 'domain-profile/structured-units/household-routing.yamlld')
SCHEMA = 'okf-dwp-structured-selection.v1'
CONTEXT = {'@vocab': BASE + 'vocab/structured-context-selection/', 'dct': 'http://purl.org/dc/terms/', 'prov': 'http://www.w3.org/ns/prov#'}
REVIEW = 'unreviewed-specialist-review-required'
DCT = 'http://purl.org/dc/terms/'


def compile_selection(author, semantic, evidence_records, unit_catalogue, authoring_path=AUTHORING):
    """Pure, fail-closed admission; no source boundaries or inherited edits."""
    require(re.fullmatch(r'domain-profile/structured-units/[a-z0-9]+(?:-[a-z0-9]+)*\.yamlld', authoring_path), 'Unregistered selection authoring path')
    require(set(author) == {'@context', '@id', 'schema', 'scope', 'assertion_status', 'review_status',
                            'specialist_review', 'source_units', 'profiles', 'source_read_notes'}, 'Unknown selection authoring fields')
    require(author['@context'] == CONTEXT and author['@id'] == BASE + 'id/authoring/structured-units/' + authoring_path.rsplit('/', 1)[-1].removesuffix('.yamlld'), 'Selection local context or authoring identity differs')
    require(author['schema'] == SCHEMA and author['assertion_status'] == 'model-derived'
            and author['review_status'] == REVIEW and author['specialist_review'] == 'not-reviewed', 'Selection authority or review upgrade')
    require(isinstance(author['scope'], str) and 0 < len(author['scope']) <= 5000, 'Missing bounded selection scope')
    require(isinstance(author['source_units'], list) and 0 < len(author['source_units']) <= 100
            and isinstance(author['profiles'], list) and 0 < len(author['profiles']) <= 32, 'Unbounded selection authoring')
    require(isinstance(author['source_read_notes'], list) and all(isinstance(n, str) and 0 < len(n) <= 5000 for n in author['source_read_notes']), 'Invalid source-read notes')
    by_id = {r['id']: r for r in evidence_records}
    require(len(by_id) == len(evidence_records), 'Duplicate evidence identity')
    inherited = deepcopy(semantic)
    concepts = {r['id']: r for r in inherited['records'] if r['kind'] == 'concept'}
    selected = {}
    for entry in author['source_units']:
        require(set(entry) == {'key', 'family', 'document_id', 'id', 'source_sha256', 'pages_sha256', 'record_sha256',
                               'spans', 'paragraph_labels', 'review_status', 'specialist_review', 'boundary_status',
                               'boundary_completeness'}, 'Unknown selection source fields')
        key, identifier = entry['key'], entry['id']
        require(re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', key) and key not in selected, 'Duplicate or invalid selection key')
        require(entry['review_status'] == 'agent-source-read-selection-only' and entry['specialist_review'] == 'not-reviewed', 'Source selection review upgrade')
        require(identifier in by_id and identifier in unit_catalogue, 'Selected source unit absent')
        record, unit = by_id[identifier], unit_catalogue[identifier]
        require(record['kind'] == 'evidence' and record['assertion_status'] == 'normalized'
                and record['authority']['class'] == 'derived', 'Selected source authority differs')
        require(record['route'].split('/')[1:3] == [entry['family'], entry['document_id']], 'Selected source document differs')
        require(record['evidence_unit']['boundary_status'] == entry['boundary_status'] == 'machine-detected'
                and record['evidence_unit']['completeness'] == entry['boundary_completeness'] == 'unresolved', 'Selection cannot upgrade a machine boundary')
        require(not unit.get('authored') and unit['spans'] == entry['spans']
                and unit['paragraph_labels'] == entry['paragraph_labels'], 'Selected boundary or paragraph identity differs')
        require(digest(canonical(record)) == entry['record_sha256'] == unit['record_sha256'], 'Selected complete-record identity differs')
        for span, declared in zip(record['evidence_unit']['spans'], entry['spans']):
            require(span['source_sha256'] == entry['source_sha256'] and span['extraction_sha256'] == entry['pages_sha256'], 'Selected frozen source identity differs')
            require(span['source_start'] == declared['start_utf8'] and span['source_end'] == declared['end_utf8']
                    and span['literal_sha256'] == declared['literal_sha256']
                    and span['source_url'].endswith('#page=' + str(declared['page'])), 'Selected exact span differs')
        require(len(record['evidence_unit']['spans']) == len(entry['spans']), 'Selected span count differs')
        selected[key] = record
    require(len({r['id'] for r in selected.values()}) == len(selected), 'Duplicate source selection identity')
    new_edges, new_requirements, pairs = {}, [], {}
    used_ids = {r['id'] for r in inherited['records']} | set(by_id)
    requirement_ids = {r['id'] for r in inherited['requirements']}
    edge_ids = {r['id'] for r in inherited['assertions']}
    obligation_ids = set()
    for profile in author['profiles']:
        require(set(profile) == {'id', 'label', 'when_all', 'covers', 'required_unit_keys', 'scope', 'missing_obligations',
                                 'assertion_status', 'review_status', 'answerability'}, 'Unknown selection profile fields')
        identifier = profile['id']
        require(isinstance(identifier, str) and re.fullmatch(re.escape(BASE) + r'id/requirement/structured/[a-z0-9]+(?:-[a-z0-9]+)*', identifier) and identifier not in requirement_ids, 'Duplicate selection requirement identity')
        requirement_ids.add(identifier)
        require(isinstance(profile['label'], str) and 0 < len(profile['label']) <= 500, 'Invalid requirement label')
        require(profile['assertion_status'] == 'model-derived' and profile['review_status'] == REVIEW
                and profile['answerability'] == 'insufficient-until-open-obligations-resolved', 'Selection profile answerability upgrade')
        triggers = profile['when_all']
        require(isinstance(triggers, list) and 0 < len(triggers) <= 8 and len(set(triggers)) == len(triggers)
                and set(triggers) <= concepts.keys(), 'Selection profile has unknown or duplicate concepts')
        require(isinstance(profile['covers'], list) and profile['covers'] and len(set(profile['covers'])) == len(profile['covers']) and set(profile['covers']) <= set(triggers), 'Selection coverage exceeds resolved concepts')
        keys = profile['required_unit_keys']
        require(isinstance(keys, list) and keys and len(set(keys)) == len(keys) and set(keys) <= selected.keys(), 'Unknown or duplicate required unit')
        require(isinstance(profile['scope'], str) and 0 < len(profile['scope']) <= 5000, 'Missing profile scope')
        require(isinstance(profile['missing_obligations'], list) and 0 < len(profile['missing_obligations']) <= 64, 'Profile must retain missing obligations')
        missing, limits = [], []
        for obligation in profile['missing_obligations']:
            require(set(obligation) == {'key', 'category', 'label', 'status'}
                    and re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', obligation['key'])
                    and obligation['status'] in {'not-established', 'not-reviewed'}
                    and isinstance(obligation['category'], str) and 0 < len(obligation['category']) <= 100
                    and isinstance(obligation['label'], str) and 0 < len(obligation['label']) <= 5000, 'Invalid or closed obligation')
            oid = BASE + 'id/obligation/structured/' + identifier.rsplit('/', 1)[-1] + '/' + obligation['key']
            require(oid not in used_ids and oid not in obligation_ids, 'Obligation identity collides or is duplicate')
            obligation_ids.add(oid); missing.append(oid)
            limits.append(obligation['category'] + ': ' + obligation['label'])
        # Only the most specific triggering concept receives these routes.
        # Foundation links must not make every narrower branch a PC seed edge.
        seed = triggers[-1]
        paths = []
        for key in keys:
            record = selected[key]
            pair = (identifier, seed, record['id'], DCT + 'references', tuple(triggers))
            edge_id = BASE + 'id/assertion/structured-selection/' + digest(canonical([authoring_path, pair]))
            if pair not in pairs:
                require(edge_id not in edge_ids, 'Selection assertion collision')
                new_edges[edge_id] = {'id': edge_id, 'source': seed, 'target': record['id'], 'predicate': DCT + 'references',
                    'label': 'references source for scoped research', 'assertion_status': 'model-derived',
                    'context_guard': {'when_all': deepcopy(triggers)},
                    'authority': {'class': 'model-assisted', 'label': 'Source-read context selection; specialist acceptance pending',
                                  'source': REPO + '/blob/main/' + authoring_path},
                    'scope': author['scope'] + ' ' + profile['scope'] + ' This is a source-selection relationship, not a legal prerequisite or a claim of applicability to other benefits or special groups.',
                    'provenance': deepcopy(record['provenance'])}
                pairs[pair] = edge_id
            paths.append({'seed': seed, 'records': [seed, record['id']], 'assertions': [edge_id]})
        new_requirements.append({'id': identifier, 'label': profile['label'], 'when_all': deepcopy(triggers),
            'covers': deepcopy(profile['covers']), 'required': [selected[k]['id'] for k in keys] + missing,
            'required_paths': paths, 'scope': profile['scope'], 'limitations': limits})
    inherited['assertions'].extend(new_edges[k] for k in sorted(new_edges))
    inherited['requirements'].extend(new_requirements)
    require(inherited['records'] == semantic['records'], 'Inherited concepts changed')
    require(inherited['assertions'][:len(semantic['assertions'])] == semantic['assertions']
            and inherited['requirements'][:len(semantic['requirements'])] == semantic['requirements'], 'Inherited assertions or obligations changed')
    return inherited


def project(inputs, semantic, evidence_records, unit_catalogue, authoring_paths=AUTHORING_PATHS):
    """Use only an explicit ordered registration; never discover authoring files."""
    require(isinstance(authoring_paths, (tuple, list)) and 0 < len(authoring_paths) <= 32
            and len(set(authoring_paths)) == len(authoring_paths)
            and all(isinstance(path, str) and re.fullmatch(r'domain-profile/structured-units/[a-z0-9]+(?:-[a-z0-9]+)*\.yamlld', path) for path in authoring_paths), 'Invalid selection registration')
    inputs.read('scripts/structured_context_profiles.py', limit=1024 * 1024)
    result = semantic
    for path in authoring_paths:
        require(re.fullmatch(r'domain-profile/structured-units/[a-z0-9]+(?:-[a-z0-9]+)*\.yamlld', path), 'Unregistered selection authoring path')
        author = strict_json(inputs.read(path, limit=4 * 1024 * 1024))
        result = compile_selection(author, result, evidence_records, unit_catalogue, path)
    return result
