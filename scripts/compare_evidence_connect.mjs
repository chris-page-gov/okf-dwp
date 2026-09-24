#!/usr/bin/env node
/** Compare two declared rankings over identical source and discovery shards. */
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const args = process.argv.slice(2);
const i = args.indexOf('--explorer-root');
assert(i >= 0 && args[i + 1], 'Usage: --explorer-root PATH [--check]');
const explorer = resolve(args[i + 1]);
const check = args.includes('--check');
const { assembleCorpusContext, validateContextCorpusManifest } = await import(pathToFileURL(
  resolve(explorer, 'apps/okf-explorer/src/lib/context/corpus.ts')));
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const raw = readFileSync(resolve(root, 'structured-context/evidence-connect-manifest.json'));
const weighted = validateContextCorpusManifest(JSON.parse(raw));
assert.equal(weighted.search.ranking.schema, 'okf-bm25-weighted.v2');
const equal = structuredClone(weighted);
equal.search.ranking = {schema:'okf-bm25.v1',k1:1.2,b:0.75,score_scale:1000000,fields:['source','discovery']};
delete equal.search.alias_routes;
validateContextCorpusManifest(equal);
const registry = JSON.parse(readFileSync(resolve(root, 'evaluation/staff-questions/cases.json')));
assert.equal(registry.cases.length, 40);
const binding = manifest => ({index_url:'https://example.invalid/structured-context/evidence-connect-manifest.json',
  index_sha256:sha(Buffer.from(JSON.stringify(manifest)))});
const allowed = new Map([weighted.base_index, ...weighted.records.shards, ...weighted.discovery.shards,
  ...Object.values(weighted.search.shards), ...Object.values(weighted.relationships.shards)].map(ref=>[ref.path,ref]));
const fetcher = async url => {
  const parsed = new URL(String(url));
  assert.equal(parsed.origin, 'https://example.invalid');
  assert(parsed.pathname.startsWith('/structured-context/'));
  const relative = parsed.pathname.slice('/structured-context/'.length);
  const ref = allowed.get(relative);
  assert(ref, 'Unbound source resource');
  const bytes = readFileSync(resolve(root, 'structured-context', relative));
  assert.equal(sha(bytes), ref.sha256);
  return new Response(bytes);
};
const spanKey = span => [span.source_url, span.source_start, span.source_end, span.literal_sha256].join('|');
const details = pack => {
  const evidence = pack.selected.filter(row => row.record.kind === 'evidence');
  const spans = new Set(evidence.flatMap(row => row.record.evidence_unit?.spans?.map(spanKey) || []));
  return {context_id:pack.context_id, evidence_status:pack.evidence_status,
    selected_ids:evidence.map(row=>row.record.id), spans:[...spans].sort(),
    requirements:pack.requirements.map(row=>({id:row.id,status:row.status,missing:row.missing})),
    missing_codes:pack.missing_evidence.map(row=>row.code),
    retrieval_omissions:pack.retrieval?.omissions?.map(row=>row.code)||[],
    context_omissions:pack.budget.omissions.map(row=>row.code),
    retrieval_candidates:pack.retrieval?.candidate_count,
    package_bytes:pack.budget.used_bytes};
};
const rows = [];
for (const item of registry.cases) {
  const budget = {max_bytes:524288,max_nodes:64,max_relationships:128,max_depth:6};
  const before = details(await assembleCorpusContext(equal,binding(equal),item.question,budget,fetcher));
  const after = details(await assembleCorpusContext(weighted,binding(weighted),item.question,budget,fetcher));
  const beforeIds = new Set(before.selected_ids), afterIds = new Set(after.selected_ids);
  const beforeSpans = new Set(before.spans), afterSpans = new Set(after.spans);
  rows.push({id:item.id,question:item.question, same_source_shards:true,
    before,after,
    delta:{gained_ids:after.selected_ids.filter(id=>!beforeIds.has(id)),
      lost_ids:before.selected_ids.filter(id=>!afterIds.has(id)),
      gained_source_spans:after.spans.filter(key=>!beforeSpans.has(key)),
      lost_source_spans:before.spans.filter(key=>!afterSpans.has(key)),
      interpretation:'Record and source-span selection changes are navigation evidence, not answer quality.'}});
  process.stdout.write(`${item.id} +${rows.at(-1).delta.gained_ids.length} -${rows.at(-1).delta.lost_ids.length}\n`);
}
const report = {schema:'okf-evidence-connect-comparison.v1',
  corpus_manifest_sha256:sha(raw),registry_sha256:sha(readFileSync(resolve(root,'evaluation/staff-questions/cases.json'))),
  engine_files:Object.fromEntries(['index.ts','corpus.ts','corpusV3.ts','types.ts'].map(name=>
    [name,sha(readFileSync(resolve(explorer,'apps/okf-explorer/src/lib/context',name)))])),
  control:'Same additive full DMG and ADM records, discovery cards, relationships, source inputs and fixed assembly budgets. The v2 arm enables weighted ranking, exact source-led alias routes and changed admission order.',
  model_calls:0,network_calls:0,rows,
  limitations:['Source span selection and evidence delivery do not establish substantive answer quality or specialist acceptance.',
    'The v2 arm changes ranking, bounded alias routing and source-dependent admission order together; this comparison does not isolate their separate effects.']};
const path = resolve(root,'evaluation/evidence-workbench/comparison.json');
const bytes = Buffer.from(JSON.stringify(report,null,2)+'\n');
if(check){assert(existsSync(path));assert.deepEqual(readFileSync(path),bytes,'Comparison drift');}
else{mkdirSync(dirname(path),{recursive:true});writeFileSync(path,bytes);}
console.log(JSON.stringify({status:check?'verified':'built',cases:rows.length,assemblies:rows.length*2,
  gained_cases:rows.filter(r=>r.delta.gained_ids.length).length,lost_cases:rows.filter(r=>r.delta.lost_ids.length).length,
  all_insufficient:rows.every(r=>r.before.evidence_status==='insufficient'&&r.after.evidence_status==='insufficient')}));
