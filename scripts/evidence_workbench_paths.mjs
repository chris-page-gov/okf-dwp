/** Strict paths for the fixed 40-question workbench export. */
import assert from 'node:assert/strict';
import { resolve, sep } from 'node:path';

export function validateCaseIds(cases) {
  assert(Array.isArray(cases) && cases.length === 40, 'Expected exactly 40 staff cases');
  const expected = Array.from({length:40},(_,i)=>`staff-${String(i+1).padStart(3,'0')}`);
  assert.deepEqual(cases.map(row=>row.id),expected,'Staff case IDs must be ordered unique fixed slugs');
  for (const row of cases) {
    assert(/^staff-[0-9]{3}$/.test(row.id),'Unsafe case ID');
    assert(typeof row.question==='string' && row.question.length>0 && row.question.length<=4000,'Invalid question');
  }
}

export function outputPath(base, relative) {
  assert(typeof relative==='string' && /^[a-z0-9._/-]+$/.test(relative), 'Unsafe output path');
  assert(relative.split('/').every(part=>part && part!=='.' && part!=='..'), 'Output path traversal');
  const root = resolve(base), path = resolve(root,relative);
  assert(path.startsWith(root+sep), 'Output escapes directory');
  return path;
}
