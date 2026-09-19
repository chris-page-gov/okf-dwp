#!/usr/bin/env node
/** Run staff questions through remote MCP; replay complete evidence, never grade by keywords. */
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
const LIMIT = 2 * 1024 * 1024;
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const flags = {};
for (let i = 2; i < process.argv.length; i++) {
  const flag = process.argv[i];
  if (flag === '--check') flags.check = true;
  else {
    assert(['--endpoint', '--explorer-root', '--output'].includes(flag), `Unknown option ${flag}`);
    assert(process.argv[i + 1] && !process.argv[i + 1].startsWith('--'), `Missing ${flag} value`);
    flags[flag.slice(2)] = process.argv[++i];
  }
}
assert(Boolean(flags.check) !== Boolean(flags.endpoint), 'Use either --check or --endpoint HTTPS_URL');
const out = path.resolve(flags.output || path.join(ROOT, 'validation/staff-questions'));
const explorer = path.resolve(flags['explorer-root'] || path.join(ROOT, '../okf-explorer'));
const corePath = path.join(explorer, 'apps/okf-explorer/src/lib/context/index.ts');
const { assembleContext, canonicalJson } = await import(pathToFileURL(corePath));
const registryBytes = await readFile(path.join(ROOT, 'evaluation/staff-questions/cases.json'));
const registry = JSON.parse(registryBytes);
assert.equal(registry.schema, 'okf-dwp-staff-question-registry.v1');
assert.equal(registry.approved_bundle.version, VERSION);
assert.equal(registry.approved_bundle.index_url, INDEX_URL);
assert.equal(registry.approved_bundle.index_sha256, INDEX_SHA);
assert.equal(registry.cases.length, 40);
assert.equal(new Set(registry.cases.map(row => row.id)).size, 40);
assert.equal(new Set(registry.cases.map(row => row.question)).size, 39);
const indexBytes = await readFile(path.join(ROOT, 'full-dmg/context/assembly-index.json'));
assert.equal(sha(indexBytes), INDEX_SHA);
const index = JSON.parse(indexBytes);
const binding = { index_url: INDEX_URL, index_sha256: INDEX_SHA };
const inventoryBytes = await readFile(path.join(ROOT, 'source/full-dmg-2026-09-15/inventory.json'));
const inventory = JSON.parse(inventoryBytes);
const assuranceBytes = await readFile(path.join(ROOT, 'validation/remote-mcp/sdk-receipt.json'));
const assurance = JSON.parse(assuranceBytes);
const transportReceiptBytes = await readFile(path.join(ROOT, 'validation/remote-mcp/receipt.json'));
const transportReceipt = JSON.parse(transportReceiptBytes);
assert.equal(assurance.schema, 'okf-remote-mcp-sdk-verification.v1');
assert.equal(assurance.passed, true);
assert.equal(assurance.bundle_version, VERSION);
assert.deepEqual(assurance.binding, binding);
assert.equal(assurance.comparison_source_assurance.classification, 'exact-runtime-inputs-match-commit');
assert.equal(assurance.comparison_source_assurance.local_build_reproduced, true);
assert.equal(assurance.comparison_source_assurance.inputs_sha256['apps/okf-explorer/src/lib/context/index.ts'], sha(await readFile(corePath)));
assert.equal(transportReceipt.endpoint, assurance.endpoint);
assert.equal(transportReceipt.protocol, PROTOCOL);
assert.equal(transportReceipt.status, 'passed');
const documents = new Map(inventory.documents.map(doc => [doc.id, doc]));
const sourceRoutesBytes = await readFile(path.join(ROOT, 'full-dmg/data/source-documents.json'));
const sourceRoutes = new Map(JSON.parse(sourceRoutesBytes).documents.map(doc => [doc.id, doc.page_routes]));
const cached = new Map();
async function verifiedSource(id) {
  if (cached.has(id)) return cached.get(id);
  const doc = documents.get(id);
  assert(doc, `Unknown frozen source ${id}`);
  const pdf = await readFile(path.join(ROOT, doc.pdf_path));
  const pageBytes = await readFile(path.join(ROOT, doc.pages_path));
  assert.equal(sha(pdf), doc.sha256);
  assert.equal(sha(pageBytes), doc.pages_sha256);
  const pages = JSON.parse(pageBytes);
  assert.equal(pages.source_sha256, doc.sha256);
  const value = { doc, pages: pages.pages };
  cached.set(id, value);
  return value;
}
const candidateIds = new Set();
for (const candidate of registry.source_candidates) {
  assert(!candidateIds.has(candidate.id), 'Duplicate source candidate');
  candidateIds.add(candidate.id);
  const { doc, pages } = await verifiedSource(candidate.document_id);
  assert.equal(candidate.source_sha256, doc.sha256);
  assert.equal(candidate.pages_sha256, doc.pages_sha256);
  assert.equal(candidate.source_pdf, doc.pdf_path);
  assert.equal(candidate.pages_path, doc.pages_path);
  assert.equal(candidate.url, `${doc.url}#page=${candidate.page}`);
  const expectedRoute = sourceRoutes.get(doc.id)?.[candidate.page - 1];
  assert(expectedRoute, 'Candidate has no published source route');
  assert.equal(candidate.route, expectedRoute);
  assert.equal(candidate.record_id, `https://chris-page-gov.github.io/okf-dwp/id/${expectedRoute}`);
  assert.equal(candidate.captured_at, doc.observed_at);
  assert.equal(candidate.source_publication_date, doc.document_dates.published_at);
  assert.equal(candidate.source_classification, doc.discovery_classification);
  assert.equal(candidate.source_role, doc.role);
  assert.equal(candidate.legal_status, doc.legal_status);
  assert.equal(candidate.context_index_membership, index.records.some(row => row.id === candidate.record_id)
    ? 'present-as-custody-evidence' : 'absent');
  assert(Number.isSafeInteger(candidate.page) && candidate.page > 0);
  const page = pages.find(row => row.page === candidate.page);
  assert(page && candidate.anchor && page.text.includes(candidate.anchor), 'Candidate anchor absent from source');
  assert.equal(candidate.literal_sha256, sha(Buffer.from(page.text)));
  assert.equal(candidate.status, 'source-candidate-only-not-complete-answer');
}
for (const row of registry.cases) {
  assert(/^staff-\d{3}$/.test(row.id));
  assert(row.question && row.question.length <= 2000);
  assert(row.candidate_ids.every(id => candidateIds.has(id)), `${row.id}: unknown source candidate`);
  if (row.duplicate_of) assert.equal(row.question, registry.cases.find(other => other.id === row.duplicate_of)?.question);
}

// This is a measured text-payload baseline, not a model-token or answer-quality benchmark.
let sourceTextBytes = 0;
let sourceTextCharacters = 0;
for (const doc of inventory.documents) {
  const text = await readFile(path.join(ROOT, doc.text_path));
  assert.equal(sha(text), doc.text_sha256);
  sourceTextBytes += text.byteLength;
  sourceTextCharacters += [...text.toString('utf8')].length;
}
const inputs = {
  registry_sha256: sha(registryBytes), index_sha256: INDEX_SHA,
  inventory_sha256: sha(inventoryBytes), core_sha256: sha(await readFile(corePath)),
  source_routes_sha256: sha(sourceRoutesBytes),
  runner_sha256: sha(await readFile(fileURLToPath(import.meta.url))),
  sdk_assurance_sha256: sha(assuranceBytes), transport_assurance_sha256: sha(transportReceiptBytes)
};
const baseline = { kind: 'all-frozen-extracted-text-files', documents: inventory.documents.length,
  utf8_bytes: sourceTextBytes, unicode_code_points: sourceTextCharacters,
  token_count: null, monetary_cost: null,
  comparable_answer_quality_established: false,
  limitation: 'Whole-corpus text and an insufficient context package do not perform equivalent tasks. Byte reduction does not establish token, cost or quality improvement.' };

let sequence = 0;
let session;
let endpoint;
let negotiated = PROTOCOL;
const calls = [];
function decodeResponse(raw, contentType, id) {
  let messages;
  if (contentType.includes('application/json')) messages = [JSON.parse(raw)];
  else if (contentType.includes('text/event-stream')) {
    messages = raw.toString('utf8').split(/\r?\n\r?\n/).flatMap(block => {
      const data = block.split(/\r?\n/).filter(line => line.startsWith('data:'))
        .map(line => line.slice(5).trimStart()).join('\n');
      return data ? [JSON.parse(data)] : [];
    });
  } else throw new Error(`Unsupported MCP response type: ${contentType}`);
  const matches = messages.filter(message => message.id === id);
  assert.equal(matches.length, 1, 'Expected exactly one matching JSON-RPC response');
  const envelope = matches[0];
  assert.equal(envelope.jsonrpc, '2.0');
  assert(!envelope.error, JSON.stringify(envelope.error));
  return envelope;
}
async function rpc(method, params, notification = false) {
  const id = notification ? undefined : ++sequence;
  const request = { jsonrpc: '2.0', ...(id === undefined ? {} : { id }), method, ...(params === undefined ? {} : { params }) };
  const start = performance.now();
  const response = await fetch(endpoint, { method: 'POST', redirect: 'error', signal: AbortSignal.timeout(30000),
    headers: { 'Content-Type': 'application/json', Accept: 'application/json, text/event-stream',
      ...(method === 'initialize' ? {} : { 'MCP-Protocol-Version': negotiated }),
      ...(session ? { 'Mcp-Session-Id': session } : {}) }, body: JSON.stringify(request) });
  if (response.headers.has('Mcp-Session-Id')) session = response.headers.get('Mcp-Session-Id');
  const chunks = [];
  let size = 0;
  for await (const chunk of response.body || []) {
    size += chunk.byteLength;
    assert(size <= LIMIT, 'Response exceeds bounded capture limit');
    chunks.push(Buffer.from(chunk));
  }
  const raw = Buffer.concat(chunks);
  const observation = { method, request_id: id ?? null, http_status: response.status,
    content_type: response.headers.get('content-type') || '',
    response_bytes: size, response_sha256: sha(raw), duration_ms: Math.round(performance.now() - start) };
  calls.push(observation);
  assert(response.ok, `${method}: HTTP ${response.status}`);
  if (notification && !size) return { observation };
  // MCP permits JSON or SSE; preserve the complete actual body before decoding either.
  const envelope = decodeResponse(raw, observation.content_type, id);
  return { result: envelope.result, raw, observation };
}

let retained;
let toolListing;
let server;
if (flags.check) {
  retained = JSON.parse(await readFile(path.join(out, 'receipt.json')));
  assert.equal(retained.schema, 'okf-dwp-staff-question-run.v1');
  assert.equal(retained.status, 'passed-transport-integrity-and-fail-closed-controls');
  assert.deepEqual(retained.inputs, inputs, 'Evaluation inputs changed; make a new observed run');
  assert.deepEqual(retained.baseline, baseline);
  assert.equal(retained.endpoint, assurance.endpoint);
  assert.equal(retained.protocol, PROTOCOL);
  assert.equal(retained.bundle_version, VERSION);
  assert.deepEqual(retained.binding, binding);
  assert.deepEqual(retained.server, transportReceipt.server);
  assert.equal(retained.client, 'independent Node.js raw HTTP MCP client');
  assert.equal(retained.capture, 'actual-fetch-decoded-http-body; JSON-or-SSE; no reconstructed envelope');
  assert(Number.isFinite(Date.parse(retained.observed_at)), 'Missing observation date');
  toolListing = JSON.parse(await readFile(path.join(out, 'tools.json')));
  assert.equal(sha(await readFile(path.join(out, 'tools.json'))), retained.tools_sha256);
} else {
  endpoint = new URL(flags.endpoint);
  assert(endpoint.protocol === 'https:', 'This staff evaluation requires a remote HTTPS endpoint');
  assert(!endpoint.username && !endpoint.password && !endpoint.search && !endpoint.hash);
  assert.equal(endpoint.href, assurance.endpoint, 'Endpoint differs from the verified deployment');
  const initial = await rpc('initialize', { protocolVersion: PROTOCOL, capabilities: {},
    clientInfo: { name: 'okf-dwp-staff-question-evaluation', version: '1.0.0' } });
  assert.equal(initial.result.protocolVersion, PROTOCOL);
  negotiated = initial.result.protocolVersion;
  server = initial.result.serverInfo;
  assert.deepEqual(server, transportReceipt.server);
  await rpc('notifications/initialized', undefined, true);
  toolListing = (await rpc('tools/list', {})).result;
  await mkdir(out, { recursive: true });
  await writeFile(path.join(out, 'tools.json'), JSON.stringify(toolListing, null, 2) + '\n');
}
const tool = toolListing.tools.find(row => row.name === 'ask_okf');
assert(tool && !toolListing.nextCursor);
assert.equal(toolListing.tools.length, 1);
assert.equal(tool.annotations?.readOnlyHint, true);
assert.equal(tool.annotations?.destructiveHint, false);
assert.equal(tool.annotations?.openWorldHint, false);
assert.equal(tool.inputSchema.additionalProperties, false);

const results = [];
for (const testCase of registry.cases) {
  const args = { bundle: 'okf-dwp', version: VERSION, question: testCase.question };
  const direct = await assembleContext(index, testCase.question, {}, binding);
  const archiveName = `${testCase.id}.response.json.gz`;
  const previous = retained?.cases.find(row => row.id === testCase.id);
  let archive;
  let raw;
  let observation;
  if (flags.check) {
    assert(previous, 'Retained case missing');
    archive = await readFile(path.join(out, archiveName));
    assert.equal(sha(archive), previous.archive_sha256);
    raw = gunzipSync(archive, { maxOutputLength: LIMIT });
    observation = previous.transport;
  } else {
    const capture = await rpc('tools/call', { name: 'ask_okf', arguments: args });
    raw = capture.raw;
    observation = capture.observation;
    archive = gzipSync(raw, { level: 9 });
  }
  assert.equal(sha(raw), observation.response_sha256);
  assert.equal(raw.byteLength, observation.response_bytes);
  assert.equal(observation.http_status, 200);
  assert.equal(observation.method, 'tools/call');
  const envelope = decodeResponse(raw, observation.content_type, observation.request_id);
  assert(!envelope.error && !envelope.result.isError);
  const packet = envelope.result;
  assert(packet.structuredContent);
  assert.equal(packet.content.length, 1);
  assert.equal(packet.content[0].type, 'text');
  const pack = packet.structuredContent;
  assert.equal(canonicalJson(JSON.parse(packet.content[0].text)), canonicalJson(pack));
  assert.equal(canonicalJson(pack), canonicalJson(direct), `${testCase.id}: remote/core mismatch`);
  assert.equal(pack.evidence_status, testCase.expected.evidence_status);
  assert.equal(pack.evidence_status, 'insufficient', 'These tasks have no governed profile in the pinned index');
  assert.equal(testCase.expected.ai_answer, null);
  assert.equal(pack.ai_answer, testCase.expected.ai_answer);
  assert.equal(testCase.expected.applicable_requirements, 0);
  assert.equal(pack.requirements.length, testCase.expected.applicable_requirements);
  assert.equal(pack.budget.truncated, testCase.expected.budget_truncated);
  assert.equal(testCase.expected.scope_retained, true);
  assert.equal(pack.scope, index.scope);
  assert(index.limitations.every(value => pack.limitations.includes(value)));
  assert.deepEqual([...new Set(pack.missing_evidence.map(row => row.code))].sort(),
    [...testCase.expected.missing_evidence_codes].sort());
  assert(pack.missing_evidence.some(row => row.code === 'no_evidence_requirements'));
  if (testCase.duplicate_of) assert.equal(pack.context_id, results.find(row => row.id === testCase.duplicate_of)?.context_id);
  const row = { id: testCase.id, question: testCase.question, section: testCase.section,
    arguments: args, duplicate_of: testCase.duplicate_of ?? null,
    archive: archiveName, archive_sha256: sha(archive), transport: observation,
    context_id: pack.context_id, package_sha256: sha(canonicalJson(pack)),
    evidence_status: pack.evidence_status, selected_records: pack.selected.length,
    selected_evidence_records: pack.selected.filter(row => row.record.kind === 'evidence').length,
    relationships: pack.relationships.length, applicable_requirements: pack.requirements.length,
    package_bytes: Buffer.byteLength(JSON.stringify(pack)), budget: pack.budget,
    unresolved_terms: pack.unresolved_terms, reported_ambiguities: pack.ambiguities,
    missing_evidence: pack.missing_evidence, ai_answer: pack.ai_answer,
    direct_core_identical: true, answerability: 'not-established-insufficient-context',
    assessor_ambiguities: testCase.ambiguities,
    assessment: { A_source_coverage: 'candidate-locators-verified-completeness-not-established',
      B_semantic_coverage: 'task-specific-profile-absent',
      C_retrieval: 'observed-concept-resolution-not-an-answer-quality-score',
      D_traversal: 'returned-custody-paths-do-not-establish-task-specific-guidance',
      E_context_assembly: 'insufficient', F_provenance: 'exact-pinned-core-parity-and-source-candidate-integrity-passed',
      G_boundaries: 'passed-no-profile-no-ai-answer-scope-and-gaps-preserved', H_answerability: 'not-established' } };
  if (flags.check) assert.deepEqual(row, previous, `${testCase.id}: recorded result differs`);
  else await writeFile(path.join(out, archiveName), archive);
  results.push(row);
}
const summary = { questions: results.length, unique_questions: new Set(results.map(row => row.question)).size,
  remote_core_parity_passed: results.filter(row => row.direct_core_identical).length,
  fail_closed_controls_passed: results.length, sufficient_contexts: 0,
  substantive_answers_generated: 0, specialist_accepted: 0,
  source_candidates_verified: candidateIds.size,
  minimum_package_bytes: Math.min(...results.map(row => row.package_bytes)),
  maximum_package_bytes: Math.max(...results.map(row => row.package_bytes)),
  truncated_packages: results.filter(row => row.budget.truncated).length,
  token_savings_hypothesis: 'not-established-no-token-count-or-equivalent-answer-quality-comparison' };
if (flags.check) {
  assert.deepEqual(retained.summary, summary);
  assert.equal(retained.cases.length, results.length);
  assert.equal(retained.calls.length, results.length + 3);
  assert.deepEqual(retained.calls.slice(0, 3).map(row => row.method), ['initialize', 'notifications/initialized', 'tools/list']);
  assert.deepEqual(retained.calls.slice(3), results.map(row => row.transport));
  assert.deepEqual(retained.calls.map(row => row.request_id), [1, null, 2, ...results.map((_, i) => i + 3)]);
  assert(retained.calls.every(row => row.http_status >= 200 && row.http_status < 300
    && Number.isSafeInteger(row.duration_ms) && row.duration_ms >= 0
    && Number.isSafeInteger(row.response_bytes) && row.response_bytes >= 0 && row.response_bytes <= LIMIT
    && /^[a-f0-9]{64}$/.test(row.response_sha256)));
} else {
  await writeFile(path.join(out, 'receipt.json'), JSON.stringify({
    schema: 'okf-dwp-staff-question-run.v1', status: 'passed-transport-integrity-and-fail-closed-controls',
    observed_at: new Date().toISOString(), endpoint: endpoint.href, protocol: negotiated,
    client: 'independent Node.js raw HTTP MCP client', server, bundle_version: VERSION,
    capture: 'actual-fetch-decoded-http-body; JSON-or-SSE; no reconstructed envelope',
    binding, inputs, baseline, tools_sha256: sha(await readFile(path.join(out, 'tools.json'))),
    summary, cases: results, calls,
    limitations: ['No model responses or individual entitlement decisions were generated by this run.',
      'A boundary-test pass is not an answered staff question or a quality score.',
      'Source candidates locate acquired evidence; they are not complete legal answers or an expanded Ask profile.',
      'The underlying index remains the immutable custody profile. This evaluation does not change it.',
      'No private correspondence, contact details or collaborative-room links are evaluation inputs.',
      'No model-token savings, monetary savings or provider comparison is established.']
  }, null, 2) + '\n');
}
console.log(JSON.stringify({ replay: Boolean(flags.check), output: out, ...summary }));
