#!/usr/bin/env node
/** Fixed-source page/unit comparison. Confined reads only; no model or network. */
import assert from 'node:assert/strict';
import { readFileSync, writeFileSync, mkdirSync, lstatSync, realpathSync, existsSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { dirname, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { gzipSync, gunzipSync } from 'node:zlib';
import { performance } from 'node:perf_hooks';
import { execFileSync } from 'node:child_process';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const args = process.argv.slice(2), check = args.includes('--check');
const rootIndex = args.indexOf('--explorer-root');
assert(rootIndex >= 0 && args[rootIndex + 1] && !args[rootIndex + 1].startsWith('--'), 'Supply the reviewed Explorer checkout');
assert.equal(args.filter(a => a === '--explorer-root').length, 1);
assert.equal(args.length, check ? 3 : 2, 'Unsupported or duplicate argument');
assert(args.every((a, n) => a === '--check' || a === '--explorer-root' || n === rootIndex + 1), 'Unsupported argument');
const explorer = realpathSync(resolve(args[rootIndex + 1]));
const sha = raw => createHash('sha256').update(raw).digest('hex');
const inputs = new Map();
function read(path, max = 8 * 1024 * 1024) {
  assert.equal(realpathSync(path), path, 'Symlink input');
  const st = lstatSync(path); assert(st.isFile() && st.size > 0 && st.size <= max, 'Input outside regular-file bound');
  const raw = readFileSync(path); assert.equal(raw.length, st.size); return raw;
}
function source(path, max) {
  const raw = read(resolve(ROOT, path), max); inputs.set(path, {path, bytes: raw.length, sha256: sha(raw)}); return raw;
}
const approved = JSON.parse(source('evaluation/logical-units/engine.json'));
assert.equal(approved.schema, 'okf-context-engine-admission.v1');
assert.match(approved.commit, /^[0-9a-f]{40}$/);
assert.deepEqual(Object.keys(approved.files).sort(), ['corpus.ts', 'index.ts', 'types.ts', 'unit.ts']);
const engine = resolve(explorer, 'apps/okf-explorer/src/lib/context');
for (const [file, hash] of Object.entries(approved.files)) {
  assert.match(hash, /^[0-9a-f]{64}$/);
  assert.equal(sha(read(resolve(engine, file))), hash, 'Unapproved engine before execution');
  const frozen = execFileSync('git', ['-C', explorer, 'show', `${approved.commit}:apps/okf-explorer/src/lib/context/${file}`], {maxBuffer: 8 * 1024 * 1024});
  assert.equal(sha(frozen), hash, 'Engine differs from approved immutable Git blob');
}
const {canonicalJson, resolveConcepts} = await import(pathToFileURL(resolve(engine, 'index.ts')));
const {assembleCorpusContext, validateContextCorpusManifest} = await import(pathToFileURL(resolve(engine, 'corpus.ts')));
const registry = JSON.parse(source('evaluation/staff-questions/cases.json'));
const profileRows = JSON.parse(source('domain-profile/logical-units/profiles.json')).profiles;
const focussed = [
  ['logical-pc-abroad', 'What happens to Pension Credit if I go abroad?'],
  ['logical-uc-temporary-absence', 'Explain Universal Credit during temporary absence abroad.'],
  ['logical-pc-household-abroad', 'What happens to Pension Credit when a partner goes abroad?'],
  ['logical-pc-temporary-care', 'What happens to Pension Credit during temporary care home residence?'],
  ['logical-pc-care-home-alternatives', 'What happens to Pension Credit during permanent care home residence?'],
];
const cases = [...registry.cases.map(c => ({id: c.id, question: c.question})), ...focussed.map(([id, question]) => ({id, question})),
  {id: 'unknown-control', question: 'xylophonicquasarteleportation'}];
const sources = [];
for (const [stage, path] of [['pages', 'combined/context/corpus/manifest.json'], ['units', 'logical-context/manifest.json']]) {
  const raw = source(path), manifest = validateContextCorpusManifest(JSON.parse(raw));
  const basePath = dirname(path), base = JSON.parse(source(basePath + '/' + manifest.base_index.path));
  const allowed = new Map([manifest.base_index, ...manifest.records.shards, ...Object.values(manifest.search.shards)].map(r => [r.path, r]));
  const cache = new Map();
  const binding = {index_url: `https://example.test/frozen-${sha(raw)}/${path}`, index_sha256: sha(raw)};
  const urlRoot = new URL('.', binding.index_url);
  const fetcher = async url => {
    const u = new URL(String(url)); assert.equal(u.origin, urlRoot.origin); assert(u.href.startsWith(urlRoot.href));
    const relative = u.href.slice(urlRoot.href.length), ref = allowed.get(relative); assert(ref, 'Unbound corpus read');
    if (!cache.has(relative)) {
      const bytes = source(basePath + '/' + relative, 8 * 1024 * 1024);
      assert.equal(bytes.length, ref.bytes); assert.equal(sha(bytes), ref.sha256); cache.set(relative, bytes);
    }
    return new Response(cache.get(relative));
  };
  sources.push({stage, manifest, base, binding, fetcher});
}
const candidate = sources[1], controls = [];
for (const question of ['Pension Credit during temporary care home residence', 'Travel within Great Britain', 'Can my pension continue on holiday?']) {
  const resolution = resolveConcepts(candidate.base, question);
  assert(!resolution.resolved.some(r => r.id.endsWith('/staff-domain/abroad')), 'Domestic/ambiguous absence became abroad');
  controls.push({question, result: 'abroad-not-inferred', passed: true});
}
for (const question of ['JSA abroad', 'ESA abroad', 'PIP abroad', 'Universal Credit abroad']) {
  const ids = new Set(resolveConcepts(candidate.base, question).resolved.map(r => r.id));
  assert(!candidate.base.requirements.some(r => r.id.endsWith('/logical-pc-abroad') && r.when_all.every(id => ids.has(id))));
  controls.push({question, result: 'pension-credit-profile-not-inferred', passed: true});
}
const rows = [], packages = new Map(), timing = [];
for (const test of cases) for (const run of sources) for (const max_bytes of [32768, 524288]) {
  const start = performance.now();
  const pack = await assembleCorpusContext(run.manifest, run.binding, test.question, {max_bytes}, run.fetcher);
  timing.push({case_id: test.id, stage: run.stage, max_bytes, elapsed_ms: Math.round((performance.now() - start) * 100) / 100});
  assert.equal(pack.evidence_status, 'insufficient'); assert.equal(pack.ai_answer, null);
  assert(!pack.missing_evidence.some(r => ['evidence_digest_mismatch', 'unit_fragment_integrity'].includes(r.code)), 'Selected evidence failed integrity checks');
  assert.equal(pack.budget.max_bytes, max_bytes);
  assert.equal(pack.budget.used_nodes, pack.selected.length);
  assert.equal(pack.budget.used_relationships, pack.relationships.length);
  assert(pack.budget.used_nodes <= pack.budget.max_nodes && pack.budget.max_nodes <= 200);
  assert(pack.budget.used_relationships <= pack.budget.max_relationships && pack.budget.max_relationships <= 1000);
  assert(pack.budget.reached_depth <= pack.budget.max_depth && pack.budget.max_depth <= 8);
  for (const selected of pack.selected) for (const path of selected.paths) {
    assert(path.assertions.length <= pack.budget.max_depth, 'Retained path exceeds requested depth');
  }
  const actualBytes = Buffer.byteLength(canonicalJson(pack));
  assert.equal(pack.budget.used_bytes, actualBytes, 'Context byte count differs from serialisation');
  assert(actualBytes <= max_bytes);
  const chosen = new Set(pack.selected.map(s => s.record.id)), selectedEdges = new Set(pack.relationships.map(e => e.id));
  const resolved = new Set(resolveConcepts(run.base, test.question).resolved.map(r => r.id));
  const requirements = run.base.requirements.filter(r => r.when_all.every(id => resolved.has(id)));
  const paths = requirements.flatMap(r => r.required_paths || []);
  const retained = paths.filter(p => p.records.every(id => chosen.has(id)) && p.assertions.every(id => selectedEdges.has(id)));
  const evidence = pack.selected.filter(s => s.record.kind === 'evidence');
  for (const {record} of evidence) {
    for (const p of record.provenance) if (p.literal_sha256) assert.equal(sha(record.text), p.literal_sha256);
    for (const span of record.evidence_unit?.spans || []) {
      const fragment = Buffer.from(record.text).subarray(span.unit_start, span.unit_end);
      assert.equal(sha(fragment), span.literal_sha256, 'Selected unit fragment differs from its literal digest');
    }
  }
  if (test.id === 'unknown-control') assert.equal(evidence.length, 0);
  if (run.stage === 'units' && test.id.startsWith('logical-') && max_bytes === 524288) {
    assert(requirements.some(r => r.id.endsWith('/' + test.id)), `${test.id}: expected scoped profile was not resolved`);
    assert(!pack.missing_evidence.some(r => r.code === 'authority_mismatch'), `${test.id}: authored authority contract differs`);
    assert.equal(retained.length, paths.length, `${test.id}: required source path missing at512KiB`);
  }
  const raw = Buffer.from(canonicalJson(pack)), archive = `${run.stage}-${test.id}-${max_bytes}.json.gz`;
  if (test.id.startsWith('logical-')) packages.set(archive, gzipSync(raw, {level: 9, mtime: 0}));
  rows.push({case_id: test.id, question: test.question, stage: run.stage, max_bytes, context_id: pack.context_id,
    sha256: sha(raw), bytes: raw.length, evidence_status: pack.evidence_status, selected_records: pack.selected.length,
    evidence_records: evidence.length, source_text_bytes: evidence.reduce((sum, s) => sum + Buffer.byteLength(s.record.text), 0),
    relationships: pack.relationships.length, required_paths: paths.length, retained_required_paths: retained.length,
    resolved_concepts: pack.resolved_concepts.map(r => r.id), resolved_before_budget: [...resolved].sort(),
    active_requirements: requirements.map(r => r.id), retrieved_referenced_units: pack.retrieval.units?.referenced_records.length || 0,
    cross_page_units: evidence.filter(s => new Set(s.record.evidence_unit?.spans.map(p => p.source_url)).size > 1).length,
    uncertain_units: evidence.filter(s => s.record.evidence_unit && s.record.evidence_unit.completeness !== 'complete-within-declared-boundary').length,
    retrieval_truncated: pack.retrieval.truncated, assembly_truncated: pack.budget.truncated,
    missing_codes: [...new Set(pack.missing_evidence.map(r => r.code))].sort(),
    archive: packages.has(archive) ? archive : null});
}
const report = {schema: 'okf-dwp-logical-context-evaluation.v1', engine: approved,
  inputs: [...inputs.values()].sort((a, b) => a.path.localeCompare(b.path, 'en')),
  runner_sha256: sha(read(fileURLToPath(import.meta.url))), network_calls: 0, model_calls: 0,
  controls, rows, profiles: profileRows.map(r => r.id),
  limitations: ['Same frozen sources and questions; development cases, not an independent held-out answer-accuracy study.',
    'Page and logical-unit modes have different explicitly declared profiles. Path counts have different denominators and are not a consecutive funnel.',
    'Every result remains insufficient. All legal, applicability and specialist-review obligations remain open.',
    'Structural coverage and preserved excerpts do not establish complete policy semantics or better model answers.',
    'In-process timing includes local confined reads and cache reuse, not remote service or client latency.']};
const out = resolve(ROOT, 'evaluation/logical-units/run');
if (check) {
  assert.deepEqual(JSON.parse(read(resolve(out, 'summary.json'), 16 * 1024 * 1024)), report);
  for (const [name, raw] of packages) {
    const expected = gunzipSync(raw, {maxOutputLength: 524288});
    assert.deepEqual(gunzipSync(read(resolve(out, name)), {maxOutputLength: expected.length}), expected);
  }
  assert.equal(sha(read(resolve(out, 'evaluator.mjs'))), report.runner_sha256);
} else {
  assert(!existsSync(out), 'Preserve prior observations; output directory already exists');
  mkdirSync(dirname(out), {recursive: true});
  mkdirSync(out); // Exclusive leaf admission: never overwrite a competing run.
  writeFileSync(resolve(out, 'evaluator.mjs'), read(fileURLToPath(import.meta.url)));
  writeFileSync(resolve(out, 'summary.json'), JSON.stringify(report, null, 2) + '\n');
  writeFileSync(resolve(out, 'timing.json'), JSON.stringify({schema: 'okf-local-timing-observation.v1', observed_at: new Date().toISOString(), rows: timing}, null, 2) + '\n');
  for (const [name, raw] of packages) writeFileSync(resolve(out, name), raw);
}
console.log(JSON.stringify({status: 'passed', assemblies: rows.length, controls: controls.length, archives: packages.size,
  all_insufficient: rows.every(r => r.evidence_status === 'insufficient'), network_calls: 0, model_calls: 0}));
