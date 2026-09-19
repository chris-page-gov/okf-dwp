#!/usr/bin/env node
/** Offline corruption controls for full-corpus question replay; no private inputs or live calls. */
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { cp, mkdir, mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { gzipSync, gunzipSync } from 'node:zlib';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const flags = {};
for (let position = 2; position < process.argv.length; position++) {
  const flag = process.argv[position];
  assert(['--explorer-root', '--directory'].includes(flag), `Unknown option ${flag}`);
  assert(process.argv[position + 1] && !process.argv[position + 1].startsWith('--'), `Missing ${flag} value`);
  flags[flag.slice(2)] = process.argv[++position];
}
const explorer = path.resolve(flags['explorer-root'] || path.join(ROOT, '../okf-explorer'));
const original = path.resolve(flags.directory || path.join(ROOT, 'validation/corpus-questions'));
const engineRelative = 'apps/okf-explorer/src/lib/context';
const { canonicalJson } = await import(pathToFileURL(path.join(explorer, engineRelative, 'index.ts')));
const sha = value => createHash('sha256').update(value).digest('hex');
const temporary = await mkdtemp(path.join(tmpdir(), 'okf-corpus-replay-controls-'));
const blockNetwork = path.join(temporary, 'no-network.mjs');
await writeFile(blockNetwork, 'globalThis.fetch = async () => { throw new Error("Network is forbidden in offline replay controls"); };\n');

function replay(directory, overrides = {}) {
  const root = overrides.root || ROOT;
  const result = spawnSync(process.execPath, ['--experimental-strip-types', '--import', blockNetwork,
    path.join(root, 'scripts/evaluate_corpus_questions.mjs'), '--check',
    '--explorer-root', overrides.explorer || explorer, '--output', directory],
  { cwd: root, encoding: 'utf8', timeout: 300000, maxBuffer: 4 * 1024 * 1024 });
  assert(!result.error, `Replay did not complete: ${result.error}`);
  assert.equal(result.signal, null, 'Replay must finish rather than be killed');
  assert(!result.stderr.includes('Network is forbidden'), 'Replay attempted a live network request');
  return result;
}

/** Rehash archive and transport metadata so semantic forgery must fail direct-engine parity. */
async function rewritePackage(receipt, directory, mutate, { preserveText = false } = {}) {
  const row = receipt.cases[0];
  const archivePath = path.join(directory, row.archive);
  const previous = gunzipSync(await readFile(archivePath), { maxOutputLength: 2 * 1024 * 1024 }).toString('utf8');
  let raw;
  let pack;
  if (row.transport) {
    const stream = !previous.trim().startsWith('{');
    const messages = stream ? previous.split(/\r?\n\r?\n/).flatMap(block => {
      const data = block.split(/\r?\n/).filter(line => line.startsWith('data:'))
        .map(line => line.slice(5).trimStart()).join('\n');
      return data ? [JSON.parse(data)] : [];
    }) : [JSON.parse(previous)];
    const matching = messages.filter(message => message.id === row.transport.id);
    assert.equal(matching.length, 1, 'Fixture must have exactly one matching RPC response');
    const envelope = matching[0];
    pack = envelope.result.structuredContent;
    mutate(pack);
    if (!preserveText) envelope.result.content[0].text = JSON.stringify(pack);
    raw = Buffer.from(stream ? messages.map(message => `event: message\ndata: ${JSON.stringify(message)}\n\n`).join('') : JSON.stringify(envelope));
    row.transport.sha256 = sha(raw);
    row.transport.bytes = raw.length;
    const ledger = receipt.calls.find(call => call.id === row.transport.id);
    assert(ledger, 'Remote fixture must retain the tool-call ledger');
    Object.assign(ledger, row.transport);
  } else {
    assert(!preserveText, 'Dual passthrough test requires a captured MCP response');
    pack = JSON.parse(previous);
    mutate(pack);
    raw = Buffer.from(JSON.stringify(pack));
  }
  const archive = gzipSync(raw, { level: 9 });
  await writeFile(archivePath, archive);
  row.archive_sha256 = sha(archive);
  row.package_sha256 = sha(canonicalJson(pack));
  row.evidence_status = pack.evidence_status;
  row.package_bytes = pack.budget.used_bytes;
}

const rejected = [];
const notApplicable = [];
try {
  const baseline = replay(original);
  assert.equal(baseline.status, 0, `Unmodified replay must pass before corruption controls:\n${baseline.stderr}`);
  const originalReceipt = JSON.parse(await readFile(path.join(original, 'receipt.json')));
  const mutations = [
    { name: 'receipt schema', mutate: receipt => { receipt.schema = 'forged-receipt.v1'; } },
    { name: 'bundle version', mutate: receipt => { receipt.version = '0'.repeat(40); } },
    { name: 'manifest URL', mutate: receipt => { receipt.binding.index_url = 'https://example.invalid/manifest.json'; } },
    { name: 'manifest hash', mutate: receipt => { receipt.binding.index_sha256 = '0'.repeat(64); } },
    { name: 'registry identity', mutate: receipt => { receipt.inputs.registry_sha256 = '0'.repeat(64); } },
    { name: 'engine receipt identity', mutate: receipt => { receipt.inputs.engine['corpus.ts'] = '0'.repeat(64); } },
    { name: 'protocol', mutate: receipt => { receipt.protocol = '1900-01-01'; } },
    { name: 'archive path escape', mutate: receipt => { receipt.cases[0].archive = '../outside.response.json.gz'; } },
    { name: 'tampered archive bytes', mutate: async (receipt, directory) => {
      const filename = path.join(directory, receipt.cases[0].archive);
      const bytes = await readFile(filename);
      bytes[Math.floor(bytes.length / 2)] ^= 1;
      await writeFile(filename, bytes);
    } },
    { name: 'rehashed forged sufficient evidence', expected: /complete package differs from shared engine/,
      mutate: (receipt, directory) => rewritePackage(receipt, directory, pack => { pack.evidence_status = 'sufficient'; }) },
    { name: 'rehashed forged source provenance hash', expected: /complete package differs from shared engine/,
      mutate: (receipt, directory) => rewritePackage(receipt, directory, pack => {
        const evidence = pack.selected.find(item => item.record.kind === 'evidence');
        assert(evidence?.record.provenance.length, 'Fixture needs retained source evidence');
        evidence.record.provenance[0].source_sha256 = 'f'.repeat(64);
      }) },
    { name: 'rehashed retrieval metadata mismatch', expected: /complete package differs from shared engine/,
      mutate: (receipt, directory) => rewritePackage(receipt, directory, pack => { pack.retrieval.corpus_pages += 1; }) },
    { name: 'case parity claim', mutate: receipt => { receipt.cases[0].parity = false; } },
    { name: 'actual engine bytes changed', mutate: async (_receipt, _directory, overrides) => {
      const clone = path.join(temporary, 'changed-explorer');
      await mkdir(path.join(clone, engineRelative), { recursive: true });
      for (const filename of ['index.ts', 'corpus.ts', 'types.ts']) await cp(path.join(explorer, engineRelative, filename), path.join(clone, engineRelative, filename));
      const filename = path.join(clone, engineRelative, 'corpus.ts');
      await writeFile(filename, (await readFile(filename, 'utf8')) + '\n// Deliberately changed offline engine identity.\n');
      overrides.explorer = clone;
    } },
    { name: 'actual hash-bound corpus file changed', expected: /integrity failed|exceeds its byte binding/,
      mutate: async (_receipt, _directory, overrides) => {
        const clone = path.join(temporary, 'changed-corpus');
        for (const filename of ['scripts/evaluate_corpus_questions.mjs', 'evaluation/staff-questions/cases.json']) {
          await mkdir(path.dirname(path.join(clone, filename)), { recursive: true });
          await cp(path.join(ROOT, filename), path.join(clone, filename));
        }
        await cp(path.join(ROOT, 'context/corpus'), path.join(clone, 'context/corpus'), { recursive: true });
        const manifest = JSON.parse(await readFile(path.join(clone, 'context/corpus/manifest.json')));
        const filename = path.join(clone, 'context/corpus', manifest.base_index.path);
        const bytes = await readFile(filename);
        bytes[Math.floor(bytes.length / 2)] ^= 1;
        await writeFile(filename, bytes);
        overrides.root = clone;
      } }
  ];
  const remoteMutations = [
    { name: 'remote endpoint', mutate: receipt => { receipt.endpoint = 'https://example.invalid/mcp'; } },
    { name: 'handshake method', mutate: receipt => { receipt.calls[0].method = 'tools/call'; } },
    { name: 'handshake status', mutate: receipt => { receipt.calls[0].status = 500; } },
    { name: 'handshake content type', mutate: receipt => { receipt.calls[0].content_type = 'text/html'; } },
    { name: 'transport ledger', mutate: receipt => { receipt.calls = []; } },
    { name: 'JSON and structured passthrough mismatch', expected: /AssertionError/,
      mutate: (receipt, directory) => rewritePackage(receipt, directory, pack => { pack.retrieval.corpus_pages += 1; }, { preserveText: true }) }
  ];
  if (originalReceipt.mode === 'remote-mcp-exact-core-parity') mutations.push(...remoteMutations);
  else notApplicable.push(...remoteMutations.map(({ name }) => ({ name, reason: 'Local-only receipt has no captured remote handshake or dual MCP representation.' })));
  for (const [position, control] of mutations.entries()) {
    const directory = path.join(temporary, `case-${position}`);
    await cp(original, directory, { recursive: true });
    const receiptFile = path.join(directory, 'receipt.json');
    const receipt = JSON.parse(await readFile(receiptFile));
    const overrides = {};
    await control.mutate(receipt, directory, overrides);
    await writeFile(receiptFile, JSON.stringify(receipt, null, 2) + '\n');
    const result = replay(directory, overrides);
    assert.notEqual(result.status, 0, `Replay accepted mutated ${control.name}`);
    assert.match(result.stderr, control.expected || /AssertionError/, `${control.name} failed for an unexpected reason:\n${result.stderr.slice(0, 1500)}`);
    rejected.push(control.name);
  }
  console.log(JSON.stringify({ passed: true, baseline_replay_passed: true, receipt_mode: originalReceipt.mode,
    rejected_mutations: rejected, not_applicable: notApplicable, network_used: false }));
} finally {
  await rm(temporary, { recursive: true, force: true });
}
