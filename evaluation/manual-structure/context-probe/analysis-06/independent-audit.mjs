#!/usr/bin/env node
/** Read retained bytes only: no assembly, source acquisition or model calls. */
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,existsSync,realpathSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
import {gunzipSync} from 'node:zlib';
import {execFileSync} from 'node:child_process';
const HERE=dirname(fileURLToPath(import.meta.url)),ROOT=resolve(HERE,'../../../..');
assert.equal(process.argv[2],'--explorer-root');assert.equal(process.argv.length,4);
const explorer=realpathSync(resolve(process.argv[3]));
const output=resolve(HERE,'independent-review.json');assert(!existsSync(output),'Preserve earlier receipt');
const hash=x=>createHash('sha256').update(x).digest('hex');
const canonical=x=>Array.isArray(x)?`[${x.map(canonical).join(',')}]`:x&&typeof x==='object'?`{${Object.keys(x).sort().filter(k=>x[k]!==undefined).map(k=>JSON.stringify(k)+':'+canonical(x[k])).join(',')}}`:JSON.stringify(x);
const same=(a,b,label)=>assert.deepEqual(a,b,label);
const file=p=>readFileSync(resolve(ROOT,p));
const bind=(p,raw=file(p))=>({path:p,bytes:raw.length,sha256:hash(raw)});
const frozen05='e85f2378';
const extraBindings=new Map(), sourceFiles=new Map(), selectedRecordIds=new Set(), sourceSpanIds=new Set();
function get(p,expected,attempt){
 assert(!p.startsWith('/')&&!p.includes('\\')&&p.split('/').every(x=>x&&x!=='.'&&x!=='..'));
 let raw=file(p);
 if(expected&&(raw.length!==expected.bytes||hash(raw)!==expected.sha256)){
  assert.equal(attempt,'attempt-05','Current final source changed: '+p);
  raw=execFileSync('git',['show',frozen05+':'+p],{cwd:ROOT,maxBuffer:32*1024*1024});
 }
 if(expected){same(raw.length,expected.bytes,p);same(hash(raw),expected.sha256,p);}
 extraBindings.set(attempt+':'+p,{attempt,...bind(p,raw)});return raw;
}
function loadRef(stage,ref,attempt){
 const raw=get(stage+'/'+ref.path,ref,attempt);
 const decoded=ref.encoding==='gzip'?gunzipSync(raw,{maxOutputLength:32*1024*1024}):raw;
 if(ref.decoded_bytes!==undefined)same(decoded.length,ref.decoded_bytes);
 if(ref.decoded_sha256)same(hash(decoded),ref.decoded_sha256);
 return JSON.parse(decoded);
}
function pathRetained(pack,path,declared,resolved){
 assert.equal(path.records.length,path.assertions.length+1);assert.equal(path.seed,path.records[0]);
 assert.equal(new Set(path.records).size,path.records.length);
 const selected=new Set(pack.selected.map(x=>x.record.id)),returned=new Map(pack.relationships.map(x=>[x.id,x]));
 return path.records.every(id=>selected.has(id))&&path.assertions.every((id,i)=>{
  const edge=returned.get(id),original=declared.get(id);
  if(!edge)return false;assert(original,'Unbound returned path edge '+id);same(edge,original,'Path assertion/guard changed');
  return edge.source===path.records[i]&&edge.target===path.records[i+1]&&(!edge.context_guard||edge.context_guard.when_all.every(c=>resolved.has(c)));
 });
}
function checkSource(record){
 if(selectedRecordIds.has(record.id))return;selectedRecordIds.add(record.id);
 const literal=Buffer.from(record.text);
 for(const p of record.provenance||[])if(p.literal_sha256)same(hash(literal),p.literal_sha256,'Whole source text hash');
 const unit=record.evidence_unit;if(!unit)return;
 const spans=[];
 for(const span of unit.spans){
  const prefix='https://github.com/chris-page-gov/okf-dwp/blob/main/';assert(span.extraction_url.startsWith(prefix));
  const path=span.extraction_url.slice(prefix.length);assert(path.startsWith('source/')&&path.endsWith('.json')&&!path.includes('..'));
  if(!sourceFiles.has(path)){const raw=file(path);sourceFiles.set(path,{raw,data:JSON.parse(raw)});}
  const {raw,data}=sourceFiles.get(path);same(hash(raw),span.extraction_sha256);same(data.source_sha256,span.source_sha256);
  const match=/^pages\[(\d+)\]\.text$/.exec(span.locator);assert(match);
  const page=Buffer.from(data.pages[Number(match[1])].text);same(page.length,span.source_text_bytes);same(hash(page),span.source_text_sha256);
  assert(0<=span.source_start&&span.source_start<span.source_end&&span.source_end<=page.length);
  const piece=page.subarray(span.source_start,span.source_end);same(hash(piece),span.literal_sha256);same(literal.subarray(span.unit_start,span.unit_end),piece);
  spans.push(piece);sourceSpanIds.add(path+':'+span.locator+':'+span.source_start+':'+span.source_end);
 }
 same(Buffer.concat(spans.flatMap((p,i)=>i?[Buffer.from(unit.joiner),p]:[p])),literal,'Complete source-span conservation');
}
const reports=Object.fromEntries(['attempt-05','attempt-06'].map(a=>[a,JSON.parse(file(`evaluation/manual-structure/context-probe/runs/${a}/report.json`))]));
const approved=reports['attempt-06'].engine;
same(reports['attempt-05'].engine,approved);same(Object.keys(approved.files).sort(),['corpus.ts','corpusV3.ts','index.ts','types.ts','unit.ts']);
for(const [name,digest]of Object.entries(approved.files)){
 const path='apps/okf-explorer/src/lib/context/'+name;
 same(hash(readFileSync(resolve(explorer,path))),digest);same(hash(execFileSync('git',['show',approved.commit+':'+path],{cwd:explorer,maxBuffer:8*1024*1024})),digest);
}
// Only the pure alias resolver is imported. Assembly and fetch modules are never invoked.
const {resolveConcepts}=await import(pathToFileURL(resolve(explorer,'apps/okf-explorer/src/lib/context/index.ts')));
const allResults=[],archiveBindings=[],baselineBytes=new Map();let baselineExact=0,returnedEdges=0,returnedPaths=0;
for(const [attempt,report]of Object.entries(reports)){
 same(report.schema,'okf-dwp-structured-context-evaluation.v1');same(report.network_calls,0);same(report.model_calls,0);
 same(hash(file(`evaluation/manual-structure/context-probe/runs/${attempt}/evaluator.mjs`)),report.runner_sha256);
 const inputMap=new Map(report.inputs.map(x=>[x.path,x]));same(inputMap.size,report.inputs.length);
 for(const ref of report.inputs)get(ref.path,ref,attempt);
 const p=report.protocol;
 same(JSON.parse(get('evaluation/manual-structure/context-probe/protocol.json',inputMap.get('evaluation/manual-structure/context-probe/protocol.json'),attempt)),p);
 same(JSON.parse(get('evaluation/manual-structure/context-probe/engine.json',inputMap.get('evaluation/manual-structure/context-probe/engine.json'),attempt)),report.engine);
 const cases=JSON.parse(get(p.cases.path,p.cases,attempt)).cases;same(cases.length,40);
 const expectedQuestions=new Map(cases.map(c=>[c.id,c.question]));expectedQuestions.set('unknown-control','xylophonicquasarteleportation');
 const expectedKeys=new Set([...expectedQuestions.keys()].flatMap(c=>p.stages.flatMap(s=>p.budgets.map(b=>`${c}|${s}|${b}`))));
 same(report.rows.length,expectedKeys.size);
 const sources=new Map();
 for(const stage of p.stages){
  const manifest=JSON.parse(get(stage+'/manifest.json',p.source_bindings.find(x=>x.path===stage+'/manifest.json'),attempt));
  const base=loadRef(stage,manifest.base_index,attempt),assertions=new Map(base.assertions.map(e=>[e.id,e]));
  for(const ref of Object.values(manifest.relationships?.shards||{}))for(const entry of loadRef(stage,ref,attempt).entries)for(const edge of [...entry.outgoing,...entry.incoming]){
   if(assertions.has(edge.id))same(assertions.get(edge.id),edge,'Conflicting declared assertion');else assertions.set(edge.id,edge);
  }
  const requiredIds=new Set(report.rows.filter(r=>r.stage===stage).flatMap(row=>JSON.parse(gunzipSync(file(`evaluation/manual-structure/context-probe/runs/${attempt}/${row.archive}`),{maxOutputLength:row.max_bytes})).selected.map(x=>x.record.id)));
  const records=new Map(base.records.map(r=>[r.id,r]));
  for(const ref of manifest.records.shards)if([...requiredIds].some(id=>id>=ref.first_id&&id<=ref.last_id)){
   for(const record of loadRef(stage,ref,attempt).records)if(requiredIds.has(record.id))records.set(record.id,record);
  }
  sources.set(stage,{manifest,base,assertions,records});
 }
 const ledger=JSON.parse(get(p.location_ledger.path,p.location_ledger,attempt)),byProfile=new Map(ledger.profiles.map(x=>[x.requirement_id,x]));
 const legacy=JSON.parse(get(p.legacy_requirements.source.path,p.legacy_requirements.source,attempt)).requirements;
 same(legacy.length,40);const open=new Set(legacy.flatMap(x=>x.required.filter(id=>id.includes('/id/obligation/staff/'))));same(open.size,203);
 for(const row of report.rows){
  const key=`${row.case_id}|${row.stage}|${row.max_bytes}`;assert(expectedKeys.delete(key),'Unexpected/duplicate cell');same(row.question,expectedQuestions.get(row.case_id));
  const archive=`evaluation/manual-structure/context-probe/runs/${attempt}/${row.archive}`;assert(!row.archive.includes('/')&&!row.archive.includes('..'));
  const compressed=file(archive),raw=gunzipSync(compressed,{maxOutputLength:row.max_bytes}),pack=JSON.parse(raw);archiveBindings.push({...bind(archive,compressed),decoded_sha256:hash(raw),decoded_bytes:raw.length});
  same(raw.toString(),canonical(pack));same(hash(raw),row.sha256);same(raw.length,row.bytes);same(raw.length,pack.budget.used_bytes);assert(raw.length<=row.max_bytes);
  const idInput={...pack,budget:{...pack.budget}};delete idInput.context_id;delete idInput.budget.used_bytes;
  same(pack.context_id,'urn:sha256:'+hash(canonical(idInput)));same(pack.context_id,row.context_id);same(pack.question,row.question);same(pack.ai_answer,null);same(pack.evidence_status,'insufficient');
  const source=sources.get(row.stage);same(pack.binding.index_sha256,p.source_bindings.find(x=>x.path===row.stage+'/manifest.json').sha256);
  const resolved=new Set(resolveConcepts(source.base,row.question).resolved.map(x=>x.id));same([...resolved].sort(),row.declared_resolved_concepts);
  const selected=new Map(pack.selected.map(x=>[x.record.id,x.record]));same(selected.size,pack.selected.length);
  const edges=new Map(pack.relationships.map(x=>[x.id,x]));same(edges.size,pack.relationships.length);
  for(const item of pack.selected){same(item.record,source.records.get(item.record.id),'Complete selected record differs from bound corpus');
   if(item.record.kind==='evidence')checkSource(item.record);
   for(const path of item.paths){assert(pathRetained(pack,path,source.assertions,resolved),'Returned selected path broken');returnedPaths++;}
  }
  for(const edge of edges.values()){same(edge,source.assertions.get(edge.id),'Returned edge differs from declared graph');assert(!edge.context_guard||edge.context_guard.when_all.every(c=>resolved.has(c)));returnedEdges++;}
  const evidence=pack.selected.filter(x=>x.record.kind==='evidence');same(evidence.length,row.evidence_records);same(evidence.reduce((n,x)=>n+Buffer.byteLength(x.record.text),0),row.source_text_bytes);
  same(pack.relationships.length,row.relationships);same(pack.resolved_concepts.map(x=>x.id),row.resolved_concepts);same(pack.missing_evidence,row.missing_evidence);
  same(pack.retrieval.truncated,row.retrieval_truncated);same(pack.budget.truncated,row.assembly_truncated);same(pack.unresolved_terms,row.unresolved_terms);
  assert(!pack.missing_evidence.some(x=>['evidence_digest_mismatch','unit_fragment_integrity','discovery_card_integrity','corpus_fetch_failed'].includes(x.code)));
  const active=source.base.requirements.filter(r=>r.when_all.every(c=>resolved.has(c)));same(active.map(x=>x.id),row.active_requirements);
  const paths=active.flatMap(r=>r.required_paths||[]);same(paths.length,row.required_paths);same(paths.filter(x=>pathRetained(pack,x,source.assertions,resolved)).length,row.retained_required_paths);
  for(const group of p.requirement_groups){const rows=active.filter(r=>group.requirement_ids.includes(r.id)),paths=rows.flatMap(x=>x.required_paths||[]);
   same(row.requirement_groups.find(x=>x.id===group.id),{id:group.id,active_requirements:rows.map(x=>x.id),required_paths:paths.length,retained_required_paths:paths.filter(x=>pathRetained(pack,x,source.assertions,resolved)).length});
  }
  const activeLegacy=legacy.filter(r=>source.base.requirements.some(x=>x.id===r.id)&&r.when_all.every(c=>resolved.has(c)));
  for(const requirement of legacy){const declared=source.base.requirements.find(x=>x.id===requirement.id);if(declared)same(declared,requirement);}
  same(activeLegacy.map(x=>x.id),row.location_navigation.active_legacy_requirement_ids);
  for(const id of open)assert(!selected.has(id));assert(!pack.requirements.some(x=>open.has(x.id)||legacy.some(l=>l.id===x.id)&&x.status==='supported-within-declared-scope'));
  const routes=activeLegacy.flatMap(r=>byProfile.get(r.id).navigation_routes);
  for(const kind of ['restored-original-route','inferred-profile-candidate-route']){
   const candidates=routes.filter(x=>x.derivation===kind),retained=candidates.filter(x=>pathRetained(pack,x,source.assertions,resolved));
   const metric=row.location_navigation.routes[kind];same(candidates.length,metric.declared_routes);same(retained.length,metric.retained_routes);
   for(const route of candidates){const edge=edges.get(route.assertion_id);if(edge)same(edge.context_guard,route.context_guard);}
  }
  if(row.case_id==='unknown-control'){same(evidence.length,0);same(pack.relationships.length,0);same(resolved.size,0);same(active.length,0);}
  if(row.stage==='logical-context'){if(attempt==='attempt-05')baselineBytes.set(key,raw);else{same(raw,baselineBytes.get(key),'Logical baseline changed');baselineExact++;}}
  allResults.push({attempt,...row});
 }
 same(expectedKeys.size,0);
}
const summary=[];
for(const attempt of Object.keys(reports))for(const stage of reports[attempt].protocol.stages)for(const max_bytes of reports[attempt].protocol.budgets){
 const rows=allResults.filter(r=>r.attempt===attempt&&r.stage===stage&&r.max_bytes===max_bytes&&r.case_id!=='unknown-control');
 summary.push({attempt,stage,max_bytes,cases:rows.length,cases_with_evidence:rows.filter(r=>r.evidence_records>0).length,
  source_read_cases:rows.filter(r=>r.requirement_groups.some(g=>['inherited-logical-source-selections','additional-source-read-selections','expanded-staff-source-read-selections'].includes(g.id)&&g.active_requirements.length)).length,
  source_read_gaps:rows.filter(r=>!r.requirement_groups.some(g=>['inherited-logical-source-selections','additional-source-read-selections','expanded-staff-source-read-selections'].includes(g.id)&&g.active_requirements.length)).map(r=>r.case_id),
  groups:reports[attempt].protocol.requirement_groups.map(g=>({id:g.id,declared:rows.reduce((n,r)=>n+r.requirement_groups.find(x=>x.id===g.id).required_paths,0),retained:rows.reduce((n,r)=>n+r.requirement_groups.find(x=>x.id===g.id).retained_required_paths,0)})),
  location_routes:Object.fromEntries(['restored-original-route','inferred-profile-candidate-route'].map(k=>[k,{declared:rows.reduce((n,r)=>n+r.location_navigation.routes[k].declared_routes,0),retained:rows.reduce((n,r)=>n+r.location_navigation.routes[k].retained_routes,0)}])),
  all_insufficient:rows.every(r=>r.evidence_status==='insufficient'),all_retrieval_truncated:rows.every(r=>r.retrieval_truncated),all_assembly_truncated:rows.every(r=>r.assembly_truncated)});
}
const receipt={schema:'okf-dwp-trial06-independent-archive-audit.v1',status:'passed-with-recorded-delivery-limitations',
 reviewer:'dependency_review: separate implementation from evaluator and summariser',assembly_calls:0,network_calls:0,model_calls:0,
 source_fallback_commit_for_trial05:execFileSync('git',['rev-parse',frozen05],{cwd:ROOT,encoding:'utf8'}).trim(),
 engine:approved,report_bindings:Object.keys(reports).map(a=>bind(`evaluation/manual-structure/context-probe/runs/${a}/report.json`)),
 audit_binding:bind('evaluation/manual-structure/context-probe/analysis-06/independent-audit.mjs'),
 checks:{complete_unique_cells_per_attempt:164,logical_baseline_byte_identical:baselineExact,input_bindings_per_attempt:Object.fromEntries(Object.entries(reports).map(([a,r])=>[a,r.inputs.length])),
 returned_edges_exactly_declared:returnedEdges,returned_selected_paths_verified:returnedPaths,unique_source_records_verified:selectedRecordIds.size,
 unique_source_spans_verified:sourceSpanIds.size,frozen_extraction_files_verified:sourceFiles.size,all_open_legacy_obligations_preserved:203,unknown_packages_zero_evidence:8},
 cells:summary,source_extractions:[...sourceFiles].map(([p,x])=>bind(p,x.raw)),read_bindings:[...extraBindings.values()],archive_bindings:archiveBindings,
 limitations:['No new assembly, retrieval, source acquisition, model or live service call.',
 'Pure engine alias resolution is checked against retained rows; scoring and graph/source conservation are independently recomputed without the evaluator metrics helper.',
 'Source spans are checked against frozen extraction bytes and retained PDF hash identifiers; this pass does not re-render PDFs or review legal meaning.',
 'All packages remain insufficient; all large staff packages truncate retrieval and assembly. All forty structured staff packages contain zero source evidence at32KiB.',
 'Location route counts are case incidences and may fall while required source-selection paths improve. All203 original obligations remain open.',
 'The separate original imprisonment/hospital acceptance run is outside this40staff denominator. This audit does not establish its success, legal completeness, specialist acceptance, answer accuracy, affordability or public deployment.']};
writeFileSync(output,JSON.stringify(receipt,null,2)+'\n');console.log(JSON.stringify({status:receipt.status,checks:receipt.checks,cells:summary},null,2));
