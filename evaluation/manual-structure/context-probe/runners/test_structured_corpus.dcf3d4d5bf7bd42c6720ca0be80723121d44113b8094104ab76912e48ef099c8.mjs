#!/usr/bin/env node
/** Offline whole-corpus v3 commitments, followed by two bounded engine controls.
 * Reads every declared shard, never acquires sources or promotes a preview to evidence.
 * Global postings are checked with ordered per-token commitments, not held twice in RAM.
 */
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { existsSync, lstatSync, mkdirSync, readFileSync, realpathSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { gunzipSync } from 'node:zlib';
import { execFileSync } from 'node:child_process';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const options = {};
for (let i = 2; i < process.argv.length; i += 2) {
  const name = process.argv[i];
  assert(['--explorer-root', '--receipt'].includes(name) && process.argv[i + 1] && !options[name], 'Expected --explorer-root and optional --receipt');
  options[name] = process.argv[i + 1];
}
assert(options['--explorer-root'], 'An explicitly pinned Explorer checkout is required');
const sha = value => createHash('sha256').update(value).digest('hex');
const ledger = new Map();
const runnerBytes = readFileSync(fileURLToPath(import.meta.url));
let phase = 'preflight';
const report = { schema: 'okf-dwp-structured-corpus-check.v1', passed: false, network_calls: 0, model_calls: 0, checks: [], limitations: [
  'Checks byte integrity, complete producer commitments and adapter contracts, not relevance, legal applicability or specialist acceptance.',
  'Global validation reads every declared shard offline. Runtime controls retain the normal per-call bounds; this is not a speed benchmark.'
] };
const receipt = options['--receipt'] ? resolve(ROOT, options['--receipt']) : null;
if (receipt) {
  assert(receipt.startsWith(ROOT + '/') && !existsSync(receipt), 'Use a new repository-local receipt path; never replace an earlier attempt');
  mkdirSync(dirname(receipt), { recursive: true });
  assert.equal(realpathSync(dirname(receipt)), dirname(receipt), 'Receipt path must not traverse a symlink');
}
globalThis.fetch = async () => { throw new Error('Network forbidden in structured-corpus checks'); };

function read(relative, expected, maximum = 16 * 1024 * 1024) {
  assert(typeof relative === 'string' && /^[A-Za-z0-9_.-]+(?:\/[A-Za-z0-9_.-]+)*$/.test(relative)
    && !relative.split('/').some(p => p === '.' || p === '..'), 'Unsafe input path');
  const path = resolve(ROOT, relative);
  assert.equal(realpathSync(path), path, 'Input path must not traverse a symlink');
  const stat = lstatSync(path); assert(stat.isFile() && stat.size <= maximum, 'Input type or byte limit');
  const bytes = readFileSync(path);
  const binding = { path: relative, bytes: bytes.length, sha256: sha(bytes) };
  if (expected) { assert.equal(binding.bytes, expected.bytes, relative + ': byte binding'); assert.equal(binding.sha256, expected.sha256, relative + ': hash binding'); }
  const old = ledger.get(relative); assert(!old || old.sha256 === binding.sha256, 'Input changed during validation');
  ledger.set(relative, binding);
  return bytes;
}

try {
  const engineRoot = realpathSync(resolve(options['--explorer-root']));
  const engine = resolve(engineRoot, 'apps/okf-explorer/src/lib/context');
  const approved = JSON.parse(read('evaluation/manual-structure/context-probe/engine.json'));
  for (const file of ['index.ts', 'corpus.ts', 'corpusV3.ts', 'types.ts', 'unit.ts']) {
    assert.match(approved.files[file] || '', /^[a-f0-9]{64}$/, 'Missing runtime module pin');
    assert.equal(sha(readFileSync(resolve(engine, file))), approved.files[file], 'Working engine module differs');
    assert.equal(sha(execFileSync('git', ['-C', engineRoot, 'show', `${approved.commit}:apps/okf-explorer/src/lib/context/${file}`],
      { maxBuffer: 8 * 1024 * 1024 })), approved.files[file], 'Committed engine module differs');
  }
  report.engine = approved;
  const { canonicalJson, validateContextIndex, governanceIssues } = await import(pathToFileURL(resolve(engine, 'index.ts')));
  const { validateContextCorpusManifest, assembleCorpusContext, corpusBucket } = await import(pathToFileURL(resolve(engine, 'corpus.ts')));
  const { discoveryTokens, discoveryText, DISCOVERY_RANKING } = await import(pathToFileURL(resolve(engine, 'corpusV3.ts')));
  const manifestBytes = read('structured-context/manifest.json', undefined, 4 * 1024 * 1024);
  const manifest = validateContextCorpusManifest(JSON.parse(manifestBytes));
  assert.equal(manifest.schema, 'okf-context-corpus.v3');
  assert.deepEqual(manifest.search.ranking, DISCOVERY_RANKING);
  report.manifest = ledger.get('structured-context/manifest.json');
  report.snapshot = manifest.bundle.snapshot;
  const refs = [manifest.base_index, ...manifest.records.shards, ...manifest.discovery.shards,
    ...Object.values(manifest.search.shards), ...Object.values(manifest.relationships.shards)];
  const admitted = new Map(refs.map(ref => [ref.path, ref]));
  assert.equal(admitted.size, refs.length, 'Manifest reference paths must be unique');
  function raw(ref) { return read('structured-context/' + ref.path, ref, ref === manifest.base_index ? 8 * 1024 * 1024 : 4 * 1024 * 1024); }
  function decoded(ref) {
    const transferred = raw(ref);
    const bytes = ref.encoding === 'gzip' ? gunzipSync(transferred, { maxOutputLength: ref.decoded_bytes }) : transferred;
    assert.equal(bytes.length, ref.decoded_bytes || ref.bytes, 'Decoded byte binding');
    assert.equal(sha(bytes), ref.decoded_sha256 || ref.sha256, 'Decoded hash binding');
    return JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(bytes));
  }
  const base = validateContextIndex(decoded(manifest.base_index), manifest.semantic_source_snapshot);
  assert.equal(base.assertions.length, 0);
  assert(base.records.every(r => r.kind === 'concept' || r.kind === 'scope'));
  const shape = { ...base, records: [], assertions: [], requirements: [] };
  const recordIds = new Set(base.records.map(r => r.id)), cardIds = new Set(), evidenceHashes = new Map();
  const expected = new Map(), totals = { source: 0, discovery: 0 };
  let multiPageUnits = 0, spanCount = 0, evidenceTextBytes = 0, sourceSpanBytes = 0, discoveryBytes = 0, firstCard;
  function* cardRows() {
    for (const ref of manifest.discovery.shards) {
      const shard = decoded(ref);
      assert.deepEqual(Object.keys(shard).sort(), ['cards', 'first_ordinal', 'schema']);
      assert.equal(shard.schema, 'okf-discovery-cards.v1'); assert.equal(shard.first_ordinal, ref.first_ordinal);
      assert.equal(shard.cards.length, ref.count);
      yield* shard.cards;
    }
  }
  const cardIterator = cardRows();
  function frequencies(tokens) {
    const result = new Map(); for (const token of tokens) result.set(token, (result.get(token) || 0) + 1); return result;
  }
  phase = 'complete source and discovery commitments';
  let ordinal = 0, previousId = '';
  for (const ref of manifest.records.shards) {
    const shard = decoded(ref);
    assert.deepEqual(Object.keys(shard).sort(), ['first_ordinal', 'records', 'schema']);
    assert.equal(shard.schema, 'okf-context-records.v1'); assert.equal(shard.first_ordinal, ordinal);
    assert.equal(shard.records.length, ref.count);
    assert.equal(shard.records[0].id, ref.first_id); assert.equal(shard.records.at(-1).id, ref.last_id);
    validateContextIndex({ ...shape, records: shard.records });
    for (const record of shard.records) {
      assert(record.id > previousId && !recordIds.has(record.id), 'Evidence order or duplicate identity');
      previousId = record.id; recordIds.add(record.id);
      assert.equal(record.kind, 'evidence'); assert(record.evidence_unit, 'Evidence must remain a complete logical unit');
      const text = Buffer.from(record.text);
      evidenceTextBytes += text.length;
      sourceSpanBytes += record.evidence_unit.spans.reduce((sum, s) => sum + s.source_end - s.source_start, 0);
      for (const p of record.provenance) if (p.literal_sha256) assert.equal(sha(text), p.literal_sha256, 'Record literal integrity');
      for (const span of record.evidence_unit.spans) assert.equal(sha(text.subarray(span.unit_start, span.unit_end)), span.literal_sha256, 'Source span integrity');
      spanCount += record.evidence_unit.spans.length;
      multiPageUnits += Number(new Set(record.evidence_unit.spans.map(s => s.source_url)).size > 1);
      const card = cardIterator.next(); assert(!card.done, 'Missing paired card');
      const c = card.value; firstCard ||= c;
      assert.deepEqual(Object.keys(c).sort(), ['id','evidence_id','evidence_sha256','label','heading_path','summary','search_aliases','assertion_status','authority','scope','provenance','rights','access'].sort());
      assert.match(c.id, /^[a-z][a-z0-9+.-]*:[\x21-\x7e]+$/); assert(c.id.length <= 2000 && !cardIds.has(c.id)); cardIds.add(c.id);
      assert.equal(c.evidence_id, record.id); assert.notEqual(c.id, record.id);
      const recordHash = sha(canonicalJson(record)); evidenceHashes.set(record.id, recordHash);
      assert.equal(c.evidence_sha256, recordHash, 'Card complete-record commitment'); assert.equal(c.access, record.access);
      assert(Array.isArray(c.heading_path) && c.heading_path.length <= 20 && c.heading_path.every(s => typeof s === 'string' && s.length <= 500));
      assert(Array.isArray(c.search_aliases) && c.search_aliases.length <= 100 && c.search_aliases.every(s => typeof s === 'string' && s.length <= 500));
      assert(typeof c.summary === 'string' && c.summary.length <= 2000 && c.assertion_status !== 'official');
      const cardShape = { id: c.id, route: 'discovery/card', label: c.label, kind: 'scope', text: c.summary,
        assertion_status: c.assertion_status, authority: c.authority, scope: c.scope, provenance: c.provenance, rights: c.rights, access: c.access };
      validateContextIndex({ ...shape, records: [cardShape] }); assert.deepEqual(governanceIssues(cardShape), []);
      discoveryBytes += Buffer.byteLength(canonicalJson(c));
      const a = discoveryTokens(record.text), b = discoveryTokens(discoveryText(c));
      totals.source += a.length; totals.discovery += b.length;
      const ac = frequencies(a), bc = frequencies(b);
      for (const token of new Set([...ac.keys(), ...bc.keys()])) {
        let value = expected.get(token);
        if (!value) { value = { hash: createHash('sha256'), count: 0, source_df: 0, discovery_df: 0 }; expected.set(token, value); }
        const row = [ordinal, ac.get(token) || 0, a.length, bc.get(token) || 0, b.length];
        value.hash.update(canonicalJson(row)).update('\n'); value.count++;
        value.source_df += Number(row[1] > 0); value.discovery_df += Number(row[3] > 0);
      }
      ordinal++;
    }
  }
  assert(cardIterator.next().done, 'Unpaired discovery cards'); assert.equal(ordinal, manifest.records.count);
  assert.equal(cardIds.size, manifest.discovery.count);
  assert([...cardIds].every(id => !recordIds.has(id)), 'Discovery identity collides with evidence, scope or concept');
  assert.deepEqual(totals, manifest.search.total_tokens, 'Global BM25 channel token totals');
  report.checks.push({ gate: phase, evidence_records: ordinal, discovery_cards: cardIds.size, multi_page_units: multiPageUnits,
    source_spans: spanCount, evidence_text_bytes_including_declared_joiners: evidenceTextBytes,
    source_span_bytes_excluding_declared_joiners: sourceSpanBytes,
    declared_joiner_bytes: evidenceTextBytes - sourceSpanBytes, card_bytes: discoveryBytes, total_tokens: totals });

  phase = 'global postings and BM25 statistics';
  const seenTokens = new Set(); let postingRows = 0;
  for (const [bucket, ref] of Object.entries(manifest.search.shards)) {
    const shard = decoded(ref);
    assert.deepEqual(Object.keys(shard).sort(), ['postings', 'schema']); assert.equal(shard.schema, 'okf-context-postings.v2');
    for (const [token, rows] of Object.entries(shard.postings)) {
      assert.equal(corpusBucket(token), bucket); assert(!seenTokens.has(token)); seenTokens.add(token);
      const expectedRows = expected.get(token); assert(expectedRows, 'Extraneous posting token');
      const commitment = createHash('sha256'); let last = -1, sourceDf = 0, discoveryDf = 0;
      for (const row of rows) {
        assert(Array.isArray(row) && row.length === 5 && row.every(Number.isSafeInteger) && row.every(v => v >= 0));
        assert(row[0] > last && row[0] < ordinal); last = row[0];
        commitment.update(canonicalJson(row)).update('\n'); sourceDf += Number(row[1] > 0); discoveryDf += Number(row[3] > 0);
      }
      assert.equal(rows.length, expectedRows.count); assert.equal(sourceDf, expectedRows.source_df); assert.equal(discoveryDf, expectedRows.discovery_df);
      assert.equal(commitment.digest('hex'), expectedRows.hash.digest('hex'), 'Global postings differ from exact source/discovery channel text');
      postingRows += rows.length;
    }
  }
  assert.equal(seenTokens.size, expected.size, 'Missing posting tokens');
  report.checks.push({ gate: phase, distinct_tokens: seenTokens.size, posting_rows: postingRows, ranking: manifest.search.ranking });
  expected.clear();

  phase = 'complete directed adjacency commitments';
  const incidentIds = new Set(), edgeCopies = new Map();
  for (const [bucket, ref] of Object.entries(manifest.relationships.shards)) {
    const shard = decoded(ref); assert.deepEqual(Object.keys(shard).sort(), ['entries', 'schema']);
    assert.equal(shard.schema, 'okf-context-adjacency-bucket.v1'); assert(shard.entries.length <= 10000);
    let previous = '';
    for (const entry of shard.entries) {
      assert.deepEqual(Object.keys(entry).sort(), ['id','outgoing','incoming','outgoing_count','incoming_count','outgoing_ids_sha256','incoming_ids_sha256'].sort());
      assert(entry.id > previous && recordIds.has(entry.id) && !incidentIds.has(entry.id)); previous = entry.id;
      assert.equal(corpusBucket(entry.id), bucket); incidentIds.add(entry.id);
      for (const direction of ['outgoing', 'incoming']) {
        const edges = entry[direction]; validateContextIndex({ ...shape, assertions: edges });
        assert.equal(edges.length, entry[direction + '_count']);
        assert.equal(sha(canonicalJson(edges.map(e => e.id))), entry[direction + '_ids_sha256']);
        let last = '';
        for (const edge of edges) {
          assert(edge.id > last); last = edge.id;
          assert.equal(edge[direction === 'outgoing' ? 'source' : 'target'], entry.id);
          assert(recordIds.has(edge.source) && recordIds.has(edge.target), 'Graph has an unbound endpoint');
          const value = edgeCopies.get(edge.id) || { sha256: sha(canonicalJson(edge)), outgoing: 0, incoming: 0 };
          assert.equal(value.sha256, sha(canonicalJson(edge)), 'Incident copies differ in scope, provenance or other content');
          value[direction]++; edgeCopies.set(edge.id, value);
        }
      }
    }
  }
  assert.equal(incidentIds.size, recordIds.size, 'Missing empty or non-empty incident entries');
  for (const copies of edgeCopies.values()) assert(copies.outgoing === 1 && copies.incoming === 1, 'One-sided or duplicated graph edge');
  report.checks.push({ gate: phase, incident_records: incidentIds.size, assertions: edgeCopies.size });

  phase = 'bounded runtime adapter controls';
  const binding = { index_url: `https://example.test/frozen-${sha(manifestBytes)}/manifest.json`, index_sha256: sha(manifestBytes) };
  const urlRoot = new URL('.', binding.index_url);
  const fetcher = async url => {
    const u = new URL(String(url)); assert.equal(u.origin, urlRoot.origin); assert(u.href.startsWith(urlRoot.href));
    const ref = admitted.get(u.href.slice(urlRoot.href.length)); assert(ref, 'Runtime requested an undeclared file');
    return new Response(raw(ref));
  };
  report.runtime = [];
  for (const [kind, question] of [['source-label-smoke', firstCard.label], ['unknown-negative', 'xylophonicquasarteleportation']]) {
    const pack = await assembleCorpusContext(manifest, binding, question, { max_bytes: 524288 }, fetcher);
    const bytes = Buffer.from(canonicalJson(pack)); assert.equal(bytes.length, pack.budget.used_bytes); assert(bytes.length <= 524288);
    assert.equal(pack.ai_answer, null);
    assert(pack.resolved_concepts.every(c => base.records.some(r => r.kind === 'concept' && r.id === c.id)), 'Discovery card was resolved as a concept');
    for (const item of pack.selected) {
      assert(!cardIds.has(item.record.id), 'Discovery card was supplied as evidence');
      if (item.record.kind === 'evidence') assert.equal(sha(canonicalJson(item.record)), evidenceHashes.get(item.record.id), 'Selected evidence was summarised or altered');
    }
    if (kind === 'unknown-negative') { assert.equal(pack.selected.filter(s => s.record.kind === 'evidence').length, 0); assert.equal(pack.evidence_status, 'insufficient'); }
    else assert(pack.selected.some(s => s.record.kind === 'evidence'), 'Positive adapter control retained no source evidence');
    report.runtime.push({ kind, question, context_id: pack.context_id, package_sha256: sha(bytes), bytes: bytes.length,
      selected_source_units: pack.selected.filter(s => s.record.kind === 'evidence').length, evidence_status: pack.evidence_status,
      retrieval_truncated: pack.retrieval?.truncated, assembly_truncated: pack.budget.truncated });
  }
  report.checks.push({ gate: phase, cases: report.runtime.length });
  phase = 'end-of-run immutable input recheck';
  for (const ref of [...ledger.values()]) read(ref.path, ref);
  for (const [file, hash] of Object.entries(approved.files)) assert.equal(sha(readFileSync(resolve(engine, file))), hash, 'Engine changed during validation');
  assert.equal(sha(readFileSync(fileURLToPath(import.meta.url))), sha(runnerBytes), 'Validator changed during execution');
  report.checks.push({ gate: phase, inputs: ledger.size, engine_modules: Object.keys(approved.files).length });
  report.passed = true;
} catch (error) {
  report.failure = { phase, message: error instanceof Error ? error.message : String(error) };
  process.exitCode = 1;
} finally {
  report.inputs = [...ledger.values()].sort((a, b) => a.path < b.path ? -1 : a.path > b.path ? 1 : 0);
  report.runner_sha256 = sha(runnerBytes);
  const bytes = JSON.stringify(report, null, 2) + '\n';
  if (receipt) writeFileSync(receipt, bytes, { flag: 'wx' });
  console.log(bytes);
}
