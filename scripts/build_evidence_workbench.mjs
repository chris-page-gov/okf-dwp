#!/usr/bin/env node
/** Reproduce 40 offline evidence packages from the additive full-corpus overlay. */
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { outputPath, validateCaseIds } from './evidence_workbench_paths.mjs';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const args = process.argv.slice(2);
const value = flag => { const i = args.indexOf(flag); assert(i >= 0 && args[i + 1], `Missing ${flag}`); return args[i + 1]; };
const check = args.includes('--check');
const explorer = resolve(value('--explorer-root'));
const deliveryRoot = resolve(args.includes('--delivery-root') ? value('--delivery-root') : explorer);
const output = resolve(root, 'evaluation/evidence-workbench');
const sha = raw => createHash('sha256').update(raw).digest('hex');
const read = relative => readFileSync(resolve(root, relative));
const engineDir = resolve(explorer, 'apps/okf-explorer/src/lib/context');
const engine = await import(pathToFileURL(resolve(engineDir, 'corpus.ts')));
const { canonicalJson } = await import(pathToFileURL(resolve(engineDir, 'index.ts')));
const { packageContextForDelivery } = await import(pathToFileURL(resolve(deliveryRoot, 'apps/okf-explorer/src/lib/context/packageDelivery.ts')));
const registryRaw = read('evaluation/staff-questions/cases.json');
const registry = JSON.parse(registryRaw);
assert.equal(registry.schema, 'okf-dwp-staff-question-registry.v1');
validateCaseIds(registry.cases);
const source = new Map(registry.source_candidates.map(row => [row.id, row]));
const corpusRelative = 'structured-context/evidence-connect-manifest.json';
const corpusRaw = read(corpusRelative);
const corpus = engine.validateContextCorpusManifest(JSON.parse(corpusRaw));
assert.equal(corpus.schema, 'okf-context-corpus.v3');
assert.equal(corpus.extensions.evidence_connect.new_group_count, 10);
const binding = { index_url: 'https://example.invalid/structured-context/evidence-connect-manifest.json',
                  index_sha256: sha(corpusRaw) };
const rootUrl = new URL('.', binding.index_url);
const allowed = new Map([corpus.base_index, ...corpus.records.shards, ...corpus.discovery.shards,
  ...Object.values(corpus.search.shards), ...Object.values(corpus.relationships.shards)].map(ref => [ref.path, ref]));
const fetcher = async url => {
  const target = new URL(String(url));
  assert.equal(target.origin, rootUrl.origin, 'Network denied');
  assert(target.href.startsWith(rootUrl.href), 'Corpus fetch escaped local root');
  const relative = target.href.slice(rootUrl.href.length);
  assert(allowed.has(relative), 'Unbound corpus resource: ' + relative);
  const raw = read('structured-context/' + relative);
  assert.equal(raw.length, allowed.get(relative).bytes);
  assert.equal(sha(raw), allowed.get(relative).sha256);
  return new Response(raw);
};
const outputs = new Map();
const questions = [], assessment = [];
for (const item of registry.cases) {
  const context = await engine.assembleCorpusContext(corpus, binding, item.question,
    { max_bytes: 524288, max_nodes: 64, max_relationships: 128, max_depth: 6 }, fetcher);
  assert.equal(context.schema, 'okf-governed-context.v1');
  assert.equal(context.ai_answer, null);
  assert.equal(context.question, item.question);
  const raw = Buffer.from(canonicalJson(context));
  assert.equal(raw.length, context.budget.used_bytes);
  assert(raw.length <= 524288);
  const packed = await packageContextForDelivery(context);
  assert.equal(packed.sha256, sha(raw));
  const packagePath = `packages/${item.id}.json`;
  outputs.set(packagePath, raw);
  const partRefs = packed.parts.map((part, index) => {
    const path = `parts/${item.id}-${String(index).padStart(3, '0')}.json`;
    const body = Buffer.from(JSON.stringify(part));
    assert(body.length <= 32768);
    outputs.set(path, body);
    return { url: path, sha256: sha(body), bytes: body.length };
  });
  questions.push({ id: item.id, label: `${item.id}: ${item.section}`,
    question: item.question, package: { url: packagePath, sha256: sha(raw), bytes: raw.length,
      parts: partRefs },
    ambiguities: item.ambiguities, required_evidence: item.required_evidence,
    scope_gaps: item.scope_gaps });
  const selected = context.selected.filter(row => row.record.kind === 'evidence');
  const candidatePages = item.candidate_ids.map(id => source.get(id)).filter(Boolean);
  const deliveredUrls = new Set(selected.flatMap(row => row.record.evidence_unit?.spans?.map(span => span.source_url) || []));
  const matched = candidatePages.filter(row => deliveredUrls.has(row.url));
  assessment.push({ id: item.id, question: item.question, context_id: context.context_id,
    package_sha256: sha(raw), package_bytes: raw.length, corpus_sha256: binding.index_sha256,
    evidence_status: context.evidence_status, selected_evidence: selected.map(row => row.record.id),
    selected_source_pages: [...deliveredUrls].sort(),
    candidate_pages: candidatePages.map(row => row.url), matched_candidate_pages: matched.map(row => row.url),
    source_delta: { candidate_page_count: candidatePages.length, matched_candidate_page_count: matched.length,
      meaning: 'Exact captured page overlap only; no answer completeness claim.' },
    missing_evidence: context.missing_evidence, unresolved_terms: context.unresolved_terms,
    retrieval_omissions: context.retrieval?.omissions || [],
    context_omissions: context.budget.omissions, requirements: context.requirements,
    requested_evidence: item.required_evidence, ambiguities: item.ambiguities,
    scope_gaps: item.scope_gaps, delivery: packed.metrics,
    answerability: 'not established by source overlap, retrieval or bounded delivery' });
  process.stdout.write(`${item.id} ${context.evidence_status} selected=${selected.length} bytes=${raw.length}\n`);
}
const manifest = { schema: 'okf-evidence-workbench.v1',
  title: 'DWP staff evidence workbench: 40 frozen questions',
  publication: { label: 'Independent experimental DWP research across frozen DMG and ADM source snapshots' },
  source: { registry: 'evaluation/staff-questions/cases.json', registry_sha256: sha(registryRaw),
    corpus: corpusRelative, corpus_sha256: binding.index_sha256,
    engine_files: Object.fromEntries(['index.ts','corpus.ts','corpusV3.ts','types.ts'].map(name =>
      [name, sha(readFileSync(resolve(engineDir, name)))])),
    delivery_sha256: sha(readFileSync(resolve(deliveryRoot, 'apps/okf-explorer/src/lib/context/packageDelivery.ts'))),
    model_calls: 0, network_calls: 0 }, questions };
outputs.set('manifest.json', Buffer.from(JSON.stringify(manifest, null, 2) + '\n'));
outputs.set('assessment.json', Buffer.from(JSON.stringify({ schema: 'okf-evidence-workbench-assessment.v1',
  source: manifest.source, cases: assessment,
  limitations: ['Candidate page overlap, package selection, missing obligations and answerability are separate measures.',
    'No model answer was generated and no independent specialist review was performed.'] }, null, 2) + '\n'));
for (const [relative, raw] of outputs) {
  const path = outputPath(output, relative);
  if (check) { assert(existsSync(path), `Missing output: ${relative}`); assert.deepEqual(readFileSync(path), raw, `Drift: ${relative}`); }
  else { mkdirSync(dirname(path), { recursive: true }); writeFileSync(path, raw); }
}
console.log(JSON.stringify({ status: check ? 'verified' : 'built', questions: questions.length,
  files: outputs.size, corpus_sha256: binding.index_sha256, model_calls: 0, network_calls: 0 }));
