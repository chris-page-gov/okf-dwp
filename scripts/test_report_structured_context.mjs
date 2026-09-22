import {test} from 'node:test';
import assert from 'node:assert/strict';
import {summariseStructuredContext, renderSummary} from './report_structured_context.mjs';

function fixture() {
  const report = {schema: 'okf-dwp-structured-context-evaluation.v1',
    protocol: {stages: ['baseline', 'candidate'], budgets: [32768], denominator: 2, comparison_mode: 'additive-source-and-semantic-increment'}, rows: []};
  for (const stage of report.protocol.stages) for (const case_id of ['one', 'two', 'unknown-control']) {
    const candidate = stage === 'candidate', unknown = case_id === 'unknown-control';
    report.rows.push({stage, case_id, question: case_id, max_bytes: 32768, evidence_records: unknown ? 0 : 1,
      source_text_bytes: unknown ? 0 : 100, bytes: 1000, active_requirements: unknown ? [] : ['inherited', ...(candidate ? ['legacy'] : [])],
      relationships: candidate && !unknown ? 1 : 0, evidence_status: 'insufficient', retrieval_truncated: false, assembly_truncated: true,
      resolved_concepts: [], declared_resolved_concepts: unknown ? [] : ['benefit'], requirement_groups: [
        {id: 'inherited', active_requirements: unknown ? [] : ['inherited'], required_paths: unknown ? 0 : 1, retained_required_paths: 0},
        {id: 'legacy', active_requirements: unknown || !candidate ? [] : ['legacy'], required_paths: unknown || !candidate ? 0 : 1, retained_required_paths: 0}],
      location_navigation: {legacy_obligations: {original_count: 1, declared_in_this_index: candidate ? 1 : 0,
        active_ids: candidate && !unknown ? ['open-obligation'] : [], selected_as_evidence: 0, closed_by_location_navigation: 0},
      routes: {'restored-original-route': {declared_routes: candidate && !unknown ? 1 : 0, retained_routes: candidate && !unknown ? 1 : 0},
        'inferred-profile-candidate-route': {declared_routes: 0, retained_routes: 0}},
      locations: {selected_mapped_unit_ids: candidate && !unknown ? ['unit'] : [], partial_or_unresolved_source_locations: []}}});
  }
  return report;
}

test('separates restored route delivery from unchanged unmet requirement paths and deduplicates obligations', () => {
  const result = summariseStructuredContext(fixture()), candidate = result.cells[1];
  assert.equal(candidate.location_navigation.routes['restored-original-route'].retained_case_route_incidences, 2);
  assert.equal(candidate.requirement_planes.find(row => row.id === 'legacy').retained_required_path_case_incidences, 0);
  assert.deepEqual(candidate.location_navigation.distinct_active_open_obligation_ids, ['open-obligation']);
  assert.equal(candidate.location_navigation.closed_by_location_navigation, 0);
  assert.equal(candidate.insufficient_cases, 2);
  assert.equal(candidate.cases[0].declared_resolved_concepts.length, 1);
  assert.equal(candidate.cases[0].delivered_resolved_concepts.length, 0);
  assert.match(renderSummary(result), /not proof of a supported answer/);
});
test('rejects duplicate cells, missing cases and altered question text', () => {
  let f = fixture(); f.rows.push(f.rows[0]); assert.throws(() => summariseStructuredContext(f), /Duplicate assembly/);
  f = fixture(); f.rows.splice(0, 1); assert.throws(() => summariseStructuredContext(f), /Incomplete comparison/);
  f = fixture(); f.rows[3].question = 'changed'; assert.throws(() => summariseStructuredContext(f), /Question changed/);
});
test('rejects positive unknown controls and purported obligation closure', () => {
  let f = fixture(); f.rows[2].evidence_records = 1; assert.throws(() => summariseStructuredContext(f), /Unknown control/);
  f = fixture(); f.rows[3].location_navigation.legacy_obligations.closed_by_location_navigation = 1;
  assert.throws(() => summariseStructuredContext(f), /claimed obligation closure/);
});
