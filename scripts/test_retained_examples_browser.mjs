import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdtemp, mkdir, writeFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { resolve } from 'node:path';
import { execFileSync } from 'node:child_process';
import { loadPlan, archiveRequest, verifyResponse, relationshipText, expectedMetadata, captureRuntime } from './check_retained_examples_browser.mjs';
const sha = raw => createHash('sha256').update(raw).digest('hex');
const bytes = value => Buffer.from(JSON.stringify(value));
const ref = (path, raw) => ({ path, bytes: raw.length, sha256: sha(raw) });
async function fixture(t, mutate = () => {}) {
  const repo = await mkdtemp(resolve(tmpdir(), 'okf-archive-browser-')); t.after(() => rm(repo, { recursive: true, force: true }));
  const prefix = 'evidence-examples/test', assets = new Map(), registry = { schema: 'okf-context-archive-registry.v1', cases: [] };
  const receipt = bytes({ kind: 'synthetic public-observation fixture; no network' }), index = { schema: 'okf-context-archive-index.v1', cases: [] };
  for (const id of ['current-care-home', 'unknown-control', 'historical-care-home']) {
    const empty = id === 'unknown-control', historical = id === 'historical-care-home';
    const item = { record: { id: 'urn:synthetic:r', label: 'Synthetic £ record', text: 'Synthetic 💷 evidence', kind: 'evidence', provenance: [] }, reasons: ['fixture'], paths: [] };
    const context = { schema: 'okf-governed-context.v1', context_id: 'urn:sha256:' + sha(Buffer.from(id)), question: id,
      selected: empty ? [] : [item], relationships: empty ? [] : [{ id: 'urn:edge', source: item.record.id, target: 'urn:omitted',
        label: 'requires', predicate: 'http://purl.org/dc/terms/requires', assertion_status: 'model-derived', authority: { label: 'Synthetic' } }],
      evidence_status: 'insufficient', ai_answer: null };
    const raw = bytes(context), hash = sha(raw), entry = { id, title: id, package: { canonical_sha256: hash },
      receipt: ref('validation/synthetic/receipt.json', receipt), source_version: 'synthetic-version', engine_id: 'synthetic-engine',
      original_engine_id: historical ? null : 'synthetic-engine', observation_kind: 'public', approved_publication: true };
    const descriptor = { schema: 'okf-context-archive.v1', id, title: id, question: context.question, context_id: context.context_id,
      package_bytes: raw.length, package_sha256: hash, observation_kind: 'public', evidence_status: 'insufficient', ai_answer: null, source_version: entry.source_version,
      engine_id: entry.engine_id, original_engine_id: entry.original_engine_id, input_receipt: entry.receipt,
      counts: { records: context.selected.length, relationships: context.relationships.length } };
    const descriptorRaw = bytes(descriptor); assets.set(`${hash}/package.json`, raw); assets.set(`${hash}/descriptor.json`, descriptorRaw);
    index.cases.push({ id, title: id, path: `${hash}/descriptor.json`, package_sha256: hash, descriptor: { bytes: descriptorRaw.length, sha256: sha(descriptorRaw) } });
    registry.cases.push(entry);
  }
  const registryRaw = bytes(registry); index.registry_sha256 = sha(registryRaw);
  assets.set('index.json', bytes(index)); assets.set('index.html', Buffer.from('<h1>Synthetic only</h1>'));
  for (const name of ['reader.mjs', 'shared.mjs', 'reader.css']) assets.set(name, Buffer.from('/* Synthetic fixture */'));
  const manifestRaw = bytes({ schema: 'okf-context-archive-artifacts.v1', registry_sha256: sha(registryRaw), exporter_files: [], files: [...assets].map(([path, raw]) => ref(path, raw)) });
  const approval = { schema: 'okf-dwp-retained-evidence-publication.v1', releases: [{ id: 'test', archive_root: prefix,
    approved_publication: true, registry: ref('evaluation/synthetic/registry.json', registryRaw),
    artifact_manifest: ref(prefix + '/artifact-manifest.json', manifestRaw), exporter: { files: [] } }] };
  const files = new Map([['evidence-examples/registry.json', bytes(approval)], ['evaluation/synthetic/registry.json', registryRaw],
    ['validation/synthetic/receipt.json', receipt], [prefix + '/artifact-manifest.json', manifestRaw],
    ['scripts/check_retained_examples_browser.mjs', Buffer.from('// Synthetic harness fixture\n')],
    ['scripts/verify_learning_site_v2.mjs', Buffer.from('// Synthetic helper fixture\n')],
    ...[...assets].map(([path, raw]) => [prefix + '/' + path, raw])]);
  mutate(files);
  for (const [path, raw] of files) { await mkdir(resolve(repo, path, '..'), { recursive: true }); await writeFile(resolve(repo, path), raw); }
  execFileSync('git', ['init', '-q', repo]); execFileSync('git', ['add', '.'], { cwd: repo });
  execFileSync('git', ['-c', 'user.name=Test', '-c', 'user.email=test@example.invalid', 'commit', '-qm', 'Synthetic archive browser fixture'], { cwd: repo });
  return { repo, commit: execFileSync('git', ['rev-parse', 'HEAD'], { cwd: repo }).toString().trim(), releaseId: 'test', assets };
}
test('all three source-bound cases admit without browser or network', async t => {
  const f = await fixture(t), plan = await loadPlan(f.repo, f.commit, f.releaseId);
  assert.equal(plan.cases.length, 3); assert.equal(plan.cases[1].context.selected.length, 0);
  assert.equal(plan.cases[2].descriptor.original_engine_id, null); assert.equal(plan.assets.size, f.assets.size + 1);
  assert.ok(plan.inputs.every(x => /^[a-f0-9]{40}$/.test(x.git_blob)));
});
test('source plan refuses changed committed archive bytes even if tree is internally valid Git', async t => {
  const f = await fixture(t, files => files.set('evidence-examples/test/reader.mjs', Buffer.from('changed')));
  await assert.rejects(loadPlan(f.repo, f.commit, f.releaseId), /binding differs/);
});
test('unexpected committed archive members are refused', async t => {
  const f = await fixture(t, files => files.set('evidence-examples/test/unlisted.json', Buffer.from('{}')));
  await assert.rejects(loadPlan(f.repo, f.commit, f.releaseId), /census differs/);
});
test('explicit publication approval cannot be omitted', async t => {
  const f = await fixture(t, files => { const path = 'evidence-examples/registry.json', v = JSON.parse(files.get(path)); v.releases[0].approved_publication = false; files.set(path, bytes(v)); });
  await assert.rejects(loadPlan(f.repo, f.commit, f.releaseId), /explicitly approved/);
});
test('same host is insufficient: only exact listed GET assets are allowed', async t => {
  const f = await fixture(t), plan = await loadPlan(f.repo, f.commit, f.releaseId);
  assert.equal(archiveRequest(plan.base + 'index.html', 'GET', plan), 'index.html');
  for (const [url, method] of [[plan.base + 'index.html', 'POST'], [plan.base + 'index.html?x=1', 'GET'],
    [plan.base + '../index.html', 'GET'], ['https://example.invalid/index.html', 'GET'], [plan.base + 'unknown.json', 'GET'],
    [plan.base.replace('https://', 'https://user:pass@') + 'index.html', 'GET']]) assert.throws(() => archiveRequest(url, method, plan));
});
test('response hashes, status and redirects are independently checked', async t => {
  const f = await fixture(t), plan = await loadPlan(f.repo, f.commit, f.releaseId), raw = f.assets.get('index.html');
  assert.equal(verifyResponse(raw, { url: plan.base + 'index.html', status: 200 }, plan).status, 'matched');
  for (const r of [{ status: 302 }, { status: 429 }, { status: 200, redirected: true }]) assert.throws(() => verifyResponse(raw, { url: plan.base + 'index.html', ...r }, plan));
  assert.throws(() => verifyResponse(Buffer.from('tampered'), { url: plan.base + 'index.html', status: 200 }, plan));
});
test('directed relationships preserve omitted endpoints, direction and assertion status', async t => {
  const f = await fixture(t), plan = await loadPlan(f.repo, f.commit, f.releaseId);
  assert.deepEqual(relationshipText(plan.cases[0].context), ['Synthetic £ record → requires → urn:omitted; http://purl.org/dc/terms/requires; model-derived; Synthetic']);
  assert.deepEqual(relationshipText(plan.cases[1].context), []);
});
test('metadata reference hashes full Unicode source without promoting it', () => {
  const item = { record: { id: 'x', text: '£💷', authority: { class: 'derived' } }, reasons: ['model-derived'], paths: [] };
  const result = expectedMetadata(item);
  assert.equal(result.record.text_reference.characters, 3); assert.equal(result.record.text_reference.sha256, sha(Buffer.from('£💷')));
  assert.equal(result.record.authority.class, 'derived'); assert.deepEqual(result.reasons, item.reasons); assert.equal('text' in result.record, false);
});
test('executed harness and helper must both match supplied immutable commit before launch', async t => {
  const f = await fixture(t), local = { harness: resolve(f.repo, 'scripts/check_retained_examples_browser.mjs'), helper: resolve(f.repo, 'scripts/verify_learning_site_v2.mjs') };
  const captured = await captureRuntime(f.repo, f.commit, local);
  assert.equal(captured.harness.sha256, sha(Buffer.from('// Synthetic harness fixture\n')));
  await writeFile(local.helper, '// Changed after approval\n');
  await assert.rejects(captureRuntime(f.repo, f.commit, local), /differs from the supplied commit/);
  assert.equal(captured.helper.raw.toString(), '// Synthetic helper fixture\n');
});
