#!/usr/bin/env node
/** Validate optional statutory admission with the actual reusable engine. */
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {pathToFileURL,fileURLToPath} from 'node:url';
const args=process.argv.slice(2);assert([2,3].includes(args.length));assert.equal(args[0],'--explorer-root');const record=args[2]==='--record';assert(args.length===2||record);
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const {validateContextIndex,assembleContext,governanceIssues}=await import(pathToFileURL(resolve(args[1],'apps/okf-explorer/src/lib/context/index.ts')));
const index=validateContextIndex(JSON.parse(readFileSync(resolve(root,'domain-profile/reading-help-law/assembly-index.json'))));
const baseline=JSON.parse(readFileSync(resolve(root,'combined/context/assembly-index.json')));
assert.deepEqual(index.requirements,baseline.requirements);
const prior=new Set([...baseline.records,...baseline.assertions].map(r=>r.id));
const {evidenceUnitIntegrity}=await import(pathToFileURL(resolve(args[1],'apps/okf-explorer/src/lib/context/unit.ts')));
const {createHash}=await import('node:crypto');
for(const row of [...index.records,...index.assertions].filter(r=>!prior.has(r.id))){
  assert.deepEqual(governanceIssues(row),[],`New admitted record lacks governance: ${row.id}`);
  if(row.kind==='evidence'){
    const digest=createHash('sha256').update(row.text).digest('hex');
    assert(row.provenance.every(p=>!p.literal_sha256||p.literal_sha256===digest),`Complete record digest differs: ${row.id}`);
    assert(await evidenceUnitIntegrity(row),`Source fragment differs: ${row.id}`);
  }
}
const variants=index.records.filter(r=>r.id.includes('/reading-help-law/body/ukpga/1992/4/section/70/'));
assert.equal(variants.length,2);assert.notEqual(variants[0].text,variants[1].text);
const pack=await assembleContext(index,'DMG 60025 Carer’s Allowance section 70 entitlement',{max_bytes:131072,max_nodes:32,max_relationships:64,max_depth:3});
assert.equal(pack.ai_answer,null);assert.equal(pack.evidence_status,'insufficient');
assert(index.assertions.some(r=>r.id.includes('/reading-help-law-citation/')),'Citation path absent from admitted index');
const engineRoot=resolve(args[1],'apps/okf-explorer/src/lib/context');
const engineFiles=readdirSync(engineRoot).filter(name=>name.endsWith('.ts')&&!name.endsWith('.test.ts')).sort().map(name=>({path:'apps/okf-explorer/src/lib/context/'+name,sha256:createHash('sha256').update(readFileSync(resolve(engineRoot,name))).digest('hex')}));
const observations={engine:{comparison:'Exact module hashes; these bytes are present at CI consumer e6084059f9b09633cfb8385be20099b952915e82 and baseline 0326460034345c7b5227c530065b7f21cb4e3970',files:engineFiles},source:{path:'domain-profile/reading-help-law/assembly-index.json',sha256:createHash('sha256').update(readFileSync(resolve(root,'domain-profile/reading-help-law/assembly-index.json'))).digest('hex'),snapshot:index.bundle.snapshot},question:pack.question,evidence_status:pack.evidence_status,bridge_selected:pack.selected.some(s=>s.record.id.includes('/reading-help-law/')),citation_path_selected:pack.relationships.some(r=>r.id.includes('/reading-help-law-citation/')),resolved_concepts:pack.resolved_concepts,budget:pack.budget,missing_evidence:pack.missing_evidence,context_id:pack.context_id,limitation:'Consumer shape validation passed. This unchanged-budget natural-language probe did not establish retrieval improvement; omissions remain explicit.'};
if(record)writeFileSync(resolve(root,'evaluation/reading-help-rollout/law-context-probe.json'),JSON.stringify(observations,null,2)+'\n');
const retained=JSON.parse(readFileSync(resolve(root,'evaluation/reading-help-rollout/law-context-probe.json')));assert.deepEqual(observations,retained,'Probe differs from retained observation');
console.log(JSON.stringify({admission_validation:'passed',retrieval_probe:'failed-to-retain-bridge',records:index.records.length,assertions:index.assertions.length,requirements:index.requirements.length,probe_status:pack.evidence_status,selected:pack.selected.length,relationships:pack.relationships.length,model_calls:0}));
