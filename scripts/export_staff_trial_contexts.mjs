#!/usr/bin/env node
/** Freeze identical, bounded contexts before either subscription provider observes them. */
import assert from 'node:assert/strict';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const flags={};
for(let i=2;i<process.argv.length;i++){
 const name=process.argv[i];assert(['--check','--explorer-root'].includes(name));
 flags[name.slice(2)]=name==='--check'?true:process.argv[++i];
}
const SPEC='evaluation/model-comparison/staff-2026-09-20';
const read=async name=>readFile(path.join(ROOT,name));
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const engine=path.resolve(flags['explorer-root']||path.join(ROOT,'../okf-explorer'),'apps/okf-explorer/src/lib/context');
const {assembleCorpusContext}=await import(pathToFileURL(path.join(engine,'corpus.ts')));
const {canonicalJson,validateContextIndex}=await import(pathToFileURL(path.join(engine,'index.ts')));
const protocolRaw=await read(SPEC+'/protocol.json');const protocol=JSON.parse(protocolRaw);
// Historical trial replay uses the exact retained input, never today's source
// projection. Original context packages, receipts and catalogue stay immutable.
const frozenCatalogue=JSON.parse(await read(SPEC+'/contexts.json'));
assert(flags.check,'This dated trial is frozen; use --check to replay its archived inputs.');
const indexRaw=await read(SPEC+'/input-snapshots/assembly-index.json');
assert.equal(sha(indexRaw),frozenCatalogue.inputs.semantic_index_sha256,'Archived trial index differs');
const originalExporter=await read(SPEC+'/input-snapshots/'+frozenCatalogue.inputs.exporter_sha256+'.mjs');
assert.equal(sha(originalExporter),frozenCatalogue.inputs.exporter_sha256,'Original trial exporter differs');
const index=validateContextIndex(JSON.parse(indexRaw));
const originalRaw=await read('context/corpus/manifest.json');const original=JSON.parse(originalRaw);
const manifest={...structuredClone(original),base_index:{path:'staff-index.json',bytes:indexRaw.length,sha256:sha(indexRaw)},
 semantic_source_snapshot:index.bundle.snapshot,bundle:index.bundle,scope:index.scope,limitations:index.limitations};
const binding={index_url:'https://example.test/corpus/manifest.json',index_sha256:sha(canonicalJson(manifest))};
const cache=new Map();
const fetcher=async raw=>{const u=new URL(String(raw));assert.equal(u.origin,'https://example.test');assert(u.pathname.startsWith('/corpus/'));
 const p=u.pathname.slice('/corpus/'.length);assert(!p.includes('..'));if(p==='staff-index.json')return new Response(indexRaw);
 if(!cache.has(p))cache.set(p,await read('context/corpus/'+p));return new Response(cache.get(p));};
const registryRaw=await read('evaluation/staff-questions/cases.json');const registry=JSON.parse(registryRaw);
const inputs={protocol_sha256:sha(protocolRaw),registry_sha256:sha(registryRaw),semantic_index_sha256:sha(indexRaw),
 original_corpus_manifest_sha256:sha(originalRaw),exporter_sha256:sha(originalExporter),engine:{}};
for(const f of ['index.ts','corpus.ts','types.ts'])inputs.engine[f]=sha(await readFile(path.join(engine,f)));
const results=[];
const outputs=new Map();
for(const id of protocol.selected_cases){
 const c=id==='control-unknown'?{id,question:'xylophonicquasarteleportation'}:registry.cases.find(x=>x.id===id);assert(c);
 const context=await assembleCorpusContext(manifest,binding,c.question,protocol.context_budget,fetcher);
 const bytes=Buffer.from(canonicalJson(context));assert(bytes.length<=protocol.context_budget.max_bytes);
 assert.equal(context.ai_answer,null);assert.equal(context.evidence_status,'insufficient');
 if(id==='control-unknown')assert.equal(context.selected.length,0);
 const file=`contexts/${id}.json`;
 outputs.set(SPEC+'/'+file,bytes);
 results.push({id,question:c.question,path:SPEC+'/'+file,sha256:sha(bytes),bytes:bytes.length,context_id:context.context_id,
  evidence_status:context.evidence_status,selected_records:context.selected.length,relationships:context.relationships.length,
  truncated:context.budget.truncated,budget:protocol.context_budget});
}
outputs.set(SPEC+'/contexts.json',Buffer.from(JSON.stringify({schema:'okf-fixed-staff-contexts.v1',inputs,binding,
 semantic_snapshot:index.bundle.snapshot,scope:'Identical shared-engine packages frozen before paired subscription calls; offline local source projection, not a public deployment.',cases:results},null,2)+'\n'));
for(const [name,bytes]of outputs){const p=path.join(ROOT,name);if(flags.check)assert.deepEqual(await readFile(p),bytes,`Fixed input changed: ${name}`);
 else{await mkdir(path.dirname(p),{recursive:true});await writeFile(p,bytes);}}
console.log(JSON.stringify({status:flags.check?'verified':'exported',cases:results.map(x=>({id:x.id,bytes:x.bytes,selected:x.selected_records,truncated:x.truncated}))}));
