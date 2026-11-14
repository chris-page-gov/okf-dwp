import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import test from 'node:test';
import { createGraphEvidenceRuntime, graphSha } from './graph_evidence_runtime.mjs';
import { loadEvidenceRouteRuntime } from './load_evidence_route_runtime.mjs';

const ENGINE = 'urn:okf:graph-engine:sha256:' + 'a'.repeat(64);
const ROOT = resolve(new URL('..', import.meta.url).pathname);
const id = value => 'urn:test:' + value;
const record = (key, kind = 'concept', text = key) => ({
  id: id(key), route: key, label: key, kind, text, aliases: [], access: 'public',
  assertion_status: 'normalized', authority: { class: 'derived', label: 'Test fixture' },
  provenance: kind === 'evidence' ? [{ source_sha256: '1'.repeat(64), literal_sha256: '2'.repeat(64) }] : [],
});
const edge = (source, target, context = []) => ({
  id: id(`edge-${source}-${target}`), source: id(source), target: id(target), predicate: 'references',
  context_guard: { when_all: context.map(id) },
});
const requirement = (key, when, required, paths = []) => ({
  id: id(`requirement-${key}`), label: key, when_all: when.map(id), required: required.map(id),
  required_paths: paths, limitations: [],
});

async function fixture({ records, assertions = [], requirements = [], resolver = () => ({ resolved: [], ambiguities: [], unresolved: [] }), routingRules = [] }) {
  const graph = { schema: 'okf-dwp-evidence-route-graph.v1', snapshot: 'test-snapshot', source_bindings: [],
    routing_rules: routingRules, index: { schema: 'okf-context-index.v1', records, assertions, requirements } };
  const graphText = JSON.stringify(graph);
  const graphSha256 = await graphSha(graphText);
  const runtime = await createGraphEvidenceRuntime({ graphText, graphSha256, engineId: ENGINE,
    resolveConcepts: resolver, validateContextIndex: index => assert.equal(index.schema, 'okf-context-index.v1') });
  return { runtime, graphText, graphSha256 };
}

const resolved = (...names) => () => ({ resolved: names.map(name => ({ id: id(name) })), ambiguities: [], unresolved: [] });

test('rejects a stale graph digest before creating the runtime', async () => {
  const { graphText } = await fixture({ records: [record('root')] });
  await assert.rejects(() => createGraphEvidenceRuntime({ graphText, graphSha256: '0'.repeat(64), engineId: ENGINE,
    resolveConcepts: resolved('root'), validateContextIndex: () => {} }), /graph digest differs/);
});

test('empty profiles and absent required evidence remain incomplete', async () => {
  const empty = await fixture({ records: [record('root')], resolver: resolved('root') });
  const emptyPlan = await empty.runtime.plan('known concept without a task profile');
  assert.equal(emptyPlan.retrieval_status, 'no-declared-profile');
  assert.equal(emptyPlan.retrieval_complete, false);
  assert(emptyPlan.diagnostics.some(row => row.code === 'no_evidence_requirements'));

  const absent = await fixture({ records: [record('root')], requirements: [requirement('missing', ['root'], ['absent'])],
    resolver: resolved('root') });
  const absentPlan = await absent.runtime.plan('find the absent evidence');
  assert.equal(absentPlan.retrieval_complete, false);
  assert(absentPlan.requirements[0].missing_record_ids.includes(id('absent')));
  assert(absentPlan.diagnostics.some(row => row.code === 'source_absent'));
});

test('a required target is reached over its directed edge and never becomes a seed', async () => {
  let resolverQuestion;
  const setup = await fixture({ records: [record('root'), record('source', 'evidence', 'Original passage text')],
    assertions: [edge('root', 'source')], requirements: [requirement('route', ['root'], ['source'])],
    resolver: (_index, question) => { resolverQuestion = question; return resolved('root')(); } });
  const plan = await setup.runtime.plan('a natural-language question');
  assert.equal(resolverQuestion, 'a natural-language question');
  assert.equal(plan.retrieval_complete, true);
  assert.deepEqual(plan.resolved_concepts.map(row => row.id), [id('root')]);
  const target = plan.selected.find(row => row.record.id === id('source'));
  assert(target);
  assert.deepEqual(target.paths.map(path => path.records), [[id('root'), id('source')]]);
});

test('unrelated resolved roots cannot satisfy another requirement', async () => {
  const setup = await fixture({ records: [record('unrelated'), record('required-root'), record('source', 'evidence')],
    assertions: [edge('unrelated', 'source')],
    requirements: [requirement('only-required-root', ['required-root'], ['source'])],
    resolver: resolved('unrelated', 'required-root') });
  const plan = await setup.runtime.plan('a question resolving two concepts');
  assert.equal(plan.retrieval_complete, false);
  assert(plan.requirements[0].missing_record_ids.includes(id('source')));
  assert(!plan.selected.some(row => row.record.id === id('source')));
});

test('exhausted concept resolution cannot report complete retrieval even when selected paths exist', async () => {
  const setup = await fixture({ records: [record('root'), record('source', 'evidence')],
    assertions: [edge('root', 'source')], requirements: [requirement('route', ['root'], ['source'])],
    resolver: () => ({ ...resolved('root')(), truncated: true }) });
  const plan = await setup.runtime.plan('a question that exhausted concept resolution');
  assert(plan.selected.some(row => row.record.id === id('source')));
  assert.equal(plan.retrieval_complete, false);
  assert.equal(plan.retrieval_status, 'incomplete');
  assert(plan.diagnostics.some(row => row.code === 'resolution_budget'));
});

test('unresolved context guards do not admit a directed edge', async () => {
  const setup = await fixture({ records: [record('root'), record('guard'), record('source', 'evidence')],
    assertions: [edge('root', 'source', ['guard'])],
    requirements: [requirement('guarded', ['root'], ['source'])], resolver: resolved('root') });
  const plan = await setup.runtime.plan('a guarded route');
  assert.equal(plan.retrieval_complete, false);
  assert(plan.requirements[0].missing_record_ids.includes(id('source')));
});

test('ambiguous alternatives neither activate profiles nor satisfy required paths', async () => {
  const setup = await fixture({ records: [record('root'), record('alternative'), record('source', 'evidence')],
    assertions: [edge('alternative', 'source')],
    requirements: [requirement('root-only', ['root'], ['source'])],
    resolver: () => ({ resolved: [{ id: id('root') }], ambiguities: [{ candidates: [id('alternative')] }], unresolved: [] }) });
  const plan = await setup.runtime.plan('a question with an ambiguous term');
  assert.equal(plan.retrieval_complete, false);
  assert(plan.requirements[0].missing_record_ids.includes(id('source')));
  assert(!plan.selected.some(row => row.record.id === id('source')));
  assert(plan.diagnostics.some(row => row.code === 'ambiguous_concepts'));
});

test('planning does not mutate source records or carry plan edits into the next run', async () => {
  const setup = await fixture({ records: [record('root'), record('source', 'evidence', 'Frozen source passage')],
    assertions: [edge('root', 'source')], requirements: [requirement('route', ['root'], ['source'])],
    resolver: resolved('root') });
  const before = await graphSha(setup.graphText);
  const first = await setup.runtime.plan('question');
  first.selected.find(row => row.record.id === id('source')).record.text = 'tampered client copy';
  const second = await setup.runtime.plan('question');
  assert.equal(await graphSha(setup.graphText), before);
  assert.equal(second.selected.find(row => row.record.id === id('source')).record.text, 'Frozen source passage');
});

test('loader binds deterministic engine and graph identities to the pinned Explorer source', {
  skip: !process.env.OKF_EXPLORER_ROOT,
  timeout: 60000,
}, async () => {
  const args = { root: ROOT, explorerRoot: process.env.OKF_EXPLORER_ROOT };
  const [first, second] = await Promise.all([loadEvidenceRouteRuntime(args), loadEvidenceRouteRuntime(args)]);
  assert.equal(first.engineId, second.engineId);
  assert.equal(first.graphSha256, second.graphSha256);
  assert.equal(first.runtime.identity.graph_sha256, first.graphSha256);
  assert.equal(first.runtime.identity.engine_id, first.engineId);
  assert.equal(first.runtime.identity.snapshot, second.runtime.identity.snapshot);
});

test('the real graph retrieves each frozen staff source target without target IDs as inputs', {
  skip: !process.env.OKF_EXPLORER_ROOT,
  timeout: 180000,
}, async () => {
  const [{ runtime }, questionsRaw] = await Promise.all([
    loadEvidenceRouteRuntime({ root: ROOT, explorerRoot: process.env.OKF_EXPLORER_ROOT }),
    readFile(resolve(ROOT, 'evaluation/staff-questions/cases.json'), 'utf8'),
  ]);
  const registry = JSON.parse(questionsRaw);
  const questions = registry.cases;
  const candidates = new Map(registry.source_candidates.map(row => [row.id, row.record_id]));
  assert.equal(questions.length, 40);
  let targetCount = 0;
  for (const row of questions) {
    const targets = row.candidate_ids.map(candidateId => candidates.get(candidateId));
    assert(targets.length && targets.every(Boolean), `no verified independent source targets for ${row.id}`);
    const plan = await runtime.plan(row.question);
    const selected = new Map(plan.selected.map(item => [item.record.id, item]));
    const missing = targets.filter(target => !selected.has(target));
    assert.deepEqual(missing, [], `${row.id} misses source targets`);
    for (const target of targets) {
      assert(!plan.resolved_concepts.some(concept => concept.id === target), `${row.id} injects target as a concept seed`);
      assert(selected.get(target).paths.length > 0, `${row.id} target lacks a directed path`);
    }
    assert.equal(plan.evidence_status, 'insufficient');
    assert.equal(plan.ai_answer, null);
    targetCount += targets.length;
  }
  assert(targetCount > 0);
});

test('the real graph retrieves all four separately declared UC source targets', {
  skip: !process.env.OKF_EXPLORER_ROOT,
  timeout: 60000,
}, async () => {
  const [{ runtime }, specRaw] = await Promise.all([
    loadEvidenceRouteRuntime({ root: ROOT, explorerRoot: process.env.OKF_EXPLORER_ROOT }),
    readFile(resolve(ROOT, 'evaluation/out-of-sample/uc-disabled-child-supersession-001.json'), 'utf8'),
  ]);
  const spec = JSON.parse(specRaw);
  const targets = spec.source_targets.map(row => row.unit_id);
  assert.equal(targets.length, 4);
  const plan = await runtime.plan(spec.question);
  const selected = new Map(plan.selected.map(item => [item.record.id, item]));
  assert.deepEqual(targets.filter(target => !selected.has(target)), []);
  for (const target of targets) {
    assert(!plan.resolved_concepts.some(concept => concept.id === target));
    assert(selected.get(target).paths.length > 0);
  }
  assert.equal(plan.evidence_status, 'insufficient');
  assert.equal(plan.ai_answer, null);
});
