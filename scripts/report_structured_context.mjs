#!/usr/bin/env node
/** Report existing frozen assemblies; never retrieves, assembles or calls a model. */
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFileSync, writeFileSync, mkdirSync, existsSync} from 'node:fs';
import {resolve} from 'node:path';
import {fileURLToPath} from 'node:url';

const total = (rows, field) => rows.reduce((n, row) => n + row[field], 0);
const unique = values => [...new Set(values)].sort();
const sha = value => createHash('sha256').update(value).digest('hex');
function range(values) {
  const sorted = [...values].sort((a, b) => a - b), mid = Math.floor(sorted.length / 2);
  return {minimum: sorted[0], median: sorted.length % 2 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2,
    maximum: sorted.at(-1)};
}

export function summariseStructuredContext(report) {
  assert.equal(report.schema, 'okf-dwp-structured-context-evaluation.v1');
  const {stages, budgets, denominator} = report.protocol;
  assert(Number.isInteger(denominator) && denominator > 0);
  assert.equal(unique(stages).length, stages.length);
  assert.equal(unique(budgets).length, budgets.length);
  const staff = report.rows.filter(row => row.case_id !== 'unknown-control');
  const cases = unique(staff.map(row => row.case_id));
  assert.equal(cases.length, denominator, 'Staff case denominator differs');
  const cellKeys = report.rows.map(row => JSON.stringify([row.case_id, row.stage, row.max_bytes]));
  assert.equal(unique(cellKeys).length, cellKeys.length, 'Duplicate assembly cell');
  assert(report.rows.every(row => stages.includes(row.stage) && budgets.includes(row.max_bytes)), 'Unexpected stage or budget');
  const questions = new Map();
  for (const row of staff) {
    if (questions.has(row.case_id)) assert.equal(row.question, questions.get(row.case_id), 'Question changed between cells');
    questions.set(row.case_id, row.question);
  }
  const cells = [];
  for (const stage of stages) for (const max_bytes of budgets) {
    const rows = staff.filter(row => row.stage === stage && row.max_bytes === max_bytes);
    assert.deepEqual(unique(rows.map(row => row.case_id)), cases, 'Incomplete comparison cell');
    const controls = report.rows.filter(row => row.case_id === 'unknown-control' && row.stage === stage && row.max_bytes === max_bytes);
    assert.equal(controls.length, 1, 'Missing unknown control');
    assert.equal(controls[0].evidence_records, 0, 'Unknown control selected evidence');
    const groupIds = unique(rows.flatMap(row => (row.requirement_groups || []).map(group => group.id)));
    const requirement_planes = groupIds.map(id => {
      const groups = rows.map(row => (row.requirement_groups || []).find(group => group.id === id));
      assert(groups.every(Boolean), 'Requirement plane missing from a case');
      return {id, case_occurrences_with_active_requirements: groups.filter(group => group.active_requirements.length).length,
        unique_active_requirement_ids: unique(groups.flatMap(group => group.active_requirements)),
        required_path_case_incidences: total(groups, 'required_paths'),
        retained_required_path_case_incidences: total(groups, 'retained_required_paths')};
    });
    const locations = rows.map(row => row.location_navigation).filter(Boolean);
    assert(locations.length === 0 || locations.length === denominator, 'Partial location metric coverage');
    let location_navigation = null;
    if (locations.length) {
      for (const location of locations) {
        assert.equal(location.legacy_obligations.closed_by_location_navigation, 0, 'Location route claimed obligation closure');
        assert.equal(location.legacy_obligations.selected_as_evidence, 0, 'Open obligation supplied as evidence');
      }
      const original = unique(locations.map(location => location.legacy_obligations.original_count));
      const declared = unique(locations.map(location => location.legacy_obligations.declared_in_this_index));
      assert.equal(original.length, 1, 'Original obligation denominator changed');
      assert.equal(declared.length, 1, 'Declared obligation denominator changed');
      location_navigation = {
        original_obligation_count: original[0], declared_obligation_count: declared[0],
        distinct_active_open_obligation_ids: unique(locations.flatMap(location => location.legacy_obligations.active_ids)),
        closed_by_location_navigation: 0,
        routes: Object.fromEntries(['restored-original-route', 'inferred-profile-candidate-route'].map(kind => [kind, {
          declared_case_route_incidences: locations.reduce((n, location) => n + location.routes[kind].declared_routes, 0),
          retained_case_route_incidences: locations.reduce((n, location) => n + location.routes[kind].retained_routes, 0)
        }])),
        distinct_selected_mapped_unit_ids: unique(locations.flatMap(location => location.locations.selected_mapped_unit_ids)),
        partial_or_unresolved_location_ids: unique(locations.flatMap(location => location.locations.partial_or_unresolved_source_locations))
      };
    }
    cells.push({stage, max_bytes, staff_case_denominator: denominator,
      cases_with_evidence: rows.filter(row => row.evidence_records > 0).length,
      cases_with_active_requirements: rows.filter(row => row.active_requirements.length > 0).length,
      cases_with_relationships: rows.filter(row => row.relationships > 0).length,
      insufficient_cases: rows.filter(row => row.evidence_status === 'insufficient').length,
      retrieval_truncated_cases: rows.filter(row => row.retrieval_truncated).length,
      assembly_truncated_cases: rows.filter(row => row.assembly_truncated).length,
      source_text_bytes: range(rows.map(row => row.source_text_bytes)),
      returned_package_bytes: range(rows.map(row => row.bytes)),
      requirement_planes, location_navigation,
      cases: rows.map(row => ({case_id: row.case_id, question: row.question, archive: row.archive,
        evidence_records: row.evidence_records, source_text_bytes: row.source_text_bytes,
        relationships: row.relationships, active_requirements: row.active_requirements,
        declared_resolved_concepts: row.declared_resolved_concepts ?? null,
        delivered_resolved_concepts: row.resolved_concepts,
        inherited_required_paths: row.inherited_required_paths ?? null,
        retained_inherited_paths: row.retained_inherited_paths ?? null,
        requirement_groups: row.requirement_groups || [], location_navigation: row.location_navigation ?? null,
        evidence_status: row.evidence_status, retrieval_truncated: row.retrieval_truncated,
        assembly_truncated: row.assembly_truncated, bytes: row.bytes,
        missing_evidence: row.missing_evidence}))});
  }
  return {schema: 'okf-dwp-structured-context-comparison.v1', comparison_mode: report.protocol.comparison_mode || 'same-authored-semantics',
    staff_case_denominator: denominator, question_source: report.protocol.cases, engine: report.engine,
    source_bindings: report.protocol.source_bindings, network_calls: 0, model_calls: 0, cells,
    limitations: ['This summarises retained assemblies; it does not execute retrieval or a model.',
      'Cases are known development questions. No independent relevance, claim accuracy or legal acceptance is measured.',
      'Path and route totals are case incidences, not distinct legal rules; shared routes can occur in several questions.',
      'Restored and inferred location routes remain separate from requirement support. Selected mapped units may have arrived lexically.',
      'Original open obligation identifiers are deduplicated, not summed across questions or budgets.',
      'Byte ranges describe this bounded delivery. They are not an affordability or controlled speed benchmark.']};
}

export function renderSummary(summary) {
  const lines = ['# Source-led context comparison', '',
    'This is an independent experimental publication. Navigation, evidence delivery and legal answerability are separate.', '',
    `The report covers **${summary.staff_case_denominator} unchanged staff question occurrences** in each stage and budget, plus a separate unknown-question control.`, '',
    '| Stage | Budget (bytes) | Cases with evidence | Cases with requirements | Cases with relationships | Insufficient | Retrieval truncated | Assembly truncated |',
    '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |'];
  for (const cell of summary.cells) lines.push(`| ${cell.stage} | ${cell.max_bytes} | ${cell.cases_with_evidence} | ${cell.cases_with_active_requirements} | ${cell.cases_with_relationships} | ${cell.insufficient_cases} | ${cell.retrieval_truncated_cases} | ${cell.assembly_truncated_cases} |`);
  lines.push('', '## Reading the measures', '', ...summary.limitations.map(text => '- ' + text), '',
    'The machine-readable companion retains every case, separate requirement planes, restored and inferred routes, original open obligation identifiers, source bytes and package bytes. A larger route count is not proof of a supported answer.', '');
  return lines.join('\n');
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const [flag, input, outputFlag, output] = process.argv.slice(2);
  assert.equal(flag, '--report'); assert.equal(outputFlag, '--output'); assert(input && output);
  const raw = readFileSync(resolve(input));
  const summary = summariseStructuredContext(JSON.parse(raw));
  summary.input = {path: input, bytes: raw.length, sha256: sha(raw)};
  summary.reporter_sha256 = sha(readFileSync(fileURLToPath(import.meta.url)));
  const directory = resolve(output); assert(!existsSync(directory), 'Preserve existing reports; choose a new output directory');
  mkdirSync(directory, {recursive: true});
  writeFileSync(resolve(directory, 'comparison.json'), JSON.stringify(summary, null, 2) + '\n');
  writeFileSync(resolve(directory, 'README.md'), renderSummary(summary));
  console.log(JSON.stringify({status: 'summarised', cases: summary.staff_case_denominator, cells: summary.cells.length}));
}
