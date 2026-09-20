#!/usr/bin/env node
/** Reproducible development-case comparison using the same shared Explorer engine for both semantic bases. */
import assert from 'node:assert/strict';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {gzipSync,gunzipSync} from 'node:zlib';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const flags={};for(let i=2;i<process.argv.length;i++){let k=process.argv[i];assert(['--check','--explorer-root'].includes(k));flags[k.slice(2)]=k==='--check'?true:process.argv[++i];}
const engine=path.resolve(flags['explorer-root']||path.join(ROOT,'../okf-explorer'),'apps/okf-explorer/src/lib/context');
const {assembleCorpusContext}=await import(pathToFileURL(path.join(engine,'corpus.ts')));
const {validateContextIndex,resolveConcepts,assembleContext,canonicalJson}=await import(pathToFileURL(path.join(engine,'index.ts')));
const sha=b=>createHash('sha256').update(b).digest('hex');
const read=async p=>readFile(path.join(ROOT,p));
const out=path.join(ROOT,'evaluation/semantic-expansion');
const base=await read('context/corpus/base-index.json');
const overlayRaw=await read('evaluation/semantic-expansion/assembly-index.json');
const overlay=validateContextIndex(JSON.parse(overlayRaw));
const registryRaw=await read('evaluation/staff-questions/cases.json');const registry=JSON.parse(registryRaw);
const profileRaw=await read('evaluation/semantic-expansion/profiles.json');const profiles=JSON.parse(profileRaw);
const originalManifest=JSON.parse(await read('context/corpus/manifest.json'));
const manifests=[originalManifest,{...structuredClone(originalManifest),base_index:{path:'staff-index.json',bytes:overlayRaw.length,sha256:sha(overlayRaw)},semantic_source_snapshot:overlay.bundle.snapshot,bundle:overlay.bundle,scope:overlay.scope,limitations:overlay.limitations}];
const input={registry_sha256:sha(registryRaw),profiles_sha256:sha(profileRaw),base_sha256:sha(base),overlay_sha256:sha(overlayRaw),runner_sha256:sha(await readFile(fileURLToPath(import.meta.url))),engine:{}};
for(const f of ['index.ts','corpus.ts','types.ts'])input.engine[f]=sha(await readFile(path.join(engine,f)));
const cache=new Map();const fetcher=async url=>{let u=new URL(String(url));assert.equal(u.origin,'https://example.test');let p=u.pathname.slice('/corpus/'.length);assert(!p.includes('..')&&u.pathname.startsWith('/corpus/'));if(p==='staff-index.json')return new Response(overlayRaw);if(!cache.has(p))cache.set(p,await read('context/corpus/'+p));return new Response(cache.get(p));};
const previous=flags.check?JSON.parse(await read('evaluation/semantic-expansion/evaluation.json')):null;if(previous)assert.deepEqual(previous.inputs,input);
const rows=[];
for(const c of registry.cases){
 const packs=[];
 for(let stage=0;stage<2;stage++){
  const m=manifests[stage];const pack=await assembleCorpusContext(m,{index_url:'https://example.test/corpus/manifest.json',index_sha256:sha(canonicalJson(m))},c.question,{},fetcher);
  assert.equal(pack.ai_answer,null);assert.equal(pack.evidence_status,'insufficient');assert(pack.budget.used_bytes<=pack.budget.max_bytes);
  for(const item of pack.selected.filter(x=>x.record.kind==='evidence'))for(const p of item.record.provenance)if(p.literal_sha256)assert.equal(sha(item.record.text),p.literal_sha256);
  packs.push(pack);
 }
 const expected=registry.source_candidates.filter(x=>c.candidate_ids.includes(x.id));
 const describe=p=>({context_id:p.context_id,resolved:p.resolved_concepts.map(x=>({id:x.id,label:x.label})),ambiguities:p.ambiguities,
  evidence_status:p.evidence_status,selected_records:p.selected.length,relationships:p.relationships.length,requirements:p.requirements.length,
  expected_candidates_retained:expected.filter(x=>p.selected.some(s=>s.record.id===x.record_id)).map(x=>x.id),
  adm_pages:p.selected.filter(x=>x.record.kind==='evidence'&&x.record.route.startsWith('page/adm/')).map(x=>x.record.route),
  semantic_adm_pages:p.selected.filter(x=>x.record.kind==='evidence'&&x.record.route.startsWith('page/adm/')&&x.paths.some(path=>path.assertions.length)).map(x=>x.record.route),
  truncation_codes:[...new Set(p.budget.omissions.map(x=>x.code))],
  missing_requirement_ids:p.requirements.flatMap(x=>x.missing),package_bytes:p.budget.used_bytes,truncated:p.budget.truncated,unresolved_terms:p.unresolved_terms});
 const profile=profiles.profiles.find(p=>p.id===c.id);const matched=packs[1].requirements.some(r=>r.id===profile.requirement_id);
 const row={id:c.id,question:c.question,duplicate_of:c.duplicate_of,before:describe(packs[0]),after:describe(packs[1]),own_profile_triggered:matched,
  assessment:{A_source:'Exact frozen source bytes verified by producer; candidate presence is not complete coverage.',B_semantics:'Proposed concepts, directed associations and explicit obligations; independent review pending.',C_retrieval:'Known development-case candidate overlap measured; no held-out accuracy claim.',D_traversal:'Returned shared-engine source paths preserved.',E_context:'Insufficient with registered obligations.',F_provenance:'Selected literal hashes verified.',G_boundaries:'No answer and no invented completion.',H_answerability:'Specialist acceptance and legal applicability remain unestablished.'}};
 const archive='cases/'+c.id+'.json.gz';const raw=Buffer.from(canonicalJson({before:packs[0],after:packs[1]}));row.archive=archive;row.archive_sha256=sha(raw);
 if(flags.check){const stored=gunzipSync(await read('evaluation/semantic-expansion/'+archive));assert.equal(sha(stored),row.archive_sha256);assert.deepEqual(row,previous.cases.find(x=>x.id===c.id));}
 else{await mkdir(path.join(out,'cases'),{recursive:true});await writeFile(path.join(out,archive),gzipSync(raw,{level:9,mtime:0}));}
 rows.push(row);
}
const term='https://chris-page-gov.github.io/okf-dwp/id/';
const pc=resolveConcepts(overlay,'Pension Credit');assert(pc.resolved.some(x=>x.id===term+'term/pension-credit'));assert(!pc.resolved.some(x=>x.id===term+'term/pc-prisoner-credit-rates'));
const sda=resolveConcepts(overlay,'SDA');assert(sda.ambiguities.some(x=>x.candidates.includes(term+'staff-domain/sda')&&x.candidates.includes(term+'staff-domain/severe-disability-addition')));
const unknown=await assembleContext(overlay,'xylophonicquasarteleportation');assert.equal(unknown.selected.length,0);assert.equal(unknown.evidence_status,'insufficient');
const removed=structuredClone(overlay);removed.records=removed.records.filter(x=>x.id!==term+'page/85/0077');const noPage=await assembleContext(removed,'Housing Benefit Pension Credit');assert(noPage.requirements.some(x=>x.missing.includes(term+'page/85/0077')));
const reversed=structuredClone(overlay);reversed.assertions=reversed.assertions.map(x=>x.id.includes('/staff-semantic/')?{...x,source:x.target,target:x.source}:x);const wrongDirection=await assembleContext(reversed,'Housing Benefit Pension Credit');assert(wrongDirection.requirements.some(x=>x.missing.some(id=>id.includes('/assertion/staff-semantic/'))));
const controls=[];
for(const [label,question,conceptId,pageRoute] of [
 ['capital-paraphrase','Explain the assessment of savings for Pension Credit',term+'term/capital','page/84/0128'],
 ['partner-paraphrase','Explain the Pension Credit household rules for a partner',term+'staff-domain/partner','page/77/0015'],
 ['pip-age-paraphrase','Explain PIP at pensionable age',term+'staff-domain/pip','page/adm/adm-chapter-p4/0013'],
 ['custody-regression','A claimant is imprisoned. Explain the effect on JSA, IS, State Pension Credit and ESA, distinguishing loss of payment from loss of entitlement, and trace each conclusion to the relevant DMG guidance.',term+'term/common-imprisonment-payability','page/dmg-vol3-ch12/0003']
]){
 const p=await assembleContext(overlay,question);
 assert(p.resolved_concepts.some(x=>x.id===conceptId),label+': neutral concept missing');
 assert(p.selected.some(x=>x.record.route===pageRoute&&x.paths.some(path=>path.assertions.length)),label+': source traversal missing');
 assert.equal(p.evidence_status,'insufficient');assert.equal(p.ai_answer,null);
 controls.push({id:label,question,context_id:p.context_id,concept_id:conceptId,source_route:pageRoute,evidence_status:p.evidence_status,passed:true});
}
const counter=await assembleContext(overlay,'Pension Credit savings of one pound automatically establish entitlement');
assert.equal(counter.evidence_status,'insufficient');assert.equal(counter.ai_answer,null);
controls.push({id:'counterfactual-not-answered',question:counter.question,evidence_status:counter.evidence_status,passed:true});
// These are development-case size observations, not model answer scores. Every
// package still carries open obligations; smaller packages may lose all paths.
const budgetObservations=[];
for(const id of ['staff-006','staff-012','staff-026','staff-038']){
 const c=registry.cases.find(x=>x.id===id);assert(c);
 for(const max_bytes of [65536,262144]){
  const m=manifests[1];
  const pack=await assembleCorpusContext(m,{index_url:'https://example.test/corpus/manifest.json',index_sha256:sha(canonicalJson(m))},c.question,{max_bytes},fetcher);
  assert.equal(pack.evidence_status,'insufficient');assert.equal(pack.ai_answer,null);
  assert(pack.budget.used_bytes<=max_bytes);assert(pack.selected.length>0,'Budget trimming discarded all usable source records');
  assert(!pack.missing_evidence.some(x=>x.code==='metadata_budget'));
  budgetObservations.push({id,context_id:pack.context_id,budget:pack.budget.max_bytes,bytes:pack.budget.used_bytes,
   records:pack.selected.length,relationships:pack.relationships.length,requirements:pack.requirements.length,
   evidence_status:pack.evidence_status,truncation_codes:[...new Set(pack.budget.omissions.map(x=>x.code))]});
 }
}
const summary={question_occurrences:rows.length,unique_questions:new Set(rows.map(x=>x.question)).size,
 before_candidate_hits:rows.reduce((n,x)=>n+x.before.expected_candidates_retained.length,0),after_candidate_hits:rows.reduce((n,x)=>n+x.after.expected_candidates_retained.length,0),
 before_cases_with_candidates:rows.filter(x=>x.before.expected_candidates_retained.length).length,after_cases_with_candidates:rows.filter(x=>x.after.expected_candidates_retained.length).length,
 own_profile_triggered:rows.filter(x=>x.own_profile_triggered).length,after_with_ADM:rows.filter(x=>x.after.adm_pages.length).length,
 sufficient_contexts:0,ai_answers:0,independent_specialist_approvals:0,controls:10};
const receipt={schema:'okf-dwp-staff-semantic-evaluation.v1',mode:'local-shared-engine-development-case-comparison',inputs:input,summary,cases:rows,generalisation_controls:controls,budget_observations:budgetObservations,
 limitations:['All staff cases are known during modelling; improved candidate overlap is not independent proof of answer accuracy.','Requirements never seed retrieval; they check actual selected evidence and named absent obligations.','The before/after runs use the same frozen lexical shards and engine; only the declared semantic base changes.','This is an offline local evaluation, not a public deployment or live client observation.']};
if(flags.check)assert.deepEqual(previous,receipt);else await writeFile(path.join(out,'evaluation.json'),JSON.stringify(receipt,null,2)+'\n');
console.log(JSON.stringify({status:flags.check?'verified':'built',...summary}));
