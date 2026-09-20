import assert from 'node:assert/strict';
import { access, readFile, writeFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { pathToFileURL, fileURLToPath } from 'node:url';
import path from 'node:path';
const dir = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(dir, '../../..');
const output = process.env.OKF_CONTEXT_COMPARISON_OUTPUT || path.join(dir, 'comparison.json');
try { await access(output); throw new Error('Refusing to overwrite an existing comparison: choose a fresh OKF_CONTEXT_COMPARISON_OUTPUT'); }
catch (error) { if (error.code !== 'ENOENT') throw error; }
const dataRoot = process.env.OKF_DWP_CHECKOUT || root;
assert(dataRoot, 'Supply OKF_DWP_CHECKOUT containing the unchanged frozen corpus shards');
const current = await import(pathToFileURL(path.join(dir, 'candidate/corpus.ts')));
const baseline = await import(pathToFileURL(path.join(dir, 'baseline/corpus.ts')));
const {canonicalJson} = await import(pathToFileURL(path.join(dir, 'baseline/index.ts')));
const sha = data => createHash('sha256').update(data).digest('hex');
const overlayRaw = await readFile(path.join(dir, 'overlay.json'));
assert.equal(sha(overlayRaw), '79ac30aef41ac467db83ec6b79ed20e4a4cc9330461d08713f45ea5830cb6e2d');
const overlay = JSON.parse(overlayRaw);
const registryRaw = await readFile(path.join(dir, 'cases.json'));
const registry = JSON.parse(registryRaw);
const manifestRaw = await readFile(path.join(dir, 'manifest.json'));
const original = JSON.parse(manifestRaw);
const manifest = {...original, base_index: {path:'staff-index.json',bytes:overlayRaw.length,sha256:sha(overlayRaw)}, semantic_source_snapshot:overlay.bundle.snapshot,bundle:overlay.bundle,scope:overlay.scope,limitations:overlay.limitations};
const binding = {index_url:'https://example.test/corpus/manifest.json',index_sha256:sha(canonicalJson(manifest))};
const bytes = new Map([['staff-index.json',overlayRaw]]);
const fetcher = async (url, latency = 0) => {
 const u = new URL(String(url)); assert.equal(u.origin,'https://example.test');
 const name = u.pathname.slice('/corpus/'.length);assert(!name.includes('..')&&u.pathname.startsWith('/corpus/'));
 if(!bytes.has(name))bytes.set(name,await readFile(path.join(dataRoot,'context/corpus',name)));
 if(typeof latency === 'number' && latency > 0)await new Promise(resolve=>setTimeout(resolve,latency));
 return new Response(bytes.get(name));
};
const runner_sha256 = sha(await readFile(fileURLToPath(import.meta.url)));
const started_at = new Date().toISOString();
const cases = [];
for(const row of registry.cases) {
 const expected = registry.source_candidates.filter(c=>row.candidate_ids.includes(c.id));
 const values=[];
 for(const engine of [baseline,current]) {
  const start=performance.now();const result=await engine.assembleCorpusContext(manifest,binding,row.question,{},fetcher);
  assert.equal(result.ai_answer,null);assert.equal(result.evidence_status,'insufficient');assert(result.budget.used_bytes<=result.budget.max_bytes);
  values.push({result,elapsed_ms:performance.now()-start});
 }
 const describe=({result:p,elapsed_ms})=>({context_id:p.context_id,elapsed_ms,records:p.selected.length,relationships:p.relationships.length,bytes:p.budget.used_bytes,expected:expected.length,hits:expected.filter(c=>p.selected.some(s=>s.record.id===c.record_id)).map(c=>c.id),ambiguities:p.ambiguities,requirements:p.requirements.length,truncated:p.budget.truncated,evidence_status:p.evidence_status});
 cases.push({id:row.id,question:row.question,before:describe(values[0]),after:describe(values[1]),identical_package:canonicalJson(values[0].result)===canonicalJson(values[1].result)});
}
const timings=[];
for(const id of ['staff-005','staff-008','staff-020','staff-024','staff-025']){
 const question=registry.cases.find(c=>c.id===id).question;
 for(let repeat=0;repeat<3;repeat++)for(const [name,engine]of(repeat%2?[['after',current],['before',baseline]]:[['before',baseline],['after',current]])){
  let active=0,peak=0,calls=0;const delayed=async url=>{active++;calls++;peak=Math.max(peak,active);try{return await fetcher(url,10);}finally{active--;}};
  const start=performance.now();const result=await engine.assembleCorpusContext(manifest,binding,question,{},delayed);
  timings.push({id,repeat,engine:name,elapsed_ms:Math.round((performance.now()-start)*100)/100,peak_fetches:peak,calls,package_bytes:result.budget.used_bytes});
 }
}
const receipt={schema:'okf-context-retrieval-development-comparison.v1',started_at,completed_at:new Date().toISOString(),runtime:{node:process.version,platform:process.platform,arch:process.arch},inputs:{runner_sha256,manifest_sha256:sha(manifestRaw),overlay_sha256:sha(overlayRaw),registry_sha256:sha(registryRaw),baseline_commit:'fc71d65b8f5cfc860d52afe98a5e45b88231f3e5',current_engine_sha256:Object.fromEntries(await Promise.all(['index.ts','corpus.ts','types.ts'].map(async name=>[name,sha(await readFile(path.join(dir,'candidate',name)))])))},summary:{before_hits:cases.reduce((n,c)=>n+c.before.hits.length,0),after_hits:cases.reduce((n,c)=>n+c.after.hits.length,0),identical_packages:cases.filter(c=>c.identical_package).length,changed_cases:cases.filter(c=>!c.identical_package).map(c=>c.id),cases:cases.length,sufficient:0,ai_answers:0},cases,timings,limits:['Read-only frozen known development corpus; no held-out answer accuracy or current-law claim.','Timings use an in-process cached byte fetcher with an artificial 10ms delay per file, no real network. Three repeats alternate engine order; this isolates serial versus four-file scheduling, not deployed performance.','Original DWP outputs and trial receipts are unchanged.']};
await writeFile(output,JSON.stringify(receipt,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify(receipt.summary));
for(const id of ['staff-005','staff-008','staff-020','staff-024','staff-025']){const rows=timings.filter(r=>r.id===id);const median=engine=>rows.filter(r=>r.engine===engine).map(r=>r.elapsed_ms).sort((a,b)=>a-b)[1];console.log(JSON.stringify({id,before_ms:median('before'),after_ms:median('after'),peak_after:Math.max(...rows.filter(r=>r.engine==='after').map(r=>r.peak_fetches))}));}
