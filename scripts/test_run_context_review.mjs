import assert from 'node:assert/strict';
import { mkdtemp, readFile, readdir, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import { test } from 'node:test';
import { createHash } from 'node:crypto';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const runner = resolve(root, 'scripts/run_context_review.mjs');
const explorerRoot = process.env.OKF_EXPLORER_ROOT || resolve(root, '../okf-explorer');

function run(args) {
  return spawnSync(process.execPath, ['--experimental-strip-types', runner,
    '--explorer-root', explorerRoot, ...args], { cwd: root, encoding: 'utf8' });
}

test('offline runner writes independently verified contexts and deterministic review artefacts', { timeout: 180000 }, async () => {
  const directory = await mkdtemp(resolve(tmpdir(), 'okf-context-review-'));
  const output = resolve(directory, 'review');
  try {
    const first = run(['--output-dir', output]);
    assert.equal(first.status, 0, first.stderr);
    const summary = JSON.parse(first.stdout);
    assert.equal(summary.schema, 'okf-dwp-context-review.v1');
    assert.equal(summary.model_calls, 0); assert.equal(summary.network_calls, 0);
    assert.equal(summary.contexts.length, 5);
    const reportRaw = await readFile(resolve(output, 'report.json'), 'utf8');
    const report = JSON.parse(reportRaw);
    assert.equal(report.ai_answer, null);
    assert(report.identity.adapter_sha256 && report.identity.progressive_client_sha256
      && report.identity.renderer_sha256 && report.identity.explorer_delivery_sha256);
    assert(report.contexts.every(context => context.delivery_complete === true
      && context.package_complete === true && context.evidence_status === 'insufficient'));
    assert(report.contexts.every(context => context.collection_sha256 && context.package_sha256));
    assert.match(await readFile(resolve(output, 'index.html'), 'utf8'), /Independent experimental publication/);
    assert.deepEqual((await readdir(resolve(output, 'contexts'))).sort(), report.contexts.map(row => row.id + '.json').sort());
    for (const context of report.contexts) {
      const collectionRaw = await readFile(resolve(output, context.collection_artifact), 'utf8');
      assert.equal(createHashHex(collectionRaw), context.collection_sha256);
      const collection = JSON.parse(collectionRaw);
      assert.equal(collection.summary.delivery_complete, true);
      assert.equal(collection.summary.package_complete, true);
      assert.equal(collection.summary.package_sha256, context.package_sha256);
      assert.equal(collection.summary.ai_answer, null);
      if (collection.schema !== 'okf-graph-evidence-collection.v1') assert.equal(collection.receipt.ai_answer, null);
      assert.equal(collection.receipt.source_instructions, 'inert-data');
    }
    const checked = run(['--output-dir', output, '--check']);
    assert.equal(checked.status, 0, checked.stderr);
    const repeated = run(['--output-dir', output]);
    assert.notEqual(repeated.status, 0);
    assert.match(repeated.stderr, /fresh output directory/);
    const unexpectedPath = resolve(output, 'unbound.json');
    await writeFile(unexpectedPath, '{}');
    const unexpected = run(['--output-dir', output, '--check']);
    assert.notEqual(unexpected.status, 0);
    assert.match(unexpected.stderr, /Unexpected or missing/);
    await rm(unexpectedPath);
    const baselinePath = resolve(output, report.contexts[0].collection_artifact);
    const original = await readFile(baselinePath, 'utf8');
    await writeFile(baselinePath, original.replace('insufficient', 'sufficient'));
    const tampered = run(['--output-dir', output, '--check']);
    assert.notEqual(tampered.status, 0);
    assert.match(tampered.stderr, /stale/);
  } finally { await rm(directory, { recursive: true, force: true }); }
});

test('optional public research question is preserved and bound in the report', { timeout: 180000 }, async () => {
  const directory = await mkdtemp(resolve(tmpdir(), 'okf-context-review-question-'));
  const question = 'When does an award of another benefit change Universal Credit?';
  try {
    const result = run(['--question', question, '--output-dir', resolve(directory, 'review')]);
    assert.equal(result.status, 0, result.stderr);
    const report = JSON.parse(await readFile(resolve(directory, 'review/report.json'), 'utf8'));
    assert.equal(report.question, question);
    assert.equal(report.identity.case_id, null);
    assert.equal(report.identity.question_sha256, createHashHex(question));
    assert(report.recovery_plan.queries.some(row => row.id === 'other-benefit-timing'));
    assert(report.contexts.every(row => row.evidence_status === 'insufficient'));
  } finally { await rm(directory, { recursive: true, force: true }); }
});

function createHashHex(value) {
  return createHash('sha256').update(value).digest('hex');
}
