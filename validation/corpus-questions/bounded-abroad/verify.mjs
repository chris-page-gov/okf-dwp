#!/usr/bin/env node
/** Capture or replay one public bounded MCP call; no model, answer or private input. */
import assert from 'node:assert/strict';
import { readFile, writeFile } from 'node:fs/promises';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { gzipSync, gunzipSync } from 'node:zlib';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const directory = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(directory, '../../..');
let explorer = path.resolve(root, '../okf-explorer');
let check = false;
for (let i = 2; i < process.argv.length; i++) {
  const flag = process.argv[i];
  if (flag === '--check') check = true;
  else if (flag === '--explorer-root') { assert(process.argv[i + 1]); explorer = path.resolve(process.argv[++i]); }
  else throw new Error(`Unknown option ${flag}`);
}
const sourceCommit = '31ee08ec259e165a478e9c36826fe3721643631d';
const version = 'bf50ef8d91b9f1ccc2cbdb354198eae74c9ed752';
const endpoint = 'https://ask-okf.crpage.chatgpt.site/okf/mcp';
const protocol = '2025-11-25';
const question = 'What happens to your benefits if you go abroad?';
const budget = { max_bytes: 32768 };
const request = { jsonrpc: '2.0', id: 1, method: 'tools/call', params: {
  name: 'ask_okf', arguments: { bundle: 'okf-dwp', version, question, budget }
} };
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const requestBytes = Buffer.from(JSON.stringify(request));
const inputHashes = {};
for (const file of ['index.ts', 'corpus.ts', 'types.ts']) {
  const relative = `apps/okf-explorer/src/lib/context/${file}`;
  const raw = await readFile(path.join(explorer, relative));
  assert.deepEqual(raw, execFileSync('git', ['-C', explorer, 'show', `${sourceCommit}:${relative}`]), 'Comparison engine must match the recorded commit exactly');
  inputHashes[relative] = sha(raw);
}
const { assembleCorpusContext } = await import(pathToFileURL(path.join(explorer, 'apps/okf-explorer/src/lib/context/corpus.ts')));
const { canonicalJson } = await import(pathToFileURL(path.join(explorer, 'apps/okf-explorer/src/lib/context/index.ts')));
const manifestRaw = await readFile(path.join(root, 'context/corpus/manifest.json'));
const binding = { index_url: `https://raw.githubusercontent.com/chris-page-gov/okf-dwp/${version}/full-dmg/context/corpus/manifest.json`,
  index_sha256: 'aa9726ba72b7495323b031f149fa13cffeae0aa8fc868af63b7af3cac0e6be95' };
assert.equal(sha(manifestRaw), binding.index_sha256);
const baseUrl = new URL('.', binding.index_url).href;
const fetcher = async url => {
  assert(String(url).startsWith(baseUrl));
  const relative = String(url).slice(baseUrl.length);
  assert(!relative.includes('..') && /^[a-zA-Z0-9_.\/-]+$/.test(relative));
  return new Response(await readFile(path.join(root, 'context/corpus', relative)));
};
const expected = await assembleCorpusContext(JSON.parse(manifestRaw), binding, question, budget, fetcher);
const sdkRaw = await readFile(path.join(directory, '../sdk-receipt.json'));
const sdk = JSON.parse(sdkRaw);
const deploymentRaw = await readFile(path.join(directory, '../deployment.json'));
const deployment = JSON.parse(deploymentRaw);
assert.equal(sdk.passed, true);
assert.equal(sdk.comparison_source_commit, sourceCommit);
assert.equal(sdk.comparison_source_assurance.classification, 'exact-runtime-inputs-match-commit');
for (const [file, hash] of Object.entries(inputHashes)) assert.equal(sdk.comparison_source_assurance.inputs_sha256[file], hash);
assert.deepEqual(sdk.binding, binding);
assert.equal(sdk.bundle_version, version);
assert.equal(deployment.explorer_source_commit, sourceCommit);
assert.equal(deployment.dwp_source_commit, version);
assert.equal(deployment.worker_sha256, sdk.comparison_worker_sha256);
assert.equal(deployment.endpoint, endpoint);
assert.equal(deployment.status, 'succeeded');

let raw; let transport; let receipt;
if (check) {
  receipt = JSON.parse(await readFile(path.join(directory, 'receipt.json')));
  const compressed = await readFile(path.join(directory, 'response.http-body.gz'));
  assert.equal(sha(compressed), receipt.response_archive.sha256);
  raw = gunzipSync(compressed, { maxOutputLength: 2 * 1024 * 1024 });
  transport = receipt.transport;
} else {
  const response = await fetch(endpoint, { method: 'POST', headers: {
    'Content-Type': 'application/json', Accept: 'application/json, text/event-stream', 'MCP-Protocol-Version': protocol
  }, body: requestBytes, signal: AbortSignal.timeout(120000) });
  const chunks = []; let length = 0;
  for await (const chunk of response.body) {
    length += chunk.length; assert(length <= 2 * 1024 * 1024); chunks.push(Buffer.from(chunk));
  }
  raw = Buffer.concat(chunks);
  transport = { status: response.status, content_type: response.headers.get('content-type'), bytes: raw.length, sha256: sha(raw) };
}
assert.equal(transport.status, 200);
assert.equal(transport.bytes, raw.length); assert.equal(transport.sha256, sha(raw));
const text = raw.toString('utf8');
const packets = text.trimStart().startsWith('{') ? [JSON.parse(text)] : text.split(/\r?\n\r?\n/)
  .filter(block => block.includes('data:')).map(block => JSON.parse(block.split(/\r?\n/).filter(line => line.startsWith('data:')).map(line => line.slice(5).trimStart()).join('\n')));
const packet = packets.find(packet => packet.id === request.id);
assert(packet && !packet.error && !packet.result.isError);
const result = packet.result; const pack = result.structuredContent;
assert.equal(result.content.length, 1); assert.equal(result.content[0].type, 'text');
assert.deepEqual(JSON.parse(result.content[0].text), pack);
assert.equal(canonicalJson(pack), canonicalJson(expected));
assert.deepEqual(pack.binding, binding);
assert.equal(pack.question, question); assert.equal(pack.budget.max_bytes, budget.max_bytes);
assert.equal(pack.evidence_status, 'insufficient'); assert.equal(pack.ai_answer, null);
assert.equal(pack.budget.truncated, true);
assert.deepEqual(pack.retrieval.query_tokens, ['benefits', 'abroad']);
const contextBytes = Buffer.from(JSON.stringify(pack));
assert(contextBytes.length <= budget.max_bytes);
const facts = {
  schema: 'okf-dwp-bounded-abroad-verification.v1', endpoint, protocol, request,
  request_sha256: sha(requestBytes), comparison_source_commit: sourceCommit,
  comparison_source_assurance: 'exact-engine-inputs-match-commit', engine_inputs_sha256: inputHashes,
  verifier_sha256: sha(await readFile(fileURLToPath(import.meta.url))),
  comparison_assurance_receipt: '../sdk-receipt.json', comparison_assurance_receipt_sha256: sha(sdkRaw),
  deployment_receipt: '../deployment.json', deployment_receipt_sha256: sha(deploymentRaw),
  deployment_id: deployment.deployment_id, worker_sha256: deployment.worker_sha256,
  bundle_version: version, binding, transport,
  capture_classification: 'Exact HTTP response body bytes, gzip-compressed without JSON reserialisation; no constructed protocol wrapper.',
  context: { path: 'context.json', bytes: contextBytes.length, sha256: sha(contextBytes), canonical_sha256: sha(canonicalJson(pack)),
    id: pack.context_id, records: pack.selected.length, relationships: pack.relationships.length,
    evidence_status: pack.evidence_status, truncated: pack.budget.truncated, applied_budget: pack.budget,
    query_tokens: pack.retrieval.query_tokens, model_answer_present: false },
  full_package_matches_direct_engine: true, text_matches_structured_content: true,
  limitations: ['This verifies machine delivery and provenance parity; ChatGPT model access and relevance review are separate observations.',
    'Lexical candidate evidence does not establish contemporary applicability, completeness or an individual benefits decision.']
};
if (check) {
  assert(Number.isFinite(Date.parse(receipt.observed_at)));
  const { observed_at, response_archive, ...recorded } = receipt;
  assert.deepEqual(recorded, facts);
  assert.deepEqual(response_archive.path, 'response.http-body.gz');
  assert.deepEqual(await readFile(path.join(directory, 'context.json')), contextBytes);
} else {
  const compressed = gzipSync(raw, { level: 9 });
  await writeFile(path.join(directory, 'response.http-body.gz'), compressed);
  await writeFile(path.join(directory, 'context.json'), contextBytes);
  await writeFile(path.join(directory, 'receipt.json'), JSON.stringify({ ...facts, observed_at: new Date().toISOString(),
    response_archive: { path: 'response.http-body.gz', sha256: sha(compressed) } }, null, 2)+'\n');
}
console.log(JSON.stringify({ replay: check, context_id: pack.context_id, bytes: contextBytes.length,
  records: pack.selected.length, relationships: pack.relationships.length, evidence_status: pack.evidence_status,
  full_package_matches_direct_engine: true, raw_http_bytes: raw.length }));
