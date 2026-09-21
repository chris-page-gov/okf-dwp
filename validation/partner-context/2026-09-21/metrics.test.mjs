import assert from 'node:assert/strict';
import { test } from 'node:test';
import { requirementCensus } from './metrics.mjs';
const route = { seed:'urn:topic',records:['urn:topic','urn:source'],assertions:['urn:edge'] };
const index={requirements:[{id:'urn:requirement',when_all:['urn:topic'],required:['urn:source','urn:review'],required_paths:[route]}]};
const resolution={resolved:[{id:'urn:topic'}],ambiguities:[],unresolved:[]};
const empty={selected:[],relationships:[],requirements:[],resolved_concepts:[],ambiguities:[]};
test('metadata fallback cannot remove authored paths or obligations from the denominator',()=>{
 const c=requirementCensus(index,resolution,empty);
 assert.equal(c.declared_paths,1);assert.equal(c.returned_paths,0);assert.equal(c.retained_paths,0);
 assert.deepEqual(c.missing_paths,[{requirement:'urn:requirement',...route}]);
 assert.deepEqual(c.omitted_requirement_ids,['urn:requirement']);assert.deepEqual(c.absent_required_ids,['urn:source','urn:review']);
 assert.deepEqual(c.activation_resolution,resolution);
});
test('omitted requirement output remains explicit even when its complete path survives',()=>{
 const p={...empty,selected:[{record:{id:'urn:topic'}},{record:{id:'urn:source'}}],relationships:[{id:'urn:edge',source:'urn:topic',target:'urn:source'}]};
 const c=requirementCensus(index,resolution,p);assert.equal(c.retained_paths,1);assert.equal(c.returned_paths,0);assert.deepEqual(c.omitted_requirement_ids,['urn:requirement']);assert.deepEqual(c.absent_required_ids,['urn:review']);
});
test('ambiguous alternatives never activate a source requirement',()=>{
 const c=requirementCensus(index,{resolved:[],ambiguities:[{phrase:'topic',candidates:['urn:topic','urn:other']}],unresolved:[]},empty);
 assert.equal(c.declared_paths,0);assert.deepEqual(c.expected_requirement_ids,[]);
});
test('reversed or absent graph edges remain missing, even if the endpoint is selected',()=>{
 const p={...empty,selected:[{record:{id:'urn:topic'}},{record:{id:'urn:source'}}],relationships:[{id:'urn:edge',source:'urn:source',target:'urn:topic'}],requirements:index.requirements};
 const c=requirementCensus(index,resolution,p);assert.equal(c.declared_paths,1);assert.equal(c.retained_paths,0);assert.equal(c.returned_paths,1);assert.deepEqual(c.omitted_requirement_ids,[]);
});
