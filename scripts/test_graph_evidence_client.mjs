import assert from 'node:assert/strict';
import test from 'node:test';
import { readFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { collectGraphEvidence } from './graph_evidence_client.mjs';
import { loadEvidenceRouteRuntime } from './load_evidence_route_runtime.mjs';
import { createGraphEvidenceRuntime, graphBytes, graphEvidenceManifest, graphSha, readGraphEvidence } from './graph_evidence_runtime.mjs';

const ENGINE = 'urn:okf:graph-engine:sha256:' + 'b'.repeat(64);
const id = value => 'urn:client-test:' + value;
const record = (key, kind, text) => ({ id: id(key), route: key, label: key, kind, text,
  aliases: [], access: 'public', assertion_status: 'normalized', authority: { class: 'derived', label: 'Client fixture' },
  provenance: kind === 'evidence' ? [{ source_sha256: '3'.repeat(64), literal_sha256: '4'.repeat(64) }] : [] });
const edge = { id: id('edge'), source: id('root'), target: id('page'), predicate: 'references', context_guard: { when_all: [] } };

function wrap(value, { jsonrpc = true, mismatchCopies = false, extraBytes = 0 } = {}) {
  const text = JSON.stringify(value);
  const structuredContent = structuredClone(value);
  if (mismatchCopies) structuredContent.evidence_status = 'altered-copy';
  const mcp = { structuredContent, content: [{ type: 'text', text }] };
  const response = jsonrpc ? { jsonrpc: '2.0', id: 1, result: mcp } : mcp;
  if (extraBytes) response.extra = 'x'.repeat(extraBytes);
  return response;
}

function settle(value) {
  for (let i = 0; i < 8; i++) value.delivery.used_bytes = graphBytes(value);
  return value;
}

async function runtimeFixture({ text = 'A verified passage.', conceptCount = 1 } = {}) {
  const roots = Array.from({ length: conceptCount }, (_, n) => record(`root-${n}`, 'concept', `root concept ${n}`));
  const page = record('page', 'evidence', text);
  const graph = { schema: 'okf-dwp-evidence-route-graph.v1', snapshot: 'client-fixture', source_bindings: [],
    routing_rules: [], index: { schema: 'okf-context-index.v1', records: [...roots, page],
      assertions: [{ ...edge, source: roots[0].id }], requirements: [{ id: id('requirement'), label: 'source', when_all: [roots[0].id],
        required: [page.id], required_paths: [], limitations: [] }] } };
  const graphText = JSON.stringify(graph), graphSha256 = await graphSha(graphText);
  const runtime = await createGraphEvidenceRuntime({ graphText, graphSha256,
    engineId: ENGINE,
    resolveConcepts: () => ({ resolved: roots.map(row => ({ id: row.id })), ambiguities: [], unresolved: [] }),
    validateContextIndex: index => assert.equal(index.schema, 'okf-context-index.v1') });
  const plan = await runtime.plan('client integration question');
  return { runtime, plan, graphText, graphSha256 };
}

function transportFor(plan, { mutateManifest, mutateRead, extraResponseBytes = 0 } = {}) {
  const responseBytes = [];
  const wireSizer = value => graphBytes(wrap(value));
  const transport = {
    manifest: async args => {
      let value = await graphEvidenceManifest(plan, { offset: args.offset, maxBytes: args.delivery_bytes }, wireSizer);
      if (mutateManifest) value = await mutateManifest(value, args);
      const response = wrap(settle(value), { extraBytes: typeof extraResponseBytes === 'function'
        ? extraResponseBytes('manifest', args) : extraResponseBytes });
      responseBytes.push(graphBytes(response));
      return response;
    },
    read: async args => {
      let value = await readGraphEvidence(plan, { ...args, maxBytes: args.delivery_bytes }, wireSizer);
      if (mutateRead) value = await mutateRead(value, args);
      const response = wrap(settle(value), { extraBytes: typeof extraResponseBytes === 'function'
        ? extraResponseBytes('read', args) : extraResponseBytes });
      responseBytes.push(graphBytes(response));
      return response;
    },
  };
  return { transport, responseBytes };
}

const optionsFor = fixture => ({ transport: fixture.transport,
  question: 'client integration question', expectedGraphSha256: fixture.graphSha256,
  expectedEngineId: ENGINE, deliveryBytes: 8192 });

test('the measured largest persona package survives 750 ms pacing inside the bounded session', async t => {
  const root = resolve(new URL('..', import.meta.url).pathname);
  const suite = JSON.parse(await readFile(resolve(root, 'evaluation/retrieval-gate/persona-cases.json'), 'utf8'));
  const question = suite.cases.find(row => row.id === 'unhinted-household-care-home').prompt.question;
  const loaded = await loadEvidenceRouteRuntime({ root,
    explorerRoot: process.env.OKF_EXPLORER_ROOT || resolve(root, '.ci/okf-explorer-current') });
  const plan = await loaded.runtime.plan(question);
  const served = transportFor(plan);
  let elapsed = 0;
  t.mock.method(performance, 'now', () => elapsed);
  const paced = Object.fromEntries(Object.entries(served.transport).map(([method, invoke]) => [method, async args => {
    const result = await invoke(args); elapsed += 750; return result;
  }]));
  const result = await collectGraphEvidence({ transport: paced, question,
    expectedGraphSha256: loaded.graphSha256, expectedEngineId: loaded.engineId, deliveryBytes: 8192 });
  assert(result.summary.delivery.calls >= 331);
  assert(elapsed > 180000 && elapsed < 600000);
  assert.equal(result.summary.delivery_complete, true);
  assert.equal(result.summary.package_complete, true);
  assert.equal(result.summary.delivery.calls, served.responseBytes.length);
  assert(Math.max(...served.responseBytes) <= 8192);
  assert.deepEqual(result.package, plan);
});

test('collects the complete package losslessly under an 8192-byte JSON-RPC/MCP envelope cap', async () => {
  const sourceText = 'Résumé and source locator 😀 — ' + 'long passage '.repeat(1200);
  const generated = await runtimeFixture({ text: sourceText });
  const served = transportFor(generated.plan);
  const result = await collectGraphEvidence({ transport: served.transport, question: 'client integration question',
    expectedGraphSha256: generated.graphSha256, expectedEngineId: ENGINE, deliveryBytes: 8192 });
  const recovered = result.package.selected.find(row => row.record.id === id('page')).record.text;
  assert.equal(recovered, sourceText);
  assert.equal(result.summary.delivery_complete, true);
  assert.equal(result.summary.package_complete, true);
  assert(result.summary.delivery.slices > 1);
  assert(served.responseBytes.every(bytes => bytes <= 8192));
  assert.equal(result.summary.delivery.max_response_bytes, Math.max(...served.responseBytes));
  assert(result.summary.delivery.max_response_bytes > 0);
});

test('rejects a read offset inside a UTF-16 surrogate pair and preserves exact Unicode slices', async () => {
  const generated = await runtimeFixture({ text: 'before 😀 after — ' + 'é'.repeat(3000) });
  const recordRow = generated.plan.selected.find(row => row.record.id === id('page')).record;
  const emojiOffset = recordRow.text.indexOf('😀') + 1;
  await assert.rejects(() => readGraphEvidence(generated.plan, { plan_id: generated.plan.plan_id,
    section: 'record_text', record_id: id('page'), offset: emojiOffset, maxBytes: 2048 }), /inside a Unicode character/);
  const collected = await collectGraphEvidence({ transport: transportFor(generated.plan).transport,
    question: 'client integration question', expectedGraphSha256: generated.graphSha256,
    expectedEngineId: ENGINE, deliveryBytes: 8192 });
  assert.equal(collected.package.selected.find(row => row.record.id === id('page')).record.text, recordRow.text);
});

test('counts the complete JSON-RPC plus duplicated MCP response against the hard delivery limit', async () => {
  const generated = await runtimeFixture();
  const served = transportFor(generated.plan, { extraResponseBytes: 9000 });
  await assert.rejects(() => collectGraphEvidence({ ...optionsFor({ ...generated, transport: served.transport }) }),
    /complete-envelope limit/);
  assert(served.responseBytes[0] > 8192);
});

test('rejects unequal structuredContent and JSON text copies', async () => {
  const generated = await runtimeFixture();
  const transport = { manifest: async args => {
    const value = await graphEvidenceManifest(generated.plan, { offset: args.offset, maxBytes: args.delivery_bytes },
      row => graphBytes(wrap(row)));
    return wrap(value, { mismatchCopies: true });
  }, read: async () => { throw new Error('read should not begin'); } };
  await assert.rejects(() => collectGraphEvidence({ transport, question: 'client integration question',
    expectedGraphSha256: generated.graphSha256, expectedEngineId: ENGINE }), /MCP copies differ/);
});

test('rejects changed graph and engine identities', async t => {
  const generated = await runtimeFixture();
  for (const [name, change] of [
    ['graph digest', value => { value.graph_sha256 = '0'.repeat(64); }],
    ['engine identity', value => { value.engine_id = 'urn:okf:graph-engine:sha256:' + '0'.repeat(64); }],
  ]) {
    await t.test(name, async () => {
      const served = transportFor(generated.plan, { mutateManifest: value => { change(value); return value; } });
      await assert.rejects(() => collectGraphEvidence({ transport: served.transport,
        question: 'client integration question', expectedGraphSha256: generated.graphSha256,
        expectedEngineId: ENGINE }), /source or engine drift/);
    });
  }
});

test('rejects plan identity drift between manifest pages', async () => {
  const generated = await runtimeFixture({ conceptCount: 180 });
  let seen = 0;
  const served = transportFor(generated.plan, { mutateManifest: value => {
    seen++;
    if (seen === 2) value.plan_id = 'urn:sha256:' + '0'.repeat(64);
    return value;
  } });
  await assert.rejects(() => collectGraphEvidence({ transport: served.transport,
    question: 'client integration question', expectedGraphSha256: generated.graphSha256,
    expectedEngineId: ENGINE }), /catalogue drift: plan_id/);
  assert(seen >= 2, 'fixture must force manifest continuation');
});

test('rejects malformed catalogue cards and duplicate IDs', async t => {
  const generated = await runtimeFixture({ conceptCount: 80 });
  for (const [name, change] of [
    ['malformed hash', value => { value.records[0].text_sha256 = 'not-a-hash'; }],
    ['duplicate identity', value => { if (value.records.length > 1) value.records[1].id = value.records[0].id; }],
  ]) {
    await t.test(name, async () => {
      const served = transportFor(generated.plan, { mutateManifest: value => { change(value); return value; } });
      await assert.rejects(() => collectGraphEvidence({ transport: served.transport,
        question: 'client integration question', expectedGraphSha256: generated.graphSha256,
        expectedEngineId: ENGINE }), /invalid or duplicate catalogue record/);
    });
  }
});

test('rejects read continuation, content hash and package text drift', async t => {
  const generated = await runtimeFixture({ text: '🙂 exact text '.repeat(1200) });
  const faults = [
    ['continuation', value => { if (value.offset === 0) value.next_offset = null; }, /read continuation/],
    ['slice text', value => { if (value.offset === 0 && value.data.length) value.data = (value.data[0] === 'x' ? 'y' : 'x') + value.data.slice(1); }, /package hash differs/],
    ['read content hash', value => { value.content_sha256 = '0'.repeat(64); }, /read value drift|package hash differs/],
  ];
  for (const [name, change, message] of faults) {
    await t.test(name, async () => {
      let changed = false;
      const served = transportFor(generated.plan, { mutateRead: value => {
        if (!changed) { change(value); changed = true; }
        return value;
      } });
      await assert.rejects(() => collectGraphEvidence({ transport: served.transport,
        question: 'client integration question', expectedGraphSha256: generated.graphSha256,
        expectedEngineId: ENGINE }), message);
    });
  }
});

test('rejects a response that skips a catalogue page', async () => {
  const generated = await runtimeFixture({ conceptCount: 100 });
  const served = transportFor(generated.plan, { mutateManifest: value => {
    if (value.delivery.next_offset !== null) value.delivery.next_offset += 1;
    return value;
  } });
  await assert.rejects(() => collectGraphEvidence({ transport: served.transport,
    question: 'client integration question', expectedGraphSha256: generated.graphSha256,
    expectedEngineId: ENGINE }), /catalogue continuation/);
});

test('enforces client call ceilings on non-progressing service pages', { timeout: 30000 }, async () => {
  const graphSha256 = 'c'.repeat(64), planId = 'urn:sha256:' + 'd'.repeat(64);
  const transport = { manifest: async args => {
    const offset = args.offset;
    return wrap(settle({ schema: 'okf-graph-evidence-manifest.v1', plan_id: planId,
      graph_sha256: graphSha256, engine_id: ENGINE, evidence_status: 'insufficient', ai_answer: null,
      retrieval_complete: false, assembly_truncated: false, package_sha256: 'e'.repeat(64),
      counts: { records: 5000, source_records: 0, relationships: 0, requirements: 0, diagnostics: 0 },
      records: [{ id: `urn:record:${offset}`, label: 'record', kind: 'evidence', text_sha256: 'f'.repeat(64), text_characters: 0 }],
      delivery: { offset, next_offset: offset < 4999 ? offset + 1 : null, total: 5000, max_bytes: 8192, used_bytes: 0 } }));
  }, read: async () => { throw new Error('read should not begin before the call ceiling'); } };
  await assert.rejects(() => collectGraphEvidence({ transport, question: 'bounded call test',
    expectedGraphSha256: graphSha256, expectedEngineId: ENGINE }), /session work ceiling/);
});
