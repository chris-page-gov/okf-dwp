#!/usr/bin/env node
/** Run prospective, source-neutral wording probes without model or network calls. */
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { existsSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const args = process.argv.slice(2);
const i = args.indexOf('--explorer-root');
assert(i >= 0 && args[i + 1], 'Usage: --explorer-root PATH [--check]');
const check = args.includes('--check');
const specName = args.includes('--confirmation') ? 'probes-confirmation.json'
  : args.includes('--pattern') ? 'probes-pattern.json' : 'probes.json';
const explorer = resolve(args[i + 1], 'apps/okf-explorer/src/lib/context');
const { assembleCorpusContext, validateContextCorpusManifest } = await import(pathToFileURL(resolve(explorer, 'corpus.ts')));
const sha = raw => createHash('sha256').update(raw).digest('hex');
const probesRaw = readFileSync(resolve(root, 'domain-profile/evidence-connect', specName));
const probes = JSON.parse(probesRaw);
assert.equal(probes.schema, 'okf-evidence-connect-probes.v1');
const raw = readFileSync(resolve(root, 'structured-context/evidence-connect-manifest.json'));
const corpus = validateContextCorpusManifest(JSON.parse(raw));
const binding = { index_url:'https://example.invalid/structured-context/evidence-connect-manifest.json', index_sha256:sha(raw) };
const allowed = new Map([corpus.base_index,...corpus.records.shards,...corpus.discovery.shards,
  ...Object.values(corpus.search.shards),...Object.values(corpus.relationships.shards)].map(ref=>[ref.path,ref]));
const fetcher = async url => {
  const parsed = new URL(String(url));
  assert.equal(parsed.origin,'https://example.invalid');
  assert(parsed.pathname.startsWith('/structured-context/'));
  const rel = parsed.pathname.slice('/structured-context/'.length);
  const bytes = readFileSync(resolve(root,'structured-context',rel));
  assert.equal(sha(bytes),allowed.get(rel)?.sha256);
  return new Response(bytes);
};
const target = 'https://chris-page-gov.github.io/okf-dwp/id/unit/zz-evidence-connect/' + probes.target_group;
const rows = [];
for (const kind of ['positive','negative']) for (const question of probes[kind]) {
  const context = await assembleCorpusContext(corpus,binding,question,
    {max_bytes:524288,max_nodes:64,max_relationships:128,max_depth:6},fetcher);
  const ordinal = context.retrieval?.candidates.findIndex(row=>row.id===target) ?? -1;
  const candidate = ordinal < 0 ? null : context.retrieval.candidates[ordinal];
  const row = {kind,question,target_rank:ordinal < 0 ? null : ordinal+1,
    target_selected:context.selected.some(row=>row.record.id===target),
    target_alias_pattern_id:candidate?.alias_pattern_id||null,
    target_matched_groups:candidate?.matched_groups||[],
    target_reasons:context.selected.find(row=>row.record.id===target)?.reasons||[],
    source_dependency_84861_selected:context.selected.some(row=>row.record.id.includes('source-0000200424-000-606242ace072')),
    evidence_status:context.evidence_status,
    retrieval_omissions:context.retrieval?.omissions.map(row=>row.code)||[],
    missing_evidence:context.missing_evidence.map(row=>row.code),
    selected_evidence:context.selected.filter(row=>row.record.kind==='evidence').map(row=>row.record.id)};
  rows.push(row);
  process.stdout.write(`${kind} rank=${row.target_rank ?? '-'} selected=${row.target_selected} dependency=${row.source_dependency_84861_selected}\n`);
}
const report = {schema:'okf-evidence-connect-probe-results.v1',probe_sha256:sha(probesRaw),
  manifest_sha256:binding.index_sha256,
  engine_files:Object.fromEntries(['index.ts','corpus.ts','corpusV3.ts','types.ts'].map(name=>
    [name,sha(readFileSync(resolve(explorer,name)))])),
  model_calls:0,network_calls:0,rows,limitation:probes.interpretation};
const path = resolve(root,'evaluation/evidence-workbench', specName);
const body = Buffer.from(JSON.stringify(report,null,2)+'\n');
if(check){assert(existsSync(path));assert.deepEqual(readFileSync(path),body,'Probe drift');}
else writeFileSync(path,body);
console.log(JSON.stringify({status:check?'verified':'built',positive:probes.positive.length,negative:probes.negative.length,
  negative_u07_selections:rows.filter(row=>row.kind==='negative'&&row.target_selected).length,
  all_insufficient:rows.every(row=>row.evidence_status==='insufficient')}));
