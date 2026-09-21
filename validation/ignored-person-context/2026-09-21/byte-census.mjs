#!/usr/bin/env node
/** Supplementary offline replay of 16 previously measured packages; no network or model calls. */
import assert from 'node:assert/strict';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {FILES,sha,boundedAt,fromGit,exactTree,admitEngines,safeName} from './guards.mjs';
import {packageByteCensus} from './bytes.mjs';
assert.equal(process.argv.length,5,'Supply DWP checkout, Explorer checkout and retained attempt directory');
const [dwp,explorer,archive]=process.argv.slice(2),here=path.dirname(fileURLToPath(import.meta.url));
const rawProtocol=await boundedAt(here,'protocol.json',32768);
assert.equal(sha(rawProtocol),'d467d0bb0b55f596000d4b7c8a059d52e150b26792d1a8065fdb297b6c7cd5e9');
const protocol=JSON.parse(rawProtocol),rawComparison=await boundedAt(archive,'comparison.json',32*1024*1024);
assert.equal(sha(rawComparison),'c45dcc69170db2d74ca144f3b9cdbbbb8fe514dbaef1e0c8695d372e82fed785');
const comparison=JSON.parse(rawComparison);
assert.equal(comparison.inputs.protocol_sha256,sha(rawProtocol));
const sourceFiles=['protocol.json','compare.mjs','guards.mjs','metrics.mjs'];
await exactTree(archive,[...sourceFiles,...['baseline','candidate'].flatMap(s=>FILES.map(n=>`engines/${s}/${n}`)),'comparison.json']);
for(const name of sourceFiles) assert.deepEqual(await boundedAt(here,name,1024*1024),await boundedAt(archive,name,1024*1024));
assert.deepEqual(comparison.inputs.engine_sha256,protocol.engine_sha256);
await admitEngines(archive,protocol.engine_sha256);
for(const stage of ['baseline','candidate'])for(const name of FILES) {
 const raw=await boundedAt(archive,`engines/${stage}/${name}`,2*1024*1024);
 assert.deepEqual(raw,fromGit(explorer,protocol[stage+'_explorer_commit'],'apps/okf-explorer/src/lib/context/'+name,2*1024*1024));
}
// Frozen digest, reviewed allowlist and exact containing commits are checked before executing the archived modules.
const {canonicalJson}=await import(pathToFileURL(path.join(path.resolve(archive),'engines/candidate/index.ts')));
const {assembleCorpusContext}=await import(pathToFileURL(path.join(path.resolve(archive),'engines/candidate/corpus.ts')));
const cases=['staff-012','staff-013','staff-014','staff-017'],rows=[];
for(const stage of ['old','new']) {
 const commit=protocol[stage+'_dwp_commit'];assert.equal(comparison.inputs.sources[stage].commit,commit);
 const refs=new Map([...comparison.inputs.sources[stage].files,...comparison.inputs.sources[stage].corpus_files].map(f=>[f.path,f]));
 const cache=new Map();
 function input(name,cap) {
  if(!cache.has(name)) {
   const ref=refs.get(name);assert(ref,'Not an observed immutable source file');
   const raw=fromGit(dwp,commit,name,cap);assert.equal(raw.length,ref.bytes);assert.equal(sha(raw),ref.sha256);cache.set(name,raw);
  }
  return cache.get(name);
 }
 const indexRaw=input('evaluation/semantic-expansion/assembly-index.json',8*1024*1024),index=JSON.parse(indexRaw);
 const original=JSON.parse(input('context/corpus/manifest.json',4*1024*1024));
 const registry=JSON.parse(input('evaluation/staff-questions/cases.json',4*1024*1024));
 const manifest={...original,base_index:{path:'staff-index.json',bytes:indexRaw.length,sha256:sha(indexRaw)},semantic_source_snapshot:index.bundle.snapshot,bundle:index.bundle,scope:index.scope,limitations:index.limitations};
 const binding={index_url:'https://example.test/qualification-corpus/manifest.json',index_sha256:sha(canonicalJson(manifest))};
 assert.deepEqual(binding,comparison.inputs.sources[stage].binding);
 const fetcher=async value=>{
  const url=new URL(String(value));assert.equal(url.origin,'https://example.test');
  assert(!url.username&&!url.password&&!url.search&&!url.hash&&url.pathname.startsWith('/qualification-corpus/'));
  const name=safeName(decodeURIComponent(url.pathname.slice('/qualification-corpus/'.length)));
  if(name==='staff-index.json')return new Response(indexRaw);
  assert(/^(?:records|search)\/[a-zA-Z0-9._-]+$/.test(name));
  return new Response(input('context/corpus/'+name,4*1024*1024));
 };
 for(const max_bytes of protocol.budgets)for(const case_id of cases) {
  const question=registry.cases.find(c=>c.id===case_id)?.question;assert(question);
  const expected=comparison.observations.find(r=>r.source===stage&&r.case_id===case_id&&r.max_bytes===max_bytes)?.candidate;assert(expected);
  const pkg=await assembleCorpusContext(manifest,binding,question,{max_bytes},fetcher);
  const package_sha256=sha(canonicalJson(pkg));assert.equal(package_sha256,expected.package_sha256,'Supplementary replay differs from measured package');
  assert.equal(pkg.ai_answer,null);assert.equal(pkg.evidence_status,'insufficient');
  const census=packageByteCensus(pkg,canonicalJson);assert.equal(census.canonical_package_bytes,expected.bytes);
  rows.push({source:stage,case_id,max_bytes,context_id:pkg.context_id,package_sha256,...census});
 }
}
assert.equal(rows.length,16);
const files={};for(const name of ['byte-census.mjs','bytes.mjs','guards.mjs'])files[name]=sha(await boundedAt(here,name,65536));
console.log(JSON.stringify({schema:'okf-context-byte-census.v1',classification:'supplementary-exact-offline-replay',
 inputs:{protocol_sha256:sha(rawProtocol),comparison_sha256:sha(rawComparison),source_commits:{old:protocol.old_dwp_commit,new:protocol.new_dwp_commit},engine_commit:protocol.candidate_explorer_commit,engine_sha256:protocol.engine_sha256.candidate,files},
 limitations:['Every measured package must match its canonical digest in the original 320-assembly observation. This does not replace that observation.',
 'Top-level property bytes plus root punctuation equal the whole canonical package. The selected-value partition is nested inside selected; do not add it again.',
 'Raw evidence text and provenance sizes are overlapping observations. The remaining bytes include necessary provenance, scope, paths, diagnostics and structure; they are not all disposable overhead.',
 'This measures selected packages only, not bytes for all omitted required source text, model tokenisation or a redesigned representation.',
 'No public-host call, model call, completeness improvement or legal acceptance is asserted.'],rows},null,2));
