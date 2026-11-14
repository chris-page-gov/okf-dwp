#!/usr/bin/env node
/** Offline retrieval-only evaluation for projected personas and frozen controls. */
import assert from 'node:assert/strict';
import { readFile, writeFile } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { collectGraphEvidence } from './graph_evidence_client.mjs';
import { graphBytes, graphEvidenceManifest, graphSha, readGraphEvidence } from './graph_evidence_runtime.mjs';
import { loadEvidenceRouteRuntime } from './load_evidence_route_runtime.mjs';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const DEFAULT_OUTPUT = 'evaluation/retrieval-gate/graph-evaluation.json';
const args = process.argv.slice(2);
function option(name) {
  const index = args.indexOf(name);
  return index < 0 ? undefined : args[index + 1];
}
for (const flag of args.filter(arg => arg.startsWith('--'))) {
  assert(['--explorer-root', '--output', '--check'].includes(flag), `Unknown option: ${flag}`);
  if (flag !== '--check') assert(option(flag) && !option(flag).startsWith('--'), `${flag} requires a value`);
}
assert.equal(args.filter(arg => arg === '--check').length, args.includes('--check') ? 1 : 0, 'Duplicate --check');
assert(!args.includes('--check') || option('--output'), '--check requires --output');
const explorerRoot = option('--explorer-root') || process.env.OKF_EXPLORER_ROOT;
assert(explorerRoot, 'Use --explorer-root PATH or set OKF_EXPLORER_ROOT');
const outputPath = resolve(ROOT, option('--output') || DEFAULT_OUTPUT);
const checkMode = args.includes('--check');
const sha = raw => graphSha(Buffer.from(raw).toString());

const inputPaths = [
  'domain-profile/staff-needs/persona-evaluation.json',
  'domain-profile/staff-needs/journeys.json',
  'evaluation/retrieval-gate/persona-cases.json',
  'evaluation/retrieval-gate/persona-coverage.json',
  'evaluation/staff-questions/cases.json',
  'evaluation/staff-needs/matrix.json',
  'evaluation/out-of-sample/uc-disabled-child-supersession-001.json',
  'evaluation/truncation/recovery-cases.json',
  'evaluation/context-assembly/imprisonment-case.json',
  'evaluation/context-assembly/source-check.json',
  'evaluation/remote-mcp/hospital-case.json',
  'evaluation/manual-structure/original-acceptance/protocol.json',
  'evaluation/manual-structure/original-acceptance/runs/acceptance-01/report.json',
  'scripts/build_evidence_route_graph.py',
  'scripts/load_evidence_route_runtime.mjs',
  'scripts/graph_evidence_runtime.mjs',
  'scripts/graph_evidence_client.mjs',
  'scripts/insufficiency_categories.mjs',
  'scripts/evaluate_graph_retrieval.mjs',
];

const rawInputs = new Map();
for (const relative of inputPaths) rawInputs.set(relative, await readFile(resolve(ROOT, relative)));
const json = relative => JSON.parse(rawInputs.get(relative).toString('utf8'));
const hashes = await Promise.all([...rawInputs].map(async ([path, raw]) => ({
  path, bytes: raw.length, sha256: await sha(raw),
})));
const byHashPath = new Map(hashes.map(row => [row.path, row]));
const personaCoverage = json('evaluation/retrieval-gate/persona-coverage.json');
const personaSuite = json('evaluation/retrieval-gate/persona-cases.json');
const staffRegistry = json('evaluation/staff-questions/cases.json');
const staffMatrix = json('evaluation/staff-needs/matrix.json');
const ucSpec = json('evaluation/out-of-sample/uc-disabled-child-supersession-001.json');
const recoveryProtocol = json('evaluation/truncation/recovery-cases.json');
const custodyFixture = json('evaluation/context-assembly/imprisonment-case.json');
const custodySourceCheck = json('evaluation/context-assembly/source-check.json');
const hospitalFixture = json('evaluation/remote-mcp/hospital-case.json');
const legacyProtocol = json('evaluation/manual-structure/original-acceptance/protocol.json');
const legacyReport = json('evaluation/manual-structure/original-acceptance/runs/acceptance-01/report.json');

assert.equal(staffRegistry.cases.length, 40, 'Frozen original question registry changed');
assert.equal(staffMatrix.occurrences, 40, 'Staff question matrix no longer maps the frozen 40');
assert.equal(personaSuite.cases.length, 75, 'Projected persona suite must retain all 75 cases');
assert.equal(personaCoverage.counts.personas, 8);
assert.equal(personaCoverage.counts.areas, 21);
const personaCaseRows = personaSuite.cases;
const retrievalCases = personaCaseRows.filter(row => row.evaluation.kind === 'retrieval');
const recallCases = retrievalCases.filter(row => row.evaluation.expected_records.length > 0);
const nonRecallCases = personaCaseRows.filter(row => row.evaluation.kind !== 'retrieval');
assert.equal(retrievalCases.length, 62);
assert.equal(recallCases.length, 62);
assert.equal(nonRecallCases.length, 13);
assert(nonRecallCases.every(row => row.evaluation.expected_records.length === 0 && !row.evaluation.recall_eligible));
assert(recallCases.every(row => row.evaluation.expected_records.length > 0 && row.evaluation.recall_eligible));

const loaded = await loadEvidenceRouteRuntime({ root: ROOT, explorerRoot: resolve(explorerRoot) });
const graph = JSON.parse(loaded.graphText);
const graphSha256 = loaded.graphSha256;
const engineId = loaded.engineId;
assert.equal(loaded.runtime.identity.graph_sha256, graphSha256);
assert.equal(loaded.runtime.identity.engine_id, engineId);
const graphIndexRecords = new Map(graph.index.records.map(row => [row.id, row]));

function jsonRpcEnvelope(value) {
  return { jsonrpc: '2.0', id: 1, result: { structuredContent: structuredClone(value),
    content: [{ type: 'text', text: JSON.stringify(value) }] } };
}
const envelopeBytes = value => graphBytes(jsonRpcEnvelope(value));
const plans = new Map();
async function planFor(question) {
  if (!plans.has(question)) plans.set(question, await loaded.runtime.plan(question));
  return plans.get(question);
}
const transport = {
  async manifest(input) {
    assert.equal(input.graph_sha256, graphSha256);
    assert.equal(input.engine_id, engineId);
    const plan = await planFor(input.question);
    return jsonRpcEnvelope(await graphEvidenceManifest(plan,
      { offset: input.offset, maxBytes: input.delivery_bytes }, envelopeBytes));
  },
  async read(input) {
    assert.equal(input.graph_sha256, graphSha256);
    assert.equal(input.engine_id, engineId);
    const plan = await planFor(input.question);
    return jsonRpcEnvelope(await readGraphEvidence(plan,
      { ...input, maxBytes: input.delivery_bytes }, envelopeBytes));
  },
};

function sourceProvenance(record) {
  return (record?.provenance ?? []).map(row => ({
    locator: row.locator ?? null, source_sha256: row.source_sha256 ?? null,
    literal_sha256: row.literal_sha256 ?? null, url: row.url ?? null,
  }));
}

function selectedEvidence(packageValue) {
  return packageValue.selected.filter(row => row.record.kind === 'evidence');
}

function targetCoverage(packageValue, targets) {
  const selected = new Map(packageValue.selected.map(row => [row.record.id, row]));
  const hits = targets.filter(id => selected.has(id));
  const misses = targets.filter(id => !selected.has(id));
  const pathScoped = hits.filter(id => {
    const selectedRow = selected.get(id);
    const requirements = packageValue.requirements.filter(row => row.required.includes(id)
      || row.required_paths.some(path => path.records.includes(id)));
    return selectedRow.paths.some(path => path.assertions.length > 0 && path.records.at(-1) === id
      && requirements.some(requirement => selectedRow.reasons.some(reason =>
        reason.endsWith(requirement.id) && (reason.startsWith('verified-directed-route:')
          || reason.startsWith('declared-directed-path:')))));
  });
  return { expected_record_ids: targets, target_hits: hits, missing_target_ids: misses,
    expected_count: targets.length, hit_count: hits.length,
    path_scoped_hits: pathScoped, path_scoped_hit_count: pathScoped.length,
    path_scoped_missing_ids: targets.filter(id => !pathScoped.includes(id)) };
}

function obligationAudit(packageValue) {
  const declared = [...new Set(packageValue.requirements.flatMap(row => row.required.filter(id => id.includes('/obligation/'))))].sort();
  const open = [...new Set(packageValue.requirements.flatMap(row => row.open_obligation_ids ?? []))].sort();
  const missing = [...new Set(packageValue.requirements.flatMap(row => row.missing_record_ids.filter(id => id.includes('/obligation/'))))].sort();
  const dropped = declared.filter(id => !open.includes(id) || !missing.includes(id));
  return { declared_count: declared.length, preserved_open_count: open.length,
    dropped_count: dropped.length, dropped_ids: dropped };
}

async function collect(question) {
  return collectGraphEvidence({ transport, question, expectedGraphSha256: graphSha256,
    expectedEngineId: engineId, deliveryBytes: 8192 });
}

function caseSummary(row, collection, targets = row.evaluation.expected_records) {
  const packageValue = collection.package;
  const selectedRows = selectedEvidence(packageValue);
  const selectedIds = selectedRows.map(item => item.record.id).sort();
  const targetIds = new Set(targets);
  const coverage = targetCoverage(packageValue, targets);
  const obligations = obligationAudit(packageValue);
  const missed = coverage.missing_target_ids.length > 0;
  const unpathed = coverage.path_scoped_missing_ids.length > 0;
  const extras = selectedIds.filter(id => !targetIds.has(id));
  return {
    id: row.id, origin: row.origin, kind: row.evaluation.kind,
    personas: row.personas, area_ids: row.area_ids, primary_journeys: row.primary_journeys ?? [],
    question: row.prompt?.question ?? row.question ?? null,
    source_question: row.source_question ?? null, adaptation_note: row.adaptation_note ?? null,
    review_decision: row.review_decision ?? null,
    question_sha256: null,
    resolved_concept_ids: packageValue.resolved_concepts ?? [],
    ambiguous_concept_ids: packageValue.ambiguities ?? [],
    evidence_status: packageValue.evidence_status, ai_answer: packageValue.ai_answer,
    delivery_complete: collection.summary.delivery_complete, package_complete: collection.summary.package_complete,
    retrieval_complete: packageValue.retrieval_complete, retrieval_status: packageValue.retrieval_status,
    assembly_truncated: packageValue.assembly_truncated,
    target_coverage: coverage, selected_source_record_count: selectedRows.length,
    expected_source_record_count: targets.length, extra_source_record_count: extras.length,
    extra_source_record_ids: extras,
    selected_source_records: selectedRows.map(item => ({ id: item.record.id, route: item.record.route,
      text_sha256: null, provenance: sourceProvenance(item.record), paths: item.paths,
      reasons: item.reasons })),
    path_scoped_coverage_status: unpathed ? 'incomplete' : 'complete-target-paths',
    original_obligation_audit: obligations,
    requirement_count: packageValue.requirements.length,
    diagnostics: packageValue.diagnostics.map(item => ({ code: item.code, ids: item.ids })),
    package_sha256: collection.summary.package_sha256, plan_id: collection.summary.plan_id,
    delivery: collection.summary.delivery,
    target_recall_case_status: missed || unpathed ? 'missed-source-target-or-path' : 'all-source-targets-reached',
    boundary_review_status: 'not-assessed',
  };
}

const personaResults = [];
const personaCollections = new Map();
for (const row of personaCaseRows) {
  const query = row.prompt.question;
  const questionSha = await sha(query);
  if (row.evaluation.kind === 'ui' || row.evaluation.kind === 'integrity') {
    personaResults.push({ id: row.id, origin: row.origin, kind: row.evaluation.kind,
      personas: row.personas, area_ids: row.area_ids, question_sha256: questionSha,
      validation_status: 'not-run', recall_eligible: false,
      reason: row.evaluation.kind === 'ui' ? 'Requires observed browser/assistive-technology task completion.'
        : 'Requires isolated mutation execution against a retained integrity fixture.' });
    continue;
  }
  try {
    const collection = await collect(query);
    personaCollections.set(row.id, collection);
    const result = caseSummary(row, collection);
    result.question_sha256 = questionSha;
    result.recall_eligible = row.evaluation.kind === 'retrieval' && row.evaluation.expected_records.length > 0;
    result.validation_status = row.evaluation.kind === 'boundary' ? 'not-run; runtime observation only'
      : result.target_recall_case_status === 'all-source-targets-reached' ? 'retrieval-only-pass' : 'retrieval-only-fail';
    if (row.evaluation.kind === 'boundary') {
      result.expected_gaps = row.evaluation.required_gaps;
      result.negative_control = row.evaluation.negative_control;
      result.boundary_validation = 'not-run';
      result.target_recall_case_status = 'not-applicable';
    }
    personaResults.push(result);
  } catch (error) {
    personaResults.push({ id: row.id, origin: row.origin, kind: row.evaluation.kind,
      personas: row.personas, area_ids: row.area_ids, question_sha256: questionSha,
      recall_eligible: row.evaluation.kind === 'retrieval' && row.evaluation.expected_records.length > 0,
      validation_status: 'delivery-error', error: String(error),
      expected_record_ids: row.evaluation.expected_records,
      expected_target_count: row.evaluation.expected_records.length,
      boundary_validation: row.evaluation.kind === 'boundary' ? 'not-run' : undefined });
  }
}

const sourceCandidates = new Map(staffRegistry.source_candidates.map(row => [row.id, row]));
const staffQuestions = [];
for (const original of staffRegistry.cases) {
  const targets = original.candidate_ids.map(candidateId => {
    const row = sourceCandidates.get(candidateId);
    assert(row, `Unknown frozen source candidate ${candidateId}`);
    return row.record_id;
  });
  try {
    const collection = personaCollections.get(original.id);
    assert(collection, `Frozen staff question was not collected as a persona case: ${original.id}`);
    const selectedCase = personaResults.find(row => row.id === original.id);
    staffQuestions.push({ id: original.id, question_sha256: await sha(original.question),
      expected_target_candidate_ids: original.candidate_ids, ...caseSummary({ ...selectedCase, id: original.id,
        question: original.question }, collection, targets),
      source_target_materiality: 'Independent staff-review candidate targets; exact machine pages, not complete answer evidence.' });
  } catch (error) {
    staffQuestions.push({ id: original.id, question_sha256: await sha(original.question),
      expected_target_candidate_ids: original.candidate_ids, expected_record_ids: targets,
      delivery_complete: false, package_complete: false, error: String(error) });
  }
}

async function runControl({ id: caseId, type, question, targets = [], expectTimingRoute = null, requireMissing = false }) {
  const questionSha = await sha(question);
  try {
    const collection = await collect(question);
    const coverage = targetCoverage(collection.package, targets);
    const activeRoutes = collection.package.navigation_hypotheses.map(row => row.id);
    const timingRouteActive = activeRoutes.includes('late-notification');
    const evidenceRows = selectedEvidence(collection.package);
    return { id: caseId, type, question, question_sha256: questionSha, expected_record_ids: targets,
      resolved_concept_ids: collection.package.resolved_concepts ?? [],
      ambiguous_concept_ids: collection.package.ambiguities ?? [],
      target_coverage: coverage, selected_source_record_count: evidenceRows.length,
      selected_source_record_ids: evidenceRows.map(row => row.record.id).sort(),
      active_navigation_hypotheses: activeRoutes, timing_route_active: timingRouteActive,
      expected_timing_route: expectTimingRoute, timing_route_observation: expectTimingRoute === null ? 'not-scored'
        : timingRouteActive === expectTimingRoute ? 'matches-protocol' : 'differs-from-protocol',
      retrieval_complete: collection.package.retrieval_complete,
      evidence_status: collection.package.evidence_status, ai_answer: collection.package.ai_answer,
      delivery_complete: collection.summary.delivery_complete, package_complete: collection.summary.package_complete,
      assembly_truncated: collection.package.assembly_truncated,
      original_obligation_audit: obligationAudit(collection.package),
      package_sha256: collection.summary.package_sha256, plan_id: collection.summary.plan_id,
      delivery: collection.summary.delivery,
      validation_status: type === 'boundary-control' ? 'not-run; source/gap observation only' : 'retrieval-only-observation'};
  } catch (error) {
    return { id: caseId, type, question_sha256: questionSha, expected_record_ids: targets,
      delivery_complete: false, package_complete: false, error: String(error),
      validation_status: 'delivery-error' };
  }
}

const recoveryTargetsByParagraph = new Map(ucSpec.source_targets.map(row => [row.paragraph, row.unit_id]));
const recoveryResults = [];
for (const row of recoveryProtocol.cases) {
  const question = row.original ? ucSpec.question : row.question;
  const targets = row.required_hits.map(label => {
    const id = recoveryTargetsByParagraph.get(label);
    assert(id, `Recovery protocol target not in independent UC source registry: ${label}`);
    return id;
  });
  recoveryResults.push(await runControl({ id: row.id, type: row.expect_timing_route ? 'unhinted-recovery-positive' : 'recovery-negative-control',
    question, targets, expectTimingRoute: row.expect_timing_route, requireMissing: targets.length === 0 }));
}

const ucPositive = await runControl({ id: ucSpec.id, type: 'fixed-out-of-sample-positive',
  question: ucSpec.question, targets: ucSpec.source_targets.map(row => row.unit_id) });

const custodyTargets = custodyFixture.expected.evidence;
const custodyControl = await runControl({ id: custodyFixture.id, type: 'legacy-custody-positive-control',
  question: custodyFixture.question, targets: custodyTargets });
const custodySourceChecks = new Map(custodySourceCheck.checks.map(row => [row.record_id, row]));
const custodyTargetMappings = custodyTargets.map(id => {
  const graphRecord = graphIndexRecords.get(id);
  const check = custodySourceChecks.get(id);
  const exactSourceHashMatch = Boolean(graphRecord && check
    && graphRecord.provenance?.some(row => row.source_sha256 === check.source_sha256
      && row.literal_sha256 === check.literal_sha256));
  return { expected_record_id: id, graph_record_present: Boolean(graphRecord),
    frozen_source_check_present: Boolean(check), exact_source_and_literal_hash_match: exactSourceHashMatch,
    route: graphRecord?.route ?? null, source_sha256: check?.source_sha256 ?? null,
    literal_sha256: check?.literal_sha256 ?? null };
});
custodyControl.expected_target_mapping = {
  method: 'Join original frozen custody expected page IDs to the separately retained context source-check records and current graph records by exact ID; verify that the graph record provenance contains the same source and literal hashes. This validates target comparability only, not retrieval, meaning or legal adequacy.',
  expected_target_count: custodyTargets.length,
  graph_record_matches: custodyTargetMappings.filter(row => row.graph_record_present).length,
  frozen_source_check_matches: custodyTargetMappings.filter(row => row.frozen_source_check_present).length,
  exact_source_and_literal_hash_matches: custodyTargetMappings.filter(row => row.exact_source_and_literal_hash_match).length,
  unmatched_target_ids: custodyTargetMappings.filter(row => !row.exact_source_and_literal_hash_match).map(row => row.expected_record_id),
  records: custodyTargetMappings,
};
const hospitalControl = await runControl({ id: hospitalFixture.id, type: 'legacy-hospital-boundary-control',
  question: hospitalFixture.question, targets: hospitalFixture.expected.evidence ?? [],
  requireMissing: true });
const unknownControl = await runControl({ id: legacyProtocol.unknown_control.id, type: 'legacy-unknown-boundary-control',
  question: legacyProtocol.unknown_control.question, targets: [], requireMissing: true });

const personaRetrievalResults = personaResults.filter(row => row.recall_eligible);
const targetRows = personaRetrievalResults.flatMap(row => row.target_coverage?.expected_record_ids ?? []);
const targetHits = personaRetrievalResults.flatMap(row => row.target_coverage?.target_hits ?? []);
const targetMissing = personaRetrievalResults.flatMap(row => row.target_coverage?.missing_target_ids ?? row.expected_record_ids ?? []);
const pathScopedTargets = personaRetrievalResults.flatMap(row => row.target_coverage?.path_scoped_hits ?? []);
const deliveryErrors = personaRetrievalResults.filter(row => row.validation_status === 'delivery-error');
const caseRecallFailures = personaRetrievalResults.filter(row => row.target_recall_case_status !== 'all-source-targets-reached');
const personaRuntimeResults = personaResults.filter(row => row.kind === 'retrieval' || row.kind === 'boundary');
const personaDeliveryErrors = personaRuntimeResults.filter(row => row.validation_status === 'delivery-error');
const envelopeSizes = [...personaRuntimeResults, ...recoveryResults, ucPositive, custodyControl, hospitalControl, unknownControl]
  .flatMap(row => row.delivery?.max_response_bytes === undefined ? [] : [row.delivery.max_response_bytes]);
const allRelevantComplete = [...personaRuntimeResults, ...recoveryResults, ucPositive, custodyControl, hospitalControl, unknownControl]
  .every(row => row.delivery_complete !== false && row.package_complete !== false && row.assembly_truncated !== true);
const obligationsByPackage = [...personaResults, ...recoveryResults, ucPositive, custodyControl, hospitalControl, unknownControl]
  .map(row => row.original_obligation_audit).filter(Boolean);
const droppedOriginalObligations = obligationsByPackage.reduce((total, row) => total + row.dropped_count, 0);

const inputHashes = hashes.concat([{ path: 'retrieval-graph/graph.json', bytes: Buffer.byteLength(loaded.graphText), sha256: graphSha256 }])
  .sort((a, b) => a.path.localeCompare(b.path));
const output = {
  schema: 'okf-dwp-graph-retrieval-evaluation.v1',
  evaluation_status: caseRecallFailures.length || deliveryErrors.length || personaDeliveryErrors.length || !allRelevantComplete
    ? 'retrieval-gate-failed' : 'retrieval-gate-passed',
  interpretation_status: 'not-assessed',
  run: { transport: 'local in-process runtime with JSON-RPC/MCP envelope simulation; no live service call',
    model_calls: 0, network_calls: 0, paid_api_calls: 0 },
  identities: { graph_sha256: graphSha256, graph_snapshot: loaded.runtime.identity.snapshot,
    engine_id: engineId, engine_admission: loaded.engineAdmission,
    graph_source_bindings: graph.source_bindings, input_hashes: inputHashes },
  protocol_hashes: {
    persona_authoring_sha256: byHashPath.get('domain-profile/staff-needs/persona-evaluation.json').sha256,
    persona_case_suite_sha256: byHashPath.get('evaluation/retrieval-gate/persona-cases.json').sha256,
    persona_coverage_sha256: byHashPath.get('evaluation/retrieval-gate/persona-coverage.json').sha256,
    frozen_staff_registry_sha256: byHashPath.get('evaluation/staff-questions/cases.json').sha256,
    staff_matrix_sha256: byHashPath.get('evaluation/staff-needs/matrix.json').sha256,
    recovery_protocol_sha256: byHashPath.get('evaluation/truncation/recovery-cases.json').sha256,
    uc_case_sha256: byHashPath.get('evaluation/out-of-sample/uc-disabled-child-supersession-001.json').sha256,
    custody_fixture_sha256: byHashPath.get('evaluation/context-assembly/imprisonment-case.json').sha256,
    custody_source_check_sha256: byHashPath.get('evaluation/context-assembly/source-check.json').sha256,
    hospital_fixture_sha256: byHashPath.get('evaluation/remote-mcp/hospital-case.json').sha256,
    legacy_original_protocol_sha256: byHashPath.get('evaluation/manual-structure/original-acceptance/protocol.json').sha256,
    legacy_original_report_sha256: byHashPath.get('evaluation/manual-structure/original-acceptance/runs/acceptance-01/report.json').sha256,
    evaluator_sha256: byHashPath.get('scripts/evaluate_graph_retrieval.mjs').sha256,
    runtime_sha256: byHashPath.get('scripts/graph_evidence_runtime.mjs').sha256,
    client_sha256: byHashPath.get('scripts/graph_evidence_client.mjs').sha256,
    loader_sha256: byHashPath.get('scripts/load_evidence_route_runtime.mjs').sha256,
    insufficiency_classifier_sha256: byHashPath.get('scripts/insufficiency_categories.mjs').sha256,
    graph_builder_sha256: byHashPath.get('scripts/build_evidence_route_graph.py').sha256,
  },
  counts: { personas: personaCoverage.counts.personas, persona_areas: personaCoverage.counts.areas,
    persona_cases: personaCaseRows.length, frozen_question_occurrences: staffRegistry.cases.length,
    persona_retrieval_cases: personaRetrievalResults.length, persona_boundary_cases: personaResults.filter(row => row.kind === 'boundary').length,
    persona_ui_cases: personaResults.filter(row => row.kind === 'ui').length,
    persona_integrity_cases: personaResults.filter(row => row.kind === 'integrity').length,
    expected_persona_target_occurrences: targetRows.length, persona_target_hits: targetHits.length,
    persona_target_misses: targetMissing.length, persona_path_scoped_hits: pathScopedTargets.length,
    max_response_bytes_observed: envelopeSizes.length ? Math.max(...envelopeSizes) : 0,
    target_recall: targetRows.length ? targetHits.length / targetRows.length : null,
    path_scoped_target_recall: targetRows.length ? pathScopedTargets.length / targetRows.length : null,
    retrieval_case_failures: caseRecallFailures.length, retrieval_delivery_errors: deliveryErrors.length,
    persona_runtime_delivery_errors: personaDeliveryErrors.length,
    open_boundary_ui_integrity_validations: personaResults.filter(row => row.validation_status === 'not-run').length },
  gate: { retrieval_target_gate: caseRecallFailures.length || deliveryErrors.length ? 'failed' : 'passed',
    complete_target_recall: targetMissing.length === 0,
    path_scoped_target_retrieval: pathScopedTargets.length === targetRows.length,
    all_deliveries_complete: allRelevantComplete,
    no_assembly_truncation: allRelevantComplete,
    original_obligations_dropped: droppedOriginalObligations > 0,
    legal_or_entitlement_sufficiency: 'not-assessed',
    boundary_nonfabrication: 'not-run; runtime observations are retained without a sufficiency pass',
    accessibility_validation: 'not-run; requires observed browser and assistive-technology task completion',
    integrity_mutation_validation: 'not-run; separate isolated mutation tests are required' },
  original_obligation_audit: { checked_packages: obligationsByPackage.length,
    dropped_obligation_count: droppedOriginalObligations,
    method: 'For every delivered requirement, compare its declared /obligation/ IDs with both open_obligation_ids and missing_record_ids; no obligation is treated as closed by retrieved sources.' },
  frozen_staff_questions: staffQuestions,
  persona_cases: personaResults,
  recovery_protocol_cases: recoveryResults,
  fixed_uc_out_of_sample_case: ucPositive,
  legacy_original_controls: { custody: custodyControl, hospital: hospitalControl, unknown_vocabulary: unknownControl,
    frozen_original_acceptance: { report_sha256: byHashPath.get('evaluation/manual-structure/original-acceptance/runs/acceptance-01/report.json').sha256,
      engine_commit: legacyProtocol.engine.commit, original_custody_case_id: custodyFixture.id,
      original_custody_question_sha256: await sha(custodyFixture.question),
      original_hospital_case_id: hospitalFixture.id, original_hospital_question_sha256: await sha(hospitalFixture.question),
      baseline_custody_512k_source_units: legacyReport.rows.find(row => row.case_id === custodyFixture.id && row.max_bytes === 524288)?.source_units ?? null,
      baseline_custody_512k_retained_passages: legacyReport.rows.find(row => row.case_id === custodyFixture.id && row.max_bytes === 524288)?.passages.length ?? null,
      baseline_hospital_512k_source_units: legacyReport.rows.find(row => row.case_id === hospitalFixture.id && row.max_bytes === 524288)?.source_units ?? null,
      baseline_unknown_control_source_units: legacyReport.rows.find(row => row.case_id === 'unknown-control')?.source_units ?? null } },
  limitations: [
    'This run measures source-record retrieval against independently retained candidate targets and declared graph targets only. It does not test legal interpretation, benefit entitlement or award calculation.',
    'The frozen forty-question registry and original custody/hospital fixtures remain unchanged. Candidate pages are not complete evidence chains or approved answers.',
    'Expected target IDs are supplied to this evaluator after query execution; only prompt.question is sent to the runtime.',
    'Boundary cases are observed but not scored for legal sufficiency or non-fabrication. UI and integrity cases remain not-run pending their dedicated human or mutation validation.',
    'Custody and hospital results are separate historical controls and do not contribute to persona-suite recall.',
    'The local MCP envelope wrapper tests bounded progressive collection; no live plugin-host or public service call is represented.',
  ],
};

const serialised = JSON.stringify(output, null, 2) + '\n';
if (checkMode) {
  const retained = await readFile(outputPath, 'utf8');
  assert.equal(retained, serialised, 'Graph retrieval evaluation differs');
} else {
  await writeFile(outputPath, serialised, { encoding: 'utf8' });
}
process.stdout.write(JSON.stringify({ schema: output.schema, evaluation_status: output.evaluation_status,
  cases: output.counts.persona_cases, persona_retrieval_cases: output.counts.persona_retrieval_cases,
  expected_targets: output.counts.expected_persona_target_occurrences,
  target_hits: output.counts.persona_target_hits, target_misses: output.counts.persona_target_misses,
  path_scoped_hits: output.counts.persona_path_scoped_hits,
  target_recall: output.counts.target_recall, path_scoped_target_recall: output.counts.path_scoped_target_recall,
  max_response_bytes: output.counts.max_response_bytes_observed, check: checkMode }, null, 2) + '\n');
if (output.gate.retrieval_target_gate === 'failed' || !allRelevantComplete) process.exitCode = 1;
