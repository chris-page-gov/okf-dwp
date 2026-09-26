#!/usr/bin/env node
/** Validate optional statutory admission with the actual reusable engine. */
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {pathToFileURL,fileURLToPath} from 'node:url';
const args=process.argv.slice(2);assert.equal(args.length,2);assert.equal(args[0],'--explorer-root');
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const {validateContextIndex,assembleContext}=await import(pathToFileURL(resolve(args[1],'apps/okf-explorer/src/lib/context/index.ts')));
const index=validateContextIndex(JSON.parse(readFileSync(resolve(root,'domain-profile/reading-help-law/assembly-index.json'))));
const baseline=JSON.parse(readFileSync(resolve(root,'combined/context/assembly-index.json')));
assert.deepEqual(index.requirements,baseline.requirements);
const variants=index.records.filter(r=>r.id.includes('/reading-help-law/body/ukpga/1992/4/section/70/'));
assert.equal(variants.length,2);assert.notEqual(variants[0].text,variants[1].text);
const pack=await assembleContext(index,'DMG 60025 Carer’s Allowance section 70 entitlement',{max_bytes:131072,max_nodes:32,max_relationships:64,max_depth:3});
assert.equal(pack.ai_answer,null);assert.equal(pack.evidence_status,'insufficient');
assert(index.assertions.some(r=>r.id.includes('/reading-help-law-citation/')),'Citation path absent from admitted index');
const observations={question:pack.question,evidence_status:pack.evidence_status,bridge_selected:pack.selected.some(s=>s.record.id.includes('/reading-help-law/')),citation_path_selected:pack.relationships.some(r=>r.id.includes('/reading-help-law-citation/')),resolved_concepts:pack.resolved_concepts,budget:pack.budget,missing_evidence:pack.missing_evidence,context_id:pack.context_id,limitation:'Consumer shape validation passed. This unchanged-budget natural-language probe did not establish retrieval improvement; omissions remain explicit.'};
const retained=JSON.parse(readFileSync(resolve(root,'evaluation/reading-help-rollout/law-context-probe.json')));assert.deepEqual(observations,retained,'Probe differs from retained observation');
console.log(JSON.stringify({admission_validation:'passed',retrieval_probe:'failed-to-retain-bridge',records:index.records.length,assertions:index.assertions.length,requirements:index.requirements.length,probe_status:pack.evidence_status,selected:pack.selected.length,relationships:pack.relationships.length,model_calls:0}));
