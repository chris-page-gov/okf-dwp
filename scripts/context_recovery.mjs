/** Source-bound, bounded discovery hypotheses. This module never produces an answer. */
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFile, realpath, stat} from 'node:fs/promises';
import {resolve, sep} from 'node:path';
import {pathToFileURL} from 'node:url';
import {gunzipSync} from 'node:zlib';

const POLICY_PATH = 'domain-profile/context-recovery/policy.yamlld';
const PREFIX = 'https://example.invalid/structured-context/';
const HASH = /^[a-f0-9]{64}$/;
// This adapter supports one reviewed immutable engine, including on shallow
// checkouts whose current files have the same bytes but no historical Git object.
const APPROVED_ENGINE_COMMIT = 'd6930bbcddaab616deec002d9e6efff6e3aae953';
const APPROVED_ENGINE_FILES = Object.freeze({
  'index.ts': '689f8b8ab1cfb5ccc21b6dd9b5527fcad04de01f5876b44cbb2dc0240fceb010',
  'corpus.ts': 'a770352c6e4628f0c391b0c12bbdaf185b476a714ca212e99459d135f8f57f6f',
  'corpusV3.ts': '944617e1630362b7a41d60da92651007b96252eff3075eb4c4b852f420f5a5c0',
  'types.ts': 'febf83b5c65153fd2e49ac070b6117525463034fb1b33534a086a1cc7bbb42cc',
  'unit.ts': '7cd989c00564ad2e0469073c66685ffb5111809e7f598dc42b6f3df1bf693aa6'
});
export const recoverySha256 = value => createHash('sha256').update(value).digest('hex');
const object = value => !!value && typeof value === 'object' && !Array.isArray(value);
function freezeData(value) {
  if (value && typeof value === 'object') {
    for (const item of Object.values(value)) freezeData(item);
    Object.freeze(value);
  }
  return value;
}
function keys(value, required, optional = []) {
  assert(object(value), 'Recovery value must be an object');
  assert(required.every(key => Object.hasOwn(value, key)), 'Recovery field missing');
  assert(Object.keys(value).every(key => required.includes(key) || optional.includes(key)), 'Unknown recovery field');
}
const words = value => value.normalize('NFKD').replace(/\p{M}/gu, '').toLowerCase().match(/[a-z0-9]{2,}/g) || [];
function phraseMatches(questionWords, phrase) {
  const parts = words(phrase);
  return questionWords.some((word, start) => word === parts[0] && parts.every((part, offset) => questionWords[start + offset] === part));
}
function text(value, max = 2000) { return typeof value === 'string' && value.length > 0 && value.length <= max; }

/** Strict data validation: policy content cannot supply paths, code or arbitrary requests. */
export function validateRecoveryPolicy(policy) {
  keys(policy, ['@context', '@id', 'schema', 'authored_at', 'assertion_status', 'review_status', 'scope',
    'source_manifest', 'engine', 'limits', 'compound_alias_guard', 'source_support', 'routes', 'limitations']);
  assert.equal(policy.schema, 'okf-dwp-context-recovery-policy.v1');
  assert.equal(policy['@id'], 'https://chris-page-gov.github.io/okf-dwp/id/context-recovery/v1');
  assert.deepEqual(policy['@context'], {'@vocab': 'https://chris-page-gov.github.io/okf-dwp/profile/context-recovery/'});
  assert.equal(policy.assertion_status, 'model-derived');
  assert.equal(policy.review_status, 'unreviewed');
  assert(text(policy.scope) && /^\d{4}-\d{2}-\d{2}$/.test(policy.authored_at), 'Recovery scope/date');
  keys(policy.source_manifest, ['path', 'sha256']);
  assert.equal(policy.source_manifest.path, 'structured-context/evidence-connect-manifest.json');
  assert(HASH.test(policy.source_manifest.sha256), 'Recovery manifest digest');
  keys(policy.engine, ['repository', 'commit', 'files']);
  assert.equal(policy.engine.repository, 'https://github.com/chris-page-gov/okf-explorer');
  assert.equal(policy.engine.commit, APPROVED_ENGINE_COMMIT, 'Unsupported recovery engine commit');
  assert.deepEqual(policy.engine.files, APPROVED_ENGINE_FILES, 'Unsupported recovery engine digests');
  assert.deepEqual(policy.limits, {max_followups: 3, max_question_characters: 2000, max_query_characters: 400});
  assert.deepEqual(policy.compound_alias_guard, {mode: 'suppress-only-single-word-aliases-with-exclusively-hyphenated-occurrences', preserve_original_context: true});
  assert(Array.isArray(policy.source_support) && policy.source_support.length > 0 && policy.source_support.length <= 16, 'Recovery source support bound');
  const ids = new Set();
  for (const support of policy.source_support) {
    keys(support, ['unit_id', 'text_sha256', 'literal', 'source_sha256', 'role']);
    assert(text(support.unit_id) && support.unit_id.startsWith('https://chris-page-gov.github.io/okf-dwp/id/unit/'), 'Recovery unit identity');
    assert(!ids.has(support.unit_id), 'Repeated recovery support'); ids.add(support.unit_id);
    assert(HASH.test(support.text_sha256) && HASH.test(support.source_sha256) && text(support.literal, 2000) && text(support.role, 300), 'Recovery support binding');
  }
  assert(Array.isArray(policy.routes) && policy.routes.length > 0 && policy.routes.length <= policy.limits.max_followups, 'Recovery route bound');
  const routeIds = new Set();
  for (const route of policy.routes) {
    keys(route, ['id', 'label', 'all_of', 'query', 'support']);
    assert(/^[a-z][a-z0-9-]{1,79}$/.test(route.id) && !routeIds.has(route.id), 'Recovery route identity'); routeIds.add(route.id);
    assert(text(route.label, 300) && text(route.query, policy.limits.max_query_characters), 'Recovery query/label');
    assert(!/\b[a-z]\d{3,}\b/i.test(route.query), 'Recovery questions cannot contain paragraph locators');
    assert(words(route.query).length >= 2 && words(route.query).length <= 24, 'Recovery query token bound');
    assert(Array.isArray(route.all_of) && route.all_of.length >= 2 && route.all_of.length <= 4, 'Recovery group bound');
    for (const group of route.all_of) {
      assert(Array.isArray(group) && group.length > 0 && group.length <= 16, 'Recovery alternative bound');
      assert(group.every(value => text(value, 120) && words(value).length > 0 && words(value).length <= 6), 'Recovery phrase bound');
    }
    assert(Array.isArray(route.support) && route.support.length > 0 && route.support.length <= 4, 'Recovery route support');
    assert(new Set(route.support).size === route.support.length && route.support.every(n => Number.isInteger(n) && n >= 0 && n < policy.source_support.length), 'Recovery support index');
  }
  assert(Array.isArray(policy.limitations) && policy.limitations.length > 0 && policy.limitations.length <= 16 && policy.limitations.every(value => text(value)), 'Recovery limitations');
  // Validation must not lend the caller references to the accepted data.
  return structuredClone(policy);
}

/** Match explicit dimensions only; dates and unstated legal facts are never inferred. */
export function planRecoveryQueries(question, policy) {
  policy = validateRecoveryPolicy(policy);
  assert(text(question, policy.limits.max_question_characters) && question.trim(), 'Enter a question of 1–2000 characters');
  const tokens = words(question);
  return policy.routes.flatMap(route => {
    const matched = route.all_of.map(group => group.filter(phrase => phraseMatches(tokens, phrase)));
    return matched.every(group => group.length) ? [{id: route.id, label: route.label, query: route.query,
      matched_phrases: matched, assertion_status: 'model-derived', review_status: 'unreviewed',
      source_support: route.support.map(n => structuredClone(policy.source_support[n]))}] : [];
  }).slice(0, policy.limits.max_followups);
}

/** Preserve a standalone alias; suppress only matches wholly inside hyphenated words. */
export function suppressCompoundAliases(index, question) {
  const copy = structuredClone(index), suppressed = [];
  const tokens = question.match(/[\p{L}\p{N}]+(?:[-\u2010-\u2015][\p{L}\p{N}]+)*/gu) || [];
  for (const record of copy.records) {
    if (record.kind !== 'concept' || !Array.isArray(record.aliases)) continue;
    record.aliases = record.aliases.filter(alias => {
      const aliasLabel = typeof alias === 'string' ? alias : alias.label;
      if (alias.case_sensitive || typeof aliasLabel !== 'string' || !/^[\p{L}\p{N}]+$/u.test(aliasLabel)) return true;
      const label = aliasLabel.toLowerCase();
      const occurrences = tokens.filter(token => token.toLowerCase().split(/[-\u2010-\u2015]/).includes(label));
      if (!occurrences.length || occurrences.some(token => token.toLowerCase() === label)) return true;
      suppressed.push({concept_id: record.id, alias: aliasLabel, compounds: [...new Set(occurrences)],
        reason: 'The alias occurs only within a hyphenated compound; baseline interpretation is retained separately.'});
      return false;
    });
  }
  return {index: copy, suppressed};
}

/** Load only confined local, hash-verified files; no network or model dependency. */
export async function createContextRecovery({root, explorerRoot, policyPath = POLICY_PATH}) {
  const rootPath = await realpath(resolve(root));
  assert.equal(policyPath, POLICY_PATH, 'Only the governed recovery policy path is accepted');
  async function local(relative, max = 8 * 1024 * 1024) {
    assert(/^[a-zA-Z0-9_.-]+(?:\/[a-zA-Z0-9_.-]+)*$/.test(relative) && !relative.split('/').some(part => part === '.' || part === '..'), 'Unsafe recovery path');
    const path = await realpath(resolve(rootPath, relative));
    assert(path.startsWith(rootPath + sep), 'Recovery file escaped repository');
    const metadata = await stat(path);
    assert(metadata.isFile() && metadata.size <= max, 'Recovery file byte limit');
    const raw = await readFile(path); assert(raw.length <= max, 'Recovery file byte limit'); return raw;
  }
  const policyRaw = await local(policyPath, 65536);
  const policy = freezeData(validateRecoveryPolicy(JSON.parse(policyRaw)));
  const policySha256 = recoverySha256(policyRaw);
  const engineDir = resolve(explorerRoot, 'apps/okf-explorer/src/lib/context');
  for (const [name, digest] of Object.entries(policy.engine.files)) assert.equal(recoverySha256(await readFile(resolve(engineDir, name))), digest, `Recovery engine drift: ${name}`);
  const {assembleCorpusContext, validateContextCorpusManifest} = await import(pathToFileURL(resolve(engineDir, 'corpus.ts')));
  const {canonicalJson} = await import(pathToFileURL(resolve(engineDir, 'index.ts')));
  const manifestRaw = await local(policy.source_manifest.path, 4 * 1024 * 1024);
  assert.equal(recoverySha256(manifestRaw), policy.source_manifest.sha256, 'Recovery source manifest drift');
  const manifest = validateContextCorpusManifest(JSON.parse(manifestRaw));
  const references = [manifest.base_index, ...manifest.records.shards, ...manifest.discovery.shards,
    ...Object.values(manifest.search.shards), ...Object.values(manifest.relationships.shards)];
  const allowed = new Map(references.map(ref => [ref.path, ref]));
  const readReference = async reference => {
    assert(allowed.has(reference.path), 'Unbound recovery source file');
    const raw = await local('structured-context/' + reference.path);
    assert.equal(raw.length, reference.bytes, 'Recovery source length drift');
    assert.equal(recoverySha256(raw), reference.sha256, 'Recovery source digest drift');
    return raw;
  };
  const decodedReference = async reference => {
    const raw = await readReference(reference);
    if (!reference.encoding) return raw;
    assert.equal(reference.encoding, 'gzip');
    const decoded = gunzipSync(raw, {maxOutputLength: reference.decoded_bytes});
    assert.equal(decoded.length, reference.decoded_bytes, 'Recovery decoded length drift');
    assert.equal(recoverySha256(decoded), reference.decoded_sha256, 'Recovery decoded digest drift');
    return decoded;
  };
  const base = JSON.parse(await decodedReference(manifest.base_index));
  const supportByShard = new Map();
  for (const support of policy.source_support) {
    const ref = manifest.records.shards.find(ref => ref.first_id <= support.unit_id && support.unit_id <= ref.last_id);
    assert(ref, 'Recovery support unit is absent from source inventory');
    if (!supportByShard.has(ref.path)) supportByShard.set(ref.path, JSON.parse(await decodedReference(ref)).records);
    const record = supportByShard.get(ref.path).find(row => row.id === support.unit_id);
    assert(record && recoverySha256(record.text) === support.text_sha256 && record.text.includes(support.literal), 'Recovery source support drift');
    assert(record.provenance.some(row => row.source_sha256 === support.source_sha256), 'Recovery PDF source binding drift');
  }
  const fetcherFor = overlays => async url => {
    const parsed = new URL(String(url));
    assert(parsed.href.startsWith(PREFIX) && parsed.origin === 'https://example.invalid' && !parsed.search && !parsed.hash, 'Recovery network request denied');
    const relative = parsed.pathname.slice('/structured-context/'.length);
    const raw = overlays?.get(relative) || await readReference(allowed.get(relative) || {});
    return new Response(raw);
  };
  const binding = freezeData({index_url: PREFIX + 'evidence-connect-manifest.json', index_sha256: recoverySha256(manifestRaw)});
  async function guardedContext(question, budget) {
    const result = suppressCompoundAliases(base, question);
    if (!result.suppressed.length) return null;
    const derived = structuredClone(manifest);
    const derivation = {source_manifest_sha256: binding.index_sha256, policy_sha256: policySha256, suppressed: result.suppressed};
    const snapshot = 'dwp-context-recovery-' + recoverySha256(canonicalJson(derivation)).slice(0, 20);
    result.index.bundle.snapshot = snapshot;
    result.index.limitations.push('Separate unreviewed compound-alias projection; the original governed context is retained.');
    const baseRaw = Buffer.from(canonicalJson(result.index));
    const basePath = 'context-recovery/base-index.json';
    derived.base_index = {path: basePath, bytes: baseRaw.length, sha256: recoverySha256(baseRaw)};
    derived.semantic_source_snapshot = snapshot; derived.bundle.snapshot = snapshot;
    derived.limitations.push('Separate unreviewed compound-alias projection. No evidence text, source span, relationship or obligation has changed.');
    const derivedRaw = Buffer.from(canonicalJson(derived));
    const derivedBinding = {index_url: PREFIX + 'context-recovery-manifest.json', index_sha256: recoverySha256(derivedRaw)};
    const context = await assembleCorpusContext(derived, derivedBinding, question, budget, fetcherFor(new Map([[basePath, baseRaw]])));
    return {derivation, source_binding: derivedBinding, context};
  }
  const identity = freezeData({policy_path: policyPath, policy_sha256: policySha256, source_binding: binding, engine: policy.engine});
  return Object.freeze({
    get identity() { return structuredClone(identity); },
    plan(question) { return {original_question: question, queries: planRecoveryQueries(question, policy),
      compound_aliases: suppressCompoundAliases(base, question).suppressed}; },
    async assemble(question, budget = {}) {
      const queries = planRecoveryQueries(question, policy);
      const baseline = await assembleCorpusContext(manifest, binding, question, budget, fetcherFor());
      const guarded = await guardedContext(question, budget);
      const followups = [];
      for (const route of queries) {
        const context = await assembleCorpusContext(manifest, binding, route.query, budget, fetcherFor());
        followups.push({...route, source_binding: binding, context});
      }
      return structuredClone({schema: 'okf-dwp-context-recovery.v1', original_question: question,
        evidence_status: 'insufficient', ai_answer: null, policy_sha256: policySha256,
        source_binding: binding, engine: policy.engine, baseline, guarded, followups,
        boundaries: ['Independent contexts retain their own exact identities, selected evidence and omissions.',
          'A source-supported recovery query is a navigation hypothesis, not a finding that its rule applies.',
          'Partial contexts are never merged into a sufficient answer. No individual entitlement or award is calculated.'],
        model_calls: 0, network_calls: 0});
    }
  });
}
