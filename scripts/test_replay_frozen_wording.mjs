import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFile } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import test from 'node:test';
import { replayFrozenTrial } from './replay_frozen_wording.mjs';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const ATTEMPT = 'evaluation/retrieval-gate/withheld/attempt-01';
const hash = bytes => createHash('sha256').update(bytes).digest('hex');

test('replays the immutable attempt-01 tree without changing retained receipts', {
  skip: !process.env.OKF_EXPLORER_ROOT,
  timeout: 8 * 60 * 1000,
}, async () => {
  const retainedPaths = ['receipt.json', 'run-summary.json'];
  const before = new Map(await Promise.all(retainedPaths.map(async name => [name,
    await readFile(resolve(ROOT, ATTEMPT, name))])));
  const result = await replayFrozenTrial({ explorerRoot: process.env.OKF_EXPLORER_ROOT });
  assert.equal(result.status, 'byte-identical-replay-passed');
  assert.equal(result.extracted_files, 38);
  assert.equal(result.counts.total_cases, 24);
  assert.equal(result.counts.positive_expected_target_occurrences, 45);
  assert.equal(result.counts.positive_target_hits, 45);
  assert.equal(result.counts.negative_controls_passed, 12);
  for (const name of retainedPaths) {
    const after = await readFile(resolve(ROOT, ATTEMPT, name));
    assert.equal(hash(after), hash(before.get(name)));
    assert(after.equals(before.get(name)));
  }
});
