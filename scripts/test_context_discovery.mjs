#!/usr/bin/env node
/** Execute broader producer output against the same reusable Explorer engine. */
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { createHash } from 'node:crypto';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const args = process.argv.slice(2);
assert.ok(args.length === 0 || (args.length === 2 && args[0] === '--explorer-root'),
  'Usage: node --experimental-strip-types scripts/test_context_discovery.mjs [--explorer-root PATH]');
const explorer = path.resolve(args[1] || path.join(root, '..', 'okf-explorer'));
const { validateContextIndex, assembleContext, canonicalJson } = await import(pathToFileURL(
  path.join(explorer, 'apps/okf-explorer/src/lib/context/index.ts')));
const raw = await readFile(path.join(root, 'context/discovery/assembly-index.json'));
const index = validateContextIndex(JSON.parse(raw));
const binding = { index_url: 'https://example.test/frozen/discovery/assembly-index.json',
  index_sha256: createHash('sha256').update(raw).digest('hex') };
assert.equal(index.requirements.length, 0);

const questions = [
  ['Family membership during hospital admission', 'page/dmg-vol4-ch24/0025'],
  ['A claimant is imprisoned. Explain the effect on JSA, IS, State Pension Credit and ESA, distinguishing loss of payment from loss of entitlement, and trace each conclusion to the relevant DMG guidance.', 'page/dmg-vol3-ch12/0003'],
];
const outcomes = [];
for (const [question, expectedPage] of questions) {
  const first = await assembleContext(index, question, {}, binding);
  const second = await assembleContext(index, question, {}, binding);
  assert.equal(canonicalJson(first), canonicalJson(second));
  assert.equal(first.evidence_status, 'insufficient');
  assert.ok(first.missing_evidence.some(row => row.code === 'no_evidence_requirements'));
  assert.ok(first.selected.some(row => row.record.route === expectedPage), 'Existing source evidence is discoverable');
  assert.ok(first.budget.used_bytes <= first.budget.max_bytes);
  for (const item of first.selected.filter(row => row.record.kind === 'evidence')) {
    const original = index.records.find(row => row.id === item.record.id);
    assert.equal(item.record.text, original.text, 'Whole source text remains unchanged');
  }
  outcomes.push({ question, context_id: first.context_id, evidence_status: first.evidence_status,
    selected: first.selected.length, relationships: first.relationships.length, used_bytes: first.budget.used_bytes });
}
const unmatched = await assembleContext(index, 'zzunmatched zzunresolved', {}, binding);
assert.equal(unmatched.selected.length, 0);
assert.equal(unmatched.evidence_status, 'insufficient');
assert.ok(unmatched.unresolved_terms.includes('zzunmatched'));
console.log(JSON.stringify({ status: 'passed', index_bytes: raw.length, outcomes }, null, 2));
