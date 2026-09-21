/** A diagnostic ID can identify a retained source or an omitted target. Never count the union as missing required records. */
export function diagnosticCensus(observation, index) {
  const known = new Set(index.records.map(row => row.id));
  const selected = new Set(observation.selected_ids);
  const expected = [...new Set(observation.expected_required_ids)];
  const requiredRecords = expected.filter(id => known.has(id));
  const diagnosticIds = [...new Set(observation.missing_evidence.flatMap(row => row.ids))].sort();
  return {
    expected_existing_required_record_ids: requiredRecords,
    missing_required_record_ids: requiredRecords.filter(id => !selected.has(id)),
    missing_registered_obligation_ids: expected.filter(id => !known.has(id) && id.includes('/obligation/staff/') && !selected.has(id)),
    missing_other_declared_ids: expected.filter(id => !known.has(id) && !id.includes('/obligation/staff/') && !selected.has(id)),
    diagnostic_union_ids: diagnosticIds,
    diagnostic_retained_record_ids: diagnosticIds.filter(id => selected.has(id)),
    diagnostic_unselected_existing_ids: diagnosticIds.filter(id => known.has(id) && !selected.has(id)),
    diagnostic_nonrecord_ids: diagnosticIds.filter(id => !known.has(id)),
  };
}
