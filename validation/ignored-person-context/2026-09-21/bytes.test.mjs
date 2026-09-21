import assert from 'node:assert/strict';
import test from 'node:test';
import {packageByteCensus} from './bytes.mjs';
const canonical=v=>Array.isArray(v)?`[${v.map(canonical).join(',')}]`:v&&typeof v==='object'?`{${Object.keys(v).filter(k=>v[k]!==undefined).sort().map(k=>`${JSON.stringify(k)}:${canonical(v[k])}`).join(',')}}`:JSON.stringify(v);
test('partitions the exact UTF-8 canonical bytes; nested raw text is explicitly overlapping',()=>{
 const p={selected:[{record:{kind:'evidence',text:'£12\n😀',provenance:[{source:'x'}]}},{record:{kind:'concept',text:'condition',provenance:[]}}],requirements:[{label:'evidence'}],z:undefined};
 const c=packageByteCensus(p,canonical),n=c.selected_value_partition;
 assert.equal(c.canonical_package_bytes,Buffer.byteLength(canonical(p)));
 assert.equal(n.evidence_text_json_bytes+n.other_record_text_json_bytes+n.remaining_selected_structure_bytes,n.total);
 assert.equal(n.evidence_text_json_bytes,Buffer.byteLength(JSON.stringify('£12\n😀')));
 assert.equal(c.overlapping_observations.evidence_text_raw_utf8_bytes,Buffer.byteLength('£12\n😀'));
 assert.equal(c.selected_evidence_records,1);
});
test('empty evidence remains zero rather than treating diagnostics or concepts as source text',()=>{
 const c=packageByteCensus({selected:[{record:{kind:'concept',text:'source says',provenance:[]}}],missing_evidence:[{label:'quoted words'}]},canonical);
 assert.equal(c.selected_evidence_records,0);assert.equal(c.selected_value_partition.evidence_text_json_bytes,0);
 assert.equal(c.overlapping_observations.evidence_text_raw_utf8_bytes,0);
});
