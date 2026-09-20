// Read-only bounded verification of the published documentation, not its corpus.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFile, open } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
const commit = '3f72ebc30128c2a3171951050a566d3ed8db7c16';
const base = 'https://chris-page-gov.github.io/okf-dwp/';
const expectedUrl = new URL('./expected-site-manifest.json', import.meta.url);
const output = process.argv[2];
assert.ok(output, 'Supply a new output JSON path; existing observations are refused');
const handle = await open(output, 'wx');
const hash = raw => createHash('sha256').update(raw).digest('hex');
const started = new Date().toISOString();
const observations = [];
let transferred = 0;
let failure = null;
let expected;
let manifestHash;
const safePath = value => typeof value === 'string' && value.length < 512 && !value.startsWith('/') &&
  !value.includes('\\') && !value.split('/').some(part => !part || part === '..' || part === '.') && !/[?#\x00-\x1f]/.test(value);
async function fetchChecked(relative, expectedBytes, expectedHash) {
  assert.ok(safePath(relative));
  assert.ok(Number.isInteger(expectedBytes) && expectedBytes >= 0 && expectedBytes <= 1024 * 1024);
  const requested = new URL(relative, base).href;
  const began = performance.now();
  const row = { path: relative, url: requested, observed_at: new Date().toISOString() };
  observations.push(row);
  try {
    const response = await fetch(requested, { redirect: 'manual', signal: AbortSignal.timeout(20000), headers: { Accept: '*/*' } });
    row.http_status = response.status; row.response_url = response.url;
    row.content_type = response.headers.get('content-type');
    row.etag = response.headers.get('etag'); row.last_modified = response.headers.get('last-modified');
    assert.equal(response.status, 200, relative + ' HTTP status');
    assert.equal(response.url, requested, 'Canonical URL');
    const reader = response.body.getReader(), parts = [];
    let size = 0;
    while (true) {
      const { done, value } = await reader.read(); if (done) break;
      size += value.byteLength; transferred += value.byteLength;
      if (size > 1024 * 1024 || transferred > 16 * 1024 * 1024) {
        await reader.cancel(); throw new Error('Observed response byte bound exceeded');
      }
      parts.push(Buffer.from(value));
    }
    const raw = Buffer.concat(parts);
    row.bytes = raw.length; row.sha256 = hash(raw);
    assert.equal(raw.length, expectedBytes, relative + ' byte length');
    assert.equal(hash(raw), expectedHash, relative + ' SHA-256');
    row.status = 'matched';
    return raw;
  } catch (error) {
    row.status = 'failed'; row.error = String(error.message || error);
    throw error;
  } finally { row.elapsed_ms = Math.round(performance.now() - began); }
}
try {
  const expectedRaw = await readFile(expectedUrl);
  assert.ok(expectedRaw.length <= 256 * 1024);
  expected = JSON.parse(expectedRaw); manifestHash = hash(expectedRaw);
  assert.equal(expected.schema, 'okf-dwp-learning-site.v1');
  assert.equal(expected.source_commit, commit);
  assert.equal(expected.page_count, 105); assert.equal(expected.source_pages.length, 105);
  assert.equal(expected.files.length, 108);
  assert.equal(new Set(expected.files.map(row => row.path)).size, expected.files.length);
  assert.ok(expected.source_pages.every(row => safePath(row.path) && row.path.endsWith('.md') && !row.path.includes('.email.md')));
  assert.ok(expected.files.every(row => safePath(row.path) && /^[a-f0-9]{64}$/.test(row.sha256) &&
    (row.path.endsWith('.html') || ['assets/learning.css', '.nojekyll'].includes(row.path))));
  assert.ok(expected.files.reduce((sum, row) => sum + row.bytes, 0) <= 16 * 1024 * 1024);
  await fetchChecked('site-manifest.json', expectedRaw.length, manifestHash);
  // Four files at a time. A failed batch fully settles; no later batch starts.
  for (let offset = 0; offset < expected.files.length; offset += 4) {
    const rows = expected.files.slice(offset, offset + 4);
    const batch = await Promise.allSettled(rows.map(row => fetchChecked(row.path, row.bytes, row.sha256)));
    const failed = batch.find(row => row.status === 'rejected');
    if (failed) throw failed.reason;
  }
} catch (error) { failure = String(error.message || error); }
const receipt = { schema: 'okf-dwp-learning-site-public-verification.v1', status: failure ? 'failed' : 'passed',
  started_at: started, observed_at: new Date().toISOString(), source_commit: commit, base_url: base,
  method: 'Actual read-only HTTPS; exact manifest and every listed output compared by byte length and SHA-256; no browser interception or corpus downloads.',
  expected_manifest_sha256: manifestHash, source_pages: expected?.page_count,
  listed_outputs: expected?.files.length, matched_requests: observations.filter(row => row.status === 'matched').length,
  transferred_bytes: transferred, limits: { concurrent_requests: 4, timeout_ms_per_request: 20000,
    max_bytes_per_response: 1048576, max_total_bytes: 16777216, retries: 0 },
  verifier_sha256: hash(await readFile(fileURLToPath(import.meta.url))),
  requests: observations.sort((a,b) => a.path.localeCompare(b.path)), error: failure,
  limitations: ['Point-in-time publication identity check; no availability or performance guarantee.',
    'The 105 source pages produce 106 HTML outputs including the home-page alias, plus a stylesheet and .nojekyll.',
    'No raw correspondence, corpus bodies, external evidence links, browser layout or accessibility acceptance is tested.'] };
await handle.writeFile(JSON.stringify(receipt, null, 2) + '\n'); await handle.close();
console.log(JSON.stringify({ status: receipt.status, source_commit: commit, matched_requests: receipt.matched_requests,
  transferred_bytes: transferred, error: failure }));
if (failure) process.exitCode = 1;
