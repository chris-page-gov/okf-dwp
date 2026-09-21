import assert from 'node:assert/strict';
// All lengths are UTF-8 bytes of the canonical JSON actually replayed.
export function packageByteCensus(pkg, canonical) {
  const size=value=>Buffer.byteLength(canonical(value));
  const total=size(pkg), entries=Object.fromEntries(Object.keys(pkg).filter(k=>pkg[k]!==undefined).sort().map(k=>[k,Buffer.byteLength(JSON.stringify(k))+1+size(pkg[k])]));
  const punctuation=2+Math.max(0,Object.keys(entries).length-1);
  assert.equal(Object.values(entries).reduce((a,b)=>a+b,0)+punctuation,total);
  let evidence=0,other=0,evidenceRaw=0;
  for(const item of pkg.selected) {
    if(item.record.text===undefined)continue;
    if(item.record.kind==='evidence') { evidence+=size(item.record.text); evidenceRaw+=Buffer.byteLength(item.record.text); }
    else other+=size(item.record.text);
  }
  const selected=size(pkg.selected),rest=selected-evidence-other; assert(rest>=0);
  return {canonical_package_bytes:total,top_level_property_bytes:entries,root_punctuation_bytes:punctuation,
    selected_value_partition:{evidence_text_json_bytes:evidence,other_record_text_json_bytes:other,remaining_selected_structure_bytes:rest,total:selected},
    overlapping_observations:{evidence_text_raw_utf8_bytes:evidenceRaw,selected_record_provenance_json_bytes:pkg.selected.reduce((n,s)=>n+size(s.record.provenance),0)},
    selected_evidence_records:pkg.selected.filter(s=>s.record.kind==='evidence').length};
}
