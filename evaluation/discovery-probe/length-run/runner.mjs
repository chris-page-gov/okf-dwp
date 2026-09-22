#!/usr/bin/env node
/** Offline, fixed-parameter length-aware ranking probe. No production writes. */
import assert from 'node:assert/strict';
import {readFileSync, writeFileSync, mkdirSync, existsSync, realpathSync, lstatSync} from 'node:fs';
import {resolve, dirname} from 'node:path';
import {fileURLToPath, pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {gunzipSync} from 'node:zlib';

const ROOT=resolve(dirname(fileURLToPath(import.meta.url)), '..');
const args=process.argv.slice(2); assert.equal(args.length,2); assert.equal(args[0],'--explorer-root');
const explorer=realpathSync(resolve(args[1]));
const out=resolve(ROOT,'evaluation/discovery-probe/length-run');
assert(!existsSync(out),'Preserve earlier probe outputs before reproducing');
const inputs=new Map();
const sha=b=>createHash('sha256').update(b).digest('hex');
function read(relative,expected,limit=16*1024*1024){
  assert(typeof relative==='string'&&!relative.startsWith('/')&&!relative.includes('\\')&&!relative.split('/').some(x=>!x||x==='..'||x==='.'),'Unconfined input');
  const path=resolve(ROOT,relative);assert.equal(realpathSync(path),path);
  const st=lstatSync(path);assert(st.isFile()&&st.size<=limit);
  const bytes=readFileSync(path);assert.equal(bytes.length,st.size);
  const ref={path:relative,sha256:sha(bytes),bytes:bytes.length};
  if(expected){assert.equal(ref.sha256,expected.sha256);assert.equal(ref.bytes,expected.bytes);}
  inputs.set(relative,ref);return bytes;
}
const protocol=JSON.parse(read('evaluation/discovery-probe/length-protocol.json'));
assert.equal(protocol.schema,'okf-dwp-length-ranking-probe-protocol.v1');
const bound=new Map(protocol.inputs.map(r=>[r.path,r]));
for(const ref of protocol.inputs)read(ref.path,ref);
const parse=path=>JSON.parse(read(path,bound.get(path)));
const approved=parse('evaluation/logical-units/engine.json');
assert.deepEqual(Object.keys(approved.files).sort(),['corpus.ts','index.ts','types.ts','unit.ts']);
const engine=resolve(explorer,'apps/okf-explorer/src/lib/context');
for(const [name,hash] of Object.entries(approved.files)){
  assert.match(hash,/^[0-9a-f]{64}$/);
  assert.equal(sha(readFileSync(resolve(engine,name))),hash);
  assert.equal(sha(execFileSync('git',['-C',explorer,'show',`${approved.commit}:apps/okf-explorer/src/lib/context/${name}`],{maxBuffer:8*1024*1024})),hash);
}
const {corpusTokens,validateContextCorpusManifest}=await import(pathToFileURL(resolve(engine,'corpus.ts')));
const {isQuestionScaffolding}=await import(pathToFileURL(resolve(engine,'index.ts')));
const manifest=validateContextCorpusManifest(parse('logical-context/manifest.json'));
const previous=parse('evaluation/discovery-probe/run/comparison.json');
const questions=parse('evaluation/staff-questions/cases.json');
const coverage=parse('evaluation/semantic-coverage/closure-2026-09-22/audit.json');
assert.equal(previous.source_snapshot,manifest.bundle.snapshot);
assert.equal(previous.cases.length,40);assert.equal(questions.cases.length,40);
const queries=new Map(previous.cases.map(c=>[c.case_id,c.query_tokens]));
for(const c of questions.cases){
  assert.deepEqual(queries.get(c.id),corpusTokens(c.question).filter(t=>t.length<=64&&!isQuestionScaffolding(t)).slice(0,24));
  assert.equal(previous.cases.find(r=>r.case_id===c.id).question,c.question);
}
const terms=new Set([...queries.values()].flat());
const postings=new Map([...terms].map(t=>[t,[]]));
const records=[];let totalTokens=0;
for(const ref of manifest.records.shards){
  let bytes=read('logical-context/'+ref.path,ref,8*1024*1024);
  if(ref.encoding==='gzip'){
    assert(ref.decoded_bytes>0&&ref.decoded_bytes<=4*1024*1024);
    bytes=gunzipSync(bytes,{maxOutputLength:ref.decoded_bytes});
    assert.equal(bytes.length,ref.decoded_bytes);assert.equal(sha(bytes),ref.decoded_sha256);
  }
  const shard=JSON.parse(bytes);assert.equal(shard.schema,'okf-context-records.v1');
  assert.equal(shard.first_ordinal,records.length);assert.equal(shard.records.length,ref.count);
  for(const r of shard.records){
    assert.equal(r.kind,'evidence');assert.equal(typeof r.text,'string');
    const tokens=r.text.normalize('NFKD').replace(/\p{M}/gu,'').toLowerCase().match(/[a-z0-9]{2,}/g)||[];
    assert.deepEqual([...new Set(tokens)],corpusTokens(r.text));
    const ordinal=records.length, counts=new Map();
    for(const token of tokens)if(terms.has(token))counts.set(token,(counts.get(token)||0)+1);
    for(const [token,tf] of counts)postings.get(token).push({ordinal,tf});
    totalTokens+=tokens.length;
    records.push({id:r.id,label:r.label,text_bytes:Buffer.byteLength(r.text),tokens:tokens.length,unit_status:r.evidence_unit.completeness,boundary_status:r.evidence_unit.boundary_status,source_urls:r.evidence_unit.spans.map(s=>s.source_url)});
  }
}
assert.equal(records.length,manifest.records.count);
const N=records.length,avgdl=totalTokens/N;
assert(avgdl>0&&Number.isFinite(avgdl));
const {k1,b,candidates:limit}=protocol.parameters;
assert.deepEqual(protocol.parameters,{k1:1.2,b:0.75,candidates:16});
function rank(query,bm25){
  const rows=new Map();
  for(const token of query){
    const list=postings.get(token);assert(list);
    const df=list.length;
    const idf=bm25?Math.log(1+(N-df+0.5)/(df+0.5)):1+Math.floor(1000*Math.log2(1+N/Math.max(1,df)));
    for(const {ordinal,tf} of list){
      const row=rows.get(ordinal)||{ordinal,score:0,matched:[]};
      const score=bm25?idf*(tf*(k1+1))/(tf+k1*(1-b+b*records[ordinal].tokens/avgdl)):idf;
      assert(Number.isFinite(score));row.score+=score;row.matched.push({token,tf,df,contribution:score});rows.set(ordinal,row);
    }
  }
  return {matching_units:rows.size,candidates:[...rows.values()].sort((a,b)=>b.score-a.score||a.ordinal-b.ordinal).slice(0,limit)};
}
const candidateSources=new Map(coverage.candidate_sources.map(r=>[r.id,r]));
const report=[];
for(const c of questions.cases){
  const old=previous.cases.find(r=>r.case_id===c.id),query=queries.get(c.id);
  const a=rank(query,false),result=rank(query,true);
  assert.deepEqual(a.candidates.map(r=>({ordinal:r.ordinal,score:r.score})),old.A.candidates.map(r=>({ordinal:r.ordinal,score:r.score})),c.id+': reconstructed A differs');
  const candidates=result.candidates.map(r=>({...r,...records[r.ordinal]}));
  const chosen=new Set(candidates.map(r=>r.id));
  const overlap=c.candidate_ids.filter(id=>{assert(candidateSources.has(id));return candidateSources.get(id).overlapping_units.some(r=>chosen.has(r.id));});
  const B1={matching_units:result.matching_units,candidates,candidate_location_overlap:overlap,total_top16_text_bytes:candidates.reduce((n,r)=>n+r.text_bytes,0)};
  report.push({case_id:c.id,question:c.question,duplicate_of:c.duplicate_of,query_tokens:query,candidate_source_ids:c.candidate_ids,baseline_reconstruction_match:true,A:old.A,B1,delta_candidate_location_overlap:overlap.length-old.A.candidate_location_overlap.length});
  console.log(c.id,JSON.stringify({A:old.A.candidate_location_overlap.length,B1:overlap.length,bytes:B1.total_top16_text_bytes}));
}
read('scripts/probe_discovery_length.mjs');
const median=values=>{const x=values.slice().sort((a,b)=>a-b);return (x[(x.length-1)>>1]+x[x.length>>1])/2;};
const output={schema:'okf-dwp-length-ranking-probe.v1',protocol,engine:approved,source_snapshot:manifest.bundle.snapshot,network_calls:0,model_calls:0,scope:'Candidate ranking only. No B1 graph expansion, context assembly or AI answering. Candidate-location overlap is not relevance or answer accuracy.',corpus:{records:N,total_tokens:totalTokens,mean_tokens:avgdl},counts:{cases:report.length,baseline_reconstruction_matches:40,candidate_overlap_increased:report.filter(r=>r.delta_candidate_location_overlap>0).length,candidate_overlap_decreased:report.filter(r=>r.delta_candidate_location_overlap<0).length,candidate_overlap_unchanged:report.filter(r=>r.delta_candidate_location_overlap===0).length},summary:Object.fromEntries(['A','B1'].map(arm=>[arm,{candidate_location_overlaps:report.reduce((n,r)=>n+r[arm].candidate_location_overlap.length,0),median_top16_text_bytes:median(report.map(r=>r[arm].total_top16_text_bytes))}])),inputs:[...inputs.values()].sort((a,b)=>a.path<b.path?-1:1),cases:report};
mkdirSync(out);writeFileSync(resolve(out,'comparison.json'),JSON.stringify(output,null,2)+'\n');
writeFileSync(resolve(out,'runner.mjs'),readFileSync(fileURLToPath(import.meta.url)));
console.log(JSON.stringify({counts:output.counts,summary:output.summary}));
