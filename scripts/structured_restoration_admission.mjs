/** Independently admit only declared historical scope records for evaluation. */
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';

export function admitRestoredScopes({author, ledger, original, candidate, canonicalJson}) {
  assert.equal(author.schema, 'okf-dwp-structured-custody-restoration.v1');
  assert.equal(ledger.schema, 'okf-dwp-custody-unit-translation.v1');
  assert.equal(ledger.original_obligations_closed, 0);
  assert.deepEqual(ledger.original_requirements, original.requirements);
  const old = new Map(original.records.map(r => [r.id, r]));
  const after = new Map(candidate.records.map(r => [r.id, r]));
  assert.equal(old.size, original.records.length);
  assert.equal(after.size, candidate.records.length);
  const scopes = ledger.added_scope_records;
  assert(Array.isArray(scopes) && scopes.length > 0 && scopes.length <= 8);
  assert.equal(author.scope_records.length, scopes.length);
  const admitted = new Map(), originalIds = new Set();
  for (const declaration of author.scope_records) {
    assert(!admitted.has(declaration.id) && !originalIds.has(declaration.original_id));
    originalIds.add(declaration.original_id);
    const source = old.get(declaration.original_id);
    assert(source, 'Unbound historical scope source');
    const sourceHash = createHash('sha256').update(canonicalJson(source) + '\n').digest('hex');
    assert.equal(sourceHash, declaration.original_record_sha256);
    const record = scopes.find(r => r.id === declaration.id);
    assert(record && record.kind === 'scope', 'Restoration cannot insert PDF evidence or a new concept');
    if (declaration.mode === 'exact-historical-scope') {
      assert.equal(source.kind, 'scope');
      assert.deepEqual(record, source);
    } else {
      assert.equal(declaration.mode, 'dated-catalogue-observation');
      assert.equal(source.kind, 'evidence');
      assert.match(source.route, /^evidence\/imprisonment-/);
      assert.match(record.id, /^https:\/\/chris-page-gov\.github\.io\/okf-dwp\/id\/scope\/custody-capture\/[a-z0-9-]+$/);
      assert.equal(record.route, record.id.split('/id/')[1]);
      assert.equal(record.label, 'Frozen catalogue observation: ' + source.label);
      assert.equal(record.scope, 'Exact captured catalogue text from the original 15 September 2026 source profile. '
        + 'This is a dated navigation/scope observation, not the absent memo body, current law '
        + 'or a claim that ADM bodies are absent from the later corpus. ' + source.scope);
      // Every substantive source/governance field must remain exact. Only the
      // explicitly declared scope identity and presentation may change.
      const presentation = new Set(['id', 'route', 'kind', 'label', 'scope']);
      assert.deepEqual(Object.fromEntries(Object.entries(record).filter(([key]) => !presentation.has(key))),
                       Object.fromEntries(Object.entries(source).filter(([key]) => !presentation.has(key))));
    }
    assert.deepEqual(after.get(record.id), record, 'Generated scope differs from its declared source');
    admitted.set(record.id, record);
  }
  assert.equal(admitted.size, scopes.length);
  const requirements = new Map(candidate.requirements.map(r => [r.id, r]));
  assert.equal(requirements.size, candidate.requirements.length, 'Duplicate candidate requirement');
  for (const requirement of original.requirements)
    assert.deepEqual(requirements.get(requirement.id), requirement, 'Original custody expectation changed');
  return admitted;
}
