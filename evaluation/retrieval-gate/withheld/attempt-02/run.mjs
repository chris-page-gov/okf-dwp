#!/usr/bin/env node
/** Replay the previously withheld wording after the bounded review corrections through the local bounded loader/client path. */
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFile, writeFile } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { collectGraphEvidence } from '../../../../scripts/graph_evidence_client.mjs';
import { graphBytes, graphEvidenceManifest, readGraphEvidence } from '../../../../scripts/graph_evidence_runtime.mjs';
import { loadEvidenceRouteRuntime } from '../../../../scripts/load_evidence_route_runtime.mjs';

const ATTEMPT = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(ATTEMPT, '../../../..');
const EXPLORER_ROOT = process.argv[2] || process.env.OKF_EXPLORER_ROOT;
assert(EXPLORER_ROOT, 'Supply Explorer root as the first argument or OKF_EXPLORER_ROOT');
const hash = value => createHash('sha256').update(value).digest('hex');
const fileHash = async path => hash(await readFile(path));
const protocolBytes = await readFile(resolve(ATTEMPT, 'protocol.json'));
const protocol = JSON.parse(protocolBytes.toString('utf8'));
const freeze = JSON.parse(await readFile(resolve(ATTEMPT, 'freeze.json'), 'utf8'));
assert.equal(hash(protocolBytes), freeze.withheld_protocol_sha256, 'Withheld protocol differs from the frozen digest');
assert.equal(protocol.counts.cases, 24);
assert.equal(protocol.counts.positive_retrieval, 12);
assert.equal(protocol.counts.negative_boundary, 12);

const registrySha = await fileHash(resolve(ROOT, 'evaluation/staff-questions/cases.json'));
const corpusSha = await fileHash(resolve(ROOT, 'combined/context/corpus/base-index.json'));
assert.equal(registrySha, protocol.source_bindings.staff_question_registry_sha256);
assert.equal(corpusSha, protocol.source_bindings.combined_corpus_base_index_sha256);
const clientSha = await fileHash(resolve(ROOT, 'scripts/graph_evidence_client.mjs'));
const loaderSha = await fileHash(resolve(ROOT, 'scripts/load_evidence_route_runtime.mjs'));
const runtimeSha = await fileHash(resolve(ROOT, 'scripts/graph_evidence_runtime.mjs'));
const classifierSha = await fileHash(resolve(ROOT, 'scripts/insufficiency_categories.mjs'));
assert.equal(clientSha, freeze.client_sha256, 'Client no longer matches frozen candidate');
assert.equal(loaderSha, freeze.loader_sha256, 'Loader no longer matches frozen candidate');
assert.equal(runtimeSha, freeze.engine_admission.modules['graph_evidence_runtime.mjs'], 'Runtime module differs from frozen candidate');
assert.equal(classifierSha, freeze.engine_admission.modules['insufficiency_categories.mjs'], 'Classifier differs from frozen candidate');

const loaded = await loadEvidenceRouteRuntime({ root: ROOT, explorerRoot: resolve(EXPLORER_ROOT) });
assert.equal(loaded.graphSha256, freeze.graph_sha256, 'Graph digest differs from frozen candidate');
assert.equal(loaded.engineId, freeze.engine_id, 'Engine identity differs from frozen candidate');
assert.deepEqual(loaded.engineAdmission, freeze.engine_admission, 'Engine admission differs from frozen candidate');
const graph = JSON.parse(loaded.graphText);
const graphRecords = new Map(graph.index.records.map(row => [row.id, row]));
const sourceRegistry = JSON.parse(await readFile(resolve(ROOT, 'evaluation/staff-questions/cases.json'), 'utf8'));
const sourceCandidates = new Map(sourceRegistry.source_candidates.map(row => [row.id, row]));

function envelope(value) {
  return { jsonrpc: '2.0', id: 1, result: { structuredContent: structuredClone(value),
    content: [{ type: 'text', text: JSON.stringify(value) }] } };
}
const envelopeBytes = value => graphBytes(envelope(value));
const plans = new Map();
async function getPlan(question) {
  if (!plans.has(question)) plans.set(question, await loaded.runtime.plan(question));
  return plans.get(question);
}
const transport = {
  async manifest(input) {
    assert.equal(input.graph_sha256, freeze.graph_sha256);
    assert.equal(input.engine_id, freeze.engine_id);
    const plan = await getPlan(input.question);
    return envelope(await graphEvidenceManifest(plan,
      { offset: input.offset, maxBytes: input.delivery_bytes }, envelopeBytes));
  },
  async read(input) {
    assert.equal(input.graph_sha256, freeze.graph_sha256);
    assert.equal(input.engine_id, freeze.engine_id);
    const plan = await getPlan(input.question);
    return envelope(await readGraphEvidence(plan,
      { ...input, maxBytes: input.delivery_bytes }, envelopeBytes));
  },
};
async function collect(question) {
  return collectGraphEvidence({ transport, question, expectedGraphSha256: freeze.graph_sha256,
    expectedEngineId: freeze.engine_id, deliveryBytes: 8192 });
}
function evidenceRows(value) { return value.package.selected.filter(row => row.record.kind === 'evidence'); }
function sourceBindingsFor(recordId) {
  return graphRecords.get(recordId)?.provenance ?? [];
}
function targetIsSourceBound(target) {
  return sourceBindingsFor(target.id).some(row => row.source_sha256 === target.source_sha256
    && row.literal_sha256 === target.literal_sha256);
}
async function verifyTargetSourceFiles(target) {
  const candidate = sourceCandidates.get(target.candidate_id);
  assert(candidate, `Unknown source candidate in holdout target: ${target.id}`);
  assert.equal(candidate.record_id, target.id);
  assert.equal(candidate.route, target.route);
  assert.equal(candidate.source_sha256, target.source_sha256);
  assert.equal(candidate.literal_sha256, target.literal_sha256);
  assert.equal(candidate.pages_sha256, target.pages_file_sha256);
  assert.equal(await fileHash(resolve(ROOT, candidate.source_pdf)), candidate.source_sha256,
    `Frozen source PDF hash changed: ${target.id}`);
  assert.equal(await fileHash(resolve(ROOT, candidate.pages_path)), candidate.pages_sha256,
    `Frozen extracted pages hash changed: ${target.id}`);
  const pages = JSON.parse(await readFile(resolve(ROOT, candidate.pages_path), 'utf8')).pages;
  const pageNumber = Number(candidate.route.split('/').at(-1));
  const page = pages.find(row => row.page === pageNumber);
  assert(page && page.text, `Frozen source page missing: ${target.id}`);
  assert.equal(hash(Buffer.from(page.text, 'utf8')), candidate.literal_sha256,
    `Frozen source page literal changed: ${target.id}`);
  assert.equal(graphRecords.get(target.id)?.text, page.text,
    `Graph record text differs from exact frozen source page: ${target.id}`);
}
function pathScopedHit(value, recordId) {
  const selected = value.package.selected.find(row => row.record.id === recordId);
  if (!selected) return false;
  const requirements = value.package.requirements.filter(row => row.required.includes(recordId)
    || row.required_paths.some(path => path.records.includes(recordId)));
  return selected.paths.some(path => path.assertions.length > 0 && path.records.at(-1) === recordId
    && requirements.some(requirement => selected.reasons.some(reason => reason.endsWith(requirement.id)
      && (reason.startsWith('verified-directed-route:') || reason.startsWith('declared-directed-path:')))));
}

const caseReceipts = [];
for (const testCase of protocol.cases) {
  const collection = await collect(testCase.question);
  const packageValue = collection.package;
  const records = evidenceRows(collection);
  const selectedIds = new Set(records.map(row => row.record.id));
  const shared = { id: testCase.id, case_class: testCase.class, question_sha256: hash(testCase.question),
    graph_sha256: freeze.graph_sha256, engine_id: freeze.engine_id,
    plan_id: collection.summary.plan_id, package_sha256: collection.summary.package_sha256,
    evidence_status: packageValue.evidence_status, ai_answer: packageValue.ai_answer,
    retrieval_complete: packageValue.retrieval_complete, retrieval_status: packageValue.retrieval_status,
    assembly_truncated: packageValue.assembly_truncated,
    delivery_complete: collection.summary.delivery_complete, package_complete: collection.summary.package_complete,
    delivery: collection.summary.delivery,
    observed_source_records: records.map(row => ({ id: row.record.id, route: row.record.route,
      provenance: row.record.provenance, paths: row.paths, reasons: row.reasons })),
    diagnostics: packageValue.diagnostics.map(row => ({ code: row.code, ids: row.ids })),
    insufficiency_categories: packageValue.insufficiency_categories };
  if (testCase.class === 'positive-retrieval') {
    assert.equal(testCase.recall_eligible, true, `${testCase.id} must be recall-eligible`);
    const expected = testCase.assessor_binding.expected_record_ids;
    assert(expected.length > 0, `${testCase.id} lacks source targets`);
    assert(testCase.assessor_binding.source_targets.every(target => targetIsSourceBound(target)
      && graphRecords.get(target.id)?.route === target.route),
      `${testCase.id} contains a target that fails frozen source-hash binding`);
    for (const target of testCase.assessor_binding.source_targets) await verifyTargetSourceFiles(target);
    const hits = expected.filter(id => selectedIds.has(id));
    const pathHits = expected.filter(id => pathScopedHit(collection, id));
    caseReceipts.push({ ...shared, expected_target_count: expected.length, expected_record_ids: expected,
      expected_target_provenance: testCase.assessor_binding.source_targets,
      target_hits: hits, target_misses: expected.filter(id => !selectedIds.has(id)),
      path_scoped_hits: pathHits, path_scoped_misses: expected.filter(id => !pathHits.includes(id)),
      target_retrieval_pass: hits.length === expected.length,
      path_scoped_retrieval_pass: pathHits.length === expected.length,
      source_target_bindings_pass: true,
      delivery_gate_pass: collection.summary.delivery_complete && collection.summary.package_complete
        && packageValue.assembly_truncated === false && collection.summary.delivery.max_response_bytes <= 8192 });
  } else {
    assert.equal(testCase.class, 'negative-boundary-control');
    assert.equal(testCase.recall_eligible, false, `${testCase.id} must not enter recall denominator`);
    assert.deepEqual(testCase.assessor_binding.expected_record_ids, [], `${testCase.id} must remain target-free`);
    caseReceipts.push({ ...shared, recall_eligible: false, recall_denominator_contribution: 0,
      expected_gap: testCase.assessor_binding.required_gap,
      negative_assertions: {
        target_free_protocol: testCase.assessor_binding.expected_record_ids.length === 0,
        no_answer_or_entitlement_claim: packageValue.ai_answer === null,
        explicitly_insufficient: packageValue.evidence_status === 'insufficient',
        delivery_complete: collection.summary.delivery_complete && collection.summary.package_complete,
        no_truncation: packageValue.assembly_truncated === false,
        bounded_full_envelope: collection.summary.delivery.max_response_bytes <= 8192,
      },
      negative_control_pass: packageValue.ai_answer === null && packageValue.evidence_status === 'insufficient'
        && collection.summary.delivery_complete && collection.summary.package_complete
        && packageValue.assembly_truncated === false && collection.summary.delivery.max_response_bytes <= 8192 });
  }
}

const positives = caseReceipts.filter(row => row.case_class === 'positive-retrieval');
const negatives = caseReceipts.filter(row => row.case_class === 'negative-boundary-control');
const expectedCount = positives.reduce((total, row) => total + row.expected_target_count, 0);
const hitCount = positives.reduce((total, row) => total + row.target_hits.length, 0);
const pathHitCount = positives.reduce((total, row) => total + row.path_scoped_hits.length, 0);
const allDeliveriesComplete = caseReceipts.every(row => row.delivery_complete && row.package_complete
  && row.assembly_truncated === false && row.delivery.max_response_bytes <= 8192);
const allPositiveTargetsReached = positives.every(row => row.target_retrieval_pass && row.path_scoped_retrieval_pass);
const allNegativeAssertionsPass = negatives.every(row => row.negative_control_pass);
const runnerBytes = await readFile(fileURLToPath(import.meta.url));
const receipt = {
  schema: 'okf-hidden-holdout-trial.v1',
  trial_status: allDeliveriesComplete && allPositiveTargetsReached && allNegativeAssertionsPass
    ? 'retrieval-and-boundary-gates-passed' : 'trial-gate-failed',
  interpretation_status: 'not-assessed', legal_or_entitlement_sufficiency: 'not-assessed',
  run: { mode: 'offline local runtime, simulated full JSON-RPC/MCP envelope through bounded client',
    model_calls: 0, network_calls: 0, paid_api_calls: 0, delivery_limit_bytes: 8192 },
  identities: { freeze_file_sha256: await fileHash(resolve(ATTEMPT, 'freeze.json')),
    protocol_sha256: hash(protocolBytes), runner_sha256: hash(runnerBytes),
    graph_sha256: loaded.graphSha256, engine_id: loaded.engineId,
    client_sha256: clientSha, loader_sha256: loaderSha, runtime_sha256: runtimeSha,
    insufficiency_classifier_sha256: classifierSha,
    engine_admission: loaded.engineAdmission,
    source_binding_sha256: { staff_question_registry: registrySha, combined_corpus_base_index: corpusSha } },
  counts: { total_cases: caseReceipts.length, positive_retrieval_cases: positives.length,
    negative_boundary_cases: negatives.length, positive_expected_target_occurrences: expectedCount,
    positive_target_hits: hitCount, positive_target_misses: expectedCount - hitCount,
    path_scoped_hits: pathHitCount, path_scoped_misses: expectedCount - pathHitCount,
    positive_target_recall: expectedCount ? hitCount / expectedCount : null,
    path_scoped_target_recall: expectedCount ? pathHitCount / expectedCount : null,
    negative_controls_passed: negatives.filter(row => row.negative_control_pass).length,
    negative_controls_failed: negatives.filter(row => !row.negative_control_pass).length,
    all_deliveries_complete: allDeliveriesComplete,
    max_response_bytes_observed: Math.max(...caseReceipts.map(row => row.delivery.max_response_bytes)) },
  gates: { positive_retrieval: allPositiveTargetsReached ? 'passed' : 'failed',
    negative_nonfabrication: allNegativeAssertionsPass ? 'passed' : 'failed',
    complete_bounded_delivery: allDeliveriesComplete ? 'passed' : 'failed',
    legal_interpretation: 'not-assessed', accessibility: 'not-assessed', human_blindness: 'regression replay of previously withheld wording; no fresh blind trial' },
  cases: caseReceipts,
  limitations: [
    'This post-review regression replay tests exact source-record retrieval and conservative target-free boundary behaviour only.',
    'The boundary assertion detects a non-null answer and an insufficient-status violation; it does not establish legal correctness.',
    'The trial uses a local in-process runtime and simulated MCP envelope, not a deployed plugin host or public service.',
    'No UI, assistive-technology, human interpretation or entitlement decision was tested.',
  ],
};
const outputPath = resolve(ATTEMPT, 'receipt.json');
await writeFile(outputPath, JSON.stringify(receipt, null, 2) + '\n', 'utf8');
await writeFile(resolve(ATTEMPT, 'run-summary.json'), JSON.stringify({ schema: receipt.schema,
  trial_status: receipt.trial_status, identities: receipt.identities, counts: receipt.counts, gates: receipt.gates }, null, 2) + '\n', 'utf8');
process.stdout.write(JSON.stringify({ trial_status: receipt.trial_status, counts: receipt.counts,
  positive_failures: positives.filter(row => !row.target_retrieval_pass || !row.path_scoped_retrieval_pass).map(row => row.id),
  negative_failures: negatives.filter(row => !row.negative_control_pass).map(row => row.id),
  receipt: outputPath }, null, 2) + '\n');
if (receipt.trial_status !== 'retrieval-and-boundary-gates-passed') process.exitCode = 1;
