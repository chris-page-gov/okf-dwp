import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdtempSync, mkdirSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { resolve } from 'node:path';
import test from 'node:test';
import { localCorpusFetcher, verifyCatalogue, verifyExactRead } from './check_current_explorer_compatibility.mjs';

const sha = text => createHash('sha256').update(text).digest('hex');
const context = { context_id: 'urn:sha256:example', evidence_status: 'insufficient',
  budget: { truncated: true }, retrieval: { truncated: false }, selected: [], relationships: [] };
function fakeRead(expected, change = () => {}) {
  return async (_context, request) => {
    let end = Math.min(expected.length, request.offset + 3);
    if (end > 0 && end < expected.length && /[\uD800-\uDBFF]/.test(expected[end - 1]) && /[\uDC00-\uDFFF]/.test(expected[end])) end--;
    const value = { schema: 'okf-context-read.v1', context_id: context.context_id, evidence_status: 'insufficient',
      context_truncated: true, retrieval_truncated: false, ai_answer: null,
      section: request.section, record_id: request.record_id ?? null,
      media_type: request.section === 'record_text' ? 'text/plain' : 'application/json',
      character_unit: 'utf-16-code-units', total_characters: expected.length,
      content_sha256: sha(expected), offset: request.offset, end_offset: end,
      data: expected.slice(request.offset, end), next_offset: end < expected.length ? end : null,
      delivery: { used_bytes: 0, max_bytes: request.max_bytes, partial: request.offset > 0 || end < expected.length } };
    change(value);
    for (let i = 0; i < 4; i++) value.delivery.used_bytes = Buffer.byteLength(JSON.stringify(value));
    return value;
  };
}

test('reconstructs all exact slices and preserves independent truncation flags', async () => {
  const source = 'Original source: £20, "quoted", café and 😀.\n';
  const result = await verifyExactRead(context, fakeRead(source), 'package', source, 8192);
  assert(result.slices > 1);
  assert.equal(result.content_sha256, sha(source));
});

test('rejects a slice that divides a Unicode surrogate pair', async () => {
  await assert.rejects(verifyExactRead(context, fakeRead('😀abc', value => {
    value.end_offset = 1; value.data = '😀abc'.slice(0, 1); value.next_offset = 1;
  }), 'package', '😀abc', 8192), /Unicode character/);
});

for (const [label, change, message] of [
  ['changed context', value => { value.context_id = 'urn:sha256:other'; }, /context identity/],
  ['upgraded status', value => { value.evidence_status = 'sufficient'; }, /evidence status/],
  ['erased assembly truncation', value => { value.context_truncated = false; }, /assembly truncation/],
  ['invented retrieval truncation', value => { value.retrieval_truncated = true; }, /retrieval truncation/],
  ['altered evidence', value => { value.data = value.data.replace(/^./, 'X'); }, /source bytes/],
  ['changed digest', value => { value.content_sha256 = '0'.repeat(64); }, /full-value hash/],
  ['skipped slice', value => { value.offset++; }, /skipped or repeated/],
  ['erased continuation', value => { value.next_offset = null; }, /continuation/]
]) test(`rejects ${label}`, async () => {
  await assert.rejects(verifyExactRead(context, fakeRead('abcdef', change), 'package', 'abcdef', 8192), message);
});

test('accepts a complete empty catalogue without claiming evidence', async () => {
  const manifest = async (_context, options) => {
    const result = { schema: 'okf-context-manifest.v1', context_id: context.context_id, evidence_status: 'insufficient',
      summary: { context_truncated: true, retrieval_truncated: false, ai_answer: null, selected_records: 0,
        relationships: 0, full_package_bytes: Buffer.byteLength(JSON.stringify(context)) },
      records: [], delivery: { offset: 0, returned: 0, total: 0, next_offset: null, max_bytes: options.max_bytes, used_bytes: 0 } };
    for (let i = 0; i < 4; i++) result.delivery.used_bytes = Buffer.byteLength(JSON.stringify(result));
    return result;
  };
  assert.equal((await verifyCatalogue(context, manifest, 8192)).records, 0);
});

test('rejects reordered catalogue source identities', async () => {
  const selected = { ...context, selected: [{ record: { id: 'urn:source:one', text: 'source', provenance: [] } }] };
  const manifest = async () => {
    const result = { schema: 'okf-context-manifest.v1', context_id: selected.context_id, evidence_status: 'insufficient',
      summary: { context_truncated: true, retrieval_truncated: false, ai_answer: null, selected_records: 1,
        relationships: 0, full_package_bytes: Buffer.byteLength(JSON.stringify(selected)) },
      records: [{ id: 'urn:source:other' }],
      delivery: { offset: 0, returned: 1, total: 1, next_offset: null, max_bytes: 8192, used_bytes: 0 } };
    for (let i = 0; i < 4; i++) result.delivery.used_bytes = Buffer.byteLength(JSON.stringify(result));
    return result;
  };
  await assert.rejects(verifyCatalogue(selected, manifest, 8192), /omitted or reordered/);
});

test('local corpus reads enforce origin, manifest admission and unchanged bytes', async t => {
  const root = mkdtempSync(resolve(tmpdir(), 'okf-current-consumer-test-'));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  mkdirSync(resolve(root, 'corpus'));
  const original = Buffer.from('{"schema":"fixture"}');
  writeFileSync(resolve(root, 'corpus/base.json'), original);
  const fixture = { base_index: { path: 'base.json', bytes: original.length, sha256: sha(original) },
    records: { shards: [] }, search: { shards: {} } };
  const { fetcher } = localCorpusFetcher(root, 'corpus', fixture);
  assert.equal(await (await fetcher('https://compatibility.invalid/corpus/base.json')).text(), original.toString());
  await assert.rejects(fetcher('https://example.org/corpus/base.json'), /Network access/);
  await assert.rejects(fetcher('https://compatibility.invalid/corpus/unlisted.json'), /absent from the manifest/);
  writeFileSync(resolve(root, 'corpus/base.json'), Buffer.alloc(original.length, 32));
  await assert.rejects(fetcher('https://compatibility.invalid/corpus/base.json'), /hash binding/);
});
