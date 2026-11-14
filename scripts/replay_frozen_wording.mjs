#!/usr/bin/env node
/** Replay attempt-01 from immutable Git blobs in a disposable source tree. */
import assert from 'node:assert/strict';
import { execFileSync, spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { mkdtemp, mkdir, readFile, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { dirname, isAbsolute, relative, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

export const PRODUCER_COMMIT = '5516e6c604793a5c98c57a3ddb9c3c13f46afe64';
export const REPLAY_LIMITS = Object.freeze({ files: 128, fileBytes: 16 * 1024 * 1024,
  totalBytes: 64 * 1024 * 1024, gitBufferBytes: 20 * 1024 * 1024 });
const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const ATTEMPT = 'evaluation/retrieval-gate/withheld/attempt-01';
const STATIC_PATHS = [
  `${ATTEMPT}/run.mjs`, `${ATTEMPT}/protocol.json`, `${ATTEMPT}/freeze.json`,
  `${ATTEMPT}/receipt.json`, `${ATTEMPT}/run-summary.json`,
  'scripts/graph_evidence_client.mjs', 'scripts/graph_evidence_runtime.mjs',
  'scripts/insufficiency_categories.mjs', 'scripts/load_evidence_route_runtime.mjs',
  'scripts/context_recovery.mjs', 'domain-profile/context-recovery/policy.yamlld',
  'retrieval-graph/graph.json', 'evaluation/staff-questions/cases.json',
  'combined/context/corpus/base-index.json',
];

const sha = bytes => createHash('sha256').update(bytes).digest('hex');
function safeRepoPath(path) {
  assert(typeof path === 'string' && path.length > 0 && path.length <= 400, 'Invalid source path');
  assert(!path.startsWith('/') && !path.includes('\\') && !path.includes('\0'), 'Unsafe source path');
  const segments = path.split('/');
  assert(segments.every(part => part && part !== '.' && part !== '..'), 'Unsafe source path segment');
  assert(/^[a-zA-Z0-9_.-]+(?:\/[a-zA-Z0-9_.-]+)*$/.test(path), 'Unsupported source path characters');
  return path;
}

function readGitBlob(repo, path) {
  safeRepoPath(path);
  try {
    return execFileSync('git', ['-C', repo, 'show', `${PRODUCER_COMMIT}:${path}`], {
      maxBuffer: REPLAY_LIMITS.gitBufferBytes, stdio: ['ignore', 'pipe', 'pipe'],
    });
  } catch {
    throw new Error(`Pinned source blob unavailable: ${path}`);
  }
}

function assertContained(root, path) {
  const rel = relative(root, path);
  assert(rel && rel !== '..' && !rel.startsWith(`..${sep}`) && !isAbsolute(rel), 'Temporary extraction escaped its root');
}

export async function replayFrozenTrial({ repo = ROOT, explorerRoot, node = process.execPath } = {}) {
  assert(explorerRoot, 'Use --explorer-root PATH');
  const producer = execFileSync('git', ['-C', repo, 'rev-parse', `${PRODUCER_COMMIT}^{commit}`], { encoding: 'utf8' }).trim();
  assert.equal(producer, PRODUCER_COMMIT, 'Frozen producer commit did not resolve exactly');

  const blobs = new Map();
  for (const path of STATIC_PATHS) blobs.set(path, readGitBlob(repo, path));
  const protocol = JSON.parse(blobs.get(`${ATTEMPT}/protocol.json`).toString('utf8'));
  const freeze = JSON.parse(blobs.get(`${ATTEMPT}/freeze.json`).toString('utf8'));
  assert.equal(sha(blobs.get(`${ATTEMPT}/protocol.json`)), freeze.withheld_protocol_sha256,
    'Frozen protocol digest differs');
  assert.equal(freeze.graph_sha256, 'ff51d877ed13f7089e7512224a4a8dcd356d0ae8e5964fe33349edf0a263b426');
  assert.equal(freeze.engine_id, 'urn:okf:graph-engine:sha256:4226899cd677b2f2bc4a3b12f163ab850339baab1646d9ddd29a36edb4d75ce7');
  assert.equal(protocol.counts.cases, 24);
  assert.equal(protocol.counts.positive_retrieval, 12);
  assert.equal(protocol.counts.negative_boundary, 12);
  assert.equal(protocol.cases.length, 24);

  const registry = JSON.parse(blobs.get('evaluation/staff-questions/cases.json').toString('utf8'));
  const candidates = new Map(registry.source_candidates.map(row => [row.id, row]));
  const requestedCandidateIds = [...new Set(protocol.cases.filter(row => row.class === 'positive-retrieval')
    .flatMap(row => row.assessor_binding?.candidate_ids ?? []))];
  assert(requestedCandidateIds.length > 0, 'No frozen source candidates referenced');
  for (const id of requestedCandidateIds) {
    const candidate = candidates.get(id);
    assert(candidate, `Frozen registry lacks source candidate ${id}`);
    for (const path of [candidate.source_pdf, candidate.pages_path]) {
      safeRepoPath(path);
      if (!blobs.has(path)) blobs.set(path, readGitBlob(repo, path));
    }
  }
  assert(blobs.size <= REPLAY_LIMITS.files, 'Frozen replay file-count ceiling exceeded');
  let totalBytes = 0;
  for (const [path, bytes] of blobs) {
    assert(bytes.length <= REPLAY_LIMITS.fileBytes, `Frozen replay file-byte ceiling exceeded: ${path}`);
    totalBytes += bytes.length;
  }
  assert(totalBytes <= REPLAY_LIMITS.totalBytes, 'Frozen replay aggregate byte ceiling exceeded');

  // A replay only reads the committed snapshot; also refuse to run against a
  // working tree where retained attempt-01 files have drifted from that snapshot.
  for (const name of ['run.mjs', 'protocol.json', 'freeze.json', 'receipt.json', 'run-summary.json']) {
    const path = `${ATTEMPT}/${name}`;
    const retained = await readFile(resolve(repo, path));
    assert(retained.equals(blobs.get(path)), `Retained frozen attempt differs from producer commit: ${name}`);
  }

  const temporaryRoot = await mkdtemp(resolve(tmpdir(), 'okf-frozen-wording-'));
  try {
    for (const [path, bytes] of blobs) {
      const target = resolve(temporaryRoot, path);
      assertContained(temporaryRoot, target);
      await mkdir(dirname(target), { recursive: true });
      await writeFile(target, bytes, { flag: 'wx' });
    }

    const runnerPath = resolve(temporaryRoot, `${ATTEMPT}/run.mjs`);
    const child = spawnSync(node, ['--experimental-strip-types', runnerPath, resolve(explorerRoot)], {
      cwd: temporaryRoot, encoding: 'utf8', timeout: 8 * 60 * 1000,
      maxBuffer: 4 * 1024 * 1024, env: { ...process.env, OKF_EXPLORER_ROOT: resolve(explorerRoot) },
    });
    if (child.error || child.status !== 0) {
      throw new Error(`Frozen trial runner failed (exit ${child.status ?? 'unavailable'}); retained outputs were not changed`);
    }
    const stdout = child.stdout.trim();
    let runSummary;
    try { runSummary = JSON.parse(stdout); }
    catch { throw new Error('Frozen trial runner did not return its expected machine-readable summary'); }
    for (const name of ['receipt.json', 'run-summary.json']) {
      const path = `${ATTEMPT}/${name}`;
      const generated = await readFile(resolve(temporaryRoot, path));
      assert(generated.equals(blobs.get(path)), `Replay output differs from frozen ${name}`);
    }
    assert.equal(runSummary.trial_status, 'retrieval-and-boundary-gates-passed');
    return { status: 'byte-identical-replay-passed', producer_commit: PRODUCER_COMMIT,
      extracted_files: blobs.size, extracted_bytes: totalBytes,
      trial_status: runSummary.trial_status, counts: runSummary.counts,
      stdout: { positive_failures: runSummary.positive_failures, negative_failures: runSummary.negative_failures } };
  } finally {
    await rm(temporaryRoot, { recursive: true, force: true });
  }
}

async function main() {
  const args = process.argv.slice(2);
  assert(args.length === 2 && args[0] === '--explorer-root' && args[1] && !args[1].startsWith('--'),
    'Usage: node scripts/replay_frozen_wording.mjs --explorer-root PATH');
  const result = await replayFrozenTrial({ explorerRoot: args[1] });
  process.stdout.write(JSON.stringify(result) + '\n');
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main().catch(error => {
    process.stderr.write(`Frozen trial replay failed: ${error instanceof Error ? error.message : 'unknown error'}\n`);
    process.exitCode = 1;
  });
}
