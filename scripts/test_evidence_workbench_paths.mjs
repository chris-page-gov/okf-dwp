import assert from 'node:assert/strict';
import { test } from 'node:test';
import { outputPath, validateCaseIds } from './evidence_workbench_paths.mjs';

const cases = () => Array.from({length:40},(_,i)=>({id:`staff-${String(i+1).padStart(3,'0')}`,question:`Question ${i+1}?`}));

test('fixed staff IDs reject traversal, duplicates and missing cases', () => {
  validateCaseIds(cases());
  for (const attack of ['../escape','staff-001/../../escape','staff-999','staff-001.json']) {
    const altered=cases();altered[0].id=attack;
    assert.throws(()=>validateCaseIds(altered));
  }
  const duplicate=cases();duplicate[1].id=duplicate[0].id;
  assert.throws(()=>validateCaseIds(duplicate));
  assert.throws(()=>validateCaseIds(cases().slice(1)));
});

test('generated path always stays within output root', () => {
  const base='/private/tmp/evidence-workbench';
  assert.equal(outputPath(base,'packages/staff-001.json'),`${base}/packages/staff-001.json`);
  for (const attack of ['../escape','packages/../../escape','/private/tmp/escape','packages//staff-001.json','packages/./staff-001.json'])
    assert.throws(()=>outputPath(base,attack));
});
