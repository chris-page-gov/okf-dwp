import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {admitRestoredScopes} from './structured_restoration_admission.mjs';

const base='https://chris-page-gov.github.io/okf-dwp/id/';
const sort=x=>Array.isArray(x)?x.map(sort):x&&typeof x==='object'?Object.fromEntries(Object.keys(x).sort().map(k=>[k,sort(x[k])])):x;
const canonicalJson=x=>JSON.stringify(sort(x));
const hash=x=>createHash('sha256').update(canonicalJson(x)+'\n').digest('hex');
function fixture(){
  const scope={id:base+'scope/chapter',kind:'scope',route:'scope/chapter',label:'Chapter',text:'Captured chapter scope.',scope:'Dated guidance.',authority:{class:'derived'}};
  const old={id:base+'evidence/imprisonment-catalogue',kind:'evidence',route:'evidence/imprisonment-catalogue',label:'Catalogue',text:'Exact captured catalogue text.',scope:'Earlier capture.',authority:{class:'derived'},provenance:[{url:'https://example.test/catalogue'}]};
  const transformed={...old,id:base+'scope/custody-capture/catalogue',route:'scope/custody-capture/catalogue',kind:'scope',label:'Frozen catalogue observation: '+old.label,scope:'Exact captured catalogue text from the original 15 September 2026 source profile. This is a dated navigation/scope observation, not the absent memo body, current law or a claim that ADM bodies are absent from the later corpus. '+old.scope};
  const requirements=[{id:base+'requirement/historical',required:[base+'page/historical']}];
  return {author:{schema:'okf-dwp-structured-custody-restoration.v1',scope_records:[
    {id:scope.id,original_id:scope.id,original_record_sha256:hash(scope),mode:'exact-historical-scope'},
    {id:transformed.id,original_id:old.id,original_record_sha256:hash(old),mode:'dated-catalogue-observation'}]},
    ledger:{schema:'okf-dwp-custody-unit-translation.v1',original_obligations_closed:0,original_requirements:structuredClone(requirements),added_scope_records:[scope,transformed]},
    original:{records:[structuredClone(scope),old],requirements},candidate:{records:[structuredClone(scope),structuredClone(transformed)],requirements:structuredClone(requirements)},canonicalJson};
}

test('admits only exact historical scope and a dated scope presentation of catalogue text',()=>{
  const args=fixture();const before=canonicalJson({...args,canonicalJson:undefined});
  assert.equal(admitRestoredScopes(args).size,2);
  assert.equal(canonicalJson({...args,canonicalJson:undefined}),before);
});
test('rejects forged source, authority or evidence promotion even when candidate agrees',()=>{
  for(const field of ['text','authority','kind','scope']){
    const args=fixture();const row=args.ledger.added_scope_records[1];
    row[field]=field==='authority'?{class:'official'}:field==='kind'?'evidence':field==='scope'?row.scope+' Invented current conclusion.':'Unbound replacement';
    args.candidate.records[1]=structuredClone(row);
    assert.throws(()=>admitRestoredScopes(args));
  }
});
test('rejects duplicate, undeclared and unbound scope records',()=>{
  for(const mutate of [a=>a.author.scope_records.push(a.author.scope_records[0]),
    a=>a.ledger.added_scope_records.push({...a.ledger.added_scope_records[0],id:base+'scope/extra'}),
    a=>a.author.scope_records[0].original_record_sha256='0'.repeat(64)]){
    const args=fixture();mutate(args);assert.throws(()=>admitRestoredScopes(args));
  }
});
test('rejects changed historical requirements or claimed obligation closure',()=>{
  for(const mutate of [a=>a.candidate.requirements[0].required=[],
    a=>a.ledger.original_requirements[0].required=[],a=>a.ledger.original_obligations_closed=1,
    a=>a.candidate.requirements.push(a.candidate.requirements[0])]){
    const args=fixture();mutate(args);assert.throws(()=>admitRestoredScopes(args));
  }
});
