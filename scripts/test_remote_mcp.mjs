#!/usr/bin/env node
/** Independent raw HTTP MCP client; compares received evidence with the shared core. */
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { gzipSync, gunzipSync } from 'node:zlib';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const VERSION = 'efb05c66616a9cd4328a86cf412780fe7bc7cf0b';
const INDEX_SHA = '38159445a60d4bcabc23cb2cf728e14cbd0a4b55013276c291356e7a1452ff54';
const INDEX_URL = `https://raw.githubusercontent.com/chris-page-gov/okf-dwp/${VERSION}/full-dmg/context/assembly-index.json`;
const PROTOCOL = '2025-11-25';
const RESPONSE_LIMIT = 2 * 1024 * 1024;
const sha256 = bytes => createHash('sha256').update(bytes).digest('hex');
const flags = {};
for (let i = 2; i < process.argv.length; i++) {
  const arg = process.argv[i];
  if (arg === '--check') flags.check = true;
  else if (['--endpoint', '--explorer-root', '--output'].includes(arg)) {
    assert(process.argv[i + 1] && !process.argv[i + 1].startsWith('--'), `Missing ${arg} value`);
    flags[arg.slice(2)] = process.argv[++i];
  } else throw new Error(`Unknown option ${arg}`);
}
assert(flags.endpoint || flags.check,
  'Usage: node --experimental-strip-types scripts/test_remote_mcp.mjs --endpoint HTTPS_URL --explorer-root PATH [--output DIRECTORY]; --check replays retained evidence without network');
const explorerRoot = path.resolve(flags['explorer-root'] || path.join(ROOT, '../okf-explorer'));
const output = path.resolve(flags.output || path.join(ROOT, 'validation/remote-mcp'));
const corePath = path.join(explorerRoot, 'apps/okf-explorer/src/lib/context/index.ts');
const assessorPath = path.join(explorerRoot, 'scripts/evaluate_context_package.mjs');
const { assembleContext } = await import(pathToFileURL(corePath));
const { canonical, evaluateContextPackage } = await import(pathToFileURL(assessorPath));
const indexBytes = await readFile(path.join(ROOT, 'full-dmg/context/assembly-index.json'));
assert.equal(sha256(indexBytes), INDEX_SHA, 'Local context index differs from the approved immutable version');
const index = JSON.parse(indexBytes);
const binding = { index_url: INDEX_URL, index_sha256: INDEX_SHA };
const inputHashes = {
  index_sha256: INDEX_SHA,
  core_sha256: sha256(await readFile(corePath)),
  assessor_sha256: sha256(await readFile(assessorPath)),
  client_sha256: sha256(await readFile(fileURLToPath(import.meta.url)))
};
const cases = [
  ['imprisonment', 'evaluation/context-assembly/imprisonment-case.json'],
  ['hospital', 'evaluation/remote-mcp/hospital-case.json']
];
let sequence = 0;
let session;
let negotiatedProtocol = PROTOCOL;
let endpoint;
const calls = [];
async function rpc(method, params, notification = false) {
  const id = notification ? undefined : ++sequence;
  const body = JSON.stringify({ jsonrpc: '2.0', ...(id === undefined ? {} : { id }), method, ...(params === undefined ? {} : { params }) });
  const started = performance.now();
  const response = await fetch(endpoint, {
    method: 'POST', redirect: 'error', signal: AbortSignal.timeout(30000),
    headers: {
      'Content-Type': 'application/json', Accept: 'application/json, text/event-stream',
      ...(method === 'initialize' ? {} : { 'MCP-Protocol-Version': negotiatedProtocol }),
      ...(session ? { 'Mcp-Session-Id': session } : {})
    }, body
  });
  if (response.headers.has('Mcp-Session-Id')) session = response.headers.get('Mcp-Session-Id');
  const chunks = [];
  let bytes = 0;
  for await (const chunk of response.body || []) {
    bytes += chunk.byteLength;
    assert(bytes <= RESPONSE_LIMIT, 'MCP response exceeds acceptance-client limit');
    chunks.push(Buffer.from(chunk));
  }
  const raw = Buffer.concat(chunks);
  calls.push({ method, http_status: response.status, response_bytes: bytes,
    response_sha256: sha256(raw), duration_ms: Math.round(performance.now() - started) });
  assert(response.ok, `${method} returned HTTP ${response.status}`);
  if (notification && !bytes) return;
  let message;
  if ((response.headers.get('content-type') || '').includes('text/event-stream')) {
    const messages = raw.toString('utf8').split(/\r?\n\r?\n/).flatMap(block => {
      const data = block.split(/\r?\n/).filter(line => line.startsWith('data:')).map(line => line.slice(5).trimStart()).join('\n');
      return data ? [JSON.parse(data)] : [];
    });
    message = messages.find(row => row.id === id);
  } else message = JSON.parse(raw);
  assert(message && message.jsonrpc === '2.0' && message.id === id, `${method}: invalid response envelope`);
  assert(!message.error, `${method}: ${JSON.stringify(message.error)}`);
  return message.result;
}

let retained;
let server;
let advertised;
if (flags.check) {
  retained = JSON.parse(await readFile(path.join(output, 'receipt.json')));
  assert.equal(retained.schema, 'okf-dwp-remote-mcp-acceptance.v1');
  assert.equal(retained.status, 'passed');
  assert.deepEqual(retained.inputs, inputHashes, 'Retained evidence implementation or index binding changed');
} else {
  endpoint = new URL(flags.endpoint);
  assert(endpoint.protocol === 'https:' || (endpoint.protocol === 'http:' && ['127.0.0.1', 'localhost', '[::1]'].includes(endpoint.hostname)),
    'Use HTTPS, or a loopback URL for a clearly labelled local test');
  assert(!endpoint.username && !endpoint.password && !endpoint.search && !endpoint.hash, 'Endpoint must not contain credentials, query or fragment');
  const initial = await rpc('initialize', { protocolVersion: PROTOCOL, capabilities: {}, clientInfo: { name: 'okf-dwp-raw-http-acceptance', version: '1.0.0' } });
  assert.equal(initial.protocolVersion, PROTOCOL, 'Unexpected negotiated MCP version');
  negotiatedProtocol = initial.protocolVersion;
  assert(initial.capabilities?.tools, 'Server does not advertise tools');
  server = initial.serverInfo;
  await rpc('notifications/initialized', undefined, true);
  const listing = await rpc('tools/list', {});
  assert(!listing.nextCursor, 'This bounded service should not need paginated tool discovery');
  advertised = listing.tools.find(tool => tool.name === 'ask_okf');
  assert(advertised, 'ask_okf was not discovered');
  assert.equal(advertised.annotations?.readOnlyHint, true);
  assert.equal(advertised.annotations?.destructiveHint, false);
  assert.equal(advertised.inputSchema.additionalProperties, false);
  await mkdir(output, { recursive: true });
  await writeFile(path.join(output, 'tools.json'), JSON.stringify(listing, null, 2) + '\n');
}

const results = [];
for (const [name, relative] of cases) {
  const caseBytes = await readFile(path.join(ROOT, relative));
  const testCase = JSON.parse(caseBytes);
  const args = { bundle: 'okf-dwp', version: VERSION, question: testCase.question };
  // The independent rubric is never passed to the engine or the server.
  const direct = await assembleContext(index, testCase.question, {}, binding);
  let packet;
  const archiveName = `${name}-tool-result.json.gz`;
  let archive;
  let raw;
  if (flags.check) {
    archive = await readFile(path.join(output, archiveName));
    raw = gunzipSync(archive, { maxOutputLength: RESPONSE_LIMIT });
    packet = JSON.parse(raw);
  } else {
    packet = await rpc('tools/call', { name: 'ask_okf', arguments: args });
    raw = Buffer.from(JSON.stringify(packet) + '\n');
    archive = gzipSync(raw, { level: 9 });
  }
  assert(!packet.isError, `${name}: tool returned an error`);
  assert(packet.structuredContent, `${name}: missing structured evidence package`);
  const pack = packet.structuredContent;
  const texts = packet.content.filter(row => row.type === 'text');
  assert.equal(texts.length, 1, `${name}: expected one JSON evidence text block`);
  assert.equal(canonical(JSON.parse(texts[0].text)), canonical(pack), `${name}: text and structured evidence differ`);
  assert.equal(canonical(pack), canonical(direct), `${name}: remote and direct engine packages differ`);
  const evaluation = evaluateContextPackage(pack, testCase, index, binding);
  assert.equal(evaluation.status, 'passed', `${name}: evidence/path/provenance assessment failed`);
  if (name === 'hospital') {
    assert.equal(pack.requirements.length, 0, 'Hospital task unexpectedly acquired a declared evidence profile');
    assert.equal(pack.missing_evidence.length, 10, 'Pinned hospital missing-evidence diagnostics changed');
    assert.equal(pack.missing_evidence.filter(row => row.code === 'uncovered_resolved_concept').length, 8);
    assert.deepEqual(pack.unresolved_terms, testCase.expected.unresolved_terms);
    assert.equal(pack.scope, index.scope);
    assert(index.limitations.every(item => pack.limitations.includes(item)));
  }
  const result = {
    name, case_path: relative, case_sha256: sha256(caseBytes), tool: 'ask_okf', arguments: args,
    archive: archiveName, archive_sha256: sha256(archive), tool_result_sha256: sha256(raw),
    package_sha256: sha256(canonical(pack)), context_id: pack.context_id,
    evidence_status: pack.evidence_status, selected_records: pack.selected.length,
    relationships: pack.relationships.length, context_bytes: pack.budget.used_bytes,
    truncated: pack.budget.truncated, missing_evidence_codes: pack.missing_evidence.map(row => row.code),
    unresolved_terms: pack.unresolved_terms, applicable_requirements: pack.requirements.length,
    ai_answer: pack.ai_answer, direct_core_identical: true,
    evaluation: { status: evaluation.status, stages: evaluation.stages.map(({ id, label, status, checks }) => ({ id, label, status, checks: checks.length })) }
  };
  if (flags.check) assert.deepEqual(result, retained.cases.find(row => row.name === name), `${name}: retained acceptance observation changed`);
  else await writeFile(path.join(output, archiveName), archive);
  results.push(result);
}
if (!flags.check) {
  await writeFile(path.join(output, 'receipt.json'), JSON.stringify({
    schema: 'okf-dwp-remote-mcp-acceptance.v1', status: 'passed', observed_at: new Date().toISOString(),
    endpoint: endpoint.href, scope: endpoint.protocol === 'https:' ? 'remote-https-mcp' : 'local-loopback-mcp',
    protocol: negotiatedProtocol, client: 'independent Node.js raw HTTP MCP client', server,
    inputs: inputHashes, bundle_version: VERSION, binding, cases: results, calls,
    limitations: [
      'This receipt proves real MCP calls and exact evidence parity; it does not alone prove ChatGPT or Voice invocation.',
      'The hospital test passes by reporting insufficient evidence; custody passages must not be presented as a hospital answer.',
      'The imprisonment result is sufficient only within the package declared frozen research scope, without specialist legal acceptance.'
    ]
  }, null, 2) + '\n');
}
console.log(JSON.stringify({ status: 'passed', replay: Boolean(flags.check), output,
  cases: results.map(({ name, context_id, evidence_status, selected_records, direct_core_identical }) => ({ name, context_id, evidence_status, selected_records, direct_core_identical })) }));
