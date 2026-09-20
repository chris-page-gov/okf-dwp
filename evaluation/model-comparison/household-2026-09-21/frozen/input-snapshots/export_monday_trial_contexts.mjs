#!/usr/bin/env node
/** Preregister/check or freeze an immutable, offline paired-trial context set. */
import assert from 'node:assert/strict';
import {readFile,writeFile,mkdir,lstat,realpath} from 'node:fs/promises';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
export const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
export const SPEC='evaluation/model-comparison/household-2026-09-21';
const ENGINE='apps/okf-explorer/src/lib/context/';
const engineFiles=['index.ts','corpus.ts','types.ts'];
const supportFiles=['scripts/export_monday_trial_contexts.mjs','scripts/run_monday_model_trials.py','scripts/run_staff_model_trials.py','scripts/evaluate_fixed_answers.py'];
export const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
export function safeRelative(value){assert.equal(typeof value,'string');assert(value&&!value.includes('\\')&&!value.includes('\0')&&!path.isAbsolute(value)&&value.split('/').every(x=>x&&x!=='.'&&x!=='..'),'Unsafe relative path');return value;}
export function validateProtocol(p){
 assert.equal(p.schema,'okf-fixed-monday-model-protocol.v1');assert.equal(p.selected_cases.length,6);assert.equal(new Set(p.selected_cases).size,6);
 assert(p.selected_cases.includes('control-unknown'));assert(p.selected_cases.every(x=>/^staff-\d{3}$/.test(x)||x==='control-unknown'));
 assert.deepEqual(p.context_budget,{max_nodes:64,max_relationships:128,max_depth:6,max_bytes:262144});
 assert.deepEqual(p.providers,['claude-subscription','codex-subscription']);assert.equal(p.timeout_seconds,240);
 for(const f of [p.system_prompt,p.user_prompt,p.answer_schema])safeRelative(f);
 return p;
}
async function bounded(root,name,limit=32*1024*1024){
 safeRelative(name);const full=path.join(root,name);const info=await lstat(full);assert(info.isFile()&&!info.isSymbolicLink()&&info.size<=limit,'Not a bounded regular file');
 const resolved=await realpath(full);assert(resolved.startsWith((await realpath(root))+path.sep),'Path escaped root');
 const raw=await readFile(full);assert(raw.length<=limit,'Read exceeded bound');return raw;
}
function committed(root,commit,name,raw){
 assert.match(commit,/^[a-f0-9]{40}$/);safeRelative(name);
 const expected=execFileSync('git',['show',`${commit}:${name}`],{cwd:root,maxBuffer:40*1024*1024});assert.deepEqual(raw,expected,`Uncommitted or changed input: ${name}`);
}
export async function main(argv=process.argv.slice(2)){
 const flags={};for(let i=0;i<argv.length;i++){const a=argv[i];assert(['--check-preregistration','--freeze','--check','--dwp-commit','--explorer-commit','--explorer-root'].includes(a),`Unknown flag ${a}`);assert(!(a in flags),'Repeated flag');flags[a]=['--check-preregistration','--freeze','--check'].includes(a)?true:argv[++i];}
 assert.equal(['--check-preregistration','--freeze','--check'].filter(x=>flags[x]).length,1,'Choose exactly one operation');
 const protocolRaw=await bounded(ROOT,SPEC+'/protocol.json',65536),protocol=validateProtocol(JSON.parse(protocolRaw));
 const system=await bounded(ROOT,SPEC+'/'+protocol.system_prompt,65536),template=await bounded(ROOT,SPEC+'/'+protocol.user_prompt,65536);
 assert.equal(template.toString().split('{{CONTEXT_JSON}}').length,2,'Prompt must have exactly one package marker');
 const schema=await bounded(ROOT,protocol.answer_schema,65536);JSON.parse(schema);
 if(flags['--check-preregistration']){console.log(JSON.stringify({status:'preregistered-not-frozen',cases:protocol.selected_cases,max_bytes:protocol.context_budget.max_bytes,model_calls:0}));return;}
 const frozen=SPEC+'/frozen';const checking=Boolean(flags['--check']);
 let retained;if(checking)retained=JSON.parse(await bounded(ROOT,frozen+'/manifest.json',262144));
 const dwpCommit=checking?retained.dwp_commit:flags['--dwp-commit'];const explorerCommit=checking?retained.explorer_commit:flags['--explorer-commit'];
 assert.match(dwpCommit||'',/^[a-f0-9]{40}$/,'Explicit immutable DWP commit required');assert.match(explorerCommit||'',/^[a-f0-9]{40}$/,'Explicit immutable Explorer commit required');
 const explorer=path.resolve(flags['--explorer-root']||'');assert(flags['--explorer-root'],'Explicit Explorer checkout required');
 if(!checking){try{await lstat(path.join(ROOT,frozen));assert.fail('Frozen directory already exists; preserve it');}catch(e){if(e.code!=='ENOENT')throw e;}}
 const snapshots=new Map(),bindings=[];
 async function input(name,label,limit){const raw=checking?await bounded(ROOT,frozen+'/input-snapshots/'+label,limit):await bounded(ROOT,name,limit);committed(ROOT,dwpCommit,name,raw);snapshots.set(label,raw);bindings.push({path:name,snapshot:'input-snapshots/'+label,bytes:raw.length,sha256:sha(raw)});return raw;}
 const indexRaw=await input('evaluation/semantic-expansion/assembly-index.json','assembly-index.json',8*1024*1024);
 const originalRaw=await input('context/corpus/manifest.json','corpus-manifest.json',4*1024*1024);
 const registryRaw=await input('evaluation/staff-questions/cases.json','registry.json',2*1024*1024);
 for(const [name,label,raw] of [[SPEC+'/protocol.json','protocol.json',protocolRaw],[SPEC+'/'+protocol.system_prompt,'system-prompt.txt',system],[SPEC+'/'+protocol.user_prompt,'user-prompt.txt',template],[protocol.answer_schema,'answer.schema.json',schema]]){
  const fixed=await input(name,label,65536);assert.deepEqual(fixed,raw,`Current protocol/prompt/schema differs from frozen input: ${name}`);
 }
 for(const name of supportFiles)await input(name,path.basename(name),1024*1024);
 const engine={};for(const f of engineFiles){const raw=await bounded(explorer,ENGINE+f,2*1024*1024);committed(explorer,explorerCommit,ENGINE+f,raw);engine[f]=sha(raw);}
 const {assembleCorpusContext}=await import(pathToFileURL(path.join(explorer,ENGINE+'corpus.ts')));
 const {canonicalJson,validateContextIndex}=await import(pathToFileURL(path.join(explorer,ENGINE+'index.ts')));
 const index=validateContextIndex(JSON.parse(indexRaw)),original=JSON.parse(originalRaw),registry=JSON.parse(registryRaw);
 const manifest={...structuredClone(original),base_index:{path:'trial-index.json',bytes:indexRaw.length,sha256:sha(indexRaw)},semantic_source_snapshot:index.bundle.snapshot,bundle:index.bundle,scope:index.scope,limitations:index.limitations};
 const binding={index_url:'https://example.test/monday-corpus/manifest.json',index_sha256:sha(canonicalJson(manifest))};
 const corpusFiles=new Map(),cache=new Map();
 const fetcher=async url=>{const u=new URL(String(url));assert.equal(u.origin,'https://example.test');assert(u.pathname.startsWith('/monday-corpus/'));assert(!u.search&&!u.hash);const name=safeRelative(decodeURIComponent(u.pathname.slice('/monday-corpus/'.length)));if(name==='trial-index.json')return new Response(indexRaw);
  if(!cache.has(name)){const file='context/corpus/'+name,raw=await bounded(ROOT,file);committed(ROOT,dwpCommit,file,raw);cache.set(name,raw);corpusFiles.set(file,{path:file,bytes:raw.length,sha256:sha(raw)});}return new Response(cache.get(name));};
 const outputs=new Map(),cases=[];
 for(const id of protocol.selected_cases){const c=id==='control-unknown'?{id,question:protocol.control_question}:registry.cases.find(x=>x.id===id);assert(c,'Unregistered case');
  const context=await assembleCorpusContext(manifest,binding,c.question,protocol.context_budget,fetcher);const raw=Buffer.from(canonicalJson(context));assert(raw.length<=protocol.context_budget.max_bytes);assert.equal(context.ai_answer,null);assert.equal(context.evidence_status,'insufficient');if(id==='control-unknown')assert.equal(context.selected.length,0);else assert(context.selected.some(x=>x.record.kind==='evidence'),'Substantive case has no evidence; review before calling models');
  const file=`contexts/${id}.json`;outputs.set(file,raw);cases.push({id,question:c.question,path:file,sha256:sha(raw),bytes:raw.length,context_id:context.context_id,evidence_status:context.evidence_status,selected_records:context.selected.length,relationships:context.relationships.length,truncated:context.budget.truncated});}
 for(const [name,raw]of snapshots)outputs.set('input-snapshots/'+name,raw);
 const receipt={schema:'okf-fixed-monday-contexts.v1',dwp_commit:dwpCommit,explorer_commit:explorerCommit,engine,inputs:bindings,binding,semantic_snapshot:index.bundle.snapshot,corpus_files:[...corpusFiles.values()].sort((a,b)=>a.path.localeCompare(b.path)),cases,scope:'Offline immutable experimental input; not a public service observation. Both providers receive identical authored inputs. All tasks remain insufficient.'};
 outputs.set('manifest.json',Buffer.from(JSON.stringify(receipt,null,2)+'\n'));
 if(checking){for(const [name,raw]of outputs)assert.deepEqual(await bounded(ROOT,frozen+'/'+name),raw,`Frozen trial bytes changed: ${name}`);}
 else{await mkdir(path.join(ROOT,frozen));for(const [name,raw]of outputs){const full=path.join(ROOT,frozen,name);await mkdir(path.dirname(full),{recursive:true});await writeFile(full,raw,{flag:'wx'});}}
 console.log(JSON.stringify({status:checking?'verified':'frozen',cases:cases.map(x=>({id:x.id,bytes:x.bytes,selected:x.selected_records})),model_calls:0}));
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url))await main();
