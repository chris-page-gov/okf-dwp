/** Independent authored-path census, using pre-budget declared-alias resolution. */
export function pathRetained(route, selected, edges) {
  return route.records.every(id => selected.has(id)) && route.assertions.every((id, i) => edges.get(id)?.source === route.records[i] && edges.get(id)?.target === route.records[i + 1]);
}
export function requirementCensus(index, resolution, context) {
  // Never derive activation or denominators from a byte-trimmed result. Ambiguous
  // alternatives are not resolved seeds and therefore do not activate profiles.
  const seeds = new Set(resolution.resolved.map(row => row.id));
  const expected = index.requirements.filter(requirement => requirement.when_all.every(id => seeds.has(id)));
  const expectedIds = new Set(expected.map(row => row.id)), returnedIds = new Set(context.requirements.map(row => row.id));
  const selected = new Map(context.selected.map(row => [row.record.id, row])), edges = new Map(context.relationships.map(edge => [edge.id, edge]));
  const paths = expected.flatMap(row => (row.required_paths || []).map(route => ({ requirement: row.id, ...route })));
  const missing = paths.filter(route => !pathRetained(route, selected, edges));
  return {
    expected_requirement_ids: [...expectedIds], returned_requirement_ids: [...returnedIds],
    omitted_requirement_ids: [...expectedIds].filter(id => !returnedIds.has(id)),
    unexpected_returned_requirement_ids: [...returnedIds].filter(id => !expectedIds.has(id)),
    expected_required_ids: [...new Set(expected.flatMap(row => row.required))],
    absent_required_ids: [...new Set(expected.flatMap(row => row.required))].filter(id => !selected.has(id)),
    declared_paths: paths.length, returned_paths: context.requirements.flatMap(row => row.required_paths || []).length,
    retained_paths: paths.length - missing.length, missing_paths: missing,
    activation_resolution: resolution
  };
}
