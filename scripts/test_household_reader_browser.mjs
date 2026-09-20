// Offline admission/package controls; no browser or network is started.
import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, mkdir, writeFile, readFile, symlink, rm } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { validateOptions, createFreshOutput, inspectPackage, sha256 } from './check_household_reader_browser.mjs';
const env = { OKF_EXPLORER_CHECKOUT: '/synthetic/checkout', OKF_HOUSEHOLD_OUTPUT: '/synthetic/fresh',
  OKF_HOUSEHOLD_APP_MANIFEST_SHA256: 'a'.repeat(64), OKF_HOUSEHOLD_SNAPSHOT: 'dwp-combined-' + 'b'.repeat(20) };
test('explicit local candidate identity is required', () => {
  assert.equal(validateOptions(env).engine, 'chrome');
  for (const key of Object.keys(env)) {
    const changed = { ...env }; delete changed[key]; assert.throws(() => validateOptions(changed));
  }
});
test('remote, credential-bearing, non-Explorer and malformed app URLs are rejected', () => {
  for (const url of ['https://127.0.0.1:8015/explore/', 'http://localhost:8015/explore/', 'http://x@127.0.0.1:8015/explore/',
    'http://127.0.0.1:8015/', 'http://127.0.0.1:8015/explore/?q=test', 'http://127.0.0.1:8015/explore/#test']) {
    assert.throws(() => validateOptions({ ...env, OKF_HOUSEHOLD_APP_URL: url }));
  }
});
test('unknown browser and unpinned expected identities are rejected', () => {
  for (const changes of [{ OKF_HOUSEHOLD_BROWSER: 'other' }, { OKF_HOUSEHOLD_APP_MANIFEST_SHA256: 'latest' },
    { OKF_HOUSEHOLD_SNAPSHOT: 'main' }]) assert.throws(() => validateOptions({ ...env, ...changes }));
});
test('existing directories, files and symlinks preserve their contents', async () => {
  const root = await mkdtemp(path.join(os.tmpdir(), 'household-admission-'));
  try {
    const directory = path.join(root, 'directory'), file = path.join(root, 'file'), link = path.join(root, 'link');
    await mkdir(directory); await writeFile(path.join(directory, 'retained'), 'evidence');
    await writeFile(file, 'file evidence'); await symlink(directory, link);
    for (const target of [directory, file, link]) await assert.rejects(createFreshOutput(target), /Fresh output/);
    assert.equal(await readFile(path.join(directory, 'retained'), 'utf8'), 'evidence');
    assert.equal(await readFile(file, 'utf8'), 'file evidence');
    const fresh = path.join(root, 'fresh'); await createFreshOutput(fresh);
    await assert.rejects(createFreshOutput(fresh), /Fresh output/);
  } finally { await rm(root, { recursive: true, force: true }); }
});
test('package identity, fail-closed status and whole JSON byte budget remain mandatory', () => {
  const manifest = Buffer.from(JSON.stringify({ semantic_source_snapshot: 'synthetic', bundle: { snapshot: 'context-synthetic' } })), descriptor = { snapshot: 'synthetic' };
  const context = { question: 'Synthetic question', ai_answer: null, evidence_status: 'insufficient',
    bundle: { snapshot: 'context-synthetic' }, binding: { index_sha256: sha256(manifest) },
    budget: { max_bytes: 10000 }, selected: [], relationships: [], ambiguities: [] };
  inspectPackage(context, context.question, descriptor, manifest);
  for (const mutate of [x => x.ai_answer = 'invented', x => x.question = 'different', x => x.evidence_status = 'sufficient',
    x => x.bundle.snapshot = 'different', x => x.binding.index_sha256 = '0'.repeat(64),
    x => x.budget.max_bytes = 524289, x => x.budget.max_bytes = 1]) {
    const changed = structuredClone(context); mutate(changed);
    assert.throws(() => inspectPackage(changed, context.question, descriptor, manifest));
  }
});
