import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, mkdir, writeFile, readFile, symlink, rm } from 'node:fs/promises';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { resolve } from 'node:path';
import { tmpdir } from 'node:os';
import { BASE, LIMITS, admit, observe, run, strictJson, safePath, boundedFile, validateManifest } from './verify_learning_site_v2.mjs';
const hash = raw => createHash('sha256').update(raw).digest('hex');
const ref = (path, raw) => ({ path, bytes: raw.length, sha256: hash(raw) });
const json = value => Buffer.from(JSON.stringify(value));
async function fixture(t) {
  const root = await mkdtemp(resolve(tmpdir(), 'okf-learning-v2-')); t.after(() => rm(root, { recursive: true, force: true }));
  const repo = resolve(root, 'repo'), site = resolve(root, 'site'); await mkdir(repo); await mkdir(site);
  const sources = new Map([['NOTICE.md', Buffer.from('# Notice\n')], ['evidence-examples/registry.json', json({ approved: 'synthetic' })]]);
  const outputs = new Map([['NOTICE.html', Buffer.from('<h1>Notice</h1>')], ['index.html', Buffer.from('<h1>Start</h1>')], ['assets/learning.css', Buffer.from('body{}')], ['.nojekyll', Buffer.alloc(0)]]);
  const prefix = 'evidence-examples/synthetic';
  for (const name of ['index.html', 'index.json', 'reader.mjs', 'shared.mjs', 'reader.css', 'artifact-manifest.json']) {
    const bytes = Buffer.from(name.endsWith('.json') ? '{}' : '/* Synthetic */');
    sources.set(prefix + '/' + name, bytes); outputs.set(prefix + '/' + name, bytes);
  }
  for (const [path, raw] of sources) { await mkdir(resolve(repo, path, '..'), { recursive: true }); await writeFile(resolve(repo, path), raw); }
  execFileSync('git', ['init', '-q', repo]); execFileSync('git', ['add', '.'], { cwd: repo });
  execFileSync('git', ['-c', 'user.name=Test', '-c', 'user.email=test@example.invalid', 'commit', '-qm', 'Synthetic v2 fixture'], { cwd: repo });
  const commit = execFileSync('git', ['rev-parse', 'HEAD'], { cwd: repo }).toString().trim();
  const manifest = { schema: 'okf-dwp-learning-site.v2', source_commit: commit, page_count: 1,
    source_pages: [ref('NOTICE.md', sources.get('NOTICE.md'))],
    retained_evidence: { approval: ref('evidence-examples/registry.json', sources.get('evidence-examples/registry.json')),
      inputs: [...sources].filter(([path]) => path !== 'NOTICE.md').map(([path, raw]) => ref(path, raw)),
      releases: [{ id: 'synthetic', archive_root: prefix, cases: 1 }] },
    files: [...outputs].map(([path, raw]) => ref(path, raw)), scope: 'Synthetic verification control.' };
  outputs.set('site-manifest.json', json(manifest));
  for (const [path, raw] of outputs) { await mkdir(resolve(site, path, '..'), { recursive: true }); await writeFile(resolve(site, path), raw); }
  return { root, repo, site, commit, manifest, outputs };
}
function response(url, raw, status = 200, extras = {}) {
  const r = new Response(raw, { status }); Object.defineProperty(r, 'url', { value: url });
  for (const [key, value] of Object.entries(extras)) Object.defineProperty(r, key, { value });
  return r;
}
function fetcher(f, calls) {
  return async (url, options) => {
    calls.push({ url, options }); assert.ok(url.startsWith(BASE));
    return response(url, f.outputs.get(url.slice(BASE.length)));
  };
}
test('immutable source/local admission and all exact mocked public files succeed', async t => {
  const f = await fixture(t), admission = await admit(f.repo, f.site, f.commit), calls = [];
  const receipt = await run({ ...f, output: resolve(f.root, 'observation') }, fetcher(f, calls));
  assert.equal(receipt.status, 'passed'); assert.equal(receipt.matched_requests, f.outputs.size);
  assert.equal(receipt.git_inputs.length, admission.plan.inputs.size);
  assert.equal(calls[0].url, BASE + 'site-manifest.json');
  assert.ok(calls.every(x => x.options.redirect === 'error' && x.options.credentials === 'omit'));
  assert.equal(receipt.limits.retries, 0);
  const inventory = JSON.parse(await readFile(resolve(f.root, 'observation/artifact-manifest.json')));
  for (const row of inventory.files) { const bytes = await readFile(resolve(f.root, 'observation', row.path)); assert.equal(bytes.length, row.bytes); assert.equal(hash(bytes), row.sha256); }
});
test('no-registry v1 cannot be mistaken for a v2 publication', async t => {
  const f = await fixture(t); f.manifest.schema = 'okf-dwp-learning-site.v1';
  assert.throws(() => validateManifest(f.manifest, f.commit), /v2 source/);
});
test('source and archive Git bindings reject recomputed wrong hashes', async t => {
  const f = await fixture(t);
  f.manifest.source_pages[0] = ref('NOTICE.md', Buffer.from('invented'));
  await writeFile(resolve(f.site, 'site-manifest.json'), json(f.manifest));
  await assert.rejects(admit(f.repo, f.site, f.commit), /Immutable input size|SHA-256/);
});
test('changed local expected output fails before any public request', async t => {
  const f = await fixture(t); await writeFile(resolve(f.site, 'NOTICE.html'), 'changed'); let calls = 0;
  const receipt = await run({ ...f, output: resolve(f.root, 'failed') }, async () => { calls++; });
  assert.equal(receipt.status, 'failed'); assert.equal(calls, 0); assert.equal(receipt.matched_requests, 0);
});
test('unlisted local files cannot escape the published file census', async t => {
  const f = await fixture(t); await writeFile(resolve(f.site, 'unlisted.json'), '{}');
  await assert.rejects(admit(f.repo, f.site, f.commit), /Unlisted/);
});
test('failed first manifest is retained with no later requests or retries', async t => {
  const f = await fixture(t), admission = await admit(f.repo, f.site, f.commit); let calls = 0;
  const result = await observe(admission, async url => { calls++; return response(url, Buffer.from('wrong')); });
  assert.equal(result.status, 'failed'); assert.equal(calls, 1); assert.equal(result.requests.length, 1);
});
test('late exact response cannot pass the overall deadline even if transport ignores abort', async t => {
  const f = await fixture(t), admission = await admit(f.repo, f.site, f.commit);
  let clock = 0, calls = 0;
  const result = await observe(admission, async url => {
    calls++; clock = LIMITS.timeout_ms_overall + 1;
    return response(url, f.outputs.get('site-manifest.json'));
  }, () => clock);
  assert.equal(result.status, 'failed'); assert.match(result.error, /deadline exceeded/);
  assert.equal(calls, 1); assert.equal(result.matched_requests, 0);
});
test('redirect, changed response URL and 429 all fail closed without retry', async t => {
  const f = await fixture(t), admission = await admit(f.repo, f.site, f.commit);
  for (const variant of ['redirect', 'other-url', '429']) {
    let calls = 0;
    const result = await observe(admission, async url => { calls++; return response(variant === 'other-url' ? 'https://example.invalid/' : url,
      f.outputs.get('site-manifest.json'), variant === '429' ? 429 : 200, variant === 'redirect' ? { redirected: true } : {}); });
    assert.equal(result.status, 'failed'); assert.equal(calls, 1);
  }
});
test('all calls in failed four-file batch settle before stopping', async t => {
  const f = await fixture(t), admission = await admit(f.repo, f.site, f.commit); let calls = 0, pending = 0, peak = 0;
  const result = await observe(admission, async url => {
    const call = calls++; pending++; peak = Math.max(peak, pending); await new Promise(r => setTimeout(r, 2)); pending--;
    return response(url, call === 2 ? Buffer.from('tampered') : f.outputs.get(url.slice(BASE.length)));
  });
  assert.equal(result.status, 'failed'); assert.equal(calls, 5); assert.equal(pending, 0); assert.ok(peak <= 4);
  assert.equal(result.requests.length, 5);
});
test('unsafe paths, unknown output family, duplicate rows and excessive totals reject', async t => {
  const f = await fixture(t);
  for (const path of ['../secret', 'https://evil.invalid/x', 'x%2fy', 'x?y', 'x#y', 'docs/.email.md', '//example.invalid']) assert.throws(() => safePath(path));
  for (const change of [m => m.files.push(m.files[0]), m => m.files[0].path = 'source/private.json',
    m => m.retained_evidence.releases[0].cases = 4, m => m.files[0].bytes = LIMITS.max_bytes_per_response + 1]) {
    const m = structuredClone(f.manifest); change(m); assert.throws(() => validateManifest(m, f.commit));
  }
});
test('strict JSON rejects duplicate, overflow and invalid UTF-8 while accepting escaped Unicode', () => {
  for (const raw of [Buffer.from('{"a":1,"a":2}'), Buffer.from('{"a":1e999}'), Buffer.from([0xff])]) assert.throws(() => strictJson(raw));
  assert.deepEqual(strictJson(Buffer.from('{"a":"\\u00a3"}')), { a: '£' });
});
test('oversize, symlinked file, symlinked root and FIFO are rejected before reading', async t => {
  const f = await fixture(t);
  await assert.rejects(boundedFile(resolve(f.site, 'site-manifest.json'), 1), /bounded regular/);
  await symlink(resolve(f.site, 'site-manifest.json'), resolve(f.root, 'linked.json'));
  await assert.rejects(boundedFile(resolve(f.root, 'linked.json'), 100000), /regular/);
  await symlink(f.site, resolve(f.root, 'linked-site'));
  await assert.rejects(admit(f.repo, resolve(f.root, 'linked-site'), f.commit), /symlink/);
  execFileSync('mkfifo', [resolve(f.root, 'fifo')]); await assert.rejects(boundedFile(resolve(f.root, 'fifo'), 100), /regular/);
});
test('fresh output is mandatory and a failed admission still writes a failure receipt', async t => {
  const f = await fixture(t), out = resolve(f.root, 'observation');
  const receipt = await run({ ...f, commit: 'a'.repeat(40), output: out }, async () => { throw new Error('Network must not run'); });
  assert.equal(receipt.status, 'failed'); assert.equal(receipt.expected_manifest_sha256, null);
  await assert.rejects(run({ ...f, output: out }), /EEXIST/);
});
