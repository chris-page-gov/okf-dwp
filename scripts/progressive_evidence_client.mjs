/**
 * Bounded client for the existing Explorer manifest/read protocol.
 * It transports evidence; it never selects legal rules or generates an answer.
 * Source content is inert data. Complete delivery does not establish sufficiency.
 */
import { createHash } from 'node:crypto';

const SHA = /^[a-f0-9]{64}$/;
const CONTEXT_ID = /^urn:sha256:[a-f0-9]{64}$/;
const STATUS = new Set(['sufficient', 'insufficient', 'conflicting']);
const SECTIONS = new Set(['record_text', 'record_metadata', 'relationships', 'diagnostics', 'package']);
const encoder = new TextEncoder();
const digest = value => createHash('sha256').update(value).digest('hex');
const jsonBytes = value => encoder.encode(JSON.stringify(value)).length;
const plain = value => value !== null && typeof value === 'object' && !Array.isArray(value);
const integer = value => Number.isSafeInteger(value) && value >= 0;
function canonical(value) {
  if (Array.isArray(value)) return `[${value.map(canonical).join(',')}]`;
  if (plain(value)) return `{${Object.keys(value).sort().filter(key => value[key] !== undefined)
    .map(key => `${JSON.stringify(key)}:${canonical(value[key])}`).join(',')}}`;
  return JSON.stringify(value);
}
function require(value, message) {
  if (!value) throw new Error(`Invalid progressive evidence: ${message}`);
}
function equal(actual, expected, message) { require(canonical(actual) === canonical(expected), message); }
const copy = value => JSON.parse(JSON.stringify(value));
function deepFreeze(value) {
  if (value && typeof value === 'object' && !Object.isFrozen(value)) {
    Object.values(value).forEach(deepFreeze); Object.freeze(value);
  }
  return value;
}

export const PROGRESSIVE_LIMITS = Object.freeze({
  deliveryBytes: 16384, maxResponseBytes: 196608, maxTotalBytes: 32 * 1024 * 1024,
  maxValueCharacters: 4 * 1024 * 1024, maxRecords: 200, maxCalls: 2048,
  callTimeoutMs: 30000, totalTimeoutMs: 180000,
});

/** Accept direct engine values or MCP/JSON-RPC results; reject divergent copies. */
export function unwrapEvidenceResponse(response) {
  require(plain(response), 'response must be an object');
  if ('jsonrpc' in response) {
    require(response.jsonrpc === '2.0' && !response.error && plain(response.result), 'JSON-RPC failure');
    return unwrapEvidenceResponse(response.result);
  }
  if ('structuredContent' in response || 'content' in response || 'isError' in response) {
    require(!response.isError && Array.isArray(response.content), 'MCP tool failed');
    const texts = response.content.filter(item => item?.type === 'text');
    require(texts.length === 1 && typeof texts[0].text === 'string', 'expected one compact text copy');
    let text;
    try { text = JSON.parse(texts[0].text); } catch { throw new Error('Invalid progressive evidence: malformed MCP text'); }
    require(plain(text), 'MCP text must contain an object');
    if ('structuredContent' in response) equal(response.structuredContent, text, 'MCP text and structured copies differ');
    return response.structuredContent ?? text;
  }
  return response;
}

function replayIdentity(value) {
  if (value === undefined) return null;
  require(plain(value) && typeof value.engine_id === 'string' && value.engine_id.length > 0
    && SHA.test(value.package_sha256), 'malformed replay identity');
  require(['current-default', 'explicit-engine', 'historical-compatible'].includes(value.mode), 'unknown replay mode');
  require(value.original_engine_id === null || typeof value.original_engine_id === 'string', 'invalid original engine');
  require(Array.isArray(value.matching_engine_ids) && value.matching_engine_ids.length >= 1
    && value.matching_engine_ids.length <= 2 && value.matching_engine_ids.includes(value.engine_id)
    && new Set(value.matching_engine_ids).size === value.matching_engine_ids.length, 'invalid matching engines');
  return { engine_id: value.engine_id, package_sha256: value.package_sha256 };
}

function manifestIdentity(value) {
  return { context_id: value.context_id, question: value.question, bundle: value.bundle,
    binding: value.binding, evidence_status: value.evidence_status, summary: value.summary,
    replay: value.replay ?? null, replay_identity: replayIdentity(value.replay_identity) };
}

function checkManifest(value, request, limits) {
  require(value.schema === 'okf-context-manifest.v1' && CONTEXT_ID.test(value.context_id), 'invalid catalogue schema or context');
  require(value.question === request.question && STATUS.has(value.evidence_status), 'question or evidence status differs');
  require(plain(value.bundle) && ['id', 'snapshot', 'source_url'].every(k => typeof value.bundle[k] === 'string'), 'invalid bundle identity');
  require(plain(value.binding) && typeof value.binding.index_url === 'string' && SHA.test(value.binding.index_sha256), 'invalid source binding');
  if (request.context_id) require(value.context_id === request.context_id, 'catalogue context changed');
  require(plain(value.summary) && value.summary.ai_answer === null, 'catalogue supplied an answer');
  for (const name of ['selected_records', 'relationships', 'full_package_bytes', 'resolved_concepts', 'ambiguities',
    'unresolved_terms', 'missing_evidence', 'conflicts', 'requirements']) require(integer(value.summary[name]), `invalid summary ${name}`);
  require(typeof value.summary.context_truncated === 'boolean' && typeof value.summary.retrieval_truncated === 'boolean'
    && Array.isArray(value.summary.missing_evidence_codes) && value.summary.missing_evidence_codes.every(x => typeof x === 'string'), 'invalid truncation summary');
  const page = value.delivery;
  require(plain(page) && integer(page.offset) && integer(page.returned) && integer(page.total)
    && page.offset === request.offset && page.total <= limits.maxRecords
    && page.total === value.summary.selected_records && Array.isArray(value.records)
    && page.returned === value.records.length && page.offset + page.returned <= page.total, 'invalid catalogue pagination');
  const next = page.offset + page.returned;
  require(page.next_offset === (next < page.total ? next : null)
    && (page.next_offset === null || page.next_offset > page.offset), 'catalogue continuation makes no progress');
  const bytes = jsonBytes(value);
  require(integer(page.max_bytes) && page.max_bytes <= request.delivery_bytes && integer(page.used_bytes)
    && page.used_bytes <= page.max_bytes && page.used_bytes <= bytes && bytes <= request.delivery_bytes, 'catalogue byte limit differs');
  if ('response_bytes' in value) {
    require(value.response_bytes === bytes && value.response_limit === request.delivery_bytes, 'remote catalogue byte accounting differs');
  } else require(page.used_bytes === bytes, 'local catalogue byte accounting differs');
  for (const record of value.records) {
    require(plain(record) && typeof record.id === 'string' && record.id.length > 0
      && ['concept', 'evidence', 'scope'].includes(record.kind) && typeof record.label === 'string'
      && ['official', 'normalized', 'inferred', 'model-derived'].includes(record.assertion_status)
      && integer(record.text_characters) && record.text_characters <= limits.maxValueCharacters
      && SHA.test(record.text_sha256) && typeof record.source_url === 'string' && typeof record.source_locator === 'string'
      && typeof record.authority_class === 'string' && typeof record.review_status === 'string'
      && integer(record.reasons) && integer(record.paths), 'invalid catalogue record');
  }
  if (value.replay !== undefined) {
    const replay = value.replay;
    // The public service allowlist name (e.g. okf-dwp) is distinct from the
    // semantic bundle IRI in the assembled package. Pin both independently.
    require(plain(replay) && Object.keys(replay).sort().join(',') === 'budget,bundle,engine_id,version'
      && typeof replay.bundle === 'string' && replay.bundle.length > 0 && typeof replay.version === 'string'
      && typeof replay.engine_id === 'string' && plain(replay.budget)
      && Object.keys(replay.budget).sort().join(',') === 'max_bytes,max_depth,max_nodes,max_relationships'
      && ['max_bytes', 'max_nodes', 'max_depth', 'max_relationships'].every(k => integer(replay.budget[k])), 'invalid remote replay recipe');
    if (request.version !== undefined) require(replay.version === request.version, 'source version changed');
    if (request.engine_id !== undefined) require(replay.engine_id === request.engine_id, 'engine changed');
    if (request.bundle !== undefined) require(replay.bundle === request.bundle, 'bundle changed');
    for (const [key, expected] of Object.entries(request.budget ?? {})) require(replay.budget[key] === expected, `replay budget changed: ${key}`);
    require(replayIdentity(value.replay_identity)?.engine_id === replay.engine_id, 'replay engine is unbound');
  } else require(value.replay_identity === undefined, 'replay identity has no recipe');
}

/**
 * Create a verified session. The caller owns the read-only transport and writes
 * returned data to an artefact; print summary(), not the entire data, in chat.
 * A transport may honour the additional AbortSignal argument to cancel I/O.
 */
export async function createEvidenceSession({ transport, request, limits: supplied = {} }) {
  require(plain(transport) && typeof transport.manifest === 'function' && typeof transport.read === 'function', 'invalid transport');
  require(plain(request) && typeof request.question === 'string' && request.question.trim().length > 0, 'question required');
  require(Object.keys(supplied).every(k => k in PROGRESSIVE_LIMITS), 'unknown client limit');
  const limits = { ...PROGRESSIVE_LIMITS, ...supplied };
  require(Object.values(limits).every(value => integer(value) && value > 0), 'client limits must be positive integers');
  require(limits.deliveryBytes >= 8192 && limits.deliveryBytes <= 65536, 'delivery bytes outside protocol range');
  const started = performance.now();
  const stats = { calls: 0, response_bytes: 0, max_response_bytes: 0, max_value_json_bytes: 0,
    manifest_pages: 0, completed_values: 0, slices: 0 };
  const receiptCalls = [];
  const invoke = async (method, args) => {
    require(stats.calls < limits.maxCalls, 'call allowance exhausted');
    const remaining = limits.totalTimeoutMs - (performance.now() - started);
    require(remaining > 0, 'session deadline exceeded');
    stats.calls++;
    const controller = new AbortController();
    let timer;
    const call = Promise.resolve().then(() => transport[method](copy(args), controller.signal));
    const timeout = new Promise((_, reject) => { timer = setTimeout(() => {
      controller.abort(); reject(new Error('Invalid progressive evidence: transport deadline exceeded'));
    }, Math.min(limits.callTimeoutMs, remaining)); });
    let response;
    try { response = await Promise.race([call, timeout]); } finally { clearTimeout(timer); }
    require(performance.now() - started < limits.totalTimeoutMs, 'session deadline exceeded');
    const bytes = jsonBytes(response);
    require(bytes <= limits.maxResponseBytes, 'transport response exceeds allowance');
    stats.response_bytes += bytes;
    require(stats.response_bytes <= limits.maxTotalBytes, 'total response allowance exhausted');
    stats.max_response_bytes = Math.max(stats.max_response_bytes, bytes);
    const value = unwrapEvidenceResponse(response);
    stats.max_value_json_bytes = Math.max(stats.max_value_json_bytes, jsonBytes(value));
    receiptCalls.push({ method, section: args.section ?? null, record_id: args.record_id ?? null,
      offset: args.offset, response_bytes: bytes, value_sha256: digest(canonical(value)) });
    return value;
  };
  let recipe = copy(request);
  delete recipe.offset; delete recipe.delivery_bytes;
  const records = [];
  let first;
  let offset = 0;
  do {
    const args = { ...recipe, offset, delivery_bytes: limits.deliveryBytes };
    const page = await invoke('manifest', args);
    checkManifest(page, args, limits);
    if (!first) {
      first = copy(page);
      recipe = { ...recipe, ...(page.replay ?? {}), context_id: page.context_id };
    } else equal(manifestIdentity(page), manifestIdentity(first), 'catalogue identity or summary changed');
    for (const record of page.records) {
      require(!records.some(item => item.id === record.id), 'duplicate catalogue record');
      records.push(copy(record));
    }
    stats.manifest_pages++;
    offset = page.delivery.next_offset;
  } while (offset !== null);
  require(records.length === first.summary.selected_records, 'catalogue is incomplete');
  deepFreeze(first); deepFreeze(records); deepFreeze(recipe);
  // This is a client aggregation, not one fictitious oversized protocol page.
  const catalogue = deepFreeze({ schema: 'okf-progressive-catalogue.v1', ...manifestIdentity(first),
    records, source_manifest_pages: stats.manifest_pages });
  const byId = new Map(records.map(record => [record.id, record]));
  const boundReplay = replayIdentity(first.replay_identity);

  async function readValue(section, recordId) {
    require(SECTIONS.has(section), 'unsupported section');
    const recordSection = section === 'record_text' || section === 'record_metadata';
    require(recordSection ? byId.has(recordId) : recordId === undefined, 'record does not belong to verified context');
    const parts = [];
    let identity;
    let offset = 0;
    do {
      const args = { ...recipe, section, ...(recordSection ? { record_id: recordId } : {}),
        offset, delivery_bytes: limits.deliveryBytes };
      const value = await invoke('read', args);
      require(value.schema === 'okf-context-read.v1' && value.context_id === first.context_id
        && value.evidence_status === first.evidence_status && value.ai_answer === null, 'read context or evidence status changed');
      require(value.section === section && value.record_id === (recordId ?? null)
        && value.media_type === (section === 'record_text' ? 'text/plain' : 'application/json')
        && value.character_unit === 'utf-16-code-units', 'read section or character unit differs');
      require(value.context_truncated === first.summary.context_truncated
        && value.retrieval_truncated === first.summary.retrieval_truncated, 'read truncation flags changed');
      equal(replayIdentity(value.replay_identity), boundReplay, 'read replay identity changed');
      require(SHA.test(value.content_sha256) && integer(value.total_characters)
        && value.total_characters <= limits.maxValueCharacters && value.offset === offset
        && integer(value.end_offset) && value.end_offset <= value.total_characters
        && typeof value.data === 'string' && value.end_offset === offset + value.data.length
        && (value.end_offset > offset || offset === value.total_characters), 'read range makes no progress or exceeds allowance');
      require(value.next_offset === (value.end_offset < value.total_characters ? value.end_offset : null), 'read continuation differs');
      require(!/^[\uDC00-\uDFFF]/.test(value.data) && !/[\uD800-\uDBFF]$/.test(value.data), 'read splits a Unicode character');
      const bytes = jsonBytes(value);
      require(plain(value.delivery) && value.delivery.max_bytes === limits.deliveryBytes
        && value.delivery.used_bytes === bytes && bytes <= limits.deliveryBytes
        && value.delivery.partial === (offset > 0 || value.end_offset < value.total_characters), 'read byte accounting differs');
      const nextIdentity = { content_sha256: value.content_sha256, total_characters: value.total_characters };
      if (!identity) identity = nextIdentity;
      else equal(nextIdentity, identity, 'read content identity changed');
      parts.push(value.data); stats.slices++;
      offset = value.next_offset;
    } while (offset !== null);
    const text = parts.join('');
    require(text.length === identity.total_characters && digest(text) === identity.content_sha256, 'complete value hash differs');
    stats.completed_values++;
    return { text, content_sha256: identity.content_sha256, characters: text.length, slices: parts.length };
  }

  function summary() {
    return { schema: 'okf-progressive-evidence-summary.v1', question: first.question, context_id: first.context_id,
      evidence_status: first.evidence_status, context_truncated: first.summary.context_truncated,
      retrieval_truncated: first.summary.retrieval_truncated, selected_records: records.length,
      integrity_scope: 'catalogue-self-consistency', metadata_bound_to_context: false,
      selected_source_records: records.filter(row => row.kind === 'evidence').length,
      missing_evidence_codes: copy(first.summary.missing_evidence_codes),
      replay: copy(first.replay ?? null), binding: copy(first.binding), delivery: copy(stats), ai_answer: null,
      limitation: 'Verified delivery preserves the assembled package; missing source selection, legal applicability and specialist review remain unresolved.' };
  }

  function checkDiagnostics(diagnostics) {
    require(plain(diagnostics), 'diagnostics must be an object');
    for (const key of ['context_id', 'question', 'bundle', 'binding', 'evidence_status'])
      equal(diagnostics[key], first[key], `diagnostic ${key} differs`);
    require(diagnostics.ai_answer === null && diagnostics.selected_records === records.length
      && diagnostics.relationship_count === first.summary.relationships
      && diagnostics.budget?.truncated === first.summary.context_truncated
      && (diagnostics.retrieval?.truncated ?? false) === first.summary.retrieval_truncated, 'diagnostic evidence boundary changed');
    for (const key of ['resolved_concepts', 'ambiguities', 'unresolved_terms', 'missing_evidence', 'conflicts', 'requirements'])
      require(Array.isArray(diagnostics[key]) && diagnostics[key].length === first.summary[key], `diagnostic ${key} count differs`);
    equal([...new Set(diagnostics.missing_evidence.map(row => row.code))].sort(), first.summary.missing_evidence_codes,
      'diagnostic missing-evidence codes differ');
  }

  function checkCard(metadata, card) {
    require(plain(metadata) && plain(metadata.record) && metadata.record.id === card.id, 'record metadata identity differs');
    const record = metadata.record;
    for (const key of ['label', 'kind', 'assertion_status']) equal(record[key], card[key], `record ${key} differs`);
    require(record.authority?.class === card.authority_class
      && (record.review_status ?? 'not-declared') === card.review_status
      && Array.isArray(record.provenance) && (record.provenance[0]?.url ?? '') === card.source_url
      && (record.provenance[0]?.locator ?? '') === card.source_locator
      && Array.isArray(metadata.reasons) && metadata.reasons.length === card.reasons
      && Array.isArray(metadata.paths) && metadata.paths.length === card.paths, 'record provenance or selection differs');
  }

  function verifyPackage(context) {
    require(plain(context) && context.schema === 'okf-governed-context.v1'
      && Array.isArray(context.selected) && context.selected.length === records.length
      && Array.isArray(context.relationships) && context.relationships.length === first.summary.relationships,
    'invalid reconstructed package');
    const { selected, relationships, ...originalDiagnostics } = context;
    checkDiagnostics({ ...originalDiagnostics, selected_records: selected.length, relationship_count: relationships.length });
    for (let index = 0; index < records.length; index++) {
      const selectedRecord = selected[index]; const card = records[index];
      checkCard(selectedRecord, card);
      require(typeof selectedRecord.record.text === 'string'
        && selectedRecord.record.text.length === card.text_characters
        && digest(selectedRecord.record.text) === card.text_sha256, 'package record text differs from catalogue');
    }
    const packageHash = digest(canonical(context));
    if (boundReplay) require(packageHash === boundReplay.package_sha256, 'reconstructed package hash differs from replay identity');
    require(jsonBytes(context) === first.summary.full_package_bytes, 'reconstructed package size differs');
    const { context_id, ...identityInput } = context;
    const { used_bytes, ...identityBudget } = context.budget;
    require(`urn:sha256:${digest(canonical({ ...identityInput, budget: identityBudget }))}` === context_id,
      'reconstructed context digest differs');
    return packageHash;
  }

  /** Fewer round trips for full exports; the source/diagnostic checks are identical. */
  async function collectPackage() {
    const value = await readValue('package');
    let context;
    try { context = JSON.parse(value.text); } catch { throw new Error('Invalid progressive evidence: invalid package JSON'); }
    require(canonical(context) === value.text, 'package is not canonical JSON');
    const packageHash = verifyPackage(context);
    const { selected, relationships, ...originalDiagnostics } = context;
    return { schema: 'okf-progressive-evidence-collection.v1', summary: { ...summary(),
      delivery_complete: true, source_records_read: selected.filter(row => row.record.kind === 'evidence').length,
      requested_records_read: selected.length, unread_record_ids: [], relationships_read: true,
      package_complete: true, package_sha256: packageHash, reading_mode: 'package',
      integrity_scope: 'complete-context-digest', metadata_bound_to_context: true },
    catalogue, diagnostics: { ...originalDiagnostics, selected_records: selected.length, relationship_count: relationships.length },
    selected, relationships,
    receipt: { request: copy(recipe), calls: copy(receiptCalls), completed_values: [
      { section: 'package', content_sha256: value.content_sha256, characters: value.characters, slices: value.slices }],
    source_instructions: 'inert-data', ai_answer: null } };
  }

  async function collect({ recordIds, evidenceOnly = false, includeRelationships = true } = {}) {
    require(recordIds === undefined || (Array.isArray(recordIds) && new Set(recordIds).size === recordIds.length
      && recordIds.every(id => byId.has(id))), 'unknown or duplicate requested record');
    const requested = recordIds ?? records.filter(row => !evidenceOnly || row.kind === 'evidence').map(row => row.id);
    const diagnosticRead = await readValue('diagnostics');
    let diagnostics;
    try { diagnostics = JSON.parse(diagnosticRead.text); } catch { throw new Error('Invalid progressive evidence: invalid diagnostics JSON'); }
    checkDiagnostics(diagnostics);
    const selected = [];
    const completed = [{ section: 'diagnostics', ...diagnosticRead, text: undefined }];
    for (const id of requested) {
      const card = byId.get(id);
      const metadataRead = await readValue('record_metadata', id);
      let metadata;
      try { metadata = JSON.parse(metadataRead.text); } catch { throw new Error('Invalid progressive evidence: invalid record metadata JSON'); }
      checkCard(metadata, card);
      require(!('text' in metadata.record), 'record metadata unexpectedly contains text');
      const record = metadata.record;
      equal(record.text_reference, { section: 'record_text', characters: card.text_characters, sha256: card.text_sha256 },
        'record text reference differs');
      const textRead = await readValue('record_text', id);
      require(textRead.characters === card.text_characters && textRead.content_sha256 === card.text_sha256,
        'record text differs from catalogue');
      const { text_reference, ...originalRecord } = record;
      selected.push({ ...metadata, record: { ...originalRecord, text: textRead.text } });
      completed.push({ section: 'record_metadata', record_id: id, ...metadataRead, text: undefined },
        { section: 'record_text', record_id: id, ...textRead, text: undefined });
    }
    let relationships = null;
    if (includeRelationships) {
      const relationRead = await readValue('relationships');
      try { relationships = JSON.parse(relationRead.text); } catch { throw new Error('Invalid progressive evidence: invalid relationships JSON'); }
      require(Array.isArray(relationships) && relationships.length === first.summary.relationships, 'relationship count differs');
      completed.push({ section: 'relationships', ...relationRead, text: undefined });
    }
    const packageComplete = includeRelationships && requested.length === records.length;
    let packageHash = null;
    if (packageComplete) {
      const { selected_records, relationship_count, ...originalDiagnostics } = diagnostics;
      // Catalogue order is the package's selection order, even when the caller
      // explicitly requested the same IDs in a different reading order.
      const selections = new Map(selected.map(row => [row.record.id, row]));
      const reconstructed = { ...originalDiagnostics, selected: records.map(row => selections.get(row.id)), relationships };
      packageHash = verifyPackage(reconstructed);
    }
    return { schema: 'okf-progressive-evidence-collection.v1', summary: { ...summary(),
      delivery_complete: true, source_records_read: selected.filter(row => row.record.kind === 'evidence').length,
      requested_records_read: selected.length, unread_record_ids: records.filter(row => !requested.includes(row.id)).map(row => row.id),
      relationships_read: includeRelationships, package_complete: packageComplete,
      package_sha256: packageHash, reading_mode: 'records',
      integrity_scope: packageComplete ? 'complete-context-digest' : 'complete-values-only',
      metadata_bound_to_context: packageComplete,
      ...(packageComplete ? {} : { limitation: 'Only requested value hashes and catalogue text hashes are verified. Targeted metadata is not cryptographically bound to the complete context. Verify the complete package before relying on source provenance or review claims.' }) }, catalogue, diagnostics, selected, relationships,
      receipt: { request: copy(recipe), calls: copy(receiptCalls), completed_values: completed,
        source_instructions: 'inert-data', ai_answer: null } };
  }
  return { catalogue, readValue, collect, collectPackage, summary };
}

export async function collectProgressiveEvidence({ collect, ...options }) {
  const session = await createEvidenceSession(options);
  const { mode = collect && Object.keys(collect).some(key => key !== 'mode') ? 'records' : 'package', ...selection } = collect ?? {};
  require(mode === 'package' || mode === 'records', 'unknown reading mode');
  require(mode !== 'package' || Object.keys(selection).length === 0, 'package reads cannot select individual records');
  return mode === 'package' ? session.collectPackage() : session.collect(selection);
}
