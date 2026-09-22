/** Independent scoring planes for location navigation and unresolved obligations.
 * Pure observations of an assembled context; never changes or assembles it.
 */
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';

const sha=raw=>createHash('sha256').update(raw).digest('hex');
const obligation=id=>id.includes('/id/obligation/staff/');

export function retainedContextPath(context,path,resolvedConceptIds){
 const selected=new Set(context.selected.map(item=>item.record.id));
 const edges=new Map(context.relationships.map(edge=>[edge.id,edge]));
 const resolved=new Set(resolvedConceptIds);
 if(!Array.isArray(path.records)||!Array.isArray(path.assertions)||path.records.length!==path.assertions.length+1
    ||!path.records.length||new Set(path.records).size!==path.records.length||path.seed!==path.records[0])return false;
 return path.records.every(id=>selected.has(id))&&path.assertions.every((id,index)=>{
  const edge=edges.get(id);
  return edge?.source===path.records[index]&&edge.target===path.records[index+1]
   &&(!edge.context_guard||edge.context_guard.when_all.every(concept=>resolved.has(concept)));
 });
}

/** `requirements` is this run's declared base index, not returned/budgeted rows.
 * `legacyRequirements` is the separately pinned immutable original collection.
 * The same candidate ledger may be measured against baseline and candidate:
 * only legacy requirements actually declared in this index activate its routes.
 */
export function measureLocationNavigation({context,ledger,resolvedConceptIds,requirements,legacyRequirements,canonicalJson}){
 assert.equal(ledger.schema,'okf-dwp-location-migration-ledger.v1');
 assert.equal(typeof canonicalJson,'function');
 const resolved=new Set(resolvedConceptIds),declared=new Map(requirements.map(row=>[row.id,row]));
 const legacy=new Map(legacyRequirements.map(row=>[row.id,row]));
 assert.equal(legacy.size,legacyRequirements.length,'Duplicate original requirement');
 const active=legacyRequirements.filter(row=>declared.has(row.id)&&row.when_all.every(id=>resolved.has(id)));
 for(const row of legacyRequirements.filter(row=>declared.has(row.id)))assert.deepEqual(declared.get(row.id),row,'Legacy requirement changed');
 const selected=new Map(context.selected.map(item=>[item.record.id,item.record]));
 assert.equal(selected.size,context.selected.length,'Duplicate selected record');
 const allObligations=[...new Set(legacyRequirements.flatMap(row=>row.required.filter(obligation)))].sort();
 const declaredObligations=[...new Set(legacyRequirements.filter(row=>declared.has(row.id)).flatMap(row=>row.required.filter(obligation)))].sort();
 const activeObligations=[...new Set(active.flatMap(row=>row.required.filter(obligation)))].sort();
 assert(!allObligations.some(id=>selected.has(id)),'Legacy open obligation was supplied as an evidence record');
 for(const row of context.requirements.filter(row=>legacy.has(row.id))){
  assert.notEqual(row.status,'supported-within-declared-scope','Location navigation must not close an original obligation-bearing requirement');
 }
 const byProfile=new Map(ledger.profiles.map(row=>[row.requirement_id,row]));
 assert.equal(byProfile.size,ledger.profiles.length,'Duplicate location profile');
 const activeProfiles=active.map(row=>{
  const profile=byProfile.get(row.id);assert(profile,'Active legacy requirement lacks location ledger');
  assert.deepEqual(profile.when_all,row.when_all,'Location guard differs from original requirement');
  return profile;
 });
 const activeCandidateIds=[...new Set(activeProfiles.flatMap(row=>row.candidate_ids))].sort();
 const maps=new Map(ledger.source_maps.map(row=>[row.candidate_id,row]));
 assert.equal(maps.size,ledger.source_maps.length,'Duplicate source location');
 const activeMaps=activeCandidateIds.map(id=>{assert(maps.has(id),'Unknown candidate location');return maps.get(id);});
 const mapped=new Map();
 for(const location of activeMaps)for(const unit of location.new_units){
  if(mapped.has(unit.id))assert.equal(mapped.get(unit.id),unit.record_sha256,'Conflicting unit commitments');
  mapped.set(unit.id,unit.record_sha256);
 }
 const selectedMapped=[...mapped.keys()].filter(id=>selected.has(id));
 for(const id of selectedMapped){
  assert.equal(selected.get(id).kind,'evidence','Location destination is not evidence');
  // DWP catalogue hashes repository canonical JSON, including its terminal LF.
  assert.equal(sha(canonicalJson(selected.get(id))+'\n'),mapped.get(id),'Selected location unit complete-record identity differs');
 }
 const routes=activeProfiles.flatMap(row=>row.navigation_routes);
 const returnedEdges=new Map(context.relationships.map(row=>[row.id,row]));
 for(const route of routes){
  assert.equal(route.assertions.at(-1),route.assertion_id,'Location terminal edge identity differs');
  assert.equal(route.records.at(-1),route.target,'Location destination differs');
  const edge=returnedEdges.get(route.assertion_id);
  // Original prefix edges can be unguarded. The newly authored terminal edge
  // must retain the exact conjunctive guard committed by this location ledger.
  if(edge)assert.deepEqual(edge.context_guard,route.context_guard,'Location terminal guard differs');
 }
 const byKind={};
 for(const kind of ['restored-original-route','inferred-profile-candidate-route']){
  const expected=routes.filter(row=>row.derivation===kind);
  const retained=expected.filter(row=>retainedContextPath(context,row,resolved));
  byKind[kind]={declared_routes:expected.length,retained_routes:retained.length,
   omitted_route_assertion_ids:expected.filter(row=>!retainedContextPath(context,row,resolved)).map(row=>row.assertion_id),
   retained_destination_ids:[...new Set(retained.map(row=>row.target))].sort()};
 }
 assert.equal(Object.values(byKind).reduce((n,row)=>n+row.declared_routes,0),routes.length,'Unknown location route derivation');
 return {schema:'okf-location-navigation-evaluation.v1',
  active_legacy_requirement_ids:active.map(row=>row.id),
  legacy_obligations:{original_count:allObligations.length,declared_in_this_index:declaredObligations.length,
   active_count:activeObligations.length,active_ids:activeObligations,selected_as_evidence:0,closed_by_location_navigation:0},
  routes:byKind,
  locations:{active_candidate_ids:activeCandidateIds,mapped_unit_count:mapped.size,selected_mapped_unit_count:selectedMapped.length,
   selected_mapped_unit_ids:selectedMapped.sort(),
   candidates_with_all_mapped_units_selected:activeMaps.filter(row=>row.new_units.length&&row.new_units.every(unit=>selected.has(unit.id))).map(row=>row.candidate_id),
   partial_or_unresolved_source_locations:activeMaps.filter(row=>row.status!=='location-fully-mapped').map(row=>row.candidate_id)},
  original_route_gaps:{missing_profile_candidate_associations:activeProfiles.flatMap(row=>row.missing_original_routes).length,
   unresolved_prefixes:activeProfiles.flatMap(row=>row.unresolved_original_prefixes).length},
  limitations:['A location route is research navigation, not required-path support, relevance or legal applicability.',
   'Mapped units may be selected lexically without any location route; selected_mapped_unit_count is therefore separate from retained_routes.',
   'All original obligations remain open. Budgeted delivery and metadata refusal can remove records and paths without changing declared requirements.']};
}
