import {test} from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {measureLocationNavigation,retainedContextPath} from './structured_context_metrics.mjs';
const canonicalJson=value=>JSON.stringify(function sort(v){return Array.isArray(v)?v.map(sort):v&&typeof v==='object'?Object.fromEntries(Object.keys(v).sort().map(k=>[k,sort(v[k])])):v;}(value));
const sha=v=>createHash('sha256').update(v).digest('hex');
const base='https://example.test/id/';
function fixture(){
 const pc=base+'concept/benefit',topic=base+'concept/topic',other=base+'concept/other',unit={id:base+'unit/one',kind:'evidence',text:'Whole passage with its qualification.'};
 const requirement={id:base+'requirement/staff/staff-001',when_all:[pc,topic],required:[base+'page/old',base+'obligation/staff/staff-001/open'],required_paths:[{seed:topic,records:[topic,base+'page/old'],assertions:[base+'assertion/old']}],scope:'Original scope'};
 const edge={id:base+'assertion/location',source:topic,target:unit.id,context_guard:{when_all:[pc,topic]}};
 const route={seed:topic,source:topic,target:unit.id,records:[topic,unit.id],assertions:[edge.id],assertion_id:edge.id,context_guard:edge.context_guard,derivation:'inferred-profile-candidate-route'};
 const context={selected:[{record:{id:pc,kind:'concept'}},{record:{id:topic,kind:'concept'}},{record:unit}],relationships:[edge],requirements:[{...requirement,status:'insufficient'}]};
 const ledger={schema:'okf-dwp-location-migration-ledger.v1',profiles:[{requirement_id:requirement.id,when_all:requirement.when_all,candidate_ids:['source-c001'],navigation_routes:[route],missing_original_routes:[{status:'no-original-profile-route'}],unresolved_original_prefixes:[]}],source_maps:[{candidate_id:'source-c001',status:'location-partly-mapped',new_units:[{id:unit.id,record_sha256:sha(canonicalJson(unit)+'\n')}]}]};
 return {pc,topic,other,unit,edge,route,requirement,context,ledger,args:{context,ledger,resolvedConceptIds:[pc,topic],requirements:[requirement],legacyRequirements:[requirement],canonicalJson}};
}
test('counts inferred navigation separately while the old requirement and obligation remain unmet',()=>{
 const f=fixture(),r=measureLocationNavigation(f.args);
 assert.equal(r.routes['inferred-profile-candidate-route'].retained_routes,1);
 assert.equal(r.routes['restored-original-route'].retained_routes,0);
 assert.equal(r.legacy_obligations.active_count,1);assert.equal(r.legacy_obligations.closed_by_location_navigation,0);
 assert.deepEqual(r.locations.partial_or_unresolved_source_locations,['source-c001']);
 assert.equal(retainedContextPath(f.context,f.requirement.required_paths[0],f.args.resolvedConceptIds),false);
});
test('lexically selected mapped text is not a retained navigation path',()=>{
 const f=fixture();f.context.relationships=[];const r=measureLocationNavigation(f.args);
 assert.equal(r.locations.selected_mapped_unit_count,1);assert.equal(r.routes['inferred-profile-candidate-route'].retained_routes,0);
});
test('route ID membership cannot hide wrong endpoints or an unmatched guard',()=>{
 const f=fixture();f.edge.target=base+'unit/wrong';assert.equal(retainedContextPath(f.context,f.route,f.args.resolvedConceptIds),false);
 f.edge.target=f.unit.id;assert.equal(retainedContextPath(f.context,f.route,[f.topic,f.other]),false);
});
test('a missing record or metadata refusal remains an omission without closing the obligation',()=>{
 const f=fixture();f.context.selected=[];f.context.relationships=[];f.context.requirements=[];const r=measureLocationNavigation(f.args);
 assert.equal(r.routes['inferred-profile-candidate-route'].retained_routes,0);assert.equal(r.locations.selected_mapped_unit_count,0);
 assert.equal(r.legacy_obligations.active_count,1);assert.equal(r.legacy_obligations.closed_by_location_navigation,0);
});
test('the baseline without declared legacy profiles gains no new location denominator',()=>{
 const f=fixture();f.args.requirements=[];f.context.requirements=[];const r=measureLocationNavigation(f.args);
 assert.equal(r.routes['inferred-profile-candidate-route'].declared_routes,0);assert.equal(r.legacy_obligations.original_count,1);assert.equal(r.legacy_obligations.declared_in_this_index,0);
});
test('an unrelated benefit does not activate a conjunctive profile',()=>{
 const f=fixture();f.args.resolvedConceptIds=[f.other,f.topic];const r=measureLocationNavigation(f.args);
 assert.equal(r.active_legacy_requirement_ids.length,0);assert.equal(r.routes['inferred-profile-candidate-route'].declared_routes,0);
});
test('rejects a changed complete record even if its identifier and text location still match',()=>{
 const f=fixture();f.unit.text+=' altered';assert.throws(()=>measureLocationNavigation(f.args),/complete-record identity/);
});
test('rejects a supplied obligation record or a claim that navigation closed the legacy requirement',()=>{
 let f=fixture();f.context.selected.push({record:{id:f.requirement.required[1],kind:'evidence'}});assert.throws(()=>measureLocationNavigation(f.args),/open obligation/);
 f=fixture();f.context.requirements[0].status='supported-within-declared-scope';assert.throws(()=>measureLocationNavigation(f.args),/must not close/);
});
test('rejects changed original requirements and ambiguous route derivations',()=>{
 let f=fixture();f.args.requirements=structuredClone(f.args.requirements);f.args.requirements[0].required=[];assert.throws(()=>measureLocationNavigation(f.args),/Legacy requirement changed/);
 f=fixture();f.route.derivation='source-proves-answer';assert.throws(()=>measureLocationNavigation(f.args),/Unknown location route/);
});

test('rejects a missing or weakened declared terminal guard while allowing unguarded original prefixes',()=>{
 let f=fixture();delete f.edge.context_guard;assert.throws(()=>measureLocationNavigation(f.args),/terminal guard differs/);
 f=fixture();f.edge.context_guard={when_all:[f.topic]};assert.throws(()=>measureLocationNavigation(f.args),/terminal guard differs/);
 f=fixture();const prefix={id:base+'assertion/prefix',source:f.pc,target:f.topic};
 f.context.relationships.unshift(prefix);f.route.seed=f.pc;f.route.records.unshift(f.pc);f.route.assertions.unshift(prefix.id);
 assert.equal(measureLocationNavigation(f.args).routes['inferred-profile-candidate-route'].retained_routes,1);
});
