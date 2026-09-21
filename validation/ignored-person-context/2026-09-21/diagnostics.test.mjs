import assert from 'node:assert/strict';
import test from 'node:test';
import { diagnosticCensus } from './diagnostics.mjs';
test('retained dependency sources in diagnostics do not become omitted required records', () => {
  const obligation = 'https://example.test/obligation/staff/case/review';
  const index = { records: [{id:'source'},{id:'target'},{id:'optional'}] };
  const observed = { selected_ids: ['source'], expected_required_ids: ['source','target',obligation],
    missing_evidence: [{ids:['source','target']},{ids:['optional',obligation]}] };
  const result = diagnosticCensus(observed,index);
  assert.deepEqual(result.missing_required_record_ids,['target']);
  assert.deepEqual(result.missing_registered_obligation_ids,[obligation]);
  assert.deepEqual(result.diagnostic_retained_record_ids,['source']);
  assert.deepEqual(result.diagnostic_unselected_existing_ids,['optional','target']);
  assert.equal(result.diagnostic_union_ids.length,4);
});
test('empty returned requirements do not erase pre-budget expected records', () => {
  const result = diagnosticCensus({ selected_ids:[],expected_required_ids:['required','required','unknown'],
    missing_evidence:[],requirements:[] }, { records:[{id:'required'}] });
  assert.deepEqual(result.expected_existing_required_record_ids,['required']);
  assert.deepEqual(result.missing_required_record_ids,['required']);
  assert.deepEqual(result.missing_other_declared_ids,['unknown']);
  assert.deepEqual(result.diagnostic_union_ids,[]);
});
