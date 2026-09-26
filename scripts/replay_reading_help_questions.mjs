#!/usr/bin/env node
/** Offline, fixed-budget non-regression replay for the additive reading aid. */
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFileSync,writeFileSync,mkdirSync,existsSync,realpathSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {performance} from 'node:perf_hooks';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const args=process.argv.slice(2);assert.equal(args.length,4);assert.equal(args[0],'--explorer-root');assert.equal(args[2],'--attempt');
assert.match(args[3],/^[a-z0-9-]{1,60}$/);
const explorer=realpathSync(args[1]),out=resolve(root,'evaluation/reading-help-rollout/replays',args[3]);
assert(!existsSync(out),'Preserve earlier attempts; select a new attempt');
const sha=x=>createHash('sha256').update(x).digest('hex');
const read=p=>readFileSync(resolve(root,p));
const previous=JSON.parse(read('evaluation/evidence-workbench/manifest.json'));
const source=previous.source,registryRaw=read(source.registry),manifestRaw=read(source.corpus);
assert.equal(sha(registryRaw),source.registry_sha256);assert.equal(sha(manifestRaw),source.corpus_sha256);
const cases=JSON.parse(registryRaw).cases;assert.equal(cases.length,40);
const engineDir=resolve(explorer,'apps/okf-explorer/src/lib/context');
for(const [name,hash] of Object.entries(source.engine_files))assert.equal(sha(readFileSync(resolve(engineDir,name))),hash,'Engine differs: '+name);
const {assembleCorpusContext,validateContextCorpusManifest}=await import(pathToFileURL(resolve(engineDir,'corpus.ts')));
const {canonicalJson}=await import(pathToFileURL(resolve(engineDir,'index.ts')));
const manifest=validateContextCorpusManifest(JSON.parse(manifestRaw));
const binding={index_url:'https://example.invalid/structured-context/evidence-connect-manifest.json',index_sha256:sha(manifestRaw)};
const prefix=new URL('.',binding.index_url).href;
const refs=new Map([manifest.base_index,...manifest.records.shards,...manifest.discovery.shards,...Object.values(manifest.search.shards),...Object.values(manifest.relationships.shards)].map(r=>[r.path,r]));
const budget={max_bytes:524288,max_nodes:64,max_relationships:128,max_depth:6};
const protocol={schema:'okf-reading-help-question-replay.v1',source,engine_files:source.engine_files,budget,cases:cases.map(c=>c.id),model_calls:0,network_calls:0,
  purpose:'Non-regression of retained evidence while reading assistance changes separately; not a retrieval-improvement or legal-answer benchmark.',
  limitations:['Expected text and qualifications use the fixed retained packages, not an independently reviewed complete legal answer key.','Warm measurement repeats each question with the same byte cache; engine assembly is repeated.','Reading-help labels do not create concepts, applicability or evidence requirements.']};
mkdirSync(out,{recursive:true});writeFileSync(resolve(out,'protocol.json'),JSON.stringify(protocol,null,2)+'\n');
writeFileSync(resolve(out,'runner.mjs'),readFileSync(fileURLToPath(import.meta.url)));
const results=[];
for(const c of cases){
 const ref=previous.questions.find(q=>q.id===c.id).package;
 const oldRaw=read('evaluation/evidence-workbench/'+ref.url);assert.equal(sha(oldRaw),ref.sha256);
 const old=JSON.parse(oldRaw);assert.equal(old.question,c.question);
 for(const [k,v] of Object.entries(budget))assert.equal(old.budget[k],v);
 const cache=new Map(),measurements=[];let failure=null,newContext;
 for(const temperature of ['cold','warm']){
  let fetchedBytes=0,reads=0,hits=0;
  const fetcher=async input=>{
   const url=new URL(String(input));assert(url.href.startsWith(prefix),'Network or traversal denied');const relative=url.href.slice(prefix.length),ref=refs.get(relative);assert(ref,'Unbound resource');
   if(cache.has(relative))hits++;
   else{const bytes=read('structured-context/'+relative);assert.equal(bytes.length,ref.bytes);assert.equal(sha(bytes),ref.sha256);cache.set(relative,bytes);fetchedBytes+=bytes.length;reads++;}
   return new Response(cache.get(relative));
  };
  const started=performance.now();
  try{newContext=await assembleCorpusContext(manifest,binding,c.question,budget,fetcher);
   const raw=Buffer.from(canonicalJson(newContext));
   assert.deepEqual(raw,oldRaw,'Retained package drift');
   assert.equal(newContext.ai_answer,null);
   measurements.push({temperature,latency_ms:Math.round((performance.now()-started)*100)/100,bytes_read:fetchedBytes,files_read:reads,cache_hits:hits,package_sha256:sha(raw),package_bytes:raw.length});
  }catch(e){failure=String(e);break;}
 }
 const selected=(newContext||old).selected.filter(s=>s.record.kind==='evidence');
 const row={case_id:c.id,passed:!failure,failure,measurements,evidence_status:(newContext||old).evidence_status,
  selected_evidence:selected.map(s=>({id:s.record.id,text_sha256:sha(s.record.text),relationship_paths:s.paths})),
  requirements:(newContext||old).requirements,missing_evidence:(newContext||old).missing_evidence,
  qualification_retention:'Exact retained record text and relationships checked; no independent completeness claim',
  wrong_selection:'Unchanged from baseline; independent relevance adjudication remains required'};
 results.push(row);writeFileSync(resolve(out,c.id+'.json'),JSON.stringify(row,null,2)+'\n');console.log(c.id,row.passed?'PASS':'FAIL');
}
const report={...protocol,passed:results.every(r=>r.passed),cases_passed:results.filter(r=>r.passed).length,cases_failed:results.filter(r=>!r.passed).map(r=>r.case_id),
  files:results.map(r=>{const path=r.case_id+'.json',bytes=readFileSync(resolve(out,path));return{path,bytes:bytes.length,sha256:sha(bytes)}}),
  total_cold_bytes:results.reduce((n,r)=>n+(r.measurements[0]?.bytes_read||0),0),total_warm_bytes:results.reduce((n,r)=>n+(r.measurements[1]?.bytes_read||0),0)};
writeFileSync(resolve(out,'report.json'),JSON.stringify(report,null,2)+'\n');
assert(report.passed,'Failures retained; inspect this attempt');console.log(JSON.stringify({cases:40,passed:report.passed,model_calls:0,network_calls:0}));
