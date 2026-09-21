#!/usr/bin/env node
/** Offline 2×2 source/engine experiment. No source edits, model calls or public retrieval. */
import assert from 'node:assert/strict';
import { mkdir, writeFile, realpath } from 'node:fs/promises';
import { fileURLToPath, pathToFileURL } from 'node:url';
import path from 'node:path';
import { pathRetained, requirementCensus } from './metrics.mjs';
import { FILES, sha, exactFields, safeName, safeDirectory, boundedAt, fromGit, exactTree, admitEngines } from './guards.mjs';
const here = path.dirname(fileURLToPath(import.meta.url));
const flags = {};
for (let i = 2; i < process.argv.length; i++) {
  const key = process.argv[i]; assert(['--dwp-root', '--explorer-root', '--output', '--check'].includes(key) && !(key in flags), 'Unknown or duplicate flag');
  flags[key] = process.argv[++i]; assert(flags[key], 'Missing flag value');
}
assert(flags['--dwp-root'] && flags['--explorer-root'] && Boolean(flags['--output']) !== Boolean(flags['--check']), 'Supply both checkouts and exactly one fresh output or retained check');
const protocolRaw = await boundedAt(here, 'protocol.json', 32768), protocol = JSON.parse(protocolRaw);
exactFields(protocol, ['schema', 'status', 'old_dwp_commit', 'new_dwp_commit', 'new_index_sha256', 'baseline_explorer_commit', 'candidate_explorer_commit', 'engine_sha256', 'budgets', 'case_occurrences', 'focus_cases', 'household_routes', 'expected_open_obligations', 'limitations']);
assert.equal(protocol.schema, 'okf-qualification-context-protocol.v1');
assert.equal(protocol.status, 'ready-for-frozen-source-comparison', 'Protocol awaits final source approval');
assert.equal(protocol.old_dwp_commit, '3ef0e786e9a18e76fa17c7d925ff509d6d6c9f84');
assert.equal(protocol.baseline_explorer_commit, 'b9a3b68b6dbf222f9a73cc8f450dd53f126e1b55');
assert(/^[a-f0-9]{40}$/.test(protocol.candidate_explorer_commit) && /^[a-f0-9]{64}$/.test(protocol.new_index_sha256));
assert(/^[a-f0-9]{40}$/.test(protocol.new_dwp_commit) && protocol.new_dwp_commit !== protocol.old_dwp_commit);
assert.deepEqual(protocol.budgets, [262144, 524288]); assert.equal(protocol.case_occurrences, 40);
assert.equal(protocol.expected_open_obligations, 203); assert.deepEqual(protocol.focus_cases, ['staff-012', 'staff-013']);
assert.deepEqual(protocol.household_routes, ['page/77/0007','page/77/0019','page/77/0021','page/77/0023','page/77/0024','page/77/0025','page/78/0025']);
const checking = Boolean(flags['--check']), output = path.resolve(flags['--check'] || flags['--output']);
await safeDirectory(path.dirname(output)); if (!checking) await mkdir(output); await safeDirectory(output);
const prior = checking ? JSON.parse(await boundedAt(output, 'comparison.json', 32 * 1024 * 1024)) : null;
const sourceFiles = ['protocol.json', 'compare.mjs', 'guards.mjs', 'metrics.mjs'];
const archivedFiles = [...sourceFiles, ...['baseline', 'candidate'].flatMap(s => FILES.map(n => `engines/${s}/${n}`))];
if (checking) {
  exactFields(prior, ['schema', 'started_at', 'completed_at', 'runtime', 'inputs', 'source_census', 'summary', 'observations', 'limitations']);
  assert.equal(prior.schema, 'okf-qualification-context-comparison.v1');
  exactFields(prior.inputs, ['protocol_sha256', 'runner_sha256', 'guards_sha256', 'metrics_sha256', 'engine_sha256', 'sources']);
  assert.equal(prior.inputs.protocol_sha256, sha(protocolRaw)); assert.deepEqual(prior.inputs.engine_sha256, protocol.engine_sha256);
  assert(Array.isArray(prior.observations) && prior.observations.length === 160 && Array.isArray(prior.summary) && prior.summary.length === 4, 'Wrong observation census');
  await exactTree(output, [...archivedFiles, 'comparison.json']);
}
const hashes = {};
for (const name of sourceFiles) {
  const raw = await boundedAt(here, name, 1024 * 1024); hashes[name] = sha(raw);
  if (checking) assert.deepEqual(await boundedAt(output, name, 1024 * 1024), raw, 'Runner/protocol/helper archive mismatch');
  else await writeFile(path.join(output, name), raw, { flag: 'wx' });
}
if (checking) { assert.equal(prior.inputs.runner_sha256, hashes['compare.mjs']); assert.equal(prior.inputs.guards_sha256, hashes['guards.mjs']); assert.equal(prior.inputs.metrics_sha256, hashes['metrics.mjs']); }
await admitEngines(here, protocol.engine_sha256);
const dwp = await realpath(flags['--dwp-root']), explorer = await realpath(flags['--explorer-root']);
for (const stage of ['baseline', 'candidate']) for (const name of FILES) {
  const raw = await boundedAt(here, `engines/${stage}/${name}`, 2 * 1024 * 1024);
  assert.deepEqual(raw, fromGit(explorer, protocol[stage + '_explorer_commit'], 'apps/okf-explorer/src/lib/context/' + name, 2 * 1024 * 1024), 'Engine differs from immutable commit');
  if (!checking) { await mkdir(path.join(output, 'engines', stage), { recursive: true }); await writeFile(path.join(output, 'engines', stage, name), raw, { flag: 'wx' }); }
}
// Exact reviewed hashes, helper identity, archive allowlist and baseline Git proof precede all archived engine imports.
await admitEngines(output, protocol.engine_sha256);
const engines = {}, cores = {};
for (const stage of ['baseline', 'candidate']) {
  engines[stage] = await import(pathToFileURL(path.join(output, 'engines', stage, 'corpus.ts')));
  cores[stage] = await import(pathToFileURL(path.join(output, 'engines', stage, 'index.ts')));
}
const { canonicalJson } = await import(pathToFileURL(path.join(output, 'engines/baseline/index.ts')));
const sources = {}, inputSources = {}, sourceCensus = {};
for (const [stage, commit] of [['old', protocol.old_dwp_commit], ['new', protocol.new_dwp_commit]]) {
  const bindings = [];
  function input(name) { const raw = fromGit(dwp, commit, name); bindings.push({ path: name, bytes: raw.length, sha256: sha(raw) }); return raw; }
  const indexRaw = input('evaluation/semantic-expansion/assembly-index.json');
  if (stage === 'new') assert.equal(sha(indexRaw), protocol.new_index_sha256, 'Final source index digest mismatch');
  const corpusRaw = input('context/corpus/manifest.json');
  const casesRaw = input('evaluation/staff-questions/cases.json');
  const index = JSON.parse(indexRaw), original = JSON.parse(corpusRaw), registry = JSON.parse(casesRaw);
  assert.equal(registry.cases.length, protocol.case_occurrences);
  assert.equal(new Set(registry.cases.map(r => r.id)).size, protocol.case_occurrences);
  const obligations = [...new Set(index.requirements.flatMap(r => r.required).filter(id => id.includes('/obligation/staff/')))].sort();
  assert.equal(obligations.length, protocol.expected_open_obligations);
  const byCategory = {};
  for (const id of obligations) { const category = id.split('/obligation/staff/')[1].split('/')[1]; byCategory[category] = (byCategory[category] || 0) + 1; }
  const manifest = { ...original, base_index: { path: 'staff-index.json', bytes: indexRaw.length, sha256: sha(indexRaw) }, semantic_source_snapshot: index.bundle.snapshot, bundle: index.bundle, scope: index.scope, limitations: index.limitations };
  const binding = { index_url: 'https://example.test/qualification-corpus/manifest.json', index_sha256: sha(canonicalJson(manifest)) };
  const fetched = new Map(), corpusBindings = new Map();
  const fetcher = async url => {
    const parsed = new URL(String(url)); assert.equal(parsed.origin, 'https://example.test');
    assert(!parsed.username && !parsed.password && !parsed.search && !parsed.hash && parsed.pathname.startsWith('/qualification-corpus/'), 'Unapproved corpus request');
    const name = safeName(decodeURIComponent(parsed.pathname.slice('/qualification-corpus/'.length)));
    if (name === 'staff-index.json') return new Response(indexRaw);
    assert(/^(?:records|search)\/[a-zA-Z0-9._-]+$/.test(name), 'Unapproved corpus file');
    if (!fetched.has(name)) { const raw = fromGit(dwp, commit, 'context/corpus/' + name); fetched.set(name, raw); corpusBindings.set(name, { path: 'context/corpus/' + name, bytes: raw.length, sha256: sha(raw) }); }
    return new Response(fetched.get(name));
  };
  sourceCensus[stage] = { commit, index_sha256: sha(indexRaw), records: index.records.length, assertions: index.assertions.length, requirements: index.requirements.length, open_obligations: obligations, obligations_by_category: byCategory };
  sources[stage] = { index, registry, manifest, binding, fetcher };
  inputSources[stage] = { commit, files: bindings, corpus_files: corpusBindings, binding };
}
assert.deepEqual(sources.old.registry, sources.new.registry, 'Question/candidate registry changed: not the preregistered comparison');
assert.deepEqual(sourceCensus.old.open_obligations, sourceCensus.new.open_obligations, 'Open obligations changed');
function describe(p, expected, row, source, resolution) {
  const selected = new Map(p.selected.map(s => [s.record.id, s])), edges = new Map(p.relationships.map(a => [a.id, a]));
  const census = requirementCensus(source.index, resolution, p);
  const result = { context_id: p.context_id, package_sha256: sha(canonicalJson(p)), bytes: p.budget.used_bytes, records: p.selected.length, relationships: p.relationships.length,
    selected_routes: p.selected.map(s => s.record.route), selected_ids: [...selected.keys()], ...census,
    candidate_hits: expected.filter(c => selected.has(c.record_id)).map(c => c.id), evidence_status: p.evidence_status, truncated: p.budget.truncated,
    allocation_used: p.limitations.some(s => s.startsWith('One additional allocation pass')), omissions: p.budget.omissions,
    resolved_concepts: p.resolved_concepts, unresolved_terms: p.unresolved_terms, ambiguities: p.ambiguities, conflicts: p.conflicts, missing_evidence: p.missing_evidence,
    requirement_diagnostics: p.requirements.map(r => ({ id: r.id, status: r.status, missing: r.missing })) };
  if (protocol.focus_cases.includes(row.id)) {
    const id = 'https://chris-page-gov.github.io/okf-dwp/id/requirement/staff/' + row.id;
    const declared = source.index.requirements.find(r => r.id === id); assert(declared);
    const activated = census.expected_requirement_ids.includes(id);
    result.household_support = protocol.household_routes.map(route => {
      const sourceRecord = source.index.records.find(r => r.route === route); assert(sourceRecord, 'Missing household source record');
      const chosen = selected.get(sourceRecord.id), declaredPaths = (declared.required_paths || []).filter(p => p.records.at(-1) === sourceRecord.id);
      return { route, record_id: sourceRecord.id, selected: Boolean(chosen), source_text_sha256: sha(sourceRecord.text),
        selected_record_sha256: chosen ? sha(canonicalJson(chosen.record)) : null, selected_paths: chosen?.paths || [],
        declared_required: declared.required.includes(sourceRecord.id), declared_paths: declaredPaths,
        activated, retained_declared_paths: activated ? declaredPaths.filter(p => pathRetained(p, selected, edges)) : [],
        missing_dependency: p.missing_evidence.filter(i => i.ids.includes(sourceRecord.id)) };
    });
    result.focus_requirement = { ...declared, activated, output_omitted: activated && census.omitted_requirement_ids.includes(id), returned_status: p.requirements.find(r => r.id === id)?.status ?? (activated ? 'omitted-from-output' : 'not-activated') };
  }
  return result;
}
const started = new Date().toISOString(), observations = [];
for (const max_bytes of protocol.budgets) for (const sourceStage of ['old', 'new']) for (const row of sources[sourceStage].registry.cases) {
  const source = sources[sourceStage], expected = source.registry.source_candidates.filter(c => row.candidate_ids.includes(c.id));
  const packages = {}, elapsed = {}, resolutions = {};
  for (const engineStage of ['baseline', 'candidate']) {
    resolutions[engineStage] = cores[engineStage].resolveConcepts(source.index, row.question);
    const start = performance.now(); const p = await engines[engineStage].assembleCorpusContext(source.manifest, source.binding, row.question, { max_bytes }, source.fetcher); elapsed[engineStage] = performance.now() - start;
    assert.equal(p.ai_answer, null); assert.equal(p.evidence_status, 'insufficient'); assert(p.budget.used_bytes <= max_bytes);
    if (!p.missing_evidence.some(issue => issue.code === 'metadata_budget')) assert.deepEqual(p.resolved_concepts, resolutions[engineStage].resolved, 'Independent activation resolution differs from returned context');
    for (const { record } of p.selected.filter(s => s.record.kind === 'evidence')) for (const provenance of record.provenance) if (provenance.literal_sha256) assert.equal(sha(record.text), provenance.literal_sha256);
    packages[engineStage] = p;
  }
  observations.push({ source: sourceStage, case_id: row.id, question: row.question, max_bytes,
    baseline: describe(packages.baseline, expected, row, source, resolutions.baseline), candidate: describe(packages.candidate, expected, row, source, resolutions.candidate),
    exact_engine_package_preserved: canonicalJson(packages.baseline) === canonicalJson(packages.candidate), elapsed_ms: elapsed });
}
const summary = protocol.budgets.flatMap(max_bytes => ['old','new'].map(source => {
  const rows = observations.filter(r => r.max_bytes === max_bytes && r.source === source);
  const count = (stage, field) => rows.reduce((n, r) => n + (Array.isArray(r[stage][field]) ? r[stage][field].length : r[stage][field]), 0);
  return { source, max_bytes, cases: rows.length, baseline_candidate_hits: count('baseline','candidate_hits'), candidate_candidate_hits: count('candidate','candidate_hits'),
    baseline_retained_paths: count('baseline','retained_paths'), candidate_retained_paths: count('candidate','retained_paths'), baseline_declared_paths: count('baseline','declared_paths'), candidate_declared_paths: count('candidate','declared_paths'),
    baseline_expected_requirements: count('baseline','expected_requirement_ids'), candidate_expected_requirements: count('candidate','expected_requirement_ids'),
    baseline_omitted_requirements: count('baseline','omitted_requirement_ids'), candidate_omitted_requirements: count('candidate','omitted_requirement_ids'),
    allocations: rows.filter(r => r.candidate.allocation_used).length, exact_engine_packages: rows.filter(r => r.exact_engine_package_preserved).length,
    sufficient: 0, household: rows.filter(r => protocol.focus_cases.includes(r.case_id)).map(r => ({ case_id: r.case_id,
      baseline_selected: r.baseline.household_support.filter(s => s.selected).length, candidate_selected: r.candidate.household_support.filter(s => s.selected).length,
      baseline_with_declared_path: r.baseline.household_support.filter(s => s.retained_declared_paths.length).length, candidate_with_declared_path: r.candidate.household_support.filter(s => s.retained_declared_paths.length).length })) };
}));
for (const source of Object.values(inputSources)) source.corpus_files = [...source.corpus_files.values()].sort((a,b) => a.path.localeCompare(b.path));
const result = { schema: 'okf-qualification-context-comparison.v1', started_at: started, completed_at: new Date().toISOString(), runtime: { node: process.version, platform: process.platform, arch: process.arch },
  inputs: { protocol_sha256: sha(protocolRaw), runner_sha256: hashes['compare.mjs'], guards_sha256: hashes['guards.mjs'], metrics_sha256: hashes['metrics.mjs'], engine_sha256: protocol.engine_sha256, sources: inputSources },
  source_census: sourceCensus, summary, observations, limitations: [...protocol.limitations, 'One in-process timing per cell is diagnostic only; cache and execution order prevent causal performance inference.','Context package hashes bind exact deterministic reconstructions; this receipt does not retain or replace historical model-facing packages.'] };
const raw = JSON.stringify(result, null, 2) + '\n'; assert(Buffer.byteLength(raw) <= 32 * 1024 * 1024, 'Comparison receipt exceeds limit');
if (checking) {
  const stable = value => { const clone = structuredClone(value); delete clone.started_at; delete clone.completed_at; delete clone.runtime; for (const row of clone.observations) delete row.elapsed_ms; return clone; };
  assert.deepEqual(stable(result), stable(prior));
} else await writeFile(path.join(output,'comparison.json'), raw, { flag:'wx' });
console.log(JSON.stringify({ status: checking ? 'verified' : 'retained', summary }));
