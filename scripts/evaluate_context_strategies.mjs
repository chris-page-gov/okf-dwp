#!/usr/bin/env node
/** Offline strategy experiments against the unchanged, hash-bound failure case. */
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const args = process.argv.slice(2);
const option = name => { const n = args.indexOf(name); return n < 0 ? undefined : args[n + 1]; };
assert(option('--explorer-root'), 'Usage: --explorer-root PATH [--output PATH] [--check]');
assert(!args.includes('--check') || option('--output'), '--check requires --output');
const engine = resolve(option('--explorer-root'), 'apps/okf-explorer/src/lib/context');
const digest = value => createHash('sha256').update(value).digest('hex');
const spec = JSON.parse(readFileSync(resolve(root, 'evaluation/out-of-sample/uc-disabled-child-supersession-001.json')));
for (const [name, hash] of Object.entries(spec.source_binding.engine_files))
  assert.equal(digest(readFileSync(resolve(engine, name))), hash, `Pinned engine drift: ${name}`);
const manifestBytes = readFileSync(resolve(root, spec.source_binding.corpus_manifest));
assert.equal(digest(manifestBytes), spec.source_binding.corpus_sha256, 'Pinned manifest drift');
const manifest = JSON.parse(manifestBytes);
const corpusRoot = resolve(root, dirname(spec.source_binding.corpus_manifest));
const references = new Map([manifest.base_index, ...manifest.records.shards, ...manifest.discovery.shards,
  ...Object.values(manifest.search.shards), ...Object.values(manifest.relationships.shards)].map(ref => [ref.path, ref]));
const cached = new Map();
const bytesFor = ref => {
  if (!cached.has(ref.path)) {
    const path = resolve(corpusRoot, ref.path);
    assert(path.startsWith(corpusRoot + '/'), 'Resource escaped local corpus root');
    const bytes = readFileSync(path);
    assert.equal(bytes.length, ref.bytes, `Resource length drift: ${ref.path}`);
    assert.equal(digest(bytes), ref.sha256, `Resource hash drift: ${ref.path}`);
    cached.set(ref.path, bytes);
  }
  return cached.get(ref.path);
};
const { assembleCorpusContext } = await import(pathToFileURL(resolve(engine, 'corpus.ts')));
const experiment = JSON.parse(readFileSync(resolve(root, 'evaluation/truncation/strategy-cases.json')));
const rows = [];
for (const item of experiment.cases) {
  const question = item.original ? spec.question : item.question;
  const activeManifest = structuredClone(manifest);
  let derivedBase;
  if (item.remove_generic_rate_alias) {
    // Explicit counterfactual only: no frozen producer file is modified.
    const base = JSON.parse(bytesFor(manifest.base_index));
    const record = base.records.find(row => row.id === 'https://chris-page-gov.github.io/okf-dwp/id/staff-domain/rates');
    const before = record.aliases.length;
    record.aliases = record.aliases.filter(alias => (typeof alias === 'string' ? alias : alias.label) !== 'rate');
    assert.equal(record.aliases.length, before - 1, 'Counterfactual requires the exact generic alias');
    derivedBase = Buffer.from(JSON.stringify(base));
    activeManifest.base_index.bytes = derivedBase.length;
    activeManifest.base_index.sha256 = digest(derivedBase);
  }
  const fetcher = async input => {
    const url = new URL(String(input));
    assert.equal(url.origin, 'https://example.invalid', 'Network denied');
    const prefix = '/structured-context/';
    assert(url.pathname.startsWith(prefix), 'Resource escaped URL root');
    const relative = url.pathname.slice(prefix.length);
    const ref = references.get(relative);
    assert(ref, `Unbound resource: ${relative}`);
    return new Response(derivedBase && relative === manifest.base_index.path ? derivedBase : bytesFor(ref));
  };
  const budget = { ...spec.observed_replay.budget, ...item.budget };
  const indexHash = derivedBase ? digest(Buffer.from(JSON.stringify(activeManifest))) : digest(manifestBytes);
  const context = await assembleCorpusContext(activeManifest, {
    index_url: 'https://example.invalid/structured-context/evidence-connect-manifest.json', index_sha256: indexHash,
  }, question, budget, fetcher);
  const selected = new Set(context.selected.map(row => row.record.id));
  const counts = values => values.reduce((result, row) => {
    result[row.code] = (result[row.code] || 0) + 1; return result;
  }, {});
  const row = {
    id: item.id, strategy: item.strategy, question, budget,
    counterfactual: !!item.remove_generic_rate_alias,
    derived_input_sha256: derivedBase ? digest(derivedBase) : null,
    context_id: context.context_id, selected_records: context.selected.length,
    selected_evidence: context.selected.filter(row => row.record.kind === 'evidence').length,
    relationships: context.relationships.length, context_bytes: context.budget.used_bytes,
    context_truncated: context.budget.truncated, retrieval_truncated: context.retrieval.truncated,
    ranked_candidates: context.retrieval.candidate_count, admitted_candidates: context.retrieval.candidates.length,
    fetched_files: context.retrieval.fetched_files, fetched_bytes: context.retrieval.fetched_bytes,
    decoded_bytes: context.retrieval.decoded_bytes, query_tokens: context.retrieval.query_tokens,
    omitted_query_tokens: context.retrieval.omitted_query_tokens,
    resolved_concepts: context.resolved_concepts.map(row => ({ id: row.id, matched: row.matched })),
    activated_requirements: context.requirements.map(row => row.id),
    context_omissions: counts(context.budget.omissions), retrieval_omissions: counts(context.retrieval.omissions),
    targets: spec.source_targets.map(target => ({ paragraph: target.paragraph, id: target.unit_id, selected: selected.has(target.unit_id) })),
    evidence_status: context.evidence_status, ai_answer: context.ai_answer,
  };
  assert.equal(context.ai_answer, null, 'An evidence experiment must not generate an answer');
  assert.equal(context.evidence_status, 'insufficient', 'Experiments must retain source and legal gaps');
  assert(context.budget.used_bytes <= budget.max_bytes, 'Assembly exceeded its declared byte budget');
  if (item.id === 'baseline') {
    assert.equal(context.context_id, spec.observed_replay.context_id, 'Immutable baseline changed');
    assert.equal(context.budget.used_bytes, spec.observed_replay.used_bytes);
  }
  if (item.expected_targets)
    assert.deepEqual(row.targets.map(target => target.selected), item.expected_targets, `Target observation changed: ${item.id}`);
  rows.push(row);
}
const output = {
  schema: 'okf-dwp-truncation-strategy-evaluation.v1',
  evaluator_sha256: digest(readFileSync(fileURLToPath(import.meta.url))),
  source_case: spec.id, corpus_sha256: digest(manifestBytes), engine_files: spec.source_binding.engine_files,
  protocol_sha256: digest(readFileSync(resolve(root, 'evaluation/truncation/strategy-cases.json'))),
  model_calls: 0, network_calls: 0, frozen_source_changes: 0, cases: rows,
  limitations: [
    'These are development experiments. The original question and its target paragraphs were already observed before this protocol was written.',
    'Target selection is a navigation measure. It does not establish legal applicability, completeness or answer correctness.',
    'The generic-alias ablation changes only an in-memory derived base index; it is not a proposed change to the frozen corpus.',
    'The locator-bearing expert control deliberately contains A4361. All ordinary-language probes exclude that locator.',
    'File-backed execution tests the pinned consumer and exact retained bytes; it does not attest a live deployed service.',
  ],
};
const serialised = JSON.stringify(output, null, 2) + '\n';
if (option('--output')) {
  const path = resolve(option('--output'));
  if (args.includes('--check')) assert.equal(readFileSync(path, 'utf8'), serialised, 'Strategy evaluation drift');
  else writeFileSync(path, serialised);
}
process.stdout.write(JSON.stringify({ schema: output.schema, cases: rows.length,
  target_hits: rows.map(row => ({ id: row.id, context_bytes: row.context_bytes,
    selected: row.targets.filter(target => target.selected).map(target => target.paragraph) })),
  model_calls: 0, network_calls: 0 }, null, 2) + '\n');
