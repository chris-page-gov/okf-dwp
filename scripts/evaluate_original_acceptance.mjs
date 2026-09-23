#!/usr/bin/env node
/** Separate, offline original-case acceptance: no staff-question denominator. */
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,existsSync,lstatSync,realpathSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {dirname,resolve} from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {gzipSync,gunzipSync} from 'node:zlib';
import {execFileSync} from 'node:child_process';
const ROOT=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const args=process.argv.slice(2),check=args.includes('--check'),filtered=args.filter(a=>a!=='--check');
assert.equal(args.length-filtered.length,check?1:0);assert.equal(filtered.length,4);
assert.equal(filtered[0],'--explorer-root');assert.equal(filtered[2],'--attempt');
assert.match(filtered[3],/^[a-z0-9-]{1,60}$/);
const explorer=realpathSync(resolve(filtered[1])),prefix='evaluation/manual-structure/original-acceptance/';
const out=resolve(ROOT,prefix,'runs',filtered[3]);
// Reject redirected output ancestors before any checkpoint or failure write.
let outputAncestor=ROOT;
for(const part of out.slice(ROOT.length+1).split('/')){
 outputAncestor=resolve(outputAncestor,part);
 let stat;try{stat=lstatSync(outputAncestor);}catch(error){if(error.code==='ENOENT')break;throw error;}
 assert(!stat.isSymbolicLink()&&stat.isDirectory(),'Output ancestor must be a real directory');
 assert.equal(realpathSync(outputAncestor),outputAncestor,'Output ancestor escapes the repository');
}
assert(check?existsSync(out):!existsSync(out),'Use a fresh attempt, or --check an existing receipt');
const sha=b=>createHash('sha256').update(b).digest('hex'),inputs=new Map();
const runner=readFileSync(fileURLToPath(import.meta.url));
function read(relative,ref,max=16*1024*1024){
 assert(typeof relative==='string'&&!relative.startsWith('/')&&!relative.includes('\\')
  &&relative.split('/').every(p=>p&&p!=='.'&&p!=='..'),'Unsafe source path');
 const path=resolve(ROOT,relative);assert.equal(realpathSync(path),path);
 const st=lstatSync(path);assert(st.isFile()&&st.size<=max);
 const raw=readFileSync(path),binding={path:relative,bytes:raw.length,sha256:sha(raw)};
 if(ref){assert.equal(binding.bytes,ref.bytes);assert.equal(binding.sha256,ref.sha256);}
 inputs.set(relative,binding);return raw;
}
if(check)assert.deepEqual(readFileSync(resolve(out,'evaluator.mjs')),runner);
else{mkdirSync(out,{recursive:true});writeFileSync(resolve(out,'evaluator.mjs'),runner);}
const rows=[];let current={phase:'preflight'};
try{
 const protocol=JSON.parse(read(prefix+'protocol.json'));
 assert.equal(protocol.schema,'okf-dwp-original-acceptance-protocol.v1');
 assert.equal(protocol.status,'frozen-before-original-case-experiment','Freeze final source before running');
 assert.equal(protocol.engine.commit,'8a5b8d11a2d99935efca4ba8366812844061d928');
 assert.deepEqual(protocol.budgets,[32768,524288]);
 assert.deepEqual(protocol.unknown_control,{id:'unknown-control',question:'xylophonicquasarteleportation'});
 const helperPaths=['scripts/original_acceptance_metrics.mjs','scripts/structured_context_metrics.mjs','scripts/structured_restoration_admission.mjs'];
 assert.deepEqual(protocol.helpers.map(r=>r.path).sort(),[...helperPaths].sort());
 for(const ref of protocol.helpers)read(ref.path,ref);
 const {originalAcceptanceMetrics}=await import(pathToFileURL(resolve(ROOT,helperPaths[0])));
 const {admitRestoredScopes}=await import(pathToFileURL(resolve(ROOT,helperPaths[2])));
 const engine=resolve(explorer,'apps/okf-explorer/src/lib/context');
 assert.deepEqual(Object.keys(protocol.engine.files).sort(),['corpus.ts','corpusV3.ts','index.ts','types.ts','unit.ts']);
 for(const [file,hash]of Object.entries(protocol.engine.files)){
  assert.equal(sha(readFileSync(resolve(engine,file))),hash);
  assert.equal(sha(execFileSync('git',['-C',explorer,'show',protocol.engine.commit+':apps/okf-explorer/src/lib/context/'+file],{maxBuffer:8*1024*1024})),hash);
 }
 const {canonicalJson,resolveConcepts}=await import(pathToFileURL(resolve(engine,'index.ts')));
 const {assembleCorpusContext,validateContextCorpusManifest}=await import(pathToFileURL(resolve(engine,'corpus.ts')));
 const source=protocol.source;assert.equal(source.path,'structured-context/manifest.json');
 const raw=read(source.path,source),manifest=validateContextCorpusManifest(JSON.parse(raw));
 assert.equal(manifest.schema,'okf-context-corpus.v3');
 const base=JSON.parse(read('structured-context/'+manifest.base_index.path,manifest.base_index));
 const author=JSON.parse(read(protocol.author.path,protocol.author));
 const ledger=JSON.parse(read(protocol.ledger.path,protocol.ledger));
 const original=JSON.parse(read(protocol.original_index.path,protocol.original_index));
 admitRestoredScopes({author,ledger,original,candidate:base,canonicalJson});
 assert.equal(ledger.profiles.length,6);assert.equal(ledger.original_requirements.length,6);
 assert.equal(new Set(ledger.profiles.flatMap(p=>p.unit_ids)).size,53);
 const refs=[manifest.base_index,...manifest.records.shards,...Object.values(manifest.search.shards),
  ...manifest.discovery.shards,...Object.values(manifest.relationships.shards)];
 const allowed=new Map(refs.map(r=>[r.path,r])),cache=new Map(),declaredEdges=new Map();
 // These are source-bound preflight reads, not extra retrieval seeds or an AI context.
 for(const ref of Object.values(manifest.relationships.shards)){
  const data=read('structured-context/'+ref.path,ref);
  const decoded=gunzipSync(data,{maxOutputLength:ref.decoded_bytes});assert.equal(decoded.length,ref.decoded_bytes);
  assert.equal(sha(decoded),ref.decoded_sha256);
  for(const row of JSON.parse(decoded).entries)for(const edge of row.outgoing){
   assert(!declaredEdges.has(edge.id),'Duplicate outgoing relationship identity');declaredEdges.set(edge.id,edge);
  }
 }
 const binding={index_url:'https://example.test/frozen-'+sha(raw)+'/structured-context/manifest.json',index_sha256:sha(raw)};
 const urlRoot=new URL('.',binding.index_url);
 const fetcher=async url=>{
  const u=new URL(String(url));assert.equal(u.origin,urlRoot.origin);assert(u.href.startsWith(urlRoot.href));
  const relative=u.href.slice(urlRoot.href.length),ref=allowed.get(relative);assert(ref,'Unbound corpus read');
  if(!cache.has(relative))cache.set(relative,read('structured-context/'+relative,ref));return new Response(cache.get(relative));
 };
 assert.deepEqual(protocol.case_fixtures.map(r=>r.path),['evaluation/context-assembly/imprisonment-case.json','evaluation/remote-mcp/hospital-case.json']);
 const cases=protocol.case_fixtures.map(ref=>JSON.parse(read(ref.path,ref)));
 assert.equal(cases[0].id,'dwp/imprisonment-four-benefit-comparison');
 assert.equal(cases[1].id,'dwp/hospital-four-benefit-evidence-gap');
 cases.push({id:'unknown-control',question:'xylophonicquasarteleportation',scope:'Unrelated vocabulary control',expected:{}});
 const unitBindings=new Map(author.source_units.map(r=>[r.id,r]));
 for(const test of cases)for(const max_bytes of protocol.budgets){
  current={phase:'assembly',case_id:test.id,max_bytes};
  const pack=await assembleCorpusContext(manifest,binding,test.question,{max_bytes},fetcher);
  const bytes=Buffer.from(canonicalJson(pack));assert.equal(bytes.length,pack.budget.used_bytes);assert(bytes.length<=max_bytes);
  assert.equal(pack.ai_answer,null);assert.equal(pack.evidence_status,'insufficient');
  assert(!pack.missing_evidence.some(i=>['evidence_digest_mismatch','unit_fragment_integrity','discovery_card_integrity','corpus_fetch_failed'].includes(i.code)),
   'Integrity failure is not acceptable insufficiency');
  const evidence=pack.selected.filter(s=>s.record.kind==='evidence');
  for(const {record}of evidence){
   for(const p of record.provenance)if(p.literal_sha256)assert.equal(sha(record.text),p.literal_sha256);
   for(const s of record.evidence_unit?.spans||[])assert.equal(sha(Buffer.from(record.text).subarray(s.unit_start,s.unit_end)),s.literal_sha256);
   if(unitBindings.has(record.id))assert.equal(sha(canonicalJson(record)+'\n'),unitBindings.get(record.id).record_sha256);
  }
  const resolved=resolveConcepts(base,test.question).resolved.map(r=>r.id);
  const metrics=originalAcceptanceMetrics({pack,base,ledger,resolvedIds:resolved,assertions:[...declaredEdges.values()]});
  if(test.id==='unknown-control'){assert.equal(evidence.length,0);assert.equal(metrics.active_translated_requirement_ids.length,0);}
  if(test.id==='dwp/hospital-four-benefit-evidence-gap')assert.equal(metrics.active_translated_requirement_ids.length,0,'Hospital control must not acquire custody profiles');
  const archive=test.id.replaceAll('/','-')+'-'+max_bytes+'.json.gz';
  if(check)assert.deepEqual(gunzipSync(readFileSync(resolve(out,archive)),{maxOutputLength:max_bytes}),bytes);
  else writeFileSync(resolve(out,archive),gzipSync(bytes,{level:9,mtime:0}));
  const retained=new Set(evidence.map(s=>s.record.id));
  rows.push({case_id:test.id,question:test.question,original_fixture_scope:test.scope,
   original_fixture_expectations_preserved:test.expected,max_bytes,archive,context_id:pack.context_id,
   sha256:sha(bytes),bytes:bytes.length,evidence_status:pack.evidence_status,
   source_units:evidence.length,source_text_bytes:evidence.reduce((n,s)=>n+Buffer.byteLength(s.record.text),0),
   declared_resolved_concepts:resolved,delivered_resolved_concepts:pack.resolved_concepts.map(r=>r.id),
   custody:metrics,passages:author.source_units.filter(r=>r.paragraph_labels.length&&metrics.translated_selection.retained_active_unit_ids.includes(r.id))
    .map(r=>({id:r.id,paragraph_labels:r.paragraph_labels,source_sha256:r.source_sha256,spans:r.spans,retained:retained.has(r.id)})),
   contemporary_scope:{dmg12016_selected:author.source_units.some(r=>r.paragraph_labels.includes('12016')&&retained.has(r.id)),
    adm_source_family_present:!!(manifest.source_groups||manifest.extensions?.source_groups||[]).some(g=>g.id==='adm'),
    status:'Contemporary ADM bodies and legal applicability are not made complete by the legacy custody translation.'},
   missing_evidence:pack.missing_evidence,ambiguities:pack.ambiguities,unresolved_terms:pack.unresolved_terms,
   retrieval_truncated:pack.retrieval?.truncated,assembly_truncated:pack.budget.truncated,
   retrieval_omissions:pack.retrieval?.omissions||[],assembly_omissions:pack.budget.omissions,
   fetched_files:pack.retrieval?.fetched_files,relationships:pack.relationships.length});
  if(!check)writeFileSync(resolve(out,'progress.json'),JSON.stringify({completed:rows.length,last:current},null,2)+'\n');
 }
 for(const ref of inputs.values())read(ref.path,ref);
 for(const [file,hash]of Object.entries(protocol.engine.files))assert.equal(sha(readFileSync(resolve(engine,file))),hash,'Engine changed during run');
 assert.deepEqual(readFileSync(fileURLToPath(import.meta.url)),runner,'Runner changed during run');
 const report={schema:'okf-dwp-original-acceptance-evaluation.v1',protocol,runner_sha256:sha(runner),
  inputs:[...inputs.values()].sort((a,b)=>a.path.localeCompare(b.path,'en')),network_calls:0,model_calls:0,rows,
  limitations:protocol.limitations};
 if(check)assert.deepEqual(JSON.parse(readFileSync(resolve(out,'report.json'))),report);
 else writeFileSync(resolve(out,'report.json'),JSON.stringify(report,null,2)+'\n');
 console.log(JSON.stringify({assemblies:rows.length,original_cases:2,unknown_controls:2,all_insufficient:true,network_calls:0,model_calls:0}));
}catch(error){
 if(!check)writeFileSync(resolve(out,'failure.json'),JSON.stringify({current,error:String(error),stack:String(error.stack||'').slice(0,8000),
  completed_rows:rows,inputs:[...inputs.values()],runner_sha256:sha(runner),network_calls:0,model_calls:0},null,2)+'\n');
 process.exitCode=1;console.error(String(error));
}
