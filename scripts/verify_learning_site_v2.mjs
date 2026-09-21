#!/usr/bin/env node
/** Verify one exact v2 publication. Read-only HTTPS, confined paths, no retries. */
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { constants } from 'node:fs';
import { lstat, open, opendir, mkdir, writeFile } from 'node:fs/promises';
import { execFileSync } from 'node:child_process';
import { dirname, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

export const BASE = 'https://chris-page-gov.github.io/okf-dwp/';
export const LIMITS = Object.freeze({ concurrent_requests: 4, timeout_ms_per_request: 20000,
  timeout_ms_overall: 180000,
  max_bytes_per_response: 4194304, max_total_bytes: 33554432, max_manifest_bytes: 2097152,
  max_input_bytes: 67108864,
  max_files: 4096, max_inputs: 8192, retries: 0 });
const HERE = fileURLToPath(import.meta.url);
const digest = raw => createHash('sha256').update(raw).digest('hex');
const check = (ok, message) => { if (!ok) throw new Error(message); };
const roots = new Set(['README', 'CHANGELOG', 'NOTICE', 'AI_USAGE', 'LICENSE_DECISIONS', 'REPOSITORY_STATUS']);
export function safePath(value) {
  check(typeof value === 'string' && value.length > 0 && value.length <= 512
    && /^[A-Za-z0-9_./-]+$/.test(value) && !value.startsWith('/')
    && !value.split('/').some(x => !x || x === '.' || x === '..' || x.startsWith('.')),
  'Unsafe publication path');
  return value;
}
function outputPath(value) { if (value === '.nojekyll') return value; return safePath(value); }
export function strictJson(raw) {
  const text = new TextDecoder('utf-8', { fatal: true }).decode(raw), value = JSON.parse(text);
  const stack = [];
  for (const token of text.match(/"(?:[^"\\]|\\.)*"|[{}\[\],:]/g) || []) {
    if (token === '{') stack.push({ keys: new Set(), key: true });
    else if (token === '[') stack.push(null);
    else if (token === '}' || token === ']') stack.pop();
    else if (token === ',' && stack.at(-1)) stack.at(-1).key = true;
    else if (token[0] === '"' && stack.at(-1)?.key) {
      const key = JSON.parse(token); check(!stack.at(-1).keys.has(key), 'Duplicate JSON key');
      stack.at(-1).keys.add(key); stack.at(-1).key = false;
    }
  }
  function finite(x, depth = 0) {
    check(depth <= 128, 'JSON nesting exceeds bound');
    if (typeof x === 'number') check(Number.isFinite(x), 'Non-finite JSON number');
    if (x && typeof x === 'object') for (const y of Object.values(x)) finite(y, depth + 1);
  }
  finite(value); return value;
}
async function directory(path) {
  const absolute = resolve(path), parents = [];
  for (let current = absolute; ; current = dirname(current)) {
    parents.push(current); if (dirname(current) === current) break;
  }
  for (const parent of parents.reverse()) check((await lstat(parent)).isDirectory(), 'Directory or parent is a symlink or non-directory');
  return absolute;
}
export async function boundedFile(path, cap) {
  await directory(dirname(resolve(path)));
  const before = await lstat(path);
  check(before.isFile() && before.size <= cap, 'Input is not a bounded regular file');
  const handle = await open(path, constants.O_RDONLY | constants.O_NOFOLLOW | constants.O_NONBLOCK);
  try {
    const after = await handle.stat();
    check(after.isFile() && after.size === before.size && after.dev === before.dev && after.ino === before.ino, 'Input changed during admission');
    const raw = Buffer.alloc(before.size + 1); let offset = 0;
    while (offset < raw.length) { const { bytesRead } = await handle.read(raw, offset, raw.length - offset, null); if (!bytesRead) break; offset += bytesRead; }
    check(offset === before.size && offset <= cap, 'Input changed or exceeded limit');
    return raw.subarray(0, offset);
  } finally { await handle.close(); }
}
function binding(row, allowEmpty = false) {
  check(row && Object.keys(row).sort().join(',') === 'bytes,path,sha256', 'Invalid file binding fields');
  outputPath(row.path);
  check(Number.isSafeInteger(row.bytes) && row.bytes >= (allowEmpty ? 0 : 1)
    && row.bytes <= LIMITS.max_bytes_per_response && /^[a-f0-9]{64}$/.test(row.sha256), 'Invalid file byte/hash bounds');
}
function same(raw, row) { check(raw.length === row.bytes && digest(raw) === row.sha256, 'File length or SHA-256 differs: ' + row.path); }
export function validateManifest(manifest, commit) {
  check(/^[a-f0-9]{40}$/.test(commit) && manifest.schema === 'okf-dwp-learning-site.v2'
    && manifest.source_commit === commit, 'Wrong v2 source identity');
  check(Array.isArray(manifest.source_pages) && manifest.source_pages.length > 0
    && manifest.source_pages.length === manifest.page_count && manifest.page_count <= 1024, 'Invalid source page census');
  const retained = manifest.retained_evidence;
  check(retained && Array.isArray(retained.inputs) && retained.inputs.length <= LIMITS.max_inputs
    && Array.isArray(retained.releases) && retained.releases.length > 0 && retained.releases.length <= 3, 'Invalid retained evidence declaration');
  check(retained.approval?.path === 'evidence-examples/registry.json', 'Wrong approval registry');
  binding(retained.approval);
  const releases = new Set(); let cases = 0;
  for (const row of retained.releases) {
    check(/^[a-z0-9][a-z0-9-]{0,63}$/.test(row.id) && row.archive_root === `evidence-examples/${row.id}`
      && !releases.has(row.archive_root) && Number.isSafeInteger(row.cases) && row.cases > 0, 'Invalid release identity');
    releases.add(row.archive_root); cases += row.cases;
  }
  check(cases <= 3, 'Too many retained examples');
  const inputs = new Map();
  for (const row of [...manifest.source_pages, ...retained.inputs]) {
    binding(row); safePath(row.path);
    const markdown = manifest.source_pages.includes(row);
    check(markdown ? row.path.endsWith('.md') && (roots.has(row.path.slice(0, -3)) || /^(docs|evaluation)\//.test(row.path))
      : /^(evaluation|validation|evidence-examples)\//.test(row.path), 'Input lies outside the declared publication family');
    check(!inputs.has(row.path), 'Duplicate declared input'); inputs.set(row.path, row);
  }
  const approval = inputs.get(retained.approval.path);
  check(approval && approval.bytes === retained.approval.bytes && approval.sha256 === retained.approval.sha256, 'Approval input binding differs');
  check([...inputs.values()].reduce((sum, row) => sum + row.bytes, 0) <= LIMITS.max_input_bytes, 'Aggregate immutable inputs exceed bound');
  check(Array.isArray(manifest.files) && manifest.files.length > 0 && manifest.files.length <= LIMITS.max_files, 'Invalid output census');
  const outputs = new Map(); let total = 0;
  for (const row of manifest.files) {
    binding(row, row.path === '.nojekyll'); check(!outputs.has(row.path), 'Duplicate output');
    const archiveRoot = [...releases].find(prefix => row.path.startsWith(prefix + '/'));
    if (archiveRoot) {
      const member = row.path.slice(archiveRoot.length + 1);
      check(/^(?:index\.(?:html|json)|reader\.(?:mjs|css)|shared\.mjs|artifact-manifest\.json|[a-f0-9]{64}\/(?:descriptor\.json|package\.json|data\/[a-f0-9]{64}\.json))$/.test(member), 'Unexpected archive output');
      const input = inputs.get(row.path); check(input && input.bytes === row.bytes && input.sha256 === row.sha256, 'Archive output differs from committed input');
    } else check(row.path === '.nojekyll' || row.path === 'assets/learning.css' || row.path === 'index.html'
      || manifest.source_pages.some(source => source.path.replace(/\.md$/, '.html') === row.path), 'Unexpected documentation output');
    outputs.set(row.path, row); total += row.bytes;
  }
  check(total <= LIMITS.max_total_bytes, 'Total output bytes exceed bound');
  for (const required of ['index.html', 'assets/learning.css', '.nojekyll', ...manifest.source_pages.map(x => x.path.replace(/\.md$/, '.html'))])
    check(outputs.has(required), 'Missing required documentation output');
  for (const prefix of releases) for (const name of ['index.html', 'index.json', 'reader.mjs', 'shared.mjs', 'reader.css', 'artifact-manifest.json'])
    check(outputs.has(`${prefix}/${name}`), 'Missing required archive output');
  return { inputs, outputs, cases, total };
}
export async function admit(repo, site, commit) {
  await directory(repo); await directory(site);
  const raw = await boundedFile(resolve(site, 'site-manifest.json'), LIMITS.max_manifest_bytes);
  const manifest = strictJson(raw), plan = validateManifest(manifest, commit);
  check(plan.total + raw.length <= LIMITS.max_total_bytes, 'Manifest plus outputs exceed transfer bound');
  const expectedPaths = new Set(['site-manifest.json', ...plan.outputs.keys()]), actualPaths = new Set();
  const pending = ['']; let entries = 0;
  while (pending.length) {
    const prefix = pending.pop(), handle = await opendir(resolve(site, prefix));
    for await (const member of handle) {
      check(++entries <= LIMITS.max_files * 2, 'Local site tree exceeds entry bound');
      const path = prefix + member.name;
      if (member.isDirectory()) { safePath(path); pending.push(path + '/'); }
      else { check(member.isFile() && expectedPaths.has(path), 'Unlisted or non-regular local site member'); actualPaths.add(path); }
    }
  }
  check(actualPaths.size === expectedPaths.size, 'Local site file census differs');
  const tree = execFileSync('git', ['ls-tree', '-rz', commit], { cwd: repo, maxBuffer: 16 * 1024 * 1024 }).toString();
  const blobs = new Map(tree.split('\0').filter(Boolean).map(line => { const [meta, name] = line.split('\t'); return [name, meta.split(' ')]; }));
  const gitInputs = [];
  for (const row of plan.inputs.values()) {
    const entry = blobs.get(row.path); check(entry?.[0] === '100644' && entry[1] === 'blob', 'Input is not a regular immutable Git blob');
    const size = Number(execFileSync('git', ['cat-file', '-s', entry[2]], { cwd: repo, maxBuffer: 64 }).toString());
    check(size === row.bytes && size <= LIMITS.max_bytes_per_response, 'Immutable input size differs');
    const bytes = execFileSync('git', ['cat-file', 'blob', entry[2]], { cwd: repo, maxBuffer: LIMITS.max_bytes_per_response + 1024 });
    same(bytes, row); gitInputs.push({ ...row, git_blob: entry[2] });
  }
  for (const row of plan.outputs.values()) same(await boundedFile(resolve(site, row.path), LIMITS.max_bytes_per_response), row);
  return { raw, manifest, plan, gitInputs };
}
export async function observe(admission, fetcher = fetch, clock = () => performance.now()) {
  const requests = [], expected = [{ path: 'site-manifest.json', bytes: admission.raw.length, sha256: digest(admission.raw) }, ...admission.plan.outputs.values()];
  let transferred = 0, failure = null;
  const overall = AbortSignal.timeout(LIMITS.timeout_ms_overall);
  const deadline = clock() + LIMITS.timeout_ms_overall;
  const withinDeadline = () => check(!overall.aborted && clock() <= deadline, 'Overall public verification deadline exceeded');
  async function request(row) {
    const url = new URL(row.path, BASE).href;
    check(url.startsWith(BASE) && new URL(url).origin === new URL(BASE).origin, 'Request escaped fixed public site');
    const started = performance.now(), event = { path: row.path, url, observed_at: new Date().toISOString() }; requests.push(event);
    let reader;
    try {
      withinDeadline();
      const response = await fetcher(url, { redirect: 'error', credentials: 'omit', referrerPolicy: 'no-referrer',
        signal: AbortSignal.any([overall, AbortSignal.timeout(LIMITS.timeout_ms_per_request)]) });
      withinDeadline();
      event.http_status = response.status; event.response_url = response.url;
      check(response.status === 200 && response.url === url && !response.redirected && response.body, 'HTTP status, redirect or response URL differs');
      const announced = response.headers.get('content-length');
      check(announced === null || /^\d+$/.test(announced) && Number(announced) <= row.bytes, 'Excessive announced response');
      reader = response.body.getReader(); const parts = []; let bytes = 0;
      while (true) {
        const { done, value } = await reader.read(); withinDeadline(); if (done) break;
        transferred += value.byteLength; bytes += value.byteLength;
        check(bytes <= row.bytes && bytes <= LIMITS.max_bytes_per_response && transferred <= LIMITS.max_total_bytes, 'Observed byte bound exceeded');
        parts.push(Buffer.from(value));
      }
      const raw = Buffer.concat(parts); event.bytes = raw.length; event.sha256 = digest(raw); same(raw, row);
      withinDeadline(); event.status = 'matched';
    } catch (error) { event.status = 'failed'; event.error = String(error.message || error); throw error; }
    finally { if (reader) await reader.cancel().catch(() => {}); event.elapsed_ms = Math.round(performance.now() - started); }
  }
  try {
    await request(expected[0]);
    for (let i = 1; i < expected.length; i += LIMITS.concurrent_requests) {
      const batch = await Promise.allSettled(expected.slice(i, i + LIMITS.concurrent_requests).map(request));
      const failed = batch.find(x => x.status === 'rejected'); if (failed) throw failed.reason;
    }
  } catch (error) { failure = String(error.message || error); }
  requests.sort((a, b) => a.path.localeCompare(b.path));
  if (!failure) { try { withinDeadline(); } catch (error) { failure = String(error.message || error); } }
  return { requests, transferred_bytes: transferred,
    matched_requests: requests.filter(x => x.status === 'matched').length, error: failure, status: failure ? 'failed' : 'passed' };
}
export async function run({ repo, site, commit, output }, fetcher = fetch) {
  await directory(dirname(resolve(output))); await mkdir(resolve(output));
  const started = new Date().toISOString(), verifier = await boundedFile(HERE, LIMITS.max_bytes_per_response);
  let admission, result = { status: 'failed', requests: [], matched_requests: 0, transferred_bytes: 0, error: null };
  try { admission = await admit(resolve(repo), resolve(site), commit); result = await observe(admission, fetcher); }
  catch (error) { result.error = String(error.message || error); }
  const receipt = { schema: 'okf-dwp-learning-site-public-verification.v2', ...result, started_at: started,
    observed_at: new Date().toISOString(), source_commit: commit, base_url: BASE,
    expected_manifest_sha256: admission ? digest(admission.raw) : null, verifier_sha256: digest(verifier),
    source_pages: admission?.manifest.page_count ?? null, listed_outputs: admission?.plan.outputs.size ?? null,
    retained_cases: admission?.plan.cases ?? null, git_inputs: admission?.gitInputs ?? [], limits: LIMITS,
    method: 'Immutable Git input checks, exact local expected outputs, then actual read-only HTTPS against the fixed Pages host; no retries or outside requests.',
    limitations: ['Point-in-time byte identity, not browser interaction, accessibility, source correctness, legal applicability or AI answer acceptance.',
      'The expected local site is the declared build artefact; this verifier does not independently rerun its renderer or attest the remote Explorer exporter commit.'] };
  const files = new Map([['observation.json', Buffer.from(JSON.stringify(receipt, null, 2) + '\n')], ['verify-public.mjs', verifier]]);
  if (admission) files.set('expected-site-manifest.json', admission.raw);
  for (const [name, raw] of files) await writeFile(resolve(output, name), raw, { flag: 'wx' });
  const inventory = { schema: 'okf-learning-site-observation-artifacts.v2', files: [...files].map(([path, raw]) => ({ path, bytes: raw.length, sha256: digest(raw) })) };
  await writeFile(resolve(output, 'artifact-manifest.json'), JSON.stringify(inventory, null, 2) + '\n', { flag: 'wx' });
  return receipt;
}
if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  const args = process.argv.slice(2); assert.equal(args.length, 8, 'Use --repo DIR --site DIR --commit SHA --output FRESH_DIR');
  assert.deepEqual([args[0], args[2], args[4], args[6]], ['--repo', '--site', '--commit', '--output']);
  const result = await run({ repo: args[1], site: args[3], commit: args[5], output: args[7] });
  console.log(JSON.stringify({ status: result.status, source_commit: result.source_commit, matched_requests: result.matched_requests, error: result.error }));
  if (result.status !== 'passed') process.exitCode = 1;
}
