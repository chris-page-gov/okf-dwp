#!/usr/bin/env node
/** Offline candidate-ranking probe. Never modifies the production engine/index. */
import assert from 'node:assert/strict';
import {readFileSync, writeFileSync, mkdirSync, existsSync, lstatSync, realpathSync} from 'node:fs';
import {resolve, dirname} from 'node:path';
import {fileURLToPath, pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {gunzipSync} from 'node:zlib';

const ROOT=resolve(dirname(fileURLToPath(import.meta.url)), '..');
const args=process.argv.slice(2); assert.equal(args.length, 2); assert.equal(args[0], '--explorer-root');
const explorer=realpathSync(resolve(args[1]));
const sha=b=>createHash('sha256').update(b).digest('hex');
const inputs=new Map();
function read(relative, expected, limit=16*1024*1024) {
  assert(typeof relative==='string' && !relative.startsWith('/') && !relative.split('/').some(p=>!p||p==='..'||p==='.') && !relative.includes('\\'));
  const p=resolve(ROOT, relative); assert.equal(realpathSync(p),p);const st=lstatSync(p);assert(st.isFile()&&st.size<=limit);
  const raw=readFileSync(p);assert.equal(raw.length,st.size);
  const ref={path:relative,sha256:sha(raw),bytes:raw.length};
  if(expected){assert.equal(ref.sha256,expected.sha256);assert.equal(ref.bytes,expected.bytes);}
  inputs.set(relative,ref);return raw;
}
const protocol=JSON.parse(read('evaluation/discovery-probe/protocol.json'));
assert.equal(protocol.schema,'okf-dwp-discovery-probe-protocol.v1');
const bound=new Map(protocol.inputs.map(r=>[r.path,r]));
for(const r of protocol.inputs)read(r.path,r);
const approved=JSON.parse(read('evaluation/logical-units/engine.json',bound.get('evaluation/logical-units/engine.json')));
assert.deepEqual(Object.keys(approved.files).sort(),['corpus.ts','index.ts','types.ts','unit.ts']);
const engine=resolve(explorer,'apps/okf-explorer/src/lib/context');
for(const [name,hash] of Object.entries(approved.files)){
  assert.match(hash,/^[0-9a-f]{64}$/);
  assert.equal(sha(readFileSync(resolve(engine,name))),hash);
  assert.equal(sha(execFileSync('git',['-C',explorer,'show',`${approved.commit}:apps/okf-explorer/src/lib/context/${name}`],{maxBuffer:8*1024*1024})),hash);
}
const {resolveConcepts,isQuestionScaffolding}=await import(pathToFileURL(resolve(engine,'index.ts')));
const {corpusTokens,corpusBucket,validateContextCorpusManifest,assembleCorpusContext}=await import(pathToFileURL(resolve(engine,'corpus.ts')));
const manifest=validateContextCorpusManifest(JSON.parse(read('logical-context/manifest.json',bound.get('logical-context/manifest.json'))));
const prefix='logical-context/';
const allowed=new Map([manifest.base_index,...manifest.records.shards,...Object.values(manifest.search.shards)].map(r=>[r.path,r]));
const rawCache=new Map(),decodedCache=new Map();
function raw(ref){if(!rawCache.has(ref.path))rawCache.set(ref.path,read(prefix+ref.path,ref,8*1024*1024));return rawCache.get(ref.path);}
function decoded(ref){
  if(!decodedCache.has(ref.path)){
    let bytes=raw(ref);
    if(ref.encoding==='gzip'){
      assert(ref.decoded_bytes>0&&ref.decoded_bytes<=4*1024*1024);
      bytes=gunzipSync(bytes,{maxOutputLength:ref.decoded_bytes});
      assert.equal(bytes.length,ref.decoded_bytes);assert.equal(sha(bytes),ref.decoded_sha256);
    }
    decodedCache.set(ref.path,JSON.parse(bytes));
  }
  return decodedCache.get(ref.path);
}
const base=decoded(manifest.base_index),concepts=new Map(base.records.map(r=>[r.id,r]));
const registry=JSON.parse(read('evaluation/staff-questions/cases.json',bound.get('evaluation/staff-questions/cases.json')));
const coverage=JSON.parse(read('evaluation/semantic-coverage/closure-2026-09-22/audit.json',bound.get('evaluation/semantic-coverage/closure-2026-09-22/audit.json')));
const candidates=new Map(coverage.candidate_sources.map(r=>[r.id,r]));
assert.equal(registry.cases.length,40);
function eligible(text){return corpusTokens(text).filter(t=>t.length<=64&&!isQuestionScaffolding(t));}
function postings(token){
  const shard=decoded(manifest.search.shards[corpusBucket(token)]);assert.equal(shard.schema,'okf-context-postings.v1');
  const rows=Object.hasOwn(shard.postings,token)?shard.postings[token]:[];
  assert(Array.isArray(rows)&&rows.length<=manifest.records.count);
  let prev=-1;for(const n of rows){assert(Number.isInteger(n)&&n>=0&&n<manifest.records.count&&n>prev);prev=n;}
  return rows;
}
function rank(terms){
  const rows=new Map();
  for(const term of terms){const ids=postings(term.token);const idf=1+Math.floor(1000*Math.log2(1+manifest.records.count/Math.max(1,ids.length)));
    for(const ordinal of ids){const row=rows.get(ordinal)||{ordinal,score:0,matched:[]};row.score+=idf*term.weight;row.matched.push(term.token);rows.set(ordinal,row);}
  }
  return {matching_units:rows.size,candidates:[...rows.values()].sort((a,b)=>b.score-a.score||a.ordinal-b.ordinal).slice(0,protocol.limits.candidates)};
}
function record(ordinal){
  const ref=manifest.records.shards.find(r=>ordinal>=r.first_ordinal&&ordinal<r.first_ordinal+r.count);assert(ref);
  const value=decoded(ref);assert.equal(value.schema,'okf-context-records.v1');assert.equal(value.first_ordinal,ref.first_ordinal);
  const r=value.records[ordinal-ref.first_ordinal];assert(r&&r.kind==='evidence');return r;
}
const urlRoot='https://example.test/discovery/';
const fetcher=async url=>{const u=new URL(String(url));assert(u.href.startsWith(urlRoot));const ref=allowed.get(u.href.slice(urlRoot.length));assert(ref,'Unbound local source read');return new Response(raw(ref));};
const report=[];
for(const test of registry.cases){
  const query=eligible(test.question).slice(0,protocol.limits.query_tokens);
  const resolved=resolveConcepts(base,test.question).resolved;
  const extra=new Map();
  for(const item of resolved){const r=concepts.get(item.id);assert(r);for(const label of [r.label,...(r.aliases||[]).map(a=>typeof a==='string'?a:a.label)]){
    for(const token of eligible(label)){if(query.includes(token))continue;const ids=extra.get(token)||new Set();ids.add(item.id);extra.set(token,ids);}
  }}
  const tokens=[...extra.keys()].sort().slice(0,Math.min(protocol.limits.additional_alias_tokens,protocol.limits.query_tokens-query.length));
  const expansion=tokens.map(token=>({token,concept_ids:[...extra.get(token)].sort(),weight:1}));
  const baseline=rank(query.map(token=>({token,weight:1})));
  const variant=rank([...query.map(token=>({token,weight:2})),...expansion]);
  const actual=await assembleCorpusContext(manifest,{index_url:urlRoot+'manifest.json',index_sha256:bound.get('logical-context/manifest.json').sha256},test.question,{max_bytes:524288},fetcher);
  assert.deepEqual(baseline.candidates.map(r=>record(r.ordinal).id),actual.retrieval.candidates.map(r=>r.id),test.id+': baseline differs from actual engine');
  const references=test.candidate_ids.map(id=>{assert(candidates.has(id));return candidates.get(id);});
  function summarise(arm){
    const selected=arm.candidates.map(row=>{const r=record(row.ordinal);return {...row,id:r.id,label:r.label,text_bytes:Buffer.byteLength(r.text),unit_status:r.evidence_unit.completeness,boundary_status:r.evidence_unit.boundary_status,source_urls:r.evidence_unit.spans.map(s=>s.source_url)};});
    const chosen=new Set(selected.map(r=>r.id));
    const overlaps=references.filter(r=>r.overlapping_units.some(u=>chosen.has(u.id))).map(r=>r.id);
    return {matching_units:arm.matching_units,candidates:selected,candidate_location_overlap:overlaps,total_top16_text_bytes:selected.reduce((n,r)=>n+r.text_bytes,0)};
  }
  const a=summarise(baseline),b=summarise(variant);
  report.push({case_id:test.id,question:test.question,duplicate_of:test.duplicate_of,query_tokens:query,resolved_concepts:resolved.map(r=>r.id),expansion,omitted_expansion_tokens:[...extra.keys()].sort().filter(t=>!tokens.includes(t)),candidate_source_ids:test.candidate_ids,baseline_exact_engine_match:true,A:a,B0:b,delta_candidate_location_overlap:b.candidate_location_overlap.length-a.candidate_location_overlap.length});
  console.log(test.id,JSON.stringify({A:a.candidate_location_overlap.length,B0:b.candidate_location_overlap.length,aliases:tokens}));
}
read('scripts/probe_discovery_terminology.mjs');
const output={schema:'okf-dwp-discovery-probe.v1',protocol,engine:approved,source_snapshot:manifest.bundle.snapshot,network_calls:0,model_calls:0,scope:'Candidate ranking only, no new context assembly or AI answering for B0; candidate-location overlap is not relevance or answer accuracy.',counts:{cases:report.length,baseline_exact_engine_matches:report.filter(r=>r.baseline_exact_engine_match).length,candidate_overlap_increased:report.filter(r=>r.delta_candidate_location_overlap>0).length,candidate_overlap_decreased:report.filter(r=>r.delta_candidate_location_overlap<0).length,candidate_overlap_unchanged:report.filter(r=>r.delta_candidate_location_overlap===0).length},inputs:[...inputs.values()].sort((a,b)=>a.path<b.path?-1:1),cases:report};
const out=resolve(ROOT,'evaluation/discovery-probe/run');assert(!existsSync(out),'Preserve earlier probe outputs');mkdirSync(out);
writeFileSync(resolve(out,'comparison.json'),JSON.stringify(output,null,2)+'\n');writeFileSync(resolve(out,'runner.mjs'),readFileSync(fileURLToPath(import.meta.url)));
console.log(JSON.stringify(output.counts));
