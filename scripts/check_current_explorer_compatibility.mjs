#!/usr/bin/env node
/** Additive current-consumer checks. Historical replay pins remain unchanged. */
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { readFileSync, realpathSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { gunzipSync } from 'node:zlib';

export const EXPLORER_COMMIT = '40e659408485a7dfa0e8cb51ab27c1b0f890bc3c';
const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const ORIGIN = 'https://compatibility.invalid';
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const jsonBytes = value => Buffer.byteLength(JSON.stringify(value));

/** Admit only the immutable files explicitly named by this corpus manifest. */
export function localCorpusFetcher(root, prefix, manifest) {
  assert.match(prefix, /^[a-z][a-z0-9-]*(?:\/[a-z][a-z0-9-]*)*$/);
  const directory = realpathSync(resolve(root, prefix));
  const refs = [manifest.base_index, ...manifest.records.shards,
    ...(manifest.discovery?.shards || []), ...Object.values(manifest.search.shards),
    ...Object.values(manifest.relationships?.shards || {})];
  const admitted = new Map(refs.map(ref => [ref.path, ref]));
  assert.equal(admitted.size, refs.length, 'Manifest paths must be unique');
  const files = new Map(), records = new Map();
  const recordPaths = new Set([manifest.base_index.path, ...manifest.records.shards.map(ref => ref.path)]);
  const fetcher = async input => {
    const url = new URL(String(input));
    assert.equal(url.origin, ORIGIN, 'Network access is forbidden');
    assert(!url.search && !url.hash && !url.username && !url.password, 'Unexpected URL components');
    assert(url.pathname.startsWith(`/${prefix}/`), 'Resource escaped its corpus');
    const relative = url.pathname.slice(prefix.length + 2);
    const ref = admitted.get(relative);
    assert(ref, 'Resource is absent from the manifest');
    const path = resolve(directory, relative);
    assert(path.startsWith(directory + '/') && realpathSync(path) === path, 'Unsafe resource path or symlink');
    const bytes = readFileSync(path);
    assert.equal(bytes.length, ref.bytes, 'Corpus file byte binding changed');
    assert.equal(sha(bytes), ref.sha256, 'Corpus file hash binding changed');
    files.set(relative, { path: `${prefix}/${relative}`, bytes: bytes.length, sha256: ref.sha256 });
    if (recordPaths.has(relative)) {
      const decoded = ref.encoding === 'gzip' ? gunzipSync(bytes, { maxOutputLength: ref.decoded_bytes }) : bytes;
      assert.equal(decoded.length, ref.decoded_bytes || ref.bytes, 'Decoded corpus byte binding changed');
      assert.equal(sha(decoded), ref.decoded_sha256 || ref.sha256, 'Decoded corpus hash binding changed');
      for (const record of JSON.parse(decoded).records || []) records.set(record.id, record);
    }
    return new Response(bytes);
  };
  return { fetcher, files, records };
}

/** Verify exact lossless reads independently of the Explorer implementation. */
export async function verifyExactRead(context, read, section, expected, deliveryBytes, recordId) {
  let offset = 0, slices = 0, maximum = 0;
  const parts = [];
  do {
    assert(slices < 4096, 'Evidence continuation did not terminate');
    const value = await read(context, { context_id: context.context_id, section,
      ...(recordId === undefined ? {} : { record_id: recordId }), offset, max_bytes: deliveryBytes });
    assert.equal(value.schema, 'okf-context-read.v1');
    assert.equal(value.context_id, context.context_id, 'Read changed context identity');
    assert.equal(value.evidence_status, context.evidence_status, 'Read changed evidence status');
    assert.equal(value.context_truncated, context.budget.truncated, 'Read changed assembly truncation');
    assert.equal(value.retrieval_truncated, context.retrieval?.truncated ?? false, 'Read changed retrieval truncation');
    assert.equal(value.ai_answer, null, 'Evidence delivery must not create an answer');
    assert.equal(value.section, section);
    assert.equal(value.media_type, section === 'record_text' ? 'text/plain' : 'application/json');
    assert.equal(value.record_id, recordId ?? null);
    assert.equal(value.character_unit, 'utf-16-code-units');
    assert.equal(value.total_characters, expected.length);
    assert.equal(value.content_sha256, sha(expected), 'Read changed full-value hash');
    assert.equal(value.offset, offset, 'Read skipped or repeated a slice');
    assert.equal(value.end_offset, offset + value.data.length, 'Read offsets differ from source length');
    for (const boundary of [offset, value.end_offset]) {
      assert(!(boundary > 0 && boundary < expected.length
        && /[\uD800-\uDBFF]/.test(expected[boundary - 1]) && /[\uDC00-\uDFFF]/.test(expected[boundary])),
      'Read split a Unicode character');
    }
    assert.equal(value.data, expected.slice(offset, value.end_offset), 'Read changed exact source bytes');
    assert(value.end_offset <= expected.length, 'Read passed the end of the source');
    assert(value.end_offset > offset || offset === expected.length, 'Read made no progress');
    const continuation = value.end_offset < expected.length ? value.end_offset : null;
    assert.equal(value.next_offset, continuation, 'Read continuation differs from source');
    assert.equal(value.delivery.used_bytes, jsonBytes(value), 'Read byte accounting differs');
    assert.equal(value.delivery.max_bytes, deliveryBytes);
    assert(jsonBytes(value) <= deliveryBytes, 'Read exceeded delivery budget');
    assert.equal(value.delivery.partial, offset > 0 || value.end_offset < expected.length);
    parts.push(value.data); slices++; maximum = Math.max(maximum, jsonBytes(value));
    offset = value.end_offset;
    if (continuation === null) break;
  } while (true);
  assert.equal(parts.join(''), expected, 'Reconstructed evidence differs');
  assert.equal(sha(parts.join('')), sha(expected));
  return { slices, maximum_json_result_bytes: maximum, content_sha256: sha(expected), characters: expected.length };
}

export async function verifyCatalogue(context, manifest, deliveryBytes) {
  let offset = 0, pages = 0, maximum = 0;
  const ids = [];
  do {
    assert(pages < 4096, 'Catalogue continuation did not terminate');
    const value = await manifest(context, { offset, max_bytes: deliveryBytes });
    assert.equal(value.schema, 'okf-context-manifest.v1');
    assert.equal(value.context_id, context.context_id);
    assert.equal(value.evidence_status, context.evidence_status);
    assert.equal(value.question, context.question);
    assert.deepEqual(value.bundle, context.bundle);
    assert.deepEqual(value.binding, context.binding);
    assert.equal(value.summary.context_truncated, context.budget.truncated);
    assert.equal(value.summary.retrieval_truncated, context.retrieval?.truncated ?? false);
    assert.equal(value.summary.ai_answer, null);
    assert.equal(value.summary.selected_records, context.selected.length);
    assert.equal(value.summary.relationships, context.relationships.length);
    assert.equal(value.summary.full_package_bytes, jsonBytes(context));
    assert.equal(value.delivery.offset, offset);
    assert.equal(value.delivery.returned, value.records.length);
    assert.equal(value.delivery.total, context.selected.length);
    assert.equal(value.delivery.used_bytes, jsonBytes(value));
    assert.equal(value.delivery.max_bytes, deliveryBytes);
    assert(jsonBytes(value) <= deliveryBytes, 'Catalogue exceeded delivery budget');
    for (const [i, record] of value.records.entries()) {
      const original = context.selected[offset + i].record;
      assert.equal(record.id, original.id, 'Catalogue omitted or reordered a record');
      assert.equal(record.text_sha256, sha(original.text));
      assert.equal(record.text_characters, original.text.length);
      assert.equal(record.source_url, original.provenance[0]?.url ?? '');
      assert.equal(record.source_locator, original.provenance[0]?.locator ?? '');
      ids.push(record.id);
    }
    const next = offset + value.records.length;
    assert.equal(value.delivery.next_offset, next < context.selected.length ? next : null);
    assert(next > offset || next === context.selected.length, 'Catalogue made no progress');
    pages++; maximum = Math.max(maximum, jsonBytes(value)); offset = next;
    if (value.delivery.next_offset === null) break;
  } while (true);
  assert.deepEqual(ids, context.selected.map(row => row.record.id));
  return { pages, records: ids.length, maximum_json_result_bytes: maximum };
}

export async function checkCompatibility(explorerRoot) {
  const explorer = realpathSync(resolve(explorerRoot));
  const commit = execFileSync('git', ['-C', explorer, 'rev-parse', 'HEAD'], { encoding: 'utf8' }).trim();
  assert.equal(commit, EXPLORER_COMMIT, 'Use the separately pinned current Explorer checkout');
  const engine = resolve(explorer, 'apps/okf-explorer/src/lib/context');
  const modules = {};
  for (const name of ['index.ts', 'corpus.ts', 'corpusV3.ts', 'types.ts', 'unit.ts', 'delivery.ts']) {
    const bytes = readFileSync(resolve(engine, name));
    const committed = execFileSync('git', ['-C', explorer, 'show', `${commit}:apps/okf-explorer/src/lib/context/${name}`],
      { maxBuffer: 8 * 1024 * 1024 });
    assert.equal(sha(bytes), sha(committed), `Uncommitted Explorer runtime: ${name}`);
    modules[name] = sha(bytes);
  }
  const { canonicalJson, assembleContext, validateContextIndex } = await import(pathToFileURL(resolve(engine, 'index.ts')));
  const { validateContextCorpusManifest, assembleCorpusContext } = await import(pathToFileURL(resolve(engine, 'corpus.ts')));
  const { contextManifest, readContextEvidence } = await import(pathToFileURL(resolve(engine, 'delivery.ts')));
  const oldFetch = globalThis.fetch;
  globalThis.fetch = async () => { throw new Error('Network forbidden in compatibility checks'); };
  try {
    const report = { schema: 'okf-dwp-current-explorer-compatibility.v1', status: 'passed',
      explorer: { commit, modules }, runner_sha256: sha(readFileSync(fileURLToPath(import.meta.url))),
      network_calls: 0, model_calls: 0,
      delivery_bytes: 8192, cases: [], corpora: [], limitations: [
        'Offline API and byte-preservation checks, not a public browser, service deployment or AI host observation.',
        'Complete delivery does not establish complete source selection, current law, legal applicability or specialist acceptance.',
        'Delivery bounds count each JSON result. MCP envelopes and duplicated text/structured content can be larger.'
      ] };
    const staffRaw = readFileSync(resolve(ROOT, 'evaluation/staff-questions/cases.json'));
    const staff = JSON.parse(staffRaw);
    const rows = Array.isArray(staff) ? staff : staff.cases;
    assert(Array.isArray(rows) && rows.length === 40, 'Frozen staff registry changed shape');
    const supersessionRaw = readFileSync(resolve(ROOT, 'evaluation/out-of-sample/uc-disabled-child-supersession-001.json'));
    const supersession = JSON.parse(supersessionRaw);
    report.question_inputs = { staff_registry_sha256: sha(staffRaw), supersession_case_sha256: sha(supersessionRaw) };
    const questions = [
      { id: 'staff-first', question: rows[0].question },
      { id: 'custody', question: 'What happens to benefits when someone goes to prison?' },
      { id: 'uc-effective-date-ordinary', question: supersession.question },
      { id: 'uc-effective-date-locator', question: 'ADM A4361 relevant benefit supersession UC award of other benefits effective date' },
      { id: 'unknown', question: 'zzunmatched zzunresolved' }
    ];
    for (const file of ['context/corpus/manifest.json', 'combined/context/corpus/manifest.json',
      'logical-context/manifest.json', 'structured-context/manifest.json',
      'structured-context/evidence-connect-manifest.json']) {
      const raw = readFileSync(resolve(ROOT, file));
      const manifest = validateContextCorpusManifest(JSON.parse(raw));
      const prefix = dirname(file);
      const binding = { index_url: `${ORIGIN}/${file}`, index_sha256: sha(raw) };
      const local = localCorpusFetcher(ROOT, prefix, manifest);
      const subset = file.startsWith('structured-') ? questions : questions.filter(q => ['custody', 'unknown'].includes(q.id));
      for (const entry of subset) for (const maxBytes of [32768, 524288]) {
        const budget = { max_bytes: maxBytes, max_nodes: 64, max_relationships: 128, max_depth: 6 };
        const context = await assembleCorpusContext(manifest, binding, entry.question, budget, local.fetcher);
        const replay = await assembleCorpusContext(manifest, binding, entry.question, budget, local.fetcher);
        assert.equal(canonicalJson(context), canonicalJson(replay), 'Current context is not deterministic');
        assert.equal(context.evidence_status, 'insufficient', 'Compatibility must preserve unreviewed evidence gaps');
        assert.equal(context.ai_answer, null);
        assert(context.budget.used_bytes <= maxBytes, 'Assembly exceeded its own byte budget');
        for (const selected of context.selected.filter(row => row.record.kind === 'evidence')) {
          const original = local.records.get(selected.record.id);
          assert(original, 'Selected source record was not read from a bound corpus file');
          assert.equal(canonicalJson(selected.record), canonicalJson(original), 'Selected evidence differs from original corpus bytes');
        }
        if (entry.id === 'unknown') assert.equal(context.selected.filter(row => row.record.kind === 'evidence').length, 0);
        const catalogue = await verifyCatalogue(context, contextManifest, report.delivery_bytes);
        const packageRead = await verifyExactRead(context, readContextEvidence, 'package', canonicalJson(context), report.delivery_bytes);
        for (const selected of context.selected.filter(row => row.record.kind === 'evidence').slice(0, 2)) {
          await verifyExactRead(context, readContextEvidence, 'record_text', selected.record.text, report.delivery_bytes, selected.record.id);
        }
        await assert.rejects(() => readContextEvidence(context, { context_id: 'urn:sha256:stale', section: 'package' }), /identity/);
        await assert.rejects(() => readContextEvidence(context, { context_id: context.context_id, section: 'package', offset: -1 }), /offset/);
        await assert.rejects(() => readContextEvidence(context, { context_id: context.context_id, section: 'record_text', record_id: 'urn:unselected' }), /not selected/);
        report.cases.push({ id: `${file}:${entry.id}:${maxBytes}`, manifest_sha256: sha(raw),
          question_sha256: sha(entry.question),
          context_id: context.context_id, evidence_status: context.evidence_status,
          selected_records: context.selected.length, selected_source_records: context.selected.filter(row => row.record.kind === 'evidence').length,
          relationships: context.relationships.length, assembly_bytes: context.budget.used_bytes,
          context_truncated: context.budget.truncated, retrieval_truncated: context.retrieval?.truncated ?? false,
          omission_codes: [...new Set((context.retrieval?.omissions || []).map(row => row.code))].sort(),
          catalogue, package_read: packageRead });
      }
      report.corpora.push({ path: file, sha256: sha(raw), schema: manifest.schema,
        snapshot: manifest.bundle.snapshot, distinct_files_verified: local.files.size,
        accessed_file_ledger_sha256: sha(canonicalJson([...local.files.values()].sort((a, b) => a.path.localeCompare(b.path)))) });
    }
    // The original direct index remains consumable without being relabelled as a current-law answer.
    const directRaw = readFileSync(resolve(ROOT, 'context/discovery/assembly-index.json'));
    const index = validateContextIndex(JSON.parse(directRaw));
    const direct = await assembleContext(index, 'Family membership during hospital admission', {},
      { index_url: `${ORIGIN}/context/discovery/assembly-index.json`, index_sha256: sha(directRaw) });
    assert.equal(direct.evidence_status, 'insufficient');
    assert(direct.selected.some(row => row.record.route === 'page/dmg-vol4-ch24/0025'));
    report.direct_index = { sha256: sha(directRaw), context_id: direct.context_id,
      selected_records: direct.selected.length, evidence_status: direct.evidence_status };
    return report;
  } finally { globalThis.fetch = oldFetch; }
}

async function main() {
  const options = {};
  for (let i = 2; i < process.argv.length; i += 2) {
    const option = process.argv[i];
    assert(['--explorer-root', '--report'].includes(option) && process.argv[i + 1] && !options[option],
      'Usage: --explorer-root PATH [--report NEW_FILE]');
    options[option] = process.argv[i + 1];
  }
  assert(options['--explorer-root'], 'An explicit current Explorer checkout is required');
  const result = await checkCompatibility(options['--explorer-root']);
  if (options['--report']) writeFileSync(resolve(options['--report']), JSON.stringify(result, null, 2) + '\n', { flag: 'wx' });
  process.stdout.write(JSON.stringify(result, null, 2) + '\n');
}
if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) await main();
