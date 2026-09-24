#!/usr/bin/env node
/** Replay the archived out-of-sample observation without network or model calls. */
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const args = process.argv.slice(2);
const index = args.indexOf('--explorer-root');
assert(index >= 0 && args[index + 1], 'Usage: --explorer-root PATH');
const engineDir = resolve(args[index + 1], 'apps/okf-explorer/src/lib/context');
const spec = JSON.parse(readFileSync(resolve(root, 'evaluation/out-of-sample/uc-disabled-child-supersession-001.json')));
assert.equal(spec.schema, 'okf-dwp-out-of-sample-evidence-case.v1');
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
assert.equal(sha(Buffer.from(spec.question)), spec.question_sha256);
for (const [name, digest] of Object.entries(spec.source_binding.engine_files)) {
  assert.equal(sha(readFileSync(resolve(engineDir, name))), digest, `Engine drift: ${name}`);
}
for (const target of spec.source_targets) {
  assert.equal(sha(readFileSync(resolve(root, 'source/adm-2026-09-19/pdf', `${target.document}.pdf`))),
    target.source_sha256, `PDF drift: ${target.document}`);
}
const { assembleCorpusContext, validateContextCorpusManifest } = await import(
  pathToFileURL(resolve(engineDir, 'corpus.ts')));
const manifestRaw = readFileSync(resolve(root, spec.source_binding.corpus_manifest));
assert.equal(sha(manifestRaw), spec.source_binding.corpus_sha256);
const corpus = validateContextCorpusManifest(JSON.parse(manifestRaw));
const allowed = new Map([corpus.base_index, ...corpus.records.shards, ...corpus.discovery.shards,
  ...Object.values(corpus.search.shards), ...Object.values(corpus.relationships.shards)]
  .map(ref => [ref.path, ref]));
const fetcher = async url => {
  const parsed = new URL(String(url));
  assert.equal(parsed.origin, 'https://example.invalid', 'Network denied');
  assert(parsed.pathname.startsWith('/structured-context/'), 'Resource escaped corpus root');
  const relative = parsed.pathname.slice('/structured-context/'.length);
  assert(!relative.split('/').some(part => !part || part === '.' || part === '..'), 'Unsafe corpus path');
  const ref = allowed.get(relative);
  assert(ref, `Unbound corpus resource: ${relative}`);
  const bytes = readFileSync(resolve(root, 'structured-context', relative));
  assert.equal(bytes.length, ref.bytes);
  assert.equal(sha(bytes), ref.sha256);
  return new Response(bytes);
};
const observed = spec.observed_replay;
const context = await assembleCorpusContext(corpus, {
  index_url: 'https://example.invalid/structured-context/evidence-connect-manifest.json',
  index_sha256: sha(manifestRaw),
}, spec.question, observed.budget, fetcher);
const selected = new Set(context.selected.filter(row => row.record.kind === 'evidence').map(row => row.record.id));
const targets = spec.source_targets.map(row => ({ paragraph: row.paragraph,
  selected: selected.has(row.unit_id) }));
const omissions = [...new Set(context.retrieval?.omissions.map(row => row.code) || [])];
const summary = {
  schema: 'okf-dwp-out-of-sample-replay.v1',
  case_id: spec.id, context_id: context.context_id,
  evidence_status: context.evidence_status,
  ai_answer: context.ai_answer,
  used_bytes: context.budget.used_bytes,
  selected_evidence_count: selected.size,
  retrieval_candidate_count: context.retrieval?.candidate_count,
  targets, omission_codes: omissions,
  unrelated_requirement_selected: context.requirements.some(row => row.id === observed.unrelated_requirement_id),
  model_calls: 0, network_calls: 0,
};
assert.equal(summary.context_id, observed.context_id);
assert.equal(summary.evidence_status, observed.evidence_status);
assert.equal(summary.ai_answer, null);
assert.equal(summary.used_bytes, observed.used_bytes);
assert.equal(summary.selected_evidence_count, observed.selected_evidence_count);
assert.equal(summary.retrieval_candidate_count, observed.retrieval_candidate_count);
assert.deepEqual(targets.map(row => row.selected), spec.source_targets.map(row => row.observed_selected));
assert(observed.omission_codes_observed.every(code => omissions.includes(code)));
assert(summary.unrelated_requirement_selected);
process.stdout.write(JSON.stringify(summary, null, 2) + '\n');
