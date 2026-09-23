#!/usr/bin/env node
/** Fixed Chapter 84 source-selection comparison. No network or model calls. */
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {existsSync, lstatSync, mkdirSync, readFileSync, realpathSync, writeFileSync} from 'node:fs';
import {dirname, resolve} from 'node:path';
import {fileURLToPath, pathToFileURL} from 'node:url';
import {gzipSync, gunzipSync} from 'node:zlib';
import {performance} from 'node:perf_hooks';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const argv = process.argv.slice(2);
const check = argv.includes('--check');
const args = argv.filter(value => value !== '--check');
assert.equal(argv.filter(value => value === '--check').length, check ? 1 : 0);
assert.equal(args.length, 4, 'Usage: --explorer-root PATH --attempt attempt-NN [--check]');
assert.equal(args[0], '--explorer-root');
assert.equal(args[2], '--attempt');
assert.match(args[3], /^attempt-[0-9]{2,4}$/);
const explorer = realpathSync(resolve(args[1]));
const out = resolve(ROOT, 'evaluation/capital-pilot/runs', args[3]);
assert(check ? existsSync(out) : !existsSync(out), check ? 'Retained attempt is missing' : 'Attempt exists; use a fresh name');
const runnerBytes = readFileSync(fileURLToPath(import.meta.url));
const sha = raw => createHash('sha256').update(raw).digest('hex');
const inputs = new Map();
function read(relative, expected, limit = 64 * 1024 * 1024) {
  assert(typeof relative === 'string' && /^[a-zA-Z0-9_.\/-]+$/.test(relative)
    && relative.split('/').every(part => part && part !== '.' && part !== '..'), 'Unsafe input path');
  const path = resolve(ROOT, relative);
  assert.equal(realpathSync(path), path, 'Symlinked input');
  const stat = lstatSync(path);
  assert(stat.isFile() && stat.size <= limit, 'Input too large or not regular: ' + relative);
  const raw = readFileSync(path), ref = {path: relative, bytes: raw.length, sha256: sha(raw)};
  if (expected) {
    assert.equal(ref.bytes, expected.bytes, 'Input byte count changed: ' + relative);
    assert.equal(ref.sha256, expected.sha256, 'Input hash changed: ' + relative);
  }
  inputs.set(relative, ref);
  return raw;
}
if (check) assert.deepEqual(readFileSync(resolve(out, 'evaluator.mjs')), runnerBytes, 'Evaluator changed since attempt');
else { mkdirSync(out, {recursive: true}); writeFileSync(resolve(out, 'evaluator.mjs'), runnerBytes); }
const rows = [], timings = [];
let current = {phase: 'preflight'};
try {
  const protocol = JSON.parse(read('evaluation/capital-pilot/protocol.json'));
  assert.equal(protocol.schema, 'okf-capital-pilot-evaluation.v1');
  assert.deepEqual(protocol.arms, ['baseline', 'candidate']);
  assert.deepEqual(protocol.budgets, [32768, 524288]);
  assert.deepEqual(protocol.budget_controls, {max_nodes: 64, max_relationships: 128, max_depth: 6});
  assert.equal(protocol.cases.length, 13);
  assert.deepEqual(protocol.cases.map(row => row.id), [
    ...Array.from({length: 10}, (_, i) => `capital-${String(i + 1).padStart(2, '0')}`),
    'staff-006', 'unknown', 'other-benefit']);
  assert.equal(protocol.engine.commit, '8a5b8d11a2d99935efca4ba8366812844061d928');
  const engine = resolve(explorer, 'apps/okf-explorer/src/lib/context');
  for (const [name, hash] of Object.entries(protocol.engine.files)) {
    assert.equal(sha(readFileSync(resolve(engine, name))), hash, 'Engine file differs: ' + name);
    assert.equal(sha(execFileSync('git', ['-C', explorer, 'show', `${protocol.engine.commit}:apps/okf-explorer/src/lib/context/${name}`], {maxBuffer: 8 * 1024 * 1024})), hash,
      'Pinned engine commit differs: ' + name);
  }
  const {canonicalJson} = await import(pathToFileURL(resolve(engine, 'index.ts')));
  const {assembleCorpusContext, validateContextCorpusManifest} = await import(pathToFileURL(resolve(engine, 'corpus.ts')));
  const helper = 'scripts/capital_pilot_metrics.mjs'; read(helper);
  const {measureSourceCoverage, sourceIntervals} = await import(pathToFileURL(resolve(ROOT, helper)));
  const build = JSON.parse(read('capital-pilot/build.json'));
  assert.equal(build.schema, 'okf-capital-pilot-build.v1');
  assert.equal(build.source_commit, protocol.source_commit);
  const built = new Map(build.outputs.map(ref => [ref.path, ref]));
  const readBuilt = path => {assert(built.has(path), 'Missing build output binding: ' + path); return read(path, built.get(path));};
  const groups = JSON.parse(readBuilt('capital-pilot/groups.json')).groups;
  assert.equal(groups.length, 10);
  assert.deepEqual(groups.map(group => group.key), protocol.cases.slice(0, 10).map(test => test.required_groups[0]));
  const groupByKey = new Map(groups.map(group => [group.key, group]));
  const sourceCataloguePath = 'structured-units/documents/dmg/dmg-vol14-ch84.json.gz';
  const {gunzipSync: unzip} = await import('node:zlib');
  const catalogue = JSON.parse(unzip(read(sourceCataloguePath)));
  const requiredParagraphSpans = new Map();
  for (const number of new Set(protocol.cases.flatMap(test => test.required_paragraphs || []))) {
    const units = catalogue.units.filter(unit => unit.paragraph_labels.includes(number));
    assert.equal(units.length, 1, 'Paragraph binding must resolve once: ' + number);
    requiredParagraphSpans.set(number, units[0].spans);
  }
  const source = [];
  for (const arm of protocol.arms) {
    const prefix = `capital-pilot/${arm}/`;
    const raw = readBuilt(prefix + 'manifest.json');
    const manifest = validateContextCorpusManifest(JSON.parse(raw));
    assert.equal(manifest.schema, 'okf-context-corpus.v3');
    const index = JSON.parse(readBuilt(prefix + 'index.json'));
    const refs = [manifest.base_index, ...manifest.records.shards, ...manifest.discovery.shards,
      ...Object.values(manifest.search.shards), ...Object.values(manifest.relationships.shards)];
    const allowed = new Map(refs.map(ref => [ref.path, ref]));
    const binding = {index_url: `https://example.invalid/capital-pilot/${arm}/manifest.json`, index_sha256: sha(raw)};
    const rootUrl = new URL('.', binding.index_url);
    const fetcher = async url => {
      const target = new URL(String(url));
      assert.equal(target.origin, rootUrl.origin, 'Network fetch denied');
      assert(target.href.startsWith(rootUrl.href), 'Corpus fetch escaped arm');
      const relative = target.href.slice(rootUrl.href.length);
      assert(allowed.has(relative), 'Unbound corpus fetch: ' + relative);
      return new Response(readBuilt(prefix + relative));
    };
    source.push({arm, manifest, index, binding, fetcher});
  }
  assert.deepEqual(source[0].manifest.counts, source[1].manifest.counts, 'Physical source census differs');
  assert.equal(source[0].manifest.extensions.pilot_source_identity.source_commit, protocol.source_commit);
  assert.deepEqual(source[0].manifest.extensions.pilot_source_identity.inputs,
    source[1].manifest.extensions.pilot_source_identity.inputs, 'Source versions differ between arms');
  for (const test of protocol.cases) for (const run of source) for (const max_bytes of protocol.budgets) {
    current = {phase: 'assembly', case_id: test.id, arm: run.arm, max_bytes};
    const start = performance.now();
    const pack = await assembleCorpusContext(run.manifest, run.binding, test.question,
      {...protocol.budget_controls, max_bytes}, run.fetcher);
    timings.push({...current, elapsed_ms: Math.round((performance.now() - start) * 100) / 100});
    const raw = Buffer.from(canonicalJson(pack));
    assert.equal(raw.length, pack.budget.used_bytes);
    assert(raw.length <= max_bytes);
    assert.equal(pack.ai_answer, null);
    assert.equal(pack.evidence_status, 'insufficient', 'Open obligations must remain insufficient');
    const integrity = pack.missing_evidence.filter(issue => /integrity|digest_mismatch|corpus_fetch_failed/.test(issue.code));
    assert.equal(integrity.length, 0, 'Context integrity failure');
    const evidence = pack.selected.filter(selection => selection.record.kind === 'evidence');
    if (test.must_select_no_evidence) assert.equal(evidence.length, 0, 'Unknown control selected evidence');
    const selectedSpans = evidence.flatMap(selection => {
      const record = selection.record, spans = record.evidence_unit?.spans;
      assert(Array.isArray(spans) && spans.length, 'Selected evidence lacks bound source spans');
      for (const span of spans) {
        assert.equal(sha(Buffer.from(record.text).subarray(span.unit_start, span.unit_end)), span.literal_sha256,
          'Selected source literal digest differs');
      }
      return spans;
    });
    const expectedGroups = test.required_groups.map(key => {assert(groupByKey.has(key)); return groupByKey.get(key);});
    const paragraphs = (test.required_paragraphs || []).flatMap(number => requiredParagraphSpans.get(number));
    const coverage = measureSourceCoverage(selectedSpans, expectedGroups, paragraphs);
    const delivery = selectedSpans.reduce((sum, span) => sum + span.source_end - span.source_start, 0);
    const archivalName = `${run.arm}-${test.id}-${max_bytes}.json.gz`;
    if (check) assert.deepEqual(gunzipSync(readFileSync(resolve(out, archivalName))), raw, 'Archived context differs');
    else writeFileSync(resolve(out, archivalName), gzipSync(raw, {level: 9, mtime: 0}));
    rows.push({case_id: test.id, question: test.question, arm: run.arm, max_bytes,
      context_id: pack.context_id, context_sha256: sha(raw), package_bytes: raw.length,
      evidence_status: pack.evidence_status, selected_evidence: evidence.length,
      selected_evidence_ids: evidence.map(selection => selection.record.id),
      ...coverage, delivered_source_bytes: delivery, full_context_bytes: raw.length,
      relationships: pack.relationships.length, missing_evidence: pack.missing_evidence,
      unresolved_terms: pack.unresolved_terms, retrieval_truncated: pack.retrieval?.truncated ?? false,
      assembly_truncated: pack.budget.truncated, retrieval_omissions: pack.retrieval?.omissions || [],
      assembly_omissions: pack.budget.omissions, integrity_errors: integrity,
      fetched_files: pack.retrieval?.fetched_files ?? 0, fetched_bytes: pack.retrieval?.fetched_bytes ?? 0,
      selected_span_count: sourceIntervals(selectedSpans).length, archive: archivalName});
    if (!check) writeFileSync(resolve(out, 'progress.json'), JSON.stringify({completed: rows.length, last: current}, null, 2) + '\n');
  }
  for (const ref of inputs.values()) read(ref.path, ref);
  for (const [name, hash] of Object.entries(protocol.engine.files)) assert.equal(sha(readFileSync(resolve(engine, name))), hash, 'Engine changed during attempt');
  assert.deepEqual(readFileSync(fileURLToPath(import.meta.url)), runnerBytes, 'Evaluator changed during attempt');
  const report = {schema: 'okf-capital-pilot-evaluation.v1', protocol_sha256: inputs.get('evaluation/capital-pilot/protocol.json').sha256,
    engine: protocol.engine, source_commit: protocol.source_commit, source_snapshot: build.snapshot,
    source_identity: source[0].manifest.extensions.pilot_source_identity,
    inputs: [...inputs.values()].sort((a, b) => a.path.localeCompare(b.path, 'en')),
    evaluator_sha256: sha(runnerBytes), model_calls: 0, network_calls: 0, rows,
    limitations: protocol.limits};
  if (check) assert.deepEqual(JSON.parse(readFileSync(resolve(out, 'report.json'))), report, 'Replay report differs');
  else {
    writeFileSync(resolve(out, 'report.json'), JSON.stringify(report, null, 2) + '\n');
    writeFileSync(resolve(out, 'timing.json'), JSON.stringify({observed_at: new Date().toISOString(),
      timing_scope: 'Local sequential execution; timings are observations, not a controlled speed benchmark.', rows: timings}, null, 2) + '\n');
  }
  console.log(JSON.stringify({attempt: args[3], check, assemblies: rows.length, all_insufficient: true, model_calls: 0, network_calls: 0}));
} catch (error) {
  if (!check) writeFileSync(resolve(out, 'failure.json'), JSON.stringify({status: 'failed', current,
    error: String(error), stack: String(error.stack || '').slice(0, 8000), completed_rows: rows,
    inputs: [...inputs.values()], evaluator_sha256: sha(runnerBytes), model_calls: 0, network_calls: 0}, null, 2) + '\n');
  console.error(String(error)); process.exitCode = 1;
}
