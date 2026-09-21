#!/usr/bin/env node
/** Offline source comparison. Never calls a provider, network service or answer model. */
import assert from 'node:assert/strict';
import { readFileSync, writeFileSync, mkdirSync, lstatSync, realpathSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { dirname, resolve, relative, isAbsolute } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const ROOT=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const SOURCE='723bcc5b015ab38a026625c2148edbd784edf7c7';
const ENGINE='c4f2de0a99b7bc2f8b8c8a06a3c715fb56b66d8e';
const HASHES={
  'index.ts':'cc9fe1c162e1ad505f080712b6eacf0bad843f0e32d6f953b697b8349b2c4ca8',
  'corpus.ts':'72fec179d1015df39fd16834d5876740b95a6477f70b6013821f24398a69eb65',
  'types.ts':'d9eff934ec504c3fbd2afff672ae1d3a8a275e84cc11b71fed8a3e1b0edfdcf3'
};
const args={};for(let n=2;n<process.argv.length;n+=2){
  assert(['--explorer-root','--output'].includes(process.argv[n])&&process.argv[n+1],'Unsupported argument');
  assert(!args[process.argv[n]],'Duplicate argument');args[process.argv[n]]=process.argv[n+1];
}
assert(args['--explorer-root'],'Supply --explorer-root with the pinned c4f checkout');
const sha=b=>createHash('sha256').update(b).digest('hex');
function local(file,max){
  const path=resolve(file);assert.equal(realpathSync(path),path,'Symlinked input');
  const st=lstatSync(path);assert(st.isFile()&&st.size>0&&st.size<=max,'Non-regular or oversized input');
  const raw=readFileSync(path);assert.equal(raw.length,st.size);assert(raw.length<=max);return raw;
}
function git(file,max){
  assert(/^[A-Za-z0-9_./-]+$/.test(file)&&!file.split('/').includes('..'));
  const object=SOURCE+':'+file;
  const size=Number(execFileSync('git',['-C',ROOT,'cat-file','-s',object],{maxBuffer:1000}).toString().trim());
  assert(Number.isSafeInteger(size)&&size>0&&size<=max,'Oversized Git input');
  const raw=execFileSync('git',['-C',ROOT,'show',object],{maxBuffer:max});assert.equal(raw.length,size);return raw;
}
const engineRoot=resolve(args['--explorer-root'],'apps/okf-explorer/src/lib/context');
for(const [file,hash] of Object.entries(HASHES))assert.equal(sha(local(resolve(engineRoot,file),1024*1024)),hash,'Engine differs before import');
const {resolveConcepts,canonicalJson}=await import(pathToFileURL(resolve(engineRoot,'index.ts')));
const {assembleCorpusContext,validateContextCorpusManifest}=await import(pathToFileURL(resolve(engineRoot,'corpus.ts')));
const manifestPath='combined/context/corpus/manifest.json';
const manifestRoot=dirname(manifestPath);
const sources=[];
for(const stage of ['baseline','candidate']){
  const read=(file,max)=>stage==='baseline'?git(file,max):local(resolve(ROOT,file),max);
  const raw=read(manifestPath,4*1024*1024),manifest=validateContextCorpusManifest(JSON.parse(raw));
  const baseRaw=read(manifestRoot+'/'+manifest.base_index.path,8*1024*1024);
  assert.equal(sha(baseRaw),manifest.base_index.sha256);
  const index=JSON.parse(baseRaw);
  const entries=[manifest.base_index,...manifest.records.shards,...Object.values(manifest.search.shards)];
  const allowed=new Map(entries.map(e=>[e.path,e]));const cache=new Map();
  const binding={index_url:stage==='baseline'
    ?`https://raw.githubusercontent.com/chris-page-gov/okf-dwp/${SOURCE}/${manifestPath}`
    :`https://example.test/unpublished-${sha(raw)}/${manifestPath}`,index_sha256:sha(raw)};
  const baseURL=new URL('.',binding.index_url);
  const fetcher=async url=>{
    const u=new URL(String(url));assert.equal(u.origin,baseURL.origin);assert(u.href.startsWith(baseURL.href));
    const file=u.href.slice(baseURL.href.length);const entry=allowed.get(file);assert(entry,'Undeclared local corpus read');
    if(!cache.has(file))cache.set(file,read(manifestRoot+'/'+file,file===manifest.base_index.path?8*1024*1024:4*1024*1024));
    const raw=cache.get(file);assert.equal(raw.length,entry.bytes);assert.equal(sha(raw),entry.sha256);
    return new Response(raw);
  };
  sources.push({stage,manifest,index,raw,binding,fetcher,base_sha256:sha(baseRaw)});
}
// These additional phrasings were absent from the original staff register. They
// are authored regression cases, not an independent held-out accuracy sample.
const cases=[
  ['staff-001','What happens to your benefits if you go abroad?',false],
  ['staff-023','What happens to Pension Credit if someone moves abroad?',true],
  ['overseas-general','What happens to my benefits if I travel overseas?',false],
  ['overseas-pc','Can Pension Credit continue while I am overseas?',true],
  ['abroad-pc-treatment','What happens to Pension Credit when I go abroad for treatment?',true],
  ['outside-gb','Explain Pension Credit when a person is outside Great Britain.',true],
];
const ID='https://chris-page-gov.github.io/okf-dwp/id/';
const pages=Array.from({length:7},(_,n)=>ID+`page/dmg-vol2-ch7-part6/${String(n+8).padStart(4,'0')}`);
const candidate=sources[1];
const controls=[];
for(const question of [
  'What happens to Pension Credit during a temporary absence?',
  'Can I take Pension Credit on holiday?',
  'Will my pension stop on holiday?',
  'Pension Credit during a temporary stay in a care home',
  'What happens when I travel within Great Britain?',
]){
  const r=resolveConcepts(candidate.index,question);
  assert(!r.resolved.some(c=>c.id===ID+'staff-domain/abroad'),'Domestic/unspecified absence became abroad');
  controls.push({question,resolved:r.resolved.map(c=>c.id),abroad_resolved:false,passed:true});
}
for(const question of ['JSA abroad','ESA abroad','PIP abroad','UC abroad','Universal Credit overseas']){
  const r=resolveConcepts(candidate.index,question);const ids=new Set(r.resolved.map(c=>c.id));
  assert(ids.has(ID+'staff-domain/abroad'));
  const active=candidate.index.requirements.filter(x=>x.when_all.every(id=>ids.has(id)));
  assert(!active.some(x=>x.id.endsWith('/staff-023')),'Other benefit activated Pension Credit requirements');
  assert(!r.resolved.some(c=>/universal credit/i.test(c.label)),'Universal Credit coverage invented');
  controls.push({question,resolved:[...ids],requirements:active.map(x=>x.id),unresolved:r.unresolved,passed:true});
}
const rows=[],packets=[];
for(const [id,question,pc] of cases)for(const source of sources)for(const max_bytes of [32768,524288]){
  const resolution=resolveConcepts(source.index,question);const seeds=new Set(resolution.resolved.map(c=>c.id));
  const activated=source.index.requirements.filter(r=>r.when_all.every(i=>seeds.has(i)));
  const target=activated.find(r=>r.id.endsWith('/staff-023'));
  // Derive the denominator before budget trimming can clear returned metadata.
  const expected=target?.required_paths||[];
  const pack=await assembleCorpusContext(source.manifest,source.binding,question,{max_bytes},source.fetcher);
  assert.equal(pack.evidence_status,'insufficient');assert.equal(pack.ai_answer,null);
  assert(pack.budget.used_bytes<=max_bytes);
  const selected=new Set(pack.selected.map(s=>s.record.id)),relations=new Set(pack.relationships.map(e=>e.id));
  const complete=p=>p.records.every(i=>selected.has(i))&&p.assertions.every(i=>relations.has(i));
  const missingPaths=expected.filter(p=>!complete(p));
  for(const item of pack.selected.filter(s=>s.record.kind==='evidence')){
    for(const p of item.record.provenance)if(p.literal_sha256)assert.equal(sha(item.record.text),p.literal_sha256);
  }
  if(source.stage==='candidate'){
    assert(seeds.has(ID+'staff-domain/abroad'));
    if(pc){assert(target);assert(pages.every(p=>target.required.includes(p)));}
    if(pc&&max_bytes===524288){
      assert(pages.every(p=>selected.has(p)),id+': whole SPC continuation missing at512KiB');
      assert.equal(missingPaths.length,0,id+': required path missing at512KiB');
    }
    if(pc&&missingPaths.length){
      assert(pack.budget.truncated);
      assert(pack.missing_evidence.some(x=>['metadata_budget','missing_required_evidence'].includes(x.code)),
        'Lost qualification paths must remain visibly insufficient');
    }
  }
  const raw=Buffer.from(canonicalJson(pack));
  const row={case_id:id,question,stage:source.stage,max_bytes,context_id:pack.context_id,canonical_sha256:sha(raw),
    evidence_status:pack.evidence_status,ai_answer:pack.ai_answer,bytes:pack.budget.used_bytes,
    resolved:pack.resolved_concepts.map(c=>c.id),resolved_before_budget:[...seeds],unresolved:pack.unresolved_terms,
    selected_records:pack.selected.length,relationships:pack.relationships.length,
    expected_staff023_paths:expected.length,retained_staff023_paths:expected.length-missingPaths.length,
    omitted_staff023_paths:missingPaths,returned_requirement_ids:pack.requirements.map(r=>r.id),
    qualification_pages_retained:pages.filter(p=>selected.has(p)),qualification_pages_missing:pages.filter(p=>!selected.has(p)),
    truncation_codes:[...new Set(pack.budget.omissions.map(x=>x.code))],missing_codes:[...new Set(pack.missing_evidence.map(x=>x.code))],
    package_path:`${source.stage}-${id}-${max_bytes}.json`};
  rows.push(row);packets.push([row.package_path,raw]);
}
const report={schema:'okf-abroad-source-comparison.v1',engine_commit:ENGINE,engine_files:HASHES,
  runner_sha256:sha(local(fileURLToPath(import.meta.url),128*1024)),baseline_source_commit:SOURCE,
  candidate_source:'uncommitted generated source; bind by retained input hashes, not a release',
  sources:sources.map(s=>({stage:s.stage,manifest_sha256:sha(s.raw),base_sha256:s.base_sha256,snapshot:s.manifest.bundle.snapshot})),
  network_calls:0,model_calls:0,controls,rows,
  limitations:['Every package remains insufficient; the 203 legal, applicability, review and source-closure obligations are not closed.',
    'This is a local source comparison on one pinned engine, not a public client observation or answer-accuracy evaluation.',
    'The generic abroad question does not identify a benefit. The Pension Credit branch does not establish rules for all benefits.',
    'These extra phrasings are model-authored regression cases, not independently collected held-out questions.']};
if(args['--output']){
  const output=resolve(args['--output']);assert.equal(realpathSync(dirname(output)),dirname(output),'Symlinked output parent');
  const rel=relative(ROOT,output);assert(rel.startsWith('..')||isAbsolute(rel),'Keep this observation outside the source checkout');
  mkdirSync(output); // Existing directories, files and links must refuse.
  for(const [file,raw] of packets)writeFileSync(resolve(output,file),raw,{flag:'wx'});
  writeFileSync(resolve(output,'summary.json'),JSON.stringify(report,null,2)+'\n',{flag:'wx'});
}
console.log(JSON.stringify({status:'passed',network_calls:0,model_calls:0,controls:controls.length,
  assemblies:rows.length,results:rows.map(({case_id,stage,max_bytes,selected_records,relationships,expected_staff023_paths,
    retained_staff023_paths,qualification_pages_retained,bytes,missing_codes})=>({case_id,stage,max_bytes,selected_records,
    relationships,required_paths:`${retained_staff023_paths}/${expected_staff023_paths}`,
    qualification_pages:qualification_pages_retained.length,bytes,missing_codes}))},null,2));
