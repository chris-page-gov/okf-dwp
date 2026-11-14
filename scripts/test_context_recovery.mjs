import assert from 'node:assert/strict';
import {mkdtemp, mkdir, readFile, writeFile, rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {dirname, resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {test} from 'node:test';
import {createContextRecovery, planRecoveryQueries, suppressCompoundAliases, validateRecoveryPolicy} from './context_recovery.mjs';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const explorerRoot = process.env.OKF_EXPLORER_ROOT || resolve(root, '../okf-explorer');
const policyPath = 'domain-profile/context-recovery/policy.yamlld';
const policy = JSON.parse(await readFile(resolve(root, policyPath)));
const spec = JSON.parse(await readFile(resolve(root, 'evaluation/out-of-sample/uc-disabled-child-supersession-001.json')));

test('compound alias guard preserves independent mentions, sensitive aliases and original input', () => {
  const index = {records: [{id: 'https://example.test/rates', kind: 'concept', aliases: ['rate', 'care', {label: 'PIP', case_sensitive: true}]}]};
  const frozen = structuredClone(index);
  const compound = suppressCompoundAliases(index, 'highest-rate care and PIP-related queries');
  assert.deepEqual(compound.suppressed.map(row => row.alias), ['rate']);
  assert.deepEqual(index, frozen);
  assert.deepEqual(compound.index.records[0].aliases, ['care', {label: 'PIP', case_sensitive: true}]);
  assert.equal(suppressCompoundAliases(index, 'highest-rate and rate').suppressed.length, 0);
  assert.equal(suppressCompoundAliases(index, 'highest–rate').suppressed[0].alias, 'rate');
  assert.equal(suppressCompoundAliases(index, 'separate rating').suppressed.length, 0);
});

test('dimension planning uses bounded conjunctions and no dates, answer or paragraph identifier', () => {
  const positives = [
    spec.question,
    'My child’s DLA was increased retrospectively but I told UC much later. When should the extra disabled-child amount start?',
    'When does an award of another benefit change Universal Credit?',
    'A daughter received PIP. What is the effective date of the UC change?',
    'Does UC backdate the child addition when DLA is awarded?',
  ];
  for (const question of positives) {
    const queries = planRecoveryQueries(question, policy);
    assert(queries.some(row => row.id === 'other-benefit-timing'), question);
    assert(queries.length <= 3);
    assert(queries.every(row => !/\b[A-Z]\d{3,}\b/.test(row.query)));
    assert(queries.every(row => row.assertion_status === 'model-derived' && row.review_status === 'unreviewed'));
  }
  for (const question of [
    'What are the Pension Credit rates?',
    'DLA was awarded to my child. Explain the conditions.',
    'The rent change was reported late to Universal Credit.',
    'How many days were between 26 January 2025 and 28 March 2026?',
    'xylophonicquasarteleportation',
  ]) assert(!planRecoveryQueries(question, policy).some(row => row.id === 'other-benefit-timing'), question);
  const noInferredLate = planRecoveryQueries(spec.question, policy);
  assert(!noInferredLate.some(row => row.id === 'late-notification'), 'Date arithmetic must not infer late notification');
  assert(planRecoveryQueries('I reported a change late to UC. What happens?', policy).some(row => row.id === 'late-notification'));
});

test('policy rejects executable/unknown fields, missing support and unbounded or locator-based queries', () => {
  validateRecoveryPolicy(policy);
  for (const change of [
    value => { value.command = 'arbitrary command'; },
    value => { value.engine.files['extra.ts'] = 'a'.repeat(64); },
    value => { value.engine.commit = '0'.repeat(40); },
    value => { value.engine.files['unit.ts'] = '0'.repeat(64); },
    value => { value.routes[0].query = 'Universal Credit A4361'; },
    value => { value.routes[0].query = 'UC a4361'; },
    value => { value.routes[0].query = 'UC f1123'; },
    value => { value.routes[0].support = [999]; },
    value => { value.routes.push(value.routes[0]); },
    value => { value.limits.max_followups = 999; },
    value => { value.source_manifest.path = '../outside.json'; },
  ]) {
    const changed = structuredClone(policy); change(changed);
    assert.throws(() => validateRecoveryPolicy(changed));
  }
  assert.throws(() => planRecoveryQueries('x'.repeat(2001), policy));
});

test('pure validation and planning return detached nested source support and route data', () => {
  const original = structuredClone(policy);
  const accepted = validateRecoveryPolicy(original);
  accepted.engine.commit = '0'.repeat(40);
  accepted.routes[0].all_of[0][0] = 'fabricated scope';
  accepted.source_support[0].literal = 'FABRICATED SUPPORT';
  assert.deepEqual(original, policy);
  const plan = planRecoveryQueries(spec.question, original);
  plan[0].source_support[0].literal = 'FABRICATED SUPPORT';
  plan[0].matched_phrases[0].push('fabricated scope');
  plan[0].query = 'fabricated question';
  assert.deepEqual(original, policy);
  assert.notEqual(planRecoveryQueries(spec.question, original)[0].source_support[0].literal, 'FABRICATED SUPPORT');
});

test('source manifest drift fails before any source passage can be returned', async () => {
  const fixture = await mkdtemp(resolve(tmpdir(), 'okf-recovery-source-control-'));
  try {
    for (const [relative, raw] of [[policyPath, await readFile(resolve(root, policyPath))], [policy.source_manifest.path, Buffer.from('{}')]]) {
      const destination = resolve(fixture, relative); await mkdir(dirname(destination), {recursive: true}); await writeFile(destination, raw);
    }
    await assert.rejects(createContextRecovery({root: fixture, explorerRoot}), /Recovery source manifest drift/);
  } finally { await rm(fixture, {recursive: true, force: true}); }
});

test('a policy cannot substitute a different quotation for the frozen source support', async () => {
  const fixture = await mkdtemp(resolve(tmpdir(), 'okf-recovery-support-control-'));
  try {
    const changed = structuredClone(policy); changed.source_support[0].literal = 'A quotation absent from the frozen source';
    const manifest = JSON.parse(await readFile(resolve(root, policy.source_manifest.path)));
    const first = changed.source_support[0];
    const shard = manifest.records.shards.find(row => row.first_id <= first.unit_id && first.unit_id <= row.last_id);
    const files = [policy.source_manifest.path, 'structured-context/' + manifest.base_index.path, 'structured-context/' + shard.path];
    for (const relative of files) {
      const destination = resolve(fixture, relative); await mkdir(dirname(destination), {recursive: true});
      await writeFile(destination, await readFile(resolve(root, relative)));
    }
    const destination = resolve(fixture, policyPath); await mkdir(dirname(destination), {recursive: true});
    await writeFile(destination, JSON.stringify(changed));
    await assert.rejects(createContextRecovery({root: fixture, explorerRoot}), /Recovery source support drift/);
  } finally { await rm(fixture, {recursive: true, force: true}); }
});

test('recovery preserves original failure and separately discovers missing source without claiming a decision', {timeout: 180000}, async () => {
  const session = await createContextRecovery({root, explorerRoot});
  const result = await session.assemble(spec.question);
  assert.equal(result.evidence_status, 'insufficient'); assert.equal(result.ai_answer, null);
  assert.equal(result.baseline.context_id, spec.observed_replay.context_id);
  assert.equal(result.baseline.budget.used_bytes, spec.observed_replay.used_bytes);
  assert(result.baseline.requirements.some(row => row.id.endsWith('/staff-008')));
  assert(result.guarded && result.guarded.derivation.suppressed.some(row => row.alias === 'rate'));
  assert(!result.guarded.context.requirements.some(row => row.id.endsWith('/staff-008')));
  assert.notEqual(result.guarded.source_binding.index_sha256, result.source_binding.index_sha256);
  const all = [result.baseline, result.guarded.context, ...result.followups.map(row => row.context)];
  const originalF1123 = spec.source_targets.find(row => row.paragraph === 'F1123').unit_id;
  const missingA4361 = spec.source_targets.find(row => row.paragraph === 'A4361').unit_id;
  assert(result.guarded.context.selected.some(row => row.record.id === originalF1123));
  assert(!result.baseline.selected.some(row => row.record.id === missingA4361));
  assert(result.followups.find(row => row.id === 'other-benefit-timing').context.selected.some(row => row.record.id === missingA4361));
  assert.equal(result.followups.length, 2);
  for (const context of all) {
    assert.equal(context.ai_answer, null); assert.equal(context.evidence_status, 'insufficient');
    assert(context.missing_evidence.length > 0);
    assert(context.budget.used_bytes <= context.budget.max_bytes);
    assert(context.budget.max_bytes <= 524288);
  }
  assert.equal(result.model_calls, 0); assert.equal(result.network_calls, 0);
});

test('identity, plan and assembled output mutations cannot change retained session bindings or support', {timeout: 180000}, async () => {
  const session = await createContextRecovery({root, explorerRoot});
  const identity = session.identity, expectedIdentity = structuredClone(identity);
  const expectedPlan = session.plan(spec.question);
  identity.source_binding.index_sha256 = '0'.repeat(64);
  identity.engine.commit = '0'.repeat(40);
  identity.engine.files['unit.ts'] = '0'.repeat(64);
  const changedPlan = session.plan(spec.question);
  changedPlan.queries[0].source_support[0].literal = 'FABRICATED SUPPORT';
  changedPlan.queries[0].matched_phrases[0].push('fabricated scope');
  changedPlan.compound_aliases[0].compounds.push('fabricated-rate');
  assert.deepEqual(session.identity, expectedIdentity);
  assert.deepEqual(session.plan(spec.question), expectedPlan);
  const result = await session.assemble(spec.question);
  assert.deepEqual(result.source_binding, expectedIdentity.source_binding);
  assert.deepEqual(result.engine, expectedIdentity.engine);
  assert.deepEqual(result.followups[0].source_support, expectedPlan.queries[0].source_support);
  const expectedContext = result.baseline.context_id;
  result.source_binding.index_sha256 = '0'.repeat(64);
  result.engine.commit = '0'.repeat(40);
  result.engine.files['unit.ts'] = '0'.repeat(64);
  result.baseline.binding.index_sha256 = '0'.repeat(64);
  result.followups[0].source_binding.index_sha256 = '0'.repeat(64);
  result.followups[0].source_support[0].literal = 'FABRICATED SUPPORT';
  assert.deepEqual(session.identity, expectedIdentity);
  assert.deepEqual(session.plan(spec.question), expectedPlan);
  const replay = await session.assemble(spec.question);
  assert.equal(replay.baseline.context_id, expectedContext);
  assert.deepEqual(replay.source_binding, expectedIdentity.source_binding);
  assert.deepEqual(replay.engine, expectedIdentity.engine);
  assert.deepEqual(replay.followups[0].source_support, expectedPlan.queries[0].source_support);
});
