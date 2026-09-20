// Offline controls for the public browser verifier. No browser or network is used.
import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import { readFile } from 'node:fs/promises';
import { checkCatalogue, checkContentSecurityPolicy, checkSlice, createCallPacer, decodeTool, MINIMUM_CALL_INTERVAL_MS, installNativeResponseObserver, sha256, validateInputs } from './check_staff_service_browser.mjs';
const base = new URL('../validation/compact-delivery/v0.3.1/', import.meta.url);
const sdk = JSON.parse(await readFile(new URL('sdk-receipt.json', base)));
const deployment = JSON.parse(await readFile(new URL('deployment.json', base)));
const origin = 'https://ask-okf.crpage.chatgpt.site';
const clone = value => structuredClone(value);

test('existing independently retained SDK/deployment identities validate without network', () => {
  const result = validateInputs(sdk, deployment, origin);
  assert.equal(result.expected.selected_records, sdk.compact_delivery.selected_records);
  assert.equal(result.recipe.question, 'What happens to your benefits if you go abroad?');
});
test('context recipe question and budget must match the SDK', () => {
  for (const mutate of [recipe => recipe.question += ' different', recipe => recipe.budget.max_bytes++]) {
    const other = clone(sdk), url = new URL(other.compact_delivery.review_url);
    const recipe = JSON.parse(Buffer.from(url.hash.slice(1), 'base64url'));
    mutate(recipe); url.hash = Buffer.from(JSON.stringify(recipe)).toString('base64url');
    other.compact_delivery.review_url = url.href;
    assert.throws(() => validateInputs(other, deployment, origin));
  }
});
test('failed SDK, unmatched runtime and unmatched deployment origin fail closed', () => {
  const failed = clone(sdk); failed.passed = false;
  assert.throws(() => validateInputs(failed, deployment, origin));
  const different = clone(deployment); different.runtime_commit = 'a'.repeat(40);
  assert.throws(() => validateInputs(sdk, different, origin));
  assert.throws(() => validateInputs(sdk, deployment, 'https://different.example'));
});
test('non-public and credential-bearing origins are rejected before network', () => {
  for (const url of ['http://localhost', 'https://user:password@example.com', origin + '/path', origin + '?token=value']) {
    assert.throws(() => validateInputs(sdk, deployment, url));
  }
});
test('receipt must include complete verified diagnostics and provenance reads', () => {
  for (const section of ['record_metadata', 'diagnostics']) {
    const other = clone(sdk); other.compact_delivery.reads = other.compact_delivery.reads.filter(row => row.section !== section);
    assert.throws(() => validateInputs(other, deployment, origin));
  }
});
test('JSON and SSE envelopes preserve text/structured parity and refuse tool failures', () => {
  const content = { context_id: 'test' };
  const response = { jsonrpc: '2.0', result: { content: [{ type: 'text', text: JSON.stringify(content) }], structuredContent: content } };
  assert.deepEqual(decodeTool(JSON.stringify(response)), content);
  assert.deepEqual(decodeTool('event: message\ndata: ' + JSON.stringify(response) + '\n\n'), content);
  const mismatch = clone(response); mismatch.result.content[0].text = '{}';
  assert.throws(() => decodeTool(JSON.stringify(mismatch)));
  response.result.isError = true; assert.throws(() => decodeTool(JSON.stringify(response)));
  assert.throws(() => decodeTool('x'.repeat(300001)));
});
function fixture() {
  const data = 'A claimant\nwith source text.';
  const expected = { section: 'record_text', record_id: 'urn:example:source', content_sha256: sha256(data), characters: data.length };
  const part = { context_id: 'urn:example:context', section: expected.section, record_id: expected.record_id,
    offset: 0, data, end_offset: data.length, next_offset: null, total_characters: data.length,
    content_sha256: expected.content_sha256, delivery: { used_bytes: 0, max_bytes: 8192 } };
  for (let i = 0; i < 5; i++) part.delivery.used_bytes = Buffer.byteLength(JSON.stringify(part));
  return { part, expected };
}
test('selected evidence slice must match exact identity, UTF-16 length and declared byte limit', () => {
  const { part, expected } = fixture();
  checkSlice(part, expected, 'urn:example:context', 0);
  for (const mutate of [p => p.context_id = 'other', p => p.record_id = 'other', p => p.content_sha256 = 'b'.repeat(64),
    p => p.end_offset++, p => p.delivery.used_bytes--, p => p.delivery.max_bytes = 1]) {
    const bad = clone(part); mutate(bad);
    assert.throws(() => checkSlice(bad, expected, 'urn:example:context', 0));
  }
});
test('pagination cannot repeat an offset, skip characters or claim false completion', () => {
  const { part, expected } = fixture();
  for (const mutate of [p => p.next_offset = 0, p => p.offset = 1, p => p.next_offset = 20, p => p.total_characters++]) {
    const bad = clone(part); mutate(bad);
    assert.throws(() => checkSlice(bad, expected, 'urn:example:context', 0));
  }
});


test('shared request pacer waits from observed starts and does not retry actions', async () => {
  let now = 1000;
  const waits = [];
  const pacer = createCallPacer({ now: () => now, sleep: async milliseconds => { waits.push(milliseconds); now += milliseconds; } });
  await pacer.wait(); assert.deepEqual(waits, [], 'First request needs no delay');
  pacer.markRequest(); now += 200;
  await pacer.wait(); assert.deepEqual(waits, [MINIMUM_CALL_INTERVAL_MS - 200]);
  pacer.markRequest();
  await pacer.wait(); assert.deepEqual(waits, [550, 750], 'Pacer carries state across callers and engines');
  pacer.markRequest(); now += 2000;
  await pacer.wait(); assert.equal(waits.length, 2, 'Slow replies already satisfy the interval');
});
test('request pacer does not admit an early timer wake-up', async () => {
  let now = 0;
  const waits = [];
  const pacer = createCallPacer({ now: () => now, sleep: async milliseconds => { waits.push(milliseconds); now += waits.length === 1 ? 500 : milliseconds; } });
  pacer.markRequest(); await pacer.wait();
  assert.deepEqual(waits, [750, 250]); assert.equal(now, 750);
});


test('credential-bearing review and deployment URLs are rejected before browser launch', () => {
  for (const credentials of ['synthetic-user@', ':synthetic-password@', 'synthetic-user:synthetic-password@']) {
    const otherSDK = clone(sdk);
    otherSDK.compact_delivery.review_url = otherSDK.compact_delivery.review_url.replace('https://', 'https://' + credentials);
    assert.throws(() => validateInputs(otherSDK, deployment, origin));
    const otherDeployment = clone(deployment);
    otherDeployment.deployment.url = otherDeployment.deployment.url.replace('https://', 'https://' + credentials);
    assert.throws(() => validateInputs(sdk, otherDeployment, origin));
  }
});
const intendedCSP = "default-src 'none'; script-src 'self'; connect-src 'self'; style-src 'unsafe-inline'; img-src data:; base-uri 'none'; form-action 'none'; frame-ancestors 'none'";
test('security policy requires exact restricted directives, allowing harmless order and whitespace', () => {
  checkContentSecurityPolicy(intendedCSP);
  checkContentSecurityPolicy(intendedCSP.split(';').reverse().join(';  ') + ';');
  for (const bad of [undefined, intendedCSP.replace("script-src 'self'", "script-src 'self' 'unsafe-inline' https:"),
    intendedCSP.replace("connect-src 'self'", 'connect-src *'), intendedCSP.replace("; frame-ancestors 'none'", ''),
    intendedCSP + "; script-src 'self'", intendedCSP + "; script-src-elem https:"]) {
    assert.throws(() => checkContentSecurityPolicy(bad));
  }
});
test('catalogue metadata is bound to independently reconstructed source records', () => {
  const selected = [{ record: { id: 'urn:example:source', label: 'Source heading', kind: 'evidence', assertion_status: 'normalised',
    text: 'Exact source text.', provenance: [{ url: 'https://example.gov.uk/source.pdf', locator: 'Page 2' }],
    authority: { class: 'official-guidance' }, review_status: 'machine-extracted' }, reasons: ['one'], paths: ['one', 'two'] }];
  const catalogue = [{ id: 'urn:example:source', label: 'Source heading', kind: 'evidence', assertion_status: 'normalised',
    text_characters: 18, text_sha256: sha256('Exact source text.'), source_url: 'https://example.gov.uk/source.pdf', source_locator: 'Page 2',
    authority_class: 'official-guidance', review_status: 'machine-extracted', reasons: 1, paths: 2 }];
  checkCatalogue(catalogue, selected);
  for (const [field, value] of Object.entries({ id: 'urn:wrong:id', label: 'Misleading heading', kind: 'concept', assertion_status: 'official',
    text_characters: 999, text_sha256: 'f'.repeat(64), source_url: 'https://wrong.example/source', source_locator: 'Page 99',
    authority_class: 'legislation', review_status: 'human-reviewed', reasons: 8, paths: 0 })) {
    const bad = clone(catalogue); bad[0][field] = value;
    assert.throws(() => checkCatalogue(bad, selected), field + ' tampering must fail');
  }
});


test('native response observer preserves Unicode and the original application fetch result', async () => {
  const value = { label: 'Child DLA — £500 and café 😀' };
  const text = JSON.stringify({ jsonrpc: '2.0', id: 7, result: { content: [{ type: 'text', text: JSON.stringify(value) }], structuredContent: value } });
  const originalResponse = new Response(text, { status: 200 });
  const originalPromise = Promise.resolve(originalResponse);
  const invocations = [];
  const window = { location: { href: origin + '/review/', origin }, fetch: (...args) => { invocations.push(args); return originalPromise; } };
  vm.runInNewContext('(' + installNativeResponseObserver.toString() + ')()', { window, URL, TextEncoder });
  const options = { method: 'POST', body: JSON.stringify({ id: 7 }), credentials: 'omit' };
  const result = window.fetch('/okf/mcp', options);
  assert.equal(result, originalPromise); assert.equal(await result, originalResponse);
  assert.deepEqual(invocations, [['/okf/mcp', options]]);
  assert.equal(await (await result).text(), text, 'Application response body remains readable and unchanged');
  while (!window.__okfEvidenceObservation.last.done) await new Promise(resolve => setImmediate(resolve));
  const observed = window.__okfEvidenceObservation.last;
  assert.equal(observed.error, null); assert.equal(observed.text, text); assert.equal(observed.rpc_id, 7);
  assert.deepEqual(decodeTool(observed.text), value);
  const syntheticDriverDecoding = Buffer.from(text, 'utf8').toString('latin1');
  assert.notEqual(Buffer.byteLength(syntheticDriverDecoding), Buffer.byteLength(observed.text));
  assert.notEqual(sha256(syntheticDriverDecoding), sha256(observed.text));
});
test('native observer ignores unrelated requests and bounds retained response text', async () => {
  const response = Promise.resolve(new Response('x'.repeat(300001)));
  const window = { location: { href: origin + '/review/', origin }, fetch: () => response };
  vm.runInNewContext('(' + installNativeResponseObserver.toString() + ')()', { window, URL, TextEncoder });
  assert.equal(window.fetch('/review.js'), response); assert.equal(window.__okfEvidenceObservation.last, null);
  window.fetch('/okf/mcp', { method: 'POST', body: JSON.stringify({ id: 8 }) });
  while (!window.__okfEvidenceObservation.last.done) await new Promise(resolve => setImmediate(resolve));
  assert.equal(window.__okfEvidenceObservation.last.text, null);
  assert.match(window.__okfEvidenceObservation.last.error, /exceeds observation limit/);
});
