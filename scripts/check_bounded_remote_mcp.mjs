#!/usr/bin/env node
/** Offline integrity and direct-engine replay of explicitly bounded HTTPS captures. */
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const flags = {};
for (let i = 2; i < process.argv.length; i++) {
  assert(['--explorer-root', '--directory'].includes(process.argv[i]), 'Unknown replay option');
  assert(process.argv[i + 1] && !process.argv[i + 1].startsWith('--'), 'Missing replay option value');
  flags[process.argv[i].slice(2)] = process.argv[++i];
}
const explorer = path.resolve(flags['explorer-root'] || path.join(ROOT, '../okf-explorer'));
const directory = path.resolve(flags.directory || path.join(ROOT, 'validation/remote-mcp/bounded'));
const corePath = path.join(explorer, 'apps/okf-explorer/src/lib/context/index.ts');
const { assembleContext, canonicalJson } = await import(pathToFileURL(corePath));
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const receipt = JSON.parse(await readFile(path.join(directory, 'receipt.json')));
assert.equal(receipt.schema, 'okf-bounded-remote-mcp-verification.v1');
assert.equal(receipt.passed, true);
assert.equal(receipt.default_service_budget_unchanged, true);
assert.equal(receipt.adapter_summary, false);
const VERSION = 'efb05c66616a9cd4328a86cf412780fe7bc7cf0b';
const INDEX_SHA = '38159445a60d4bcabc23cb2cf728e14cbd0a4b55013276c291356e7a1452ff54';
const INDEX_URL = 'https://raw.githubusercontent.com/chris-page-gov/okf-dwp/' + VERSION + '/full-dmg/context/assembly-index.json';
assert.equal(receipt.bundle_version, VERSION, 'Receipt changed the approved immutable bundle version');
assert.deepEqual(receipt.binding, { index_url: INDEX_URL, index_sha256: INDEX_SHA });
assert.deepEqual(receipt.other_budget_values, { max_nodes: 64, max_relationships: 128, max_depth: 6 });
assert.equal(receipt.capture.response_representation, 'fetch-decoded-http-response-text');
assert.equal(receipt.capture.reconstructed_jsonrpc_envelope, false);
const assuranceBytes = await readFile(path.resolve(directory, '../sdk-receipt.json'));
assert.equal(sha(assuranceBytes), receipt.comparison_assurance_receipt_sha256, 'SDK assurance receipt digest changed');
const assurance = JSON.parse(assuranceBytes);
assert.equal(assurance.schema, 'okf-remote-mcp-sdk-verification.v1');
assert.equal(assurance.passed, true);
assert.equal(assurance.endpoint, receipt.endpoint);
assert.equal(assurance.bundle_version, VERSION);
assert.deepEqual(assurance.binding, receipt.binding);
assert.equal(assurance.comparison_source_commit, receipt.comparison_source_commit);
assert.equal(assurance.comparison_source_assurance.classification, 'exact-runtime-inputs-match-commit');
assert.equal(assurance.comparison_source_assurance.local_build_reproduced, true);
assert.equal(assurance.comparison_source_assurance.inputs_sha256['apps/okf-explorer/src/lib/context/index.ts'], receipt.inputs.core_sha256);
const indexBytes = await readFile(path.join(ROOT, 'full-dmg/context/assembly-index.json'));
assert.equal(sha(indexBytes), receipt.binding.index_sha256);
assert.equal(sha(await readFile(corePath)), receipt.inputs.core_sha256);
assert.equal(sha(await readFile(fileURLToPath(import.meta.url))), receipt.inputs.offline_checker_sha256);
const cases = new Map(await Promise.all([
  ['imprisonment', 'evaluation/context-assembly/imprisonment-case.json'],
  ['hospital', 'evaluation/remote-mcp/hospital-case.json']
].map(async ([id, source]) => {
  const bytes = await readFile(path.join(ROOT, source));
  assert.equal(sha(bytes), receipt.inputs.cases[id].sha256);
  return [id, JSON.parse(bytes)];
})));
assert.equal(receipt.results.length, 6);
assert.deepEqual(new Set(receipt.results.map(row => `${row.id}:${row.budget.max_bytes}`)),
  new Set([...cases.keys()].flatMap(id => [32768, 85000, 98304].map(size => `${id}:${size}`))));
for (const row of receipt.results) {
  assert.deepEqual(Object.keys(row.budget), ['max_bytes'], 'Bounded request must change only max_bytes');
  assert.equal(row.full_package_matches_direct_engine, true);
  assert.equal(row.text_matches_structured_content, true);
  const data = {};
  for (const role of ['input', 'package', 'response']) {
    const reference = row.files[role];
    assert.equal(typeof reference.path, 'string');
    const file = path.resolve(directory, reference.path);
    assert(file.startsWith(directory + path.sep), 'Receipt file escapes its capture directory');
    const bytes = await readFile(file);
    assert.equal(sha(bytes), reference.sha256, `${row.id}: ${role} hash mismatch`);
    assert.equal(bytes.byteLength, reference.bytes);
    data[role] = JSON.parse(bytes);
  }
  assert.deepEqual(data.input, { bundle: 'okf-dwp', version: receipt.bundle_version,
    question: cases.get(row.id).question, budget: row.budget });
  assert.equal(data.response.jsonrpc, '2.0');
  assert(['number', 'string'].includes(typeof data.response.id), 'Expected an actual JSON-RPC response identifier');
  assert.equal(row.mcp_response_bytes, row.files.response.bytes);
  assert(!data.response.error && !data.response.result.isError);
  const packet = data.response.result;
  assert.equal(canonicalJson(packet.structuredContent), canonicalJson(data.package));
  assert.equal(packet.content.length, 1);
  assert.equal(packet.content[0].type, 'text');
  assert.equal(canonicalJson(JSON.parse(packet.content[0].text)), canonicalJson(data.package));
  const direct = await assembleContext(JSON.parse(indexBytes), data.input.question, row.budget, receipt.binding);
  assert.equal(canonicalJson(data.package), canonicalJson(direct));
  assert.equal(sha(canonicalJson(direct)), row.package_canonical_sha256);
  assert.equal(direct.context_id, row.context_id);
  assert.equal(direct.evidence_status, row.evidence_status);
  assert.equal(direct.budget.truncated, true);
  assert.equal(row.truncated, direct.budget.truncated);
  assert.equal(direct.ai_answer, null);
  assert.equal(direct.selected.length, row.records);
  assert.equal(direct.relationships.length, row.relationships);
  assert.equal(Buffer.byteLength(JSON.stringify(direct)), row.package_bytes);
  assert.deepEqual(direct.selected.filter(item => item.record.kind === 'evidence').map(item => ({ id: item.record.id, label: item.record.label })), row.evidence_records);
  assert.deepEqual([...new Set(direct.missing_evidence.map(item => item.code))].sort(), row.missing_evidence_codes);
  assert.deepEqual(direct.unresolved_terms, row.unresolved_terms);
}
console.log(JSON.stringify({ passed: true, network_used: false, cases: receipt.results.length,
  directory, outcomes: receipt.results.map(row => ({ id: row.id, budget: row.budget,
    context_id: row.context_id, evidence_status: row.evidence_status, records: row.records,
    relationships: row.relationships, truncated: row.truncated })) }));
