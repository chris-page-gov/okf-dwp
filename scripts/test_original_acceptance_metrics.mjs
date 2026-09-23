import test from 'node:test';
import assert from 'node:assert/strict';
import {originalAcceptanceMetrics} from './original_acceptance_metrics.mjs';

function fixture(){
 const concept='urn:concept:custody',unit='urn:unit:12003',support='urn:unit:12002',scope='urn:scope:24';
 const edge=(source,target,id)=>({id:'urn:/assertion/custody-restoration/'+id,source,target,predicate:'http://purl.org/dc/terms/references',context_guard:{when_all:[concept]}});
 const primary=edge(concept,unit,'primary'),dependency=edge(unit,support,'dependency'),chapter=edge(unit,scope,'chapter');
 const path={seed:concept,records:[concept,unit],assertions:[primary.id]};
 const historical=Array.from({length:6},(_,n)=>({id:'urn:old:'+n,required:['urn:page:'+n]}));
 const profile={id:'urn:profile:units',unit_ids:[unit,support],required_paths:[path],open_obligation_ids:['urn:obligation:legal']};
 return {pack:{selected:[{record:{id:concept,kind:'concept'}},{record:{id:unit,kind:'evidence'}},{record:{id:support,kind:'evidence'}},{record:{id:scope,kind:'scope'}}],relationships:[primary,dependency,chapter],budget:{omissions:[]},missing_evidence:[]},
  base:{requirements:[...structuredClone(historical),{id:profile.id,when_all:[concept],required_paths:[path]}]},
  ledger:{original_requirements:historical,profiles:[profile],dependencies:[{source:unit,target:support}],chapter_routes:[{source:unit,target:scope}],unresolved_selectors:[{status:'unresolved'}]},
  resolvedIds:[concept],assertions:[primary,dependency,chapter]};
}
test('counts active source units and exact directed context independently from open obligations',()=>{
 const a=fixture(),r=originalAcceptanceMetrics(a);
 assert.equal(r.translated_selection.retained_active_unit_count,2);
 assert.equal(r.translated_selection.retained_required_path_count,1);
 assert.equal(r.source_context_dependencies[0].whole_endpoints_and_relationship_retained,true);
 assert.equal(r.literal_chapter_routes[0].whole_endpoints_and_relationship_retained,true);
 assert.deepEqual(r.open_obligation_ids,['urn:obligation:legal']);assert.equal(r.original_obligations_closed,0);
});
test('reports omitted source and broken path rather than passing on an edge alone',()=>{
 const a=fixture();a.pack.selected=a.pack.selected.filter(s=>s.record.id!=='urn:unit:12003');
 a.pack.budget.omissions=[{code:'byte_budget',ids:['urn:unit:12003'],message:'Whole item omitted.'}];
 const r=originalAcceptanceMetrics(a);
 assert.equal(r.translated_selection.retained_active_unit_count,1);assert.equal(r.translated_selection.retained_required_path_count,0);
 assert.equal(r.translated_selection.omitted_active_units[0].reasons[0].code,'byte_budget');
 assert.equal(r.source_context_dependencies[0].whole_endpoints_and_relationship_retained,false);
});
test('inactive custody profiles do not acquire evidence requirements from selected lexical units',()=>{
 const a=fixture();a.resolvedIds=[];const r=originalAcceptanceMetrics(a);
 assert.equal(r.translated_selection.active_unit_count,0);assert.equal(r.active_translated_requirement_ids.length,0);
 assert.equal(r.translated_selection.selected_union_units_without_active_profile.length,2);
 assert.equal(r.literal_chapter_routes[0].whole_endpoints_and_relationship_retained,false);
});
test('rejects altered old requirements, returned edges or fabricated obligation evidence',()=>{
 for(const mutate of [a=>a.base.requirements[0].required=[],a=>a.pack.relationships[1]={...a.pack.relationships[1],context_guard:{when_all:[]}},a=>a.pack.selected.push({record:{id:'urn:obligation:legal',kind:'evidence'}})]){
  const a=fixture();mutate(a);assert.throws(()=>originalAcceptanceMetrics(a));
 }
});
test('rejects weakened or absent primary path guards against the exact declared assertion',()=>{
 for(const guard of [undefined,{when_all:[]}]){
  const a=fixture();a.pack.relationships[0]={...a.pack.relationships[0]};
  if(guard===undefined)delete a.pack.relationships[0].context_guard;
  else a.pack.relationships[0].context_guard=guard;
  assert.throws(()=>originalAcceptanceMetrics(a),/Returned required-path relationship differs/);
 }
});
