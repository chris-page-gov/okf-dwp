#!/usr/bin/env node
/** Mutation controls for the public staff-question replay; no private inputs. */
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { cp, mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { gzipSync, gunzipSync } from 'node:zlib';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const flags = {};
for (let i = 2; i < process.argv.length; i++) {
  const flag = process.argv[i];
  assert(['--explorer-root', '--directory'].includes(flag), `Unknown option ${flag}`);
  assert(process.argv[i + 1] && !process.argv[i + 1].startsWith('--'), `Missing ${flag} value`);
  flags[flag.slice(2)] = process.argv[++i];
}
const explorer = path.resolve(flags['explorer-root'] || path.join(root, '../okf-explorer'));
const original = path.resolve(flags.directory || path.join(root, 'validation/staff-questions'));
const hash = bytes => createHash('sha256').update(bytes).digest('hex');
function replay(directory) {
  const result = spawnSync(process.execPath, ['--experimental-strip-types',
    path.join(root, 'scripts/evaluate_staff_questions.mjs'), '--check',
    '--explorer-root', explorer, '--output', directory],
  { cwd: root, encoding: 'utf8', timeout: 120000, maxBuffer: 1024 * 1024 });
  assert(!result.error, `Replay could not run: ${result.error}`);
  return result;
}

const baseline = replay(original);
assert.equal(baseline.status, 0, `Unmodified replay must pass before mutation controls:\n${baseline.stderr}`);
const mutations = [
  ['bundle version', receipt => { receipt.bundle_version = '0'.repeat(40); }],
  ['index binding', receipt => { receipt.binding.index_sha256 = '0'.repeat(64); }],
  ['remote endpoint', receipt => { receipt.endpoint = 'https://example.invalid/mcp'; }],
  ['negotiated protocol', receipt => { receipt.protocol = '1900-01-01'; }],
  ['capture claim', receipt => { receipt.capture = 'reconstructed-response'; }],
  ['transport ledger', receipt => { receipt.calls = []; }],
  ['case parity claim', receipt => { receipt.cases[0].direct_core_identical = false; }],
  ['forged sufficient evidence with consistent archive hashes', async (receipt, directory) => {
    const row = receipt.cases[0];
    const archivePath = path.join(directory, row.archive);
    const originalRaw = gunzipSync(await readFile(archivePath));
    const isStream = row.transport.content_type.includes('text/event-stream');
    const messages = isStream
      ? originalRaw.toString('utf8').split(/\r?\n\r?\n/).flatMap(block => {
        const data = block.split(/\r?\n/).filter(line => line.startsWith('data:'))
          .map(line => line.slice(5).trimStart()).join('\n');
        return data ? [JSON.parse(data)] : [];
      }) : [JSON.parse(originalRaw)];
    const matching = messages.filter(message => message.id === row.transport.request_id);
    assert.equal(matching.length, 1);
    const envelope = matching[0];
    envelope.result.structuredContent.evidence_status = 'sufficient';
    envelope.result.content[0].text = JSON.stringify(envelope.result.structuredContent);
    const raw = Buffer.from(isStream
      ? `event: message\ndata: ${JSON.stringify(envelope)}\n\n` : JSON.stringify(envelope));
    const archive = gzipSync(raw, { level: 9 });
    await writeFile(archivePath, archive);
    row.archive_sha256 = hash(archive);
    row.transport.response_sha256 = hash(raw);
    row.transport.response_bytes = raw.byteLength;
    // Preserve the ledger consistency so direct-core parity must reject the lie.
    const call = receipt.calls.find(call => call.request_id === row.transport.request_id);
    assert(call, 'Fixture requires a recorded tool call');
    Object.assign(call, row.transport);
  }],
];

const temporary = await mkdtemp(path.join(tmpdir(), 'okf-staff-replay-controls-'));
try {
  for (const [position, [name, mutate]] of mutations.entries()) {
    const directory = path.join(temporary, String(position));
    await cp(original, directory, { recursive: true });
    const receiptPath = path.join(directory, 'receipt.json');
    const receipt = JSON.parse(await readFile(receiptPath));
    await mutate(receipt, directory);
    await writeFile(receiptPath, JSON.stringify(receipt, null, 2) + '\n');
    const result = replay(directory);
    assert.notEqual(result.status, 0, `Replay accepted mutated ${name}`);
    if (name.startsWith('forged sufficient')) {
      assert.match(result.stderr, /remote\/core mismatch/, 'Forged evidence must fail direct-core parity');
    }
  }
} finally {
  await rm(temporary, { recursive: true, force: true });
}
console.log(JSON.stringify({ passed: true, baseline_replay_passed: true,
  rejected_mutations: mutations.map(([name]) => name), network_used: false }));
