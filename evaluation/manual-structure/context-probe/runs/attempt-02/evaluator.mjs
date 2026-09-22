#!/usr/bin/env node
/** Fixed-source discovery comparison; exact engine, offline, retained attempts. */
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,lstatSync,realpathSync,existsSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {dirname,resolve} from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {gzipSync,gunzipSync} from 'node:zlib';
import {execFileSync} from 'node:child_process';
import {performance} from 'node:perf_hooks';
const ROOT=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const rawArgs=process.argv.slice(2),check=rawArgs.includes('--check');
assert(rawArgs.filter(a=>a==='--check').length<=1);
const args=rawArgs.filter(a=>a!=='--check');
assert.equal(args.length,4);assert.equal(args[0],'--explorer-root');assert.equal(args[2],'--attempt');
assert.match(args[3],/^[a-z0-9-]{1,60}$/);
const explorer=realpathSync(resolve(args[1]));
const out=resolve(ROOT,'evaluation/manual-structure/context-probe/runs',args[3]);
assert(check?existsSync(out):!existsSync(out),check?'Missing retained attempt':'Retain earlier attempts; choose a fresh name');
const sha=raw=>createHash('sha256').update(raw).digest('hex'),inputs=new Map();
function read(relative,expected,max=16*1024*1024){
 assert(!relative.startsWith('/')&&!relative.includes('\\')&&relative.split('/').every(p=>p&&p!=='.'&&p!=='..'),'Unsafe input');
 const path=resolve(ROOT,relative);assert.equal(realpathSync(path),path);const st=lstatSync(path);assert(st.isFile()&&st.size<=max);
 const raw=readFileSync(path),ref={path:relative,bytes:raw.length,sha256:sha(raw)};
 if(expected){assert.equal(ref.bytes,expected.bytes);assert.equal(ref.sha256,expected.sha256);}
 inputs.set(relative,ref);return raw;
}
if(check)assert.deepEqual(readFileSync(resolve(out,'evaluator.mjs')),readFileSync(fileURLToPath(import.meta.url)),'Replay runner differs');
else {mkdirSync(out,{recursive:true});writeFileSync(resolve(out,'evaluator.mjs'),readFileSync(fileURLToPath(import.meta.url)));}
const rows=[],timing=[]; let current={phase:'preflight'};
try {
const prefix='evaluation/manual-structure/context-probe/';
const protocol=JSON.parse(read(prefix+'protocol.json')),approved=JSON.parse(read(prefix+'engine.json'));
const questions=JSON.parse(read(protocol.cases.path,protocol.cases));assert.equal(questions.cases.length,40);
const engine=resolve(explorer,'apps/okf-explorer/src/lib/context');
for(const [file,hash] of Object.entries(approved.files)){
 assert.equal(sha(readFileSync(resolve(engine,file))),hash);
 assert.equal(sha(execFileSync('git',['-C',explorer,'show',`${approved.commit}:apps/okf-explorer/src/lib/context/${file}`],{maxBuffer:8*1024*1024})),hash);
}
const {canonicalJson,resolveConcepts}=await import(pathToFileURL(resolve(engine,'index.ts')));
const {assembleCorpusContext,validateContextCorpusManifest}=await import(pathToFileURL(resolve(engine,'corpus.ts')));
const sources=[];
for(const stage of protocol.stages){
 const frozen=protocol.source_bindings?.find(r=>r.path===stage+'/manifest.json');assert(frozen,'Freeze source manifests before the first context comparison');
 const raw=read(stage+'/manifest.json',frozen),manifest=validateContextCorpusManifest(JSON.parse(raw));
 const refs=[manifest.base_index,...manifest.records.shards,...Object.values(manifest.search.shards),
   ...(manifest.discovery?.shards||[]),...Object.values(manifest.relationships?.shards||{})];
 const allowed=new Map(refs.map(ref=>[ref.path,ref])),cache=new Map();
 const binding={index_url:`https://example.test/frozen-${sha(raw)}/${stage}/manifest.json`,index_sha256:sha(raw)};
 const urlRoot=new URL('.',binding.index_url);
 const fetcher=async url=>{const u=new URL(String(url));assert.equal(u.origin,urlRoot.origin);assert(u.href.startsWith(urlRoot.href));
  const relative=u.href.slice(urlRoot.href.length),ref=allowed.get(relative);assert(ref,'Unbound corpus read');
  if(!cache.has(relative))cache.set(relative,read(stage+'/'+relative,ref));return new Response(cache.get(relative));};
 const base=JSON.parse(read(stage+'/'+manifest.base_index.path,manifest.base_index));
 sources.push({stage,manifest,binding,fetcher,base});
}
const physical=['documents','pages','nonempty_pages','empty_pages'];
const groups=source=>source.manifest.source_groups||source.manifest.extensions.source_groups;
assert.deepEqual(groups(sources[0]).map(g=>({id:g.id,inventory:g.inventory})),groups(sources[1]).map(g=>({id:g.id,inventory:g.inventory})),'Frozen source inventory differs');
for(const field of physical)assert.equal(sources[0].manifest.counts[field],sources[1].manifest.counts[field],'Physical census differs: '+field);
assert.deepEqual(sources[0].base.records,sources[1].base.records,'Authored semantic records differ');
assert.deepEqual(sources[0].base.requirements,sources[1].base.requirements,'Authored evidence obligations differ');
const cases=[...questions.cases,{id:'unknown-control',question:'xylophonicquasarteleportation'}];
for(const test of cases)for(const run of sources)for(const max_bytes of protocol.budgets){
 current={phase:'assembly',case_id:test.id,stage:run.stage,max_bytes};
 const started=performance.now();
 const pack=await assembleCorpusContext(run.manifest,run.binding,test.question,{max_bytes},run.fetcher);
 timing.push({case_id:test.id,stage:run.stage,max_bytes,elapsed_ms:Math.round((performance.now()-started)*100)/100});
 const bytes=Buffer.from(canonicalJson(pack));assert.equal(bytes.length,pack.budget.used_bytes);assert(bytes.length<=max_bytes);
 assert.equal(pack.ai_answer,null);
 assert(!pack.missing_evidence.some(issue=>['evidence_digest_mismatch','unit_fragment_integrity','discovery_card_integrity','corpus_fetch_failed'].includes(issue.code)),
  'Input integrity/admission failure is not an acceptable insufficient answer');
 const evidence=pack.selected.filter(s=>s.record.kind==='evidence');
 for(const {record} of evidence){
  for(const p of record.provenance)if(p.literal_sha256)assert.equal(sha(record.text),p.literal_sha256);
  for(const s of record.evidence_unit?.spans||[])assert.equal(sha(Buffer.from(record.text).subarray(s.unit_start,s.unit_end)),s.literal_sha256);
 }
 if(test.id==='unknown-control')assert.equal(evidence.length,0);
 const selected=new Set(pack.selected.map(s=>s.record.id)),edges=new Set(pack.relationships.map(e=>e.id));
 const resolved=new Set(resolveConcepts(run.base,test.question).resolved.map(r=>r.id));
 const requirements=run.base.requirements.filter(r=>r.when_all.every(id=>resolved.has(id))),paths=requirements.flatMap(r=>r.required_paths||[]);
 const archive=`${run.stage}-${test.id}-${max_bytes}.json.gz`,archived=gzipSync(bytes,{level:9,mtime:0});
 if(check)assert.deepEqual(gunzipSync(readFileSync(resolve(out,archive)),{maxOutputLength:max_bytes}),bytes,'Archived context replay differs');
 else writeFileSync(resolve(out,archive),archived);
 rows.push({case_id:test.id,question:test.question,stage:run.stage,max_bytes,context_id:pack.context_id,sha256:sha(bytes),bytes:bytes.length,
  evidence_status:pack.evidence_status,evidence_records:evidence.length,source_text_bytes:evidence.reduce((sum,s)=>sum+Buffer.byteLength(s.record.text),0),
  resolved_concepts:pack.resolved_concepts.map(r=>r.id),active_requirements:requirements.map(r=>r.id),
  required_paths:paths.length,retained_required_paths:paths.filter(p=>p.records.every(id=>selected.has(id))&&p.assertions.every(id=>edges.has(id))).length,
  relationships:pack.relationships.length,unresolved_terms:pack.unresolved_terms,missing_evidence:pack.missing_evidence,
  retrieval_truncated:pack.retrieval?.truncated,assembly_truncated:pack.budget.truncated,
  card_diagnostic_bytes:Buffer.byteLength(canonicalJson(pack.retrieval?.discovery||null)),
  candidate_units:pack.retrieval?.candidates.length||0,archive});
 if(!check)writeFileSync(resolve(out,'progress.json'),JSON.stringify({completed:rows.length,last:{case_id:test.id,stage:run.stage,max_bytes}},null,2)+'\n');
}
const report={schema:'okf-dwp-structured-context-evaluation.v1',protocol,engine:approved,inputs:[...inputs.values()].sort((a,b)=>a.path.localeCompare(b.path,'en')),
 timing_scope:'Local sequential cached-order observation; mixed cold/warm reads, not a controlled speed benchmark or remote latency.',
 runner_sha256:sha(readFileSync(fileURLToPath(import.meta.url))),network_calls:0,model_calls:0,rows,
 limitations:protocol.limits};
if(check)assert.deepEqual(JSON.parse(readFileSync(resolve(out,'report.json'))),report,'Evaluation replay differs');
else writeFileSync(resolve(out,'report.json'),JSON.stringify(report,null,2)+'\n');
if(!check)writeFileSync(resolve(out,'timing.json'),JSON.stringify({observed_at:new Date().toISOString(),rows:timing},null,2)+'\n');
console.log(JSON.stringify({assemblies:rows.length,staff_occurrences:40,all_insufficient:rows.every(r=>r.evidence_status==='insufficient'),network_calls:0,model_calls:0}));

} catch(error) {
 if(!check)writeFileSync(resolve(out,'failure.json'),JSON.stringify({status:'failed',current,error:String(error),stack:String(error.stack||'').slice(0,8000),
  completed_rows:rows,inputs:[...inputs.values()],runner_sha256:sha(readFileSync(fileURLToPath(import.meta.url))),network_calls:0,model_calls:0},null,2)+'\n');
 process.exitCode=1; console.error(String(error));
}
