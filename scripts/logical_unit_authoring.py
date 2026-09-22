"""Admit explicitly registered additive authoring without rewriting frozen inputs.

Every read is bounded and hash-accounted by Inputs. Extensions may add source
units and review proposals, but cannot replace earlier identities or obligations.
The unit producer still validates all merged boundaries against frozen bytes.
"""
from copy import deepcopy
import re

from build_logical_units import require, strict_json

PREFIX = 'domain-profile/logical-units/'
REGISTRY = PREFIX + 'authoring-registry.json'
SCHEMA = 'okf-dwp-logical-closure-authoring.v1'
REVIEW = 'unreviewed-specialist-review-required'
LIMIT = 4 * 1024 * 1024


def read_json(inputs, path):
    return strict_json(inputs.read(path, limit=LIMIT))


def attributed(row, path):
    require(isinstance(row, dict) and 'authoring_path' not in row,
            'Authoring provenance is assigned by the registered loader')
    return {**deepcopy(row), 'authoring_path': path}


def extensions(inputs):
    inputs.read('scripts/logical_unit_authoring.py', limit=1024 * 1024)
    registry = read_json(inputs, REGISTRY)
    require(set(registry) == {'schema', 'extensions'} and
            registry['schema'] == 'okf-dwp-logical-authoring-registry.v1', 'Unsupported authoring registry')
    paths = registry['extensions']
    require(isinstance(paths, list) and len(paths) <= 64 and
            all(isinstance(p, str) and re.fullmatch(r'closure-[a-z0-9-]+\.yamlld', p) for p in paths),
            'Invalid registered authoring path')
    require(paths == sorted(set(paths)), 'Authoring registry must be unique and sorted')
    result = []
    fields = {'@context', '@id', 'schema', 'review_status', 'specialist_review', 'scope',
              'documents', 'profiles', 'profile_additions', 'concept_additions', 'alias_additions',
              'reference_additions', 'reference_dispositions', 'controls'}
    for filename in paths:
        path = PREFIX + filename
        item = read_json(inputs, path)
        require(isinstance(item, dict) and not set(item) - fields and item.get('schema') == SCHEMA,
                'Unsupported closure authoring fields or schema')
        require(item.get('specialist_review') == 'not-reviewed' and
                item.get('review_status') == 'agent-reviewed-boundary-and-target-only' and isinstance(item.get('scope'), str) and item['scope'].strip(),
                'Closure authoring cannot imply specialist acceptance')
        for field in fields - {'@context', '@id', 'schema', 'review_status', 'specialist_review', 'scope'}:
            require(isinstance(item.get(field, []), list) and len(item.get(field, [])) <= 1000,
                    'Unbounded closure authoring list: ' + field)
        result.append((path, item))
    return result


def load_overrides(inputs, additions=None):
    source = PREFIX + 'overrides.json'
    result = read_json(inputs, source)
    require(result.get('schema') == 'okf-dwp-logical-unit-overrides.v1', 'Unknown logical-unit overrides')
    docs, keys = {}, set()
    for path, rows in [(source, result['documents']), *[(p, x.get('documents', [])) for p, x in (extensions(inputs) if additions is None else additions)]]:
        seen = set()
        for document in rows:
            key = (document['family'], document['document_id'])
            require(key not in seen, 'Duplicate authoring document within one source')
            seen.add(key)
            identity = {k: v for k, v in document.items() if k not in ('units', 'proposals')}
            if key in docs:
                previous = {k: v for k, v in docs[key].items() if k not in ('units', 'proposals')}
                require(previous == identity, 'Conflicting immutable document binding')
            else:
                docs[key] = {**deepcopy(identity), 'units': [], 'proposals': []}
            for unit in document['units']:
                require(unit['key'] not in keys, 'Duplicate global authored unit key')
                keys.add(unit['key'])
                docs[key]['units'].append(attributed(unit, path))
            docs[key]['proposals'].extend(attributed(p, path) for p in document['proposals'])
    result['documents'] = [docs[key] for key in sorted(docs)]
    return result


def reference_key(row):
    return row['document_id'], row['source_unit_key'], row['literal_reference']


def load_semantics(inputs):
    additions = extensions(inputs)
    overrides = load_overrides(inputs, additions)
    declarations = read_json(inputs, PREFIX + 'concepts.yamlld')
    declarations['@graph'] = [attributed(r, PREFIX + 'concepts.yamlld') for r in declarations['@graph']]
    declarations['alias_additions'] = [attributed(r, PREFIX + 'concepts.yamlld') for r in declarations.get('alias_additions', [])]
    profiles = read_json(inputs, PREFIX + 'profiles.json')
    refs = read_json(inputs, PREFIX + 'reference-review.json')
    require(refs.get('schema') == 'okf-dwp-logical-reference-review.v1', 'Unsupported reference review')
    profile_ids = {p['id'] for p in profiles['profiles']}
    require(len(profile_ids) == len(profiles['profiles']), 'Duplicate profile identity')
    references = {reference_key(r): r for r in refs['references']}
    require(len(references) == len(refs['references']), 'Duplicate unresolved reference')
    dispositions, updated = [], set()
    for path, extension in additions:
        declarations['@graph'].extend(attributed(r, path) for r in extension.get('concept_additions', []))
        declarations['alias_additions'].extend(attributed(r, path) for r in extension.get('alias_additions', []))
        for profile in extension.get('profiles', []):
            require(profile['id'] not in profile_ids, 'Cannot replace an existing profile')
            profile_ids.add(profile['id'])
            profiles['profiles'].append(attributed(profile, path))
        for addition in extension.get('profile_additions', []):
            require(set(addition) <= {'id', 'required_unit_keys', 'required_paths', 'missing_obligations'}, 'Profile additions must preserve existing scope and obligations')
            matches = [p for p in profiles['profiles'] if p['id'] == addition['id']]
            require(len(matches) == 1, 'Unknown profile addition target')
            for field in ('required_unit_keys', 'required_paths', 'missing_obligations'):
                require(isinstance(addition.get(field, []), list), 'Invalid profile addition list')
                for value in addition.get(field, []):
                    if field == 'missing_obligations':
                        same_id = [r for r in matches[0][field] if r['id'] == value['id']]
                        require(not same_id or same_id == [value], 'Conflicting obligation identity')
                    if value not in matches[0][field]:
                        matches[0][field].append(deepcopy(value))
        for row in extension.get('reference_additions', []):
            key = reference_key(row)
            require(key not in references and row.get('status') == 'unresolved', 'Duplicate or resolved reference addition')
            references[key] = attributed(row, path)
            refs['references'].append(references[key])
        for row in extension.get('reference_dispositions', []):
            key = reference_key(row)
            require(key in references and key not in updated, 'Unknown or repeated reference disposition')
            require(row.get('evidence_spans') == references[key]['evidence_spans'] and row.get('status') == 'unresolved'
                    and row.get('legal_effect_status') == 'unresolved' and row.get('specialist_review') == 'not-reviewed'
                    and row.get('review_status') == 'agent-reviewed-target-identification-only', 'Disposition cannot change source or resolve legal effect')
            require(isinstance(row.get('target_unit_keys'), list) and isinstance(row.get('target_status'), str)
                    and isinstance(row.get('note'), str) and row['note'], 'Invalid reference disposition')
            updated.add(key)
            dispositions.append(attributed(row, path))
    return overrides, declarations, profiles, refs, dispositions
