#!/usr/bin/env node
/** Exercise the published descriptor through Explorer's actual Reader and Ask loader. */
import assert from 'node:assert/strict';
import { existsSync, readFileSync, writeFileSync, unlinkSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const args = process.argv.slice(2);
const position = args.indexOf('--explorer-root');
assert(position >= 0 && args[position + 1], 'Usage: --explorer-root PATH');
const explorer = resolve(args[position + 1], 'apps/okf-explorer');
const vitest = resolve(explorer, 'node_modules/.bin/vitest');
assert(existsSync(vitest), 'Explorer Vitest installation is missing');
const original = JSON.parse(readFileSync(resolve(root, 'structured-context/okf-explorer.json')));
const successor = JSON.parse(readFileSync(resolve(root, 'structured-context/evidence-connect-explorer.json')));
assert.equal(successor.snapshot, original.snapshot, 'Reader snapshot changed');
assert.equal(successor.snapshot_id, original.snapshot_id, 'Reader snapshot ID changed');
for (const name of ['data_manifest', 'overview_index', 'endpoint_labels', 'search_manifest', 'relationship_adjacency']) {
  assert.deepEqual(successor.entrypoints[name], original.entrypoints[name], `${name} Reader entrypoint changed`);
  assert.deepEqual(successor.entrypoint_integrity[name], original.entrypoint_integrity[name], `${name} Reader integrity changed`);
}
const manifest = JSON.parse(readFileSync(resolve(root, 'structured-context/evidence-connect-manifest.json')));
assert.equal(manifest.semantic_source_snapshot, successor.snapshot, 'Context source snapshot differs from Reader');
assert.notEqual(manifest.bundle.snapshot, successor.snapshot, 'Successor overlay snapshot is not distinct');
const fixture = resolve(explorer, `src/lib/context/dwp_descriptor_${process.pid}.test.ts`);
const source = `import { afterEach, expect, it, vi } from 'vitest';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { loadLargeCorpus } from '../sources/largeCorpus';
import { assembleCorpusContext } from './corpus';

const root = resolve(process.env.OKF_DWP_ROOT!, 'structured-context');
const base = 'https://example.invalid/structured-context/';
afterEach(() => vi.unstubAllGlobals());
it('loads the DWP successor Reader and assembles Ask context', async () => {
  const descriptor = JSON.parse(readFileSync(resolve(root, 'evidence-connect-explorer.json'), 'utf8'));
  const fetcher = vi.fn(async (input: string | Request | URL) => {
    const url = new URL(String(input));
    expect(url.origin).toBe('https://example.invalid');
    expect(url.pathname.startsWith('/structured-context/')).toBe(true);
    const relative = url.pathname.slice('/structured-context/'.length);
    expect(relative.includes('..')).toBe(false);
    try { return new Response(readFileSync(resolve(root, relative)), { status: 200 }); }
    catch { return new Response('', { status: 404 }); }
  });
  vi.stubGlobal('fetch', fetcher);
  const source = await loadLargeCorpus(base + 'evidence-connect-explorer.json', descriptor);
  expect(source.overview).toBeTruthy();
  const bound = await source.loadContextAssembly!();
  expect('corpus' in bound).toBe(true);
  if (!('corpus' in bound)) throw new Error('Expected context corpus');
  expect(bound.corpus.semantic_source_snapshot).toBe(descriptor.snapshot);
  expect(bound.corpus.bundle.snapshot).not.toBe(descriptor.snapshot);
  const context = await assembleCorpusContext(bound.corpus, bound.binding,
    'For Pension Credit, can savings I gave away still be treated as capital?',
    { max_bytes: 524288, max_nodes: 64, max_relationships: 128, max_depth: 6 }, fetcher as typeof fetch);
  expect(context.selected.length).toBeGreaterThan(0);
  expect(context.selected.some(row => row.record.id.includes('pc-capital-u07'))).toBe(true);
  expect(context.evidence_status).toBe('insufficient');
  expect(context.bundle.snapshot).toBe(bound.corpus.bundle.snapshot);
});
`;
try {
  writeFileSync(fixture, source, { flag: 'wx' });
  const run = spawnSync(vitest, ['run', `src/lib/context/dwp_descriptor_${process.pid}.test.ts`], {
    cwd: explorer, env: { ...process.env, OKF_DWP_ROOT: root }, encoding: 'utf8'
  });
  process.stdout.write(run.stdout || '');
  process.stderr.write(run.stderr || '');
  if (run.status !== 0) process.exitCode = run.status || 1;
} finally {
  if (existsSync(fixture)) unlinkSync(fixture);
}
