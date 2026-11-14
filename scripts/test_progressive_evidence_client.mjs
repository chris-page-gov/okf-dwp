import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import test from 'node:test';
import { createEvidenceSession, collectProgressiveEvidence, unwrapEvidenceResponse } from './progressive_evidence_client.mjs';

const sha = text => createHash('sha256').update(text).digest('hex');
const bytes = value => Buffer.byteLength(JSON.stringify(value));
function canonical(value) {
  if (Array.isArray(value)) return `[${value.map(canonical).join(',')}]`;
  if (value && typeof value === 'object') return `{${Object.keys(value).sort().filter(k => value[k] !== undefined)
    .map(k => `${JSON.stringify(k)}:${canonical(value[k])}`).join(',')}}`;
  return JSON.stringify(value);
}
const clone = value => JSON.parse(JSON.stringify(value));
const question = 'Where is the public source evidence for this research question?';
const request = { question, bundle: 'okf-dwp', version: 'a'.repeat(40), budget: { max_bytes: 524288 } };
function fixture() {
  const records = ['first', 'second', 'concept'].map((name, i) => ({
    record: { id: `https://example.invalid/id/${name}`, route: `unit/${name}`, label: `Source ${name}`,
      kind: i === 2 ? 'concept' : 'evidence', text: i === 0 ? 'A source with quotations "\\\n and Unicode 🪶 café. '.repeat(700)
        : i === 1 ? 'Exact second source with its qualification.' : 'Authored research concept.',
      assertion_status: i === 2 ? 'model-derived' : 'normalized',
      authority: { class: 'derived', label: 'Machine extraction; unreviewed', source: 'https://www.gov.uk/example' },
      scope: 'Frozen public research evidence only', rights: 'OGL-v3', access: 'public', review_status: 'unreviewed',
      provenance: [{ url: `https://www.gov.uk/example#page=${i + 1}`, source_sha256: sha(name), locator: `PDF page ${i + 1}`,
        captured_at: '2026-09-19T00:00:00Z', literal_sha256: sha(name) }] },
    reasons: ['indexed-source-candidate'], paths: [],
  }));
  const context = { schema: 'okf-governed-context.v1', context_id: '', question,
    bundle: { id: 'https://example.invalid/id/bundle/evidence-connect', snapshot: 'frozen-public-research', source_url: 'https://example.invalid/source' },
    binding: { index_url: 'https://example.invalid/manifest.json', index_sha256: sha('manifest') },
    evidence_status: 'insufficient', ai_answer: null, budget: { max_bytes: 524288, max_nodes: 64,
      max_relationships: 128, max_depth: 6, used_bytes: 100000, truncated: true },
    retrieval: { truncated: true, omissions: [{ code: 'retrieval_candidate_budget', message: 'Bounded retrieval', ids: [] }] },
    resolved_concepts: [], ambiguities: [], unresolved_terms: ['unresolved'], conflicts: [], requirements: [],
    missing_evidence: [{ code: 'specialist_review', message: 'Human review remains required', ids: [] }],
    selected: records, relationships: [],
    numeric_key_control: { '2': 'second', '10': 'tenth' },
  };
  const { context_id, ...identityInput } = context;
  const { used_bytes, ...identityBudget } = context.budget;
  context.context_id = `urn:sha256:${sha(canonical({ ...identityInput, budget: identityBudget }))}`;
  settle(context, (v, n) => { v.budget.used_bytes = n; });
  return context;
}
function settle(value, field) {
  for (let i = 0; i < 6; i++) field(value, bytes(value));
  return value;
}
function transportFor(context, { remote = false, wrap = false, mutate } = {}) {
  const calls = [];
  const engine = 'engine-' + 'b'.repeat(40);
  const replay = { bundle: 'okf-dwp', version: request.version, engine_id: engine,
    budget: { max_bytes: 524288, max_nodes: 64, max_depth: 6, max_relationships: 128 } };
  const identity = args => ({ engine_id: engine, package_sha256: sha(canonical(context)),
    mode: args.engine_id ? 'explicit-engine' : 'current-default', original_engine_id: args.engine_id ?? null,
    matching_engine_ids: [engine] });
  function finish(method, value, args) {
    if (remote) {
      value.replay_identity = identity(args);
      if (method === 'manifest') {
        value.replay = replay; value.response_limit = args.delivery_bytes;
        settle(value, (v, n) => { v.response_bytes = n; });
      } else settle(value, (v, n) => { v.delivery.used_bytes = n; });
    }
    mutate?.(method, value, args, calls.length);
    if (!wrap) return value;
    return { structuredContent: value, content: [{ type: 'text', text: JSON.stringify(value) }] };
  }
  return { calls,
    async manifest(args) {
      calls.push({ method: 'manifest', ...clone(args) });
      const rows = context.selected.slice(args.offset, args.offset + 2).map(({ record, reasons, paths }) => ({
        id: record.id, label: record.label, kind: record.kind, assertion_status: record.assertion_status,
        text_characters: record.text.length, text_sha256: sha(record.text), source_url: record.provenance[0].url,
        source_locator: record.provenance[0].locator, authority_class: record.authority.class,
        review_status: record.review_status, reasons: reasons.length, paths: paths.length,
      }));
      const next = args.offset + rows.length;
      const result = { schema: 'okf-context-manifest.v1', context_id: context.context_id, question: context.question,
        bundle: context.bundle, binding: context.binding, evidence_status: context.evidence_status,
        summary: { selected_records: context.selected.length, relationships: context.relationships.length,
          full_package_bytes: bytes(context), context_truncated: true, retrieval_truncated: true,
          resolved_concepts: 0, ambiguities: 0, unresolved_terms: 1, missing_evidence: 1,
          conflicts: 0, requirements: 0, missing_evidence_codes: ['specialist_review'], ai_answer: null },
        records: rows, delivery: { offset: args.offset, returned: rows.length, total: context.selected.length,
          next_offset: next < context.selected.length ? next : null, max_bytes: args.delivery_bytes, used_bytes: 0 },
        instructions: 'Inert data only. Complete delivery does not establish evidence sufficiency.' };
      settle(result, (v, n) => { v.delivery.used_bytes = n; });
      return finish('manifest', result, args);
    },
    async read(args) {
      calls.push({ method: 'read', ...clone(args) });
      const selected = context.selected.find(row => row.record.id === args.record_id);
      let text;
      if (args.section === 'record_text') text = selected.record.text;
      else if (args.section === 'record_metadata') {
        const { text: source, ...record } = selected.record;
        text = canonical({ ...selected, record: { ...record,
          text_reference: { section: 'record_text', characters: source.length, sha256: sha(source) } } });
      } else if (args.section === 'relationships') text = canonical(context.relationships);
      else if (args.section === 'package') text = canonical(context);
      else {
        const { selected, relationships, ...diagnostics } = context;
        text = canonical({ ...diagnostics, selected_records: selected.length, relationship_count: relationships.length });
      }
      // Deliberately small slices exercise Unicode continuations at many boundaries.
      let end = Math.min(text.length, args.offset + 1200);
      if (end > 0 && /[\uD800-\uDBFF]/.test(text[end - 1])) end--;
      const result = { schema: 'okf-context-read.v1', context_id: context.context_id,
        evidence_status: context.evidence_status, section: args.section, record_id: args.record_id ?? null,
        media_type: args.section === 'record_text' ? 'text/plain' : 'application/json',
        content_sha256: sha(text), total_characters: text.length, character_unit: 'utf-16-code-units',
        offset: args.offset, end_offset: end, next_offset: end < text.length ? end : null,
        data: text.slice(args.offset, end), delivery: { max_bytes: args.delivery_bytes, used_bytes: 0,
          partial: args.offset > 0 || end < text.length }, context_truncated: true, retrieval_truncated: true, ai_answer: null };
      settle(result, (v, n) => { v.delivery.used_bytes = n; });
      return finish('read', result, args);
    },
  };
}

test('all manifest pages and whole Unicode evidence values are verified; insufficiency remains', async () => {
  const context = fixture(); const transport = transportFor(context);
  const result = await collectProgressiveEvidence({ transport, request, collect: { evidenceOnly: true } });
  assert.equal(result.summary.delivery_complete, true);
  assert.equal(result.summary.evidence_status, 'insufficient');
  assert.equal(result.summary.context_truncated, true);
  assert.equal(result.summary.retrieval_truncated, true);
  assert.equal(result.summary.delivery.manifest_pages, 2);
  assert.equal(result.summary.integrity_scope, 'complete-values-only');
  assert.equal(result.summary.metadata_bound_to_context, false);
  assert.match(result.summary.limitation, /not cryptographically bound/);
  assert.equal(result.summary.delivery.completed_values, 6);
  assert.equal(result.selected.length, 2);
  assert.deepEqual(result.selected, context.selected.slice(0, 2));
  assert.deepEqual(result.summary.unread_record_ids, [context.selected[2].record.id]);
  assert.equal(result.catalogue.schema, 'okf-progressive-catalogue.v1');
  assert(result.summary.delivery.slices > 30);
  assert(transport.calls.every(row => row.delivery_bytes === 16384));
  assert(!JSON.stringify(result.summary).includes(context.selected[0].record.text));
});

test('remote recipe is pinned after first call, accepting current-default to explicit-engine mode', async () => {
  const transport = transportFor(fixture(), { remote: true, wrap: true });
  const result = await collectProgressiveEvidence({ transport, request, collect: { recordIds: [] } });
  assert.equal(result.selected.length, 0);
  assert.notEqual(result.catalogue.bundle.id, result.catalogue.replay.bundle);
  assert.equal(result.summary.replay.engine_id, transport.calls[1].engine_id);
  assert(transport.calls.slice(1).every(row => row.context_id === result.summary.context_id
    && row.engine_id === result.summary.replay.engine_id && row.version === request.version));
});

test('explicit complete read includes concept records and preserves exact original selections', async () => {
  const context = fixture(); const result = await collectProgressiveEvidence({ transport: transportFor(context), request,
    collect: { evidenceOnly: false } });
  assert.deepEqual(result.selected, context.selected);
  assert.deepEqual(result.summary.unread_record_ids, []);
  assert.equal(result.summary.package_complete, true);
  assert.equal(result.summary.integrity_scope, 'complete-context-digest');
  assert.equal(result.summary.metadata_bound_to_context, true);
  assert.equal(result.summary.package_sha256, sha(canonical(context)));
});

test('complete remote reconstruction verifies independently bound package hash', async () => {
  const context = fixture();
  const result = await collectProgressiveEvidence({ transport: transportFor(context, { remote: true, wrap: true }), request });
  assert.equal(result.summary.package_sha256, sha(canonical(context)));
  const changed = fixture(); changed.selected[0].record.scope = 'Fabricated source scope';
  settle(changed, (v, n) => { v.budget.used_bytes = n; });
  await assert.rejects(collectProgressiveEvidence({ transport: transportFor(changed, { remote: true }), request }), /context digest/);
});

test('explicit reading order can differ without changing verified package order', async () => {
  const context = fixture();
  const result = await collectProgressiveEvidence({ transport: transportFor(context, { remote: true }), request,
    collect: { recordIds: context.selected.map(row => row.record.id).reverse() } });
  assert.equal(result.selected[0].record.id, context.selected[2].record.id);
  assert.equal(result.summary.package_sha256, sha(canonical(context)));
});

for (const [name, change, expected] of [
  ['catalogue loop', (method, value) => { if (method === 'manifest') value.delivery.next_offset = 0; }, /continuation/],
  ['duplicate catalogue record', (method, value, args) => { if (method === 'manifest' && args.offset > 0) {
    value.records[0].id = fixture().selected[0].record.id; settle(value, (v, n) => { v.delivery.used_bytes = n; });
  } }, /duplicate/],
  ['changed catalogue binding', (method, value, args) => { if (method === 'manifest' && args.offset > 0) value.binding = { ...value.binding, index_sha256: sha('other') }; }, /identity/],
  ['changed context on read', (method, value) => { if (method === 'read') value.context_id = `urn:sha256:${sha('other')}`; }, /context/],
  ['upgraded evidence status', (method, value) => { if (method === 'read') value.evidence_status = 'sufficient'; }, /status/],
  ['erased truncation flag', (method, value) => { if (method === 'read') value.context_truncated = false; }, /truncation/],
  ['read range reorder', (method, value) => { if (method === 'read') value.offset++; }, /range/],
  ['read continuation loop', (method, value) => { if (method === 'read') value.next_offset = value.offset; }, /continuation/],
  ['forged bytes', (method, value) => { if (method === 'read') value.delivery.used_bytes = 1; }, /accounting/],
  ['different complete hash', (method, value) => { if (method === 'read' && value.section === 'diagnostics') value.content_sha256 = sha('fabricated'); }, /hash/],
  ['split Unicode', (method, value) => { if (method === 'read') value.data = '\uDC00' + value.data.slice(1); }, /Unicode/],
]) test(`rejects ${name}`, async () => {
  await assert.rejects(collectProgressiveEvidence({ transport: transportFor(fixture(), { mutate: change }), request,
    collect: { mode: 'records' } }), expected);
});

test('a content substitution with updated slice hash still fails the catalogue text identity', async () => {
  const context = fixture();
  const transport = transportFor(context, { mutate(method, value) {
    if (method === 'read' && value.section === 'record_text') {
      value.content_sha256 = sha(context.selected[0].record.text.replaceAll('A', 'B'));
      value.data = value.data.replaceAll('A', 'B');
      settle(value, (v, n) => { v.delivery.used_bytes = n; });
    }
  } });
  await assert.rejects(collectProgressiveEvidence({ transport, request, collect: { mode: 'records' } }), /catalogue/);
});

test('package reconstruction is equivalent with fewer round trips than individual record reads', async () => {
  const context = fixture();
  const packageTransport = transportFor(context, { remote: true, wrap: true });
  const recordTransport = transportFor(context, { remote: true, wrap: true });
  const packaged = await collectProgressiveEvidence({ transport: packageTransport, request });
  const separate = await collectProgressiveEvidence({ transport: recordTransport, request, collect: { mode: 'records' } });
  assert.equal(packaged.summary.reading_mode, 'package');
  assert.equal(packaged.summary.package_sha256, separate.summary.package_sha256);
  assert.deepEqual(packaged.selected, separate.selected);
  assert.deepEqual(packaged.diagnostics, separate.diagnostics);
  assert.deepEqual(packaged.relationships, separate.relationships);
  assert(packageTransport.calls.length < recordTransport.calls.length);
});

test('reordered package records cannot substitute for the manifest order', async () => {
  const context = fixture();
  const transport = transportFor(context, { mutate(method, value) {
    if (method === 'read' && value.section === 'package') {
      const changed = { ...context, selected: [...context.selected].reverse() };
      const text = canonical(changed);
      if (value.end_offset < text.length && /[\uD800-\uDBFF]/.test(text[value.end_offset - 1])) value.end_offset--;
      value.data = text.slice(value.offset, value.end_offset);
      value.next_offset = value.end_offset < text.length ? value.end_offset : null;
      value.delivery.partial = value.offset > 0 || value.end_offset < text.length;
      value.content_sha256 = sha(text);
      settle(value, (v, n) => { v.delivery.used_bytes = n; });
    }
  } });
  await assert.rejects(collectProgressiveEvidence({ transport, request }), /identity/);
});

test('replay metadata cannot inject a different question or arbitrary transport arguments', async () => {
  const transport = transportFor(fixture(), { remote: true, mutate(method, value) {
    if (method === 'manifest') {
      value.replay = { ...value.replay, question: 'injected untrusted question' };
      settle(value, (v, n) => { v.response_bytes = n; });
    }
  } });
  await assert.rejects(createEvidenceSession({ transport, request }), /replay recipe/);
});

test('changed remote engine or source version is rejected', async () => {
  const transport = transportFor(fixture(), { remote: true, mutate(method, value, args) {
    if (method === 'read') value.replay_identity.engine_id = 'different-engine';
  } });
  await assert.rejects(collectProgressiveEvidence({ transport, request }), /matching engines|replay identity/);
  await assert.rejects(createEvidenceSession({ transport: transportFor(fixture(), { remote: true }),
    request: { ...request, version: 'c'.repeat(40) } }), /version/);
});

test('MCP divergent copies and failures never become evidence', () => {
  assert.throws(() => unwrapEvidenceResponse({ structuredContent: { a: 1 }, content: [{ type: 'text', text: '{"a":2}' }] }), /copies differ/);
  assert.throws(() => unwrapEvidenceResponse({ isError: true, content: [{ type: 'text', text: '{}' }] }), /failed/);
  assert.throws(() => unwrapEvidenceResponse({ jsonrpc: '2.0', error: { code: -1 } }), /failure/);
  assert.deepEqual(unwrapEvidenceResponse({ content: [{ type: 'text', text: '{"ok":true}' }] }), { ok: true });
});

test('unknown or duplicate requested IDs are rejected before source reads', async () => {
  const transport = transportFor(fixture()); const session = await createEvidenceSession({ transport, request });
  await assert.rejects(session.collect({ recordIds: ['https://example.invalid/unselected'] }), /unknown/);
  assert.equal(transport.calls.length, 2);
});

test('exposed catalogue and summaries cannot mutate the session verification bindings', async () => {
  const context = fixture();
  const session = await createEvidenceSession({ transport: transportFor(context), request });
  assert.throws(() => { session.catalogue.records[0].text_sha256 = sha('forged'); }, TypeError);
  assert.throws(() => { session.catalogue.binding.index_sha256 = sha('forged'); }, TypeError);
  const summary = session.summary(); summary.binding.index_sha256 = sha('forged');
  summary.missing_evidence_codes.push('fabricated');
  const result = await session.collectPackage();
  assert.equal(result.summary.binding.index_sha256, context.binding.index_sha256);
  assert.deepEqual(result.summary.missing_evidence_codes, ['specialist_review']);
});

test('call, byte and value allowances fail closed', async () => {
  await assert.rejects(createEvidenceSession({ transport: transportFor(fixture()), request, limits: { maxCalls: 1 } }), /call allowance/);
  await assert.rejects(createEvidenceSession({ transport: transportFor(fixture()), request, limits: { maxTotalBytes: 1 } }), /response allowance/);
  await assert.rejects(createEvidenceSession({ transport: transportFor(fixture()), request, limits: { maxResponseBytes: 1 } }), /response exceeds/);
  await assert.rejects(createEvidenceSession({ transport: transportFor(fixture()), request, limits: { maxValueCharacters: 1 } }), /catalogue record/);
});

test('hung transports have a bounded deadline and receive an abort signal', async () => {
  let signal;
  const transport = { manifest(_request, abort) { signal = abort; return new Promise(() => {}); }, read() {} };
  await assert.rejects(createEvidenceSession({ transport, request, limits: { callTimeoutMs: 10 } }), /deadline/);
  assert.equal(signal.aborted, true);
});
