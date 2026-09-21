#!/usr/bin/env node
/** Read-only derived census for this frozen experiment; prints JSON, makes no engine/model/network calls. */
import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { boundedAt, fromGit, sha } from './guards.mjs';
import { diagnosticCensus } from './diagnostics.mjs';
const here=path.dirname(fileURLToPath(import.meta.url));
assert(process.argv.length===4,'Supply local DWP checkout and retained comparison directory');
const [root,archive]=process.argv.slice(2);
const comparisonRaw=await boundedAt(archive,'comparison.json',32*1024*1024);
const comparison=JSON.parse(comparisonRaw), protocolRaw=await boundedAt(here,'protocol.json',32768),protocol=JSON.parse(protocolRaw);
assert.equal(comparison.schema,'okf-qualification-context-comparison.v1');
assert.equal(comparison.inputs.protocol_sha256,sha(protocolRaw));
assert.equal(comparison.observations.length,160);
assert.deepEqual(await boundedAt(archive,'protocol.json',32768),protocolRaw);
const inputs={comparison_sha256:sha(comparisonRaw),protocol_sha256:sha(protocolRaw),summariser_sha256:sha(await boundedAt(here,'summarise.mjs',65536)),
  diagnostics_sha256:sha(await boundedAt(here,'diagnostics.mjs',65536)),sources:{}};
const indexes={},profiles={};
for(const stage of ['old','new']) {
  const commit=protocol[stage+'_dwp_commit'];
  assert.equal(comparison.inputs.sources[stage].commit,commit);
  const raw=fromGit(root,commit,'evaluation/semantic-expansion/assembly-index.json',8*1024*1024);
  const ref=comparison.inputs.sources[stage].files.find(f=>f.path==='evaluation/semantic-expansion/assembly-index.json');
  assert(ref && ref.sha256===sha(raw) && ref.bytes===raw.length);
  indexes[stage]=JSON.parse(raw);
  const profileRaw=fromGit(root,commit,'evaluation/semantic-expansion/profiles.json',4*1024*1024);
  profiles[stage]=JSON.parse(profileRaw);
  assert.equal(profiles[stage].obligations.length,203);
  inputs.sources[stage]={commit,index_sha256:sha(raw),profiles_sha256:sha(profileRaw)};
}
assert.deepEqual(profiles.old.obligations,profiles.new.obligations,'An obligation object changed');
const catalogueRaw=fromGit(root,protocol.new_dwp_commit,'evaluation/semantic-expansion/catalogue.json',4*1024*1024);
inputs.sources.new.catalogue_sha256=sha(catalogueRaw);
const catalogue=JSON.parse(catalogueRaw),keys=['severe-disability-ignored-persons','severe-disability-normal-residence'];
const nodes=keys.map(key=>catalogue.concepts.find(c=>c.key===key));assert(nodes.every(Boolean));
const group=[...new Set(nodes.flatMap(n=>n.required_source_ids))];assert.equal(group.length,17);
const realIds=new Map(indexes.new.records.map(r=>[r.id,r]));
assert(group.every(id=>realIds.get(id)?.kind==='evidence'));
const rows=[];
for(const observation of comparison.observations) for(const engine of ['baseline','candidate']) {
  const value=observation[engine];assert.equal(value.evidence_status,'insufficient');
  const census=diagnosticCensus(value,indexes[observation.source]);
  const expectedIds=new Set(value.expected_required_ids),selected=new Set(value.selected_ids);
  const focus=['staff-012','staff-013','staff-014','staff-017'].includes(observation.case_id);
  const requiredGroup=group.filter(id=>expectedIds.has(id));
  rows.push({source:observation.source,engine,case_id:observation.case_id,max_bytes:observation.max_bytes,
    context_id:value.context_id,package_sha256:value.package_sha256,bytes:value.bytes,records:value.records,relationships:value.relationships,
    candidate_hits:value.candidate_hits.length,declared_paths:value.declared_paths,retained_paths:value.retained_paths,
    omitted_requirements:value.omitted_requirement_ids.length,evidence_status:value.evidence_status,truncated:value.truncated,...census,
    ...(focus?{ignored_person_group:{introduced_by_new_source:true,source_present:group.filter(id=>indexes[observation.source].records.some(r=>r.id===id)).length,
      declared_required:requiredGroup.length,selected:group.filter(id=>selected.has(id)).length,
      missing_required:requiredGroup.filter(id=>!selected.has(id)),all_source_routes:group.map(id=>realIds.get(id).route)},
      missing_paths:value.missing_paths,missing_evidence:value.missing_evidence,omissions:value.omissions}:{}),
  });
}
const summary=[];
for(const max_bytes of protocol.budgets) for(const source of ['old','new']) for(const engine of ['baseline','candidate']) {
 const group=rows.filter(r=>r.max_bytes===max_bytes&&r.source===source&&r.engine===engine);assert.equal(group.length,40);
 const sum=(key)=>group.reduce((n,r)=>n+(Array.isArray(r[key])?r[key].length:r[key]),0);
 summary.push({source,engine,max_bytes,cases:40,candidate_hits:sum('candidate_hits'),declared_paths:sum('declared_paths'),retained_paths:sum('retained_paths'),
  missing_required_record_occurrences:sum('missing_required_record_ids'),missing_registered_obligation_occurrences:sum('missing_registered_obligation_ids'),
  missing_other_declared_occurrences:sum('missing_other_declared_ids'),diagnostic_union_occurrences:sum('diagnostic_union_ids'),
  diagnostic_retained_record_occurrences:sum('diagnostic_retained_record_ids'),omitted_requirements:sum('omitted_requirements'),sufficient:0});
}
console.log(JSON.stringify({schema:'okf-ignored-person-derived-census.v1',classification:'offline-derived-counts-not-new-assemblies',inputs,
  limitations:['Run the retained comparison replay first; this derived census does not execute or independently re-attest the assemblers.',
    'Expected paths come from pre-budget resolution. Direct missing required records exclude registered obligations and optional dependency sources.',
    'Diagnostic unions can include retained source identifiers; their size is not a count of missing required records.',
    'The 17-page group is introduced by the new source; an undeclared old-source page is not scored as a missing old requirement.',
    'All 203 whole obligation objects are unchanged. No current-law, model accuracy, public-service or specialist acceptance follows.'],summary,rows},null,2));
