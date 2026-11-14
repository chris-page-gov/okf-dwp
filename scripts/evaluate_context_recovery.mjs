#!/usr/bin/env node
/** Retain separate before/after discovery contexts; never score an entitlement answer. */
import assert from 'node:assert/strict';
import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createContextRecovery, recoverySha256 } from './context_recovery.mjs';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const args = process.argv.slice(2);
const option = name => { const n = args.indexOf(name); return n < 0 ? undefined : args[n + 1]; };
assert(option('--explorer-root'), 'Usage: --explorer-root PATH [--output PATH] [--check]');
assert(!args.includes('--check') || option('--output'), '--check requires --output');
const spec = JSON.parse(readFileSync(resolve(root, 'evaluation/out-of-sample/uc-disabled-child-supersession-001.json')));
const adapter = await createContextRecovery({ root, explorerRoot: resolve(option('--explorer-root')) });
const protocolRaw = readFileSync(resolve(root, 'evaluation/truncation/recovery-cases.json'));
const protocol = JSON.parse(protocolRaw);
const budget = spec.observed_replay.budget;
const summary = context => ({ context_id: context.context_id, binding: context.binding,
  source_snapshot: context.bundle.snapshot, evidence_status: context.evidence_status,
  ai_answer: context.ai_answer, context_bytes: context.budget.used_bytes,
  selected_records: context.selected.length, relationships: context.relationships.length,
  context_truncated: context.budget.truncated, retrieval_truncated: context.retrieval.truncated,
  fetched_files: context.retrieval.fetched_files,
  target_hits: spec.source_targets.filter(target => context.selected.some(row => row.record.id === target.unit_id)).map(target => target.paragraph),
  compound_rate_concept_resolved: context.resolved_concepts.some(row => row.id.endsWith('/rates')),
  unrelated_staff_008_active: context.requirements.some(row => row.id.endsWith('/staff-008')),
});
const cases = [];
for (const row of protocol.cases) {
  const question = row.original ? spec.question : row.question;
  assert(!/A4361|relevant benefit|supersession/i.test(question), 'Natural-language protocol must not inject expert hints');
  const result = await adapter.assemble(question, budget);
  const contexts = [result.baseline, ...(result.guarded ? [result.guarded.context] : []), ...result.followups.map(row => row.context)];
  assert.equal(result.evidence_status, 'insufficient');
  assert.equal(result.ai_answer, null);
  assert(result.followups.length <= 3);
  for (const context of contexts) {
    assert.equal(context.evidence_status, 'insufficient');
    assert.equal(context.ai_answer, null);
    assert(context.budget.used_bytes <= budget.max_bytes);
  }
  const hits = spec.source_targets.filter(target => contexts.some(context => context.selected.some(row => row.record.id === target.unit_id))).map(target => target.paragraph);
  for (const expected of row.required_hits || []) assert(hits.includes(expected), `Missing recovery navigation target ${expected}: ${row.id}`);
  const timing = result.followups.some(row => row.id === 'other-benefit-timing');
  assert.equal(timing, row.expect_timing_route, `Timing route activation changed: ${row.id}`);
  if (row.original) {
    assert.equal(result.baseline.context_id, spec.observed_replay.context_id);
    assert(result.guarded && !summary(result.guarded.context).unrelated_staff_008_active, 'Compound alias guard must avoid unrelated staff task');
  }
  cases.push({id: row.id, question, baseline: summary(result.baseline),
    guarded: result.guarded ? { ...summary(result.guarded.context), derivation: result.guarded.derivation } : null,
    followups: result.followups.map(route => ({id: route.id, query: route.query,
      matched_phrases: route.matched_phrases, source_support: route.source_support, ...summary(route.context)})),
    combined_navigation_hits: hits, combined_evidence_status: 'insufficient', ai_answer: null,
    maximum_individual_context_bytes: Math.max(...contexts.map(context => context.budget.used_bytes)),
    total_context_bytes: contexts.reduce((total, context) => total + context.budget.used_bytes, 0),
  });
}
const originalRaw = readFileSync(resolve(root, 'evaluation/staff-questions/cases.json'));
const original = JSON.parse(originalRaw);
assert.equal(original.cases.length, 40);
const originalPlans = original.cases.map(row => ({id: row.id, question_sha256: recoverySha256(row.question),
  followup_ids: adapter.plan(row.question).queries.map(route => route.id),
  suppressed_aliases: adapter.plan(row.question).compound_aliases,
}));
assert(originalPlans.every(row => !row.followup_ids.length && !row.suppressed_aliases.length), 'Recovery unexpectedly changes an original staff question plan');
const output = {
  schema: 'okf-dwp-context-recovery-evaluation.v1', source_case: spec.id, adapter_identity: adapter.identity,
  adapter_module_sha256: recoverySha256(readFileSync(resolve(root, 'scripts/context_recovery.mjs'))),
  evaluator_sha256: recoverySha256(readFileSync(fileURLToPath(import.meta.url))),
  protocol_sha256: recoverySha256(protocolRaw), budget, cases,
  original_staff_registry_sha256: recoverySha256(originalRaw), original_staff_plans: originalPlans,
  original_staff_followup_activations: originalPlans.filter(row => row.followup_ids.length).length,
  original_staff_alias_changes: originalPlans.filter(row => row.suppressed_aliases.length).length,
  model_calls: 0, network_calls: 0, source_modifications: 0,
  limitations: [
    'These are development questions evaluated against already inspected source targets, not an independent blind test.',
    'Combined navigation hits are a set comparison only. Independent contexts and provenance are not merged into an answerable legal package.',
    'All forty original staff questions were checked for recovery-plan changes. This is a plan non-regression check, not a replay of their earlier acceptance receipts.',
    'The local adapter is a review candidate. The public Ask OKF service and frozen source projections remain unchanged.',
  ],
};
const serialised = JSON.stringify(output, null, 2) + '\n';
if (option('--output')) {
  const path = resolve(option('--output'));
  if (args.includes('--check')) assert.equal(readFileSync(path, 'utf8'), serialised, 'Recovery evaluation drift');
  else writeFileSync(path, serialised);
}
process.stdout.write(JSON.stringify({schema: output.schema, cases: cases.length,
  original_staff_followup_activations: output.original_staff_followup_activations,
  original_staff_alias_changes: output.original_staff_alias_changes,
  target_hits: cases.map(row => ({id: row.id, before: row.baseline.target_hits, after: row.combined_navigation_hits,
    followups: row.followups.map(row => row.id)})), model_calls: 0, network_calls: 0}, null, 2) + '\n');
