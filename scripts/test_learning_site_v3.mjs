import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { mkdtemp, mkdir, readFile, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { resolve } from 'node:path';
import { BASE, LIMITS, admit, observe, run, validateManifest, validateWorkbenchManifest,
  validateWorkbenchRegistry } from './verify_learning_site_v3.mjs';

const hash = raw => createHash('sha256').update(raw).digest('hex');
const json = value => Buffer.from(JSON.stringify(value));
const ref = (path, raw) => ({ path, bytes: raw.length, sha256: hash(raw) });
const prefix = 'evaluation/evidence-workbench/';
async function fixture(t) {
  const root = await mkdtemp(resolve(tmpdir(), 'okf-learning-v3-'));
  t.after(() => rm(root, { recursive: true, force: true }));
  const repo = resolve(root, 'repo'), site = resolve(root, 'site');
  await mkdir(repo); await mkdir(site);
  const sources = new Map([['NOTICE.md', Buffer.from('# Notice\n')],
    ['evidence-examples/registry.json', json({ approved: 'synthetic' })]]);
  const outputs = new Map([['NOTICE.html', Buffer.from('<h1>Notice</h1>')],
    ['index.html', Buffer.from('<h1>Start</h1>')], ['assets/learning.css', Buffer.from('body{}')],
    ['.nojekyll', Buffer.alloc(0)]]);
  const archive = 'evidence-examples/synthetic';
  for (const name of ['index.html', 'index.json', 'reader.mjs', 'shared.mjs', 'reader.css', 'artifact-manifest.json']) {
    const raw = Buffer.from(name.endsWith('.json') ? '{}' : '/* Synthetic */');
    sources.set(`${archive}/${name}`, raw); outputs.set(`${archive}/${name}`, raw);
  }
  const cases = [], questions = [];
  for (let i = 1; i <= 40; i++) {
    const id = `staff-${String(i).padStart(3, '0')}`, question = `Synthetic question ${i}?`;
    const packageName = `packages/${id}.json`, partName = `parts/${id}-000.json`;
    const packageRaw = json({ schema: 'okf-governed-context.v1', question, id });
    const partRaw = json({ schema: 'okf-context-read.v1', id });
    sources.set(prefix + packageName, packageRaw); outputs.set(prefix + packageName, packageRaw);
    sources.set(prefix + partName, partRaw); outputs.set(prefix + partName, partRaw);
    cases.push({ id, question });
    questions.push({ id, question, package: { url: packageName, bytes: packageRaw.length,
      sha256: hash(packageRaw), parts: [{ url: partName, bytes: partRaw.length, sha256: hash(partRaw) }] } });
  }
  const registryPath = 'evaluation/staff-questions/cases.json';
  const corpusPath = 'structured-context/evidence-connect-manifest.json';
  sources.set(registryPath, json({ cases })); sources.set(corpusPath, json({ schema: 'synthetic-source' }));
  const workbench = { schema: 'okf-evidence-workbench.v1', source: {
    registry: registryPath, registry_sha256: hash(sources.get(registryPath)),
    corpus: corpusPath, corpus_sha256: hash(sources.get(corpusPath)) }, questions };
  const workbenchRaw = json(workbench);
  sources.set(prefix + 'manifest.json', workbenchRaw); outputs.set(prefix + 'manifest.json', workbenchRaw);
  for (const [path, raw] of sources) {
    await mkdir(resolve(repo, path, '..'), { recursive: true }); await writeFile(resolve(repo, path), raw);
  }
  execFileSync('git', ['init', '-q', repo]); execFileSync('git', ['add', '.'], { cwd: repo });
  execFileSync('git', ['-c', 'user.name=Test', '-c', 'user.email=test@example.invalid',
    'commit', '-qm', 'Synthetic v3 fixture'], { cwd: repo });
  const commit = execFileSync('git', ['rev-parse', 'HEAD'], { cwd: repo }).toString().trim();
  const evidence = [...outputs].filter(([path]) => path.startsWith(prefix));
  const manifest = { schema: 'okf-dwp-learning-site.v3', source_commit: commit, page_count: 1,
    source_pages: [ref('NOTICE.md', sources.get('NOTICE.md'))],
    retained_evidence: { approval: ref('evidence-examples/registry.json', sources.get('evidence-examples/registry.json')),
      inputs: [...sources].filter(([path]) => path.startsWith('evidence-examples/')).map(([path, raw]) => ref(path, raw)),
      releases: [{ id: 'synthetic', archive_root: archive, cases: 1 }] },
    evidence_workbench: { schema: 'okf-dwp-workbench-publication.v1', questions: 40,
      manifest_sha256: hash(workbenchRaw), files: evidence.length,
      bytes: evidence.reduce((sum, [, raw]) => sum + raw.length, 0) },
    files: [...outputs].map(([path, raw]) => ref(path, raw)) };
  outputs.set('site-manifest.json', json(manifest));
  for (const [path, raw] of outputs) {
    await mkdir(resolve(site, path, '..'), { recursive: true }); await writeFile(resolve(site, path), raw);
  }
  return { root, repo, site, commit, sources, outputs, manifest, workbench };
}
function response(url, raw) {
  const value = new Response(raw, { status: 200 }); Object.defineProperty(value, 'url', { value: url }); return value;
}
test('exact v3 candidate and every mocked public byte pass with four requests and no retry', async t => {
  const f = await fixture(t), admission = await admit(f.repo, f.site, f.commit);
  assert.equal(admission.plan.outputs.size, f.outputs.size - 1);
  assert.equal(admission.gitInputs.length, admission.plan.inputs.size + 2);
  const calls = []; let active = 0, peak = 0;
  const receipt = await run({ ...f, output: resolve(f.root, 'observation') }, async (url, options) => {
    calls.push({ url, options }); active++; peak = Math.max(peak, active);
    await new Promise(resolve => setTimeout(resolve, 1)); active--;
    return response(url, f.outputs.get(url.slice(BASE.length)));
  });
  assert.equal(receipt.status, 'passed'); assert.equal(receipt.matched_requests, f.outputs.size);
  assert.equal(calls[0].url, BASE + 'site-manifest.json');
  assert.ok(calls.every(call => call.options.redirect === 'error' && call.options.credentials === 'omit'));
  assert.ok(peak <= 4); assert.equal(LIMITS.retries, 0);
  assert.equal(JSON.parse(await readFile(resolve(f.root, 'observation/observation.json'))).schema,
    'okf-dwp-learning-site-public-verification.v3');
});
test('v2 identity, foreign paths and unbound package references reject', async t => {
  const f = await fixture(t);
  const old = structuredClone(f.manifest); old.schema = 'okf-dwp-learning-site.v2';
  assert.throws(() => validateManifest(old, f.commit), /v3 source/);
  for (const path of ['../secret', 'source/private.json', 'evaluation/evidence-workbench/parts/../secret.json']) {
    const changed = structuredClone(f.manifest); changed.files.push(ref(path, Buffer.from('x')));
    assert.throws(() => validateManifest(changed, f.commit));
  }
  const plan = validateManifest(f.manifest, f.commit);
  const changed = structuredClone(f.workbench);
  changed.questions[0].package.parts[0].url = 'parts/../../secret.json';
  assert.throws(() => validateWorkbenchManifest(changed, plan), /Invalid workbench file reference/);
  const registry = structuredClone(JSON.parse(f.sources.get('evaluation/staff-questions/cases.json')));
  registry.cases[39] = registry.cases[38];
  assert.throws(() => validateWorkbenchRegistry(registry, new Map(f.workbench.questions.map(row => [row.id, row.question]))),
    /committed public registry/);
});
test('changed local part and changed committed registry fail before public requests', async t => {
  const f = await fixture(t);
  await writeFile(resolve(f.site, prefix, 'parts/staff-001-000.json'), 'changed');
  let calls = 0;
  const receipt = await run({ ...f, output: resolve(f.root, 'failed') }, async () => { calls++; });
  assert.equal(receipt.status, 'failed'); assert.equal(calls, 0);
  await writeFile(resolve(f.site, prefix, 'parts/staff-001-000.json'), f.outputs.get(prefix + 'parts/staff-001-000.json'));
  f.workbench.source.registry_sha256 = '0'.repeat(64);
  const raw = json(f.workbench); await writeFile(resolve(f.site, prefix, 'manifest.json'), raw);
  f.manifest.evidence_workbench.manifest_sha256 = hash(raw);
  f.manifest.files.find(row => row.path === prefix + 'manifest.json').sha256 = hash(raw);
  f.manifest.files.find(row => row.path === prefix + 'manifest.json').bytes = raw.length;
  await writeFile(resolve(f.site, 'site-manifest.json'), json(f.manifest));
  await assert.rejects(admit(f.repo, f.site, f.commit), /Immutable input size|SHA-256|File length|source hash/);
});
test('first public mismatch ends after one request without retry', async t => {
  const f = await fixture(t), admission = await admit(f.repo, f.site, f.commit);
  let calls = 0;
  const result = await observe(admission, async url => { calls++; return response(url, Buffer.from('wrong')); });
  assert.equal(result.status, 'failed'); assert.equal(calls, 1); assert.equal(result.matched_requests, 0);
});
