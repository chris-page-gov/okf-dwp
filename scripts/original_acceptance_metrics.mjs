/** Read retained original-case context without equating delivery with support. */
import assert from 'node:assert/strict';
import {retainedContextPath} from './structured_context_metrics.mjs';

export function originalAcceptanceMetrics({pack, base, ledger, resolvedIds, assertions}) {
  const resolved = new Set(resolvedIds), selected = new Map(pack.selected.map(s => [s.record.id,s.record]));
  const requirements = new Map(base.requirements.map(r => [r.id,r]));
  const original = ledger.original_requirements;
  assert.equal(original.length,6);
  for (const row of original) assert.deepEqual(requirements.get(row.id),row,'Historical custody expectation changed');
  const active = ledger.profiles.filter(p => {
    const requirement=requirements.get(p.id);assert(requirement,'Translated custody requirement absent');
    assert.deepEqual(requirement.required_paths,p.required_paths);
    return requirement.when_all.every(id=>resolved.has(id));
  });
  const expectedUnits=[...new Set(active.flatMap(p=>p.unit_ids))].sort();
  const declaredUnion=[...new Set(ledger.profiles.flatMap(p=>p.unit_ids))].sort();
  const reasons=id=>[...pack.budget.omissions,...(pack.retrieval?.omissions||[]),...pack.missing_evidence]
    .filter(o=>o.ids?.includes(id)).map(o=>({code:o.code,message:o.message}));
  const paths=active.flatMap(p=>p.required_paths);
  const retained=p=>retainedContextPath(pack,p,resolved);
  const edges=new Map(pack.relationships.map(e=>[e.id,e]));
  const declaredById=new Map(assertions.map(e=>[e.id,e]));
  assert.equal(declaredById.size,assertions.length,'Duplicate declared relationship identity');
  for(const id of new Set(paths.flatMap(p=>p.assertions))){
    assert(declaredById.has(id),'Required path assertion absent from declared source');
    if(edges.has(id))assert.deepEqual(edges.get(id),declaredById.get(id),'Returned required-path relationship differs');
  }
  const evidence=id=>selected.get(id)?.kind==='evidence';
  const inspectEdge=row=>{
    const candidates=assertions.filter(e=>e.source===row.source&&e.target===row.target
      &&e.id.includes('/assertion/custody-restoration/'));
    assert.equal(candidates.length,1,'Missing or ambiguous declared custody context edge');
    const declared=candidates[0],returned=edges.get(declared.id);
    if(returned)assert.deepEqual(returned,declared,'Returned custody context edge differs');
    const guardMatched=declared.context_guard.when_all.every(id=>resolved.has(id));
    return {source:row.source,target:row.target,assertion_id:declared.id,guard_matched:guardMatched,
      source_selected:selected.has(row.source),target_selected:selected.has(row.target),
      relationship_retained:!!returned,whole_endpoints_and_relationship_retained:guardMatched&&selected.has(row.source)&&selected.has(row.target)&&!!returned,
      omission_reasons:reasons(declared.id)};
  };
  const dependencies=ledger.dependencies.map(inspectEdge),chapterRoutes=ledger.chapter_routes.map(inspectEdge);
  const open=active.flatMap(p=>p.open_obligation_ids);
  assert(open.every(id=>!selected.has(id)),'Missing custody obligation fabricated as evidence');
  return {
    original_requirements_preserved:original.map(r=>r.id),
    active_translated_requirement_ids:active.map(p=>p.id),
    translated_selection:{declared_union_count:declaredUnion.length,active_unit_count:expectedUnits.length,
      retained_active_unit_count:expectedUnits.filter(evidence).length,
      retained_active_unit_ids:expectedUnits.filter(evidence),
      omitted_active_units:expectedUnits.filter(id=>!evidence(id)).map(id=>({id,reasons:reasons(id)})),
      selected_union_units_without_active_profile:declaredUnion.filter(id=>evidence(id)&&!expectedUnits.includes(id)),
      required_path_count:paths.length,retained_required_path_count:paths.filter(retained).length,
      omitted_required_paths:paths.filter(p=>!retained(p))},
    source_context_dependencies:dependencies,literal_chapter_routes:chapterRoutes,
    open_obligation_ids:[...new Set(open)].sort(),
    unmatched_original_selector_observations:ledger.unresolved_selectors,
    original_obligations_closed:0,
    scope_warning:'The historical page expectations and this bounded unit selection are separate. Source delivery, exact paths and catalogue metadata do not establish current ADM applicability, complete qualifications, specialist acceptance or an individual benefit decision.'
  };
}
