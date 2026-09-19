#!/usr/bin/env node
/** Exact-package replay and independent source-candidate coverage; never a keyword answer score. */
import assert from 'node:assert/strict';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { gzipSync, gunzipSync } from 'node:zlib';
import path from 'node:path';
import { pathToFileURL, fileURLToPath } from 'node:url';
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const VERSION = 'bf50ef8d91b9f1ccc2cbdb354198eae74c9ed752';
const ENDPOINT = 'https://ask-okf.crpage.chatgpt.site/okf/mcp';
const MANIFEST = `https://raw.githubusercontent.com/chris-page-gov/okf-dwp/${VERSION}/full-dmg/context/corpus/manifest.json`;
const PROTOCOL = '2025-11-25';
const sha = value => createHash('sha256').update(value).digest('hex');
const flags = {};
for (let i = 2; i < process.argv.length; i++) {
  const name = process.argv[i];
  assert(['--check', '--remote', '--explorer-root', '--output'].includes(name), `Unknown option ${name}`);
  flags[name.slice(2)] = ['--check', '--remote'].includes(name) ? true : process.argv[++i];
}
assert(!(flags.check && flags.remote));
const explorer = path.resolve(flags['explorer-root'] || '../okf-explorer');
const out = path.resolve(flags.output || path.join(ROOT, 'validation/corpus-questions'));
const engineRoot = path.join(explorer, 'apps/okf-explorer/src/lib/context');
const { assembleCorpusContext } = await import(pathToFileURL(path.join(engineRoot, 'corpus.ts')));
const { canonicalJson } = await import(pathToFileURL(path.join(engineRoot, 'index.ts')));
const registryBytes = await readFile(path.join(ROOT, 'evaluation/staff-questions/cases.json'));
const registry = JSON.parse(registryBytes);
const manifestBytes = await readFile(path.join(ROOT, 'context/corpus/manifest.json'));
const manifest = JSON.parse(manifestBytes);
const binding = { index_url: MANIFEST, index_sha256: sha(manifestBytes) };
const inputs = { registry_sha256: sha(registryBytes), manifest_sha256: sha(manifestBytes), runner_sha256: sha(await readFile(fileURLToPath(import.meta.url))), engine: {} };
for (const name of ['index.ts', 'corpus.ts', 'types.ts']) inputs.engine[name] = sha(await readFile(path.join(engineRoot, name)));
const cached = new Map();
const localFetch = async (url) => {
  assert(String(url).startsWith(new URL('.', MANIFEST).href));
  const relative = String(url).slice(new URL('.', MANIFEST).href.length); assert(!relative.includes('..'));
  if (!cached.has(relative)) cached.set(relative, await readFile(path.join(ROOT, 'context/corpus', relative)));
  return new Response(cached.get(relative));
};
const extras = [
  { id: 'control-hospital', section: 'Scope control', question: 'What happens to Pension Credit when a claimant is in hospital?', candidate_ids: [], ambiguities: ['Duration, benefit components and applicable date remain unspecified.'] },
  { id: 'control-adm', section: 'ADM discovery control', question: 'Universal Credit minimum income floor gainful self employment', candidate_ids: [], ambiguities: ['Discovery query only; no individual award or current applicability established.'] },
  { id: 'control-unknown', section: 'No-result control', question: 'xylophonicquasarteleportation', candidate_ids: [], ambiguities: [] }
];
const cases = [...registry.cases, ...extras];
let previous;
if (flags.check) { previous = JSON.parse(await readFile(path.join(out, 'receipt.json'))); assert.equal(previous.schema, 'okf-dwp-corpus-question-run.v1'); assert(Number.isFinite(Date.parse(previous.observed_at)), 'Invalid observation time'); assert.deepEqual(previous.inputs, inputs); assert.deepEqual(previous.binding, binding); assert.equal(previous.version, VERSION); assert.equal(previous.protocol, PROTOCOL); assert(['local-shared-engine', 'remote-mcp-exact-core-parity'].includes(previous.mode)); assert.equal(previous.endpoint, previous.mode.startsWith('remote') ? ENDPOINT : null); }
await mkdir(out, { recursive: true });
let requestId = 0; let session; const calls = [];
function decode(raw, id) {
  const text = raw.toString('utf8');
  const items = text.trim().startsWith('{') ? [JSON.parse(text)] : text.split(/\r?\n\r?\n/).filter(x => x.includes('data:')).map(block => JSON.parse(block.split(/\r?\n/).filter(x => x.startsWith('data:')).map(x => x.slice(5).trimStart()).join('\n')));
  const value = items.find(x => x.id === id); assert(value && !value.error, 'MCP response error or absent ID'); return value.result;
}
async function rpc(method, params, notification = false) {
  const id = notification ? undefined : ++requestId; const headers = { 'content-type': 'application/json', accept: 'application/json, text/event-stream', 'MCP-Protocol-Version': PROTOCOL };
  if (session) headers['Mcp-Session-Id'] = session;
  const response = await fetch(ENDPOINT, { method: 'POST', headers, body: JSON.stringify({ jsonrpc: '2.0', id, method, params }), signal: AbortSignal.timeout(120000) });
  if (response.headers.has('Mcp-Session-Id')) session = response.headers.get('Mcp-Session-Id');
  const chunks = []; let bytes = 0;
  for await (const chunk of response.body) { bytes += chunk.length; assert(bytes <= 2 * 1024 * 1024); chunks.push(Buffer.from(chunk)); }
  const raw = Buffer.concat(chunks); const observation = { method, id: id ?? null, status: response.status, content_type: response.headers.get('content-type'), bytes, sha256: sha(raw) }; calls.push(observation);
  assert(response.ok); return { raw, observation, result: notification && !bytes ? null : decode(raw, id) };
}
if (flags.remote) {
  const init = await rpc('initialize', { protocolVersion: PROTOCOL, capabilities: {}, clientInfo: { name: 'okf-full-corpus-evaluation', version: '1.0' } }); assert.equal(init.result.protocolVersion, PROTOCOL);
  await rpc('notifications/initialized', undefined, true);
  const tools = await rpc('tools/list', {}); const tool = tools.result.tools.find(t => t.name === 'ask_okf'); assert(tool?.annotations?.readOnlyHint); assert.equal(tool.annotations.destructiveHint, false);
}
const results = [];
for (const test of cases) {
  const direct = await assembleCorpusContext(manifest, binding, test.question, {}, localFetch);
  const old = previous?.cases.find(row => row.id === test.id);
  let pack = direct; let transport = null; let archived;
  if (flags.remote) {
    const response = await rpc('tools/call', { name: 'ask_okf', arguments: { bundle: 'okf-dwp', version: VERSION, question: test.question } });
    assert(!response.result.isError); pack = response.result.structuredContent; assert.deepEqual(JSON.parse(response.result.content[0].text), pack);
    transport = response.observation; archived = gzipSync(response.raw, { level: 9 });
  } else if (flags.check) {
    assert(old); assert.equal(old.archive, `${test.id}.response.json.gz`); archived = await readFile(path.join(out, old.archive)); assert.equal(sha(archived), old.archive_sha256);
    const raw = gunzipSync(archived, { maxOutputLength: 2 * 1024 * 1024 }); transport = old.transport;
    if (transport) { assert.equal(sha(raw), transport.sha256); assert.equal(raw.length, transport.bytes); assert.equal(transport.status, 200); assert.equal(transport.method, 'tools/call'); const packet = decode(raw, transport.id); assert(!packet.isError); pack = packet.structuredContent; assert.deepEqual(JSON.parse(packet.content[0].text), pack); }
    else pack = JSON.parse(raw);
  } else archived = gzipSync(Buffer.from(JSON.stringify(pack)), { level: 9 });
  assert.equal(canonicalJson(pack), canonicalJson(direct), `${test.id}: complete package differs from shared engine`);
  assert.equal(pack.evidence_status, 'insufficient'); assert.equal(pack.ai_answer, null); assert.equal(pack.requirements.length, 0);
  assert(pack.budget.used_bytes <= pack.budget.max_bytes); assert.equal(pack.retrieval.corpus_records, manifest.records.count);
  assert(pack.missing_evidence.some(x => x.code === 'no_evidence_requirements' || x.code === 'metadata_budget'));
  const evidence = pack.selected.filter(x => x.record.kind === 'evidence');
  for (const item of evidence) { assert(item.record.provenance.length); for (const p of item.record.provenance) { assert(/^https:\/\//.test(p.url)); assert(/^[a-f0-9]{64}$/.test(p.source_sha256)); if (p.literal_sha256) assert.equal(sha(item.record.text), p.literal_sha256); } }
  const independentlyLocated = test.candidate_ids.map(id => registry.source_candidates.find(c => c.id === id));
  const retainedCandidates = independentlyLocated.filter(c => evidence.some(x => x.record.id === c.record_id)).map(c => c.id);
  const candidateDocuments = independentlyLocated.filter(c => evidence.some(x => x.record.provenance.some(p => p.source_sha256 === c.source_sha256))).map(c => c.document_id);
  const row = { id: test.id, section: test.section, question: test.question, context_id: pack.context_id,
    archive: `${test.id}.response.json.gz`, archive_sha256: sha(archived), transport,
    package_sha256: sha(canonicalJson(pack)), package_bytes: pack.budget.used_bytes,
    evidence_status: pack.evidence_status, resolved_concepts: pack.resolved_concepts.length, selected_records: pack.selected.length,
    evidence_records: evidence.length, adm_evidence_records: evidence.filter(x => x.record.id.includes('/page/adm/')).length,
    relationships: pack.relationships.length, lexical_candidates: pack.retrieval.candidates.map(x => x.id),
    independently_located_candidates_retained: retainedCandidates, independently_located_candidates_total: independentlyLocated.length,
    candidate_documents_retained: [...new Set(candidateDocuments)],
    retrieval_truncated: pack.retrieval.truncated, package_truncated: pack.budget.truncated,
    missing_evidence: pack.missing_evidence, unresolved_terms: pack.unresolved_terms,
    assessor_ambiguities: test.ambiguities, parity: true,
    assessment: { A_source: 'frozen-page-corpus-hash-verified-not-current-law', B_semantics: 'existing-graph-preserved-no-complete-task-profile',
      C_retrieval: 'exact-page-and-document-candidate-overlap-reported-not-keyword-answer-grade', D_traversal: 'returned-existing-directed-assertions-no-inferred-legal-path',
      E_context: 'insufficient', F_provenance: 'hash-bound-corpus-and-literal-verified-original-PDF-verification-is-producer-gate', G_boundaries: 'passed-fail-closed-no-ai-answer', H_answerability: 'not-established-no-specialist-answer-acceptance' } };
  if (flags.check) assert.deepEqual(row, old); else await writeFile(path.join(out, row.archive), archived);
  if (test.duplicate_of) assert.equal(row.context_id, results.find(x => x.id === test.duplicate_of).context_id);
  if (test.id === 'control-adm') assert(row.adm_evidence_records > 0, 'ADM must be demonstrably retrievable');
  if (test.id === 'control-unknown') { assert.equal(row.evidence_records, 0); assert.equal(pack.retrieval.candidate_count, 0); }
  results.push(row);
}
const staff = results.filter(x => x.id.startsWith('staff-'));
const summary = { staff_questions: staff.length, unique_staff_questions: new Set(staff.map(x => x.question)).size,
  scope_controls: extras.length, exact_package_parity: results.length, fail_closed: results.length,
  staff_questions_with_evidence: staff.filter(x => x.evidence_records).length,
  staff_questions_with_ADM_evidence: staff.filter(x => x.adm_evidence_records).length,
  staff_questions_with_independently_located_page: staff.filter(x => x.independently_located_candidates_retained.length).length,
  staff_questions_with_independently_located_document: staff.filter(x => x.candidate_documents_retained.length).length,
  sufficient_contexts: 0, substantive_answers_generated: 0, specialist_accepted: 0,
  minimum_package_bytes: Math.min(...results.map(x => x.package_bytes)), maximum_package_bytes: Math.max(...results.map(x => x.package_bytes)) };
if (flags.check) { assert.deepEqual(previous.summary, summary); assert.equal(previous.cases.length, results.length); if (previous.mode.startsWith('remote')) { assert.equal(previous.calls.length, results.length + 3); assert.deepEqual(previous.calls.slice(0, 3).map(x => x.method), ['initialize', 'notifications/initialized', 'tools/list']); assert(previous.calls.every(x => x.status >= 200 && x.status < 300 && Number.isSafeInteger(x.bytes) && x.bytes >= 0 && x.bytes <= 2 * 1024 * 1024 && /^[a-f0-9]{64}$/.test(x.sha256))); assert(previous.calls.filter(x => x.bytes).every(x => /application\/json|text\/event-stream/.test(x.content_type)));  assert.deepEqual(previous.calls.slice(3), results.map(x => x.transport)); assert.deepEqual(previous.calls.map(x => x.id), [1, null, 2, ...results.map((_, i) => i + 3)]); } }
else await writeFile(path.join(out, 'receipt.json'), JSON.stringify({ schema: 'okf-dwp-corpus-question-run.v1', mode: flags.remote ? 'remote-mcp-exact-core-parity' : 'local-shared-engine', observed_at: new Date().toISOString(), endpoint: flags.remote ? ENDPOINT : null, protocol: PROTOCOL, version: VERSION, binding, inputs, summary, cases: results, calls,
  limitations: ['Retrieval is not an answer-quality grade; exact candidate overlap is deliberately a narrow diagnostic.', 'No question has an independently complete reviewed profile in the discovery corpus. No substantive or individual benefit answer was generated.', 'All matching text is not returned: query, candidate, file, working-index and response limits are explicit.', 'No cost, token savings, specialist acceptance or voice-client capability is established.'] }, null, 2) + '\n');
console.log(JSON.stringify({ replay: !!flags.check, output: out, ...summary }));
