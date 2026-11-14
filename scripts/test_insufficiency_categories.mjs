import { test } from 'node:test';
import assert from 'node:assert/strict';
import { categoriseInsufficiency } from './insufficiency_categories.mjs';

test('classification retains raw evidence and unknown codes without inventing closure', () => {
  const issues = [{ code: 'legal_version_unreconciled', message: 'Relevant version unknown', ids: ['urn:source'] },
    { code: 'new_engine_reason', message: 'Unclassified', ids: [] }];
  const output = categoriseInsufficiency(issues);
  assert.equal(output.find(x => x.id === 'legal_applicability').reasons[0].code, issues[0].code);
  assert.equal(output.find(x => x.id === 'unclassified').reasons[0].message, 'Unclassified');
  output[0].reasons[0].ids.push('changed');
  assert.deepEqual(issues[0].ids, ['urn:source']);
});

test('a missing working-index record is not automatically an absent source', () => {
  const issue = [{ code: 'missing_record', message: 'Missing working record', ids: ['urn:present'] }];
  assert.equal(categoriseInsufficiency(issue)[0].id, 'graph_connections');
  assert.equal(categoriseInsufficiency(issue, { availableRecordIds: ['urn:present'] })[0].id, 'retrieval');
  assert.equal(categoriseInsufficiency(issue, { availableRecordIds: [] })[0].id, 'source_coverage');
});
