/** Standalone, offline inspector for verified candidate evidence collections. */
import { createHash } from 'node:crypto';

const escapeHtml = value => String(value ?? '').replaceAll('&', '&amp;').replaceAll('<', '&lt;')
  .replaceAll('>', '&gt;').replaceAll('"', '&quot;').replaceAll("'", '&#39;');
const embeddedJson = value => JSON.stringify(value).replaceAll('<', '\\u003c').replaceAll('>', '\\u003e')
  .replaceAll('&', '\\u0026').replaceAll('\u2028', '\\u2028').replaceAll('\u2029', '\\u2029');
const hash = value => createHash('sha256').update(value).digest('base64');

/** Links are source references, never commands or local filesystem routes. */
export function safeSourceUrl(value) {
  if (typeof value !== 'string' || !value || value !== value.trim() || /[\u0000-\u0020\u007f]/u.test(value)) return null;
  try {
    const url = new URL(value);
    return ['https:', 'http:'].includes(url.protocol) && !url.username && !url.password ? url.href : null;
  } catch { return null; }
}

const style = `
:root{font-family:system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:#172c3d;background:#f4f6f7;font-size:16px;line-height:1.5;color-scheme:light}
*{box-sizing:border-box}body{margin:0}a{color:#075ea8;text-underline-offset:.15em}a:hover{text-decoration-thickness:2px}button,input,select{font:inherit}button,a,input,select,summary{outline-offset:4px}button:focus-visible,a:focus-visible,input:focus-visible,select:focus-visible,summary:focus-visible{outline:3px solid #e6bb20}
.skip-link{position:absolute;left:1rem;top:-5rem;background:#ffe57d;padding:.75rem;z-index:2}.skip-link:focus{top:.5rem}header{background:#153b53;color:#fff;border-bottom:5px solid #55b6a9}header>div,main,footer{max-width:1240px;margin:0 auto;padding:1.5rem 2rem}.eyebrow{text-transform:uppercase;letter-spacing:.08em;font-size:.76rem;font-weight:700;color:#d7eeee}h1{font-size:clamp(1.7rem,3vw,2.35rem);line-height:1.2;margin:.45rem 0 .75rem}h2{font-size:1.4rem;margin:0 0 .9rem}h3{font-size:1.08rem;margin:0 0 .7rem}p{margin:.55rem 0 1rem}.question{font-size:1.08rem;max-width:90ch}.boundary{background:#fff7d6;border-left:5px solid #b28512;padding:1rem 1.2rem;margin:0 0 1.5rem}.boundary p:last-child{margin-bottom:0}.panel{background:#fff;border:1px solid #d5dee3;border-radius:5px;padding:1.35rem;margin:0 0 1.3rem;min-width:0}.muted,.small{color:#4d6171}.small{font-size:.88rem}.status{display:inline-block;background:#e6edf3;color:#27495f;padding:.12rem .5rem;border-radius:3px;font-size:.83rem;font-weight:650}.status.warning{background:#fff1c0;color:#6d4e00}.status.complete{background:#e1f1e9;color:#205e40}.status.unknown{background:#edf0f2;color:#4d6171}.table-scroll{overflow-x:auto}table{border-collapse:collapse;width:100%;text-align:left;font-variant-numeric:tabular-nums;font-size:.9rem}th,td{padding:.7rem .6rem;border-bottom:1px solid #d5dee3;vertical-align:top}thead th{font-weight:700;background:#f5f8fa}th:first-child{min-width:190px}.context-choice{display:flex;align-items:start;gap:.6rem}.context-choice input{margin-top:.35rem;accent-color:#176a78}.context-choice label{cursor:pointer}.context-choice span{display:block}.context-choice .small{font-weight:400}.selected-row{background:#f0f8f8}.comparison-note{margin-bottom:0}.metrics{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:.75rem;margin:1rem 0}.metric{background:#f4f8fa;border:1px solid #e0e7eb;border-radius:4px;padding:.8rem}.metric strong{display:block;font-size:1.18rem}.metric span{font-size:.82rem;color:#4d6171}.toolbar{display:flex;gap:1rem;align-items:end;margin-bottom:1rem}.field{display:flex;flex-direction:column;gap:.3rem;flex:1;min-width:0}.field label{font-weight:650;font-size:.9rem}.field input,.field select{padding:.6rem .7rem;border:1px solid #7e909b;border-radius:3px;background:#fff;color:#172c3d;width:100%}.field.scope{flex:0 0 185px}.record-list{display:grid;gap:.8rem}.record{border:1px solid #d5dee3;border-radius:4px;overflow:hidden}.record>summary{padding:.9rem 1rem;background:#f7fafb;cursor:pointer;font-weight:650}.record-title{display:inline}.record-meta{margin:.45rem 0 0 1.2rem;font-weight:400;font-size:.82rem;color:#4d6171;overflow-wrap:anywhere}.record-body{padding:1rem}.source-text{white-space:pre-wrap;overflow-wrap:anywhere;font-family:inherit;line-height:1.6;background:#f8fafb;border-left:3px solid #a5becb;padding:1rem;margin:.5rem 0 1.2rem}.mono,code,pre{font-family:ui-monospace,SFMono-Regular,Consolas,monospace}.json{background:#f4f7f9;border:1px solid #dbe3e8;padding:.85rem;font-size:.8rem;white-space:pre-wrap;overflow-wrap:anywhere;max-height:28rem;overflow:auto;margin:.65rem 0 0}.identity-line{overflow-wrap:anywhere;font-size:.85rem}.provenance{padding:0;list-style:none;display:grid;gap:.75rem}.provenance li{padding:.8rem;background:#f4f7f9;border:1px solid #dbe3e8;overflow-wrap:anywhere}.provenance p{margin:.3rem 0}.source-unlinked{color:#6d4e00}details>summary{cursor:pointer}details.block{margin:.8rem 0}details.block>summary{font-weight:650}.empty{padding:1rem;background:#f4f7f9;border:1px dashed #b4c4cd}.query{background:#f4f8fa;border-left:3px solid #9bb9c9;padding:.8rem 1rem;overflow-wrap:anywhere}.diagnostic-codes{display:flex;gap:.4rem;flex-wrap:wrap;margin:.7rem 0}.code{display:inline-block;border:1px solid #d5dee3;padding:.15rem .4rem;background:#f7fafb;font-size:.8rem;overflow-wrap:anywhere}ul.limitations{padding-left:1.35rem}ul.limitations li{margin:.5rem 0}footer{color:#4d6171;font-size:.83rem;padding-top:.5rem;padding-bottom:2rem}.hidden{display:none!important}
@media(max-width:760px){header>div,main,footer{padding:1.1rem 1rem}.panel{padding:1rem}.metrics{grid-template-columns:repeat(2,minmax(0,1fr))}.toolbar{display:block}.field.scope{margin-top:.8rem}.json{font-size:.75rem}th,td{padding:.55rem .4rem}.boundary{padding:.8rem}.record-meta{margin-left:0}}
@media print{body{background:#fff}header{background:#fff;color:#172c3d;border-bottom:2px solid #172c3d}.eyebrow{color:#4d6171}.toolbar,.skip-link{display:none}.panel{break-inside:avoid}.json{max-height:none}a{color:#172c3d}.table-scroll{overflow:visible}main{padding:1rem 0}}
`;

// This script never parses source text as HTML and never makes a network request.
const script = `
'use strict';
const report=JSON.parse(document.getElementById('review-data').textContent);
const byId=id=>document.getElementById(id);
const node=(tag,text,className)=>{const result=document.createElement(tag);if(text!==undefined)result.textContent=String(text);if(className)result.className=className;return result;};
const stringify=value=>typeof value==='string'?value:JSON.stringify(value,null,2);
const display=value=>value===undefined||value===null?'Not recorded':String(value);
const numeric=value=>Number.isFinite(value)?new Intl.NumberFormat('en-GB').format(value):'Not recorded';
const jsonBlock=value=>node('pre',JSON.stringify(value??{},null,2),'json');
const details=(label,value,open=false)=>{const element=node('details',undefined,'block');element.open=open;element.append(node('summary',label),jsonBlock(value));return element;};
const safeUrl=value=>{if(typeof value!=='string'||!value||value!==value.trim()||/[\\u0000-\\u0020\\u007f]/u.test(value))return null;try{const url=new URL(value);return ['https:','http:'].includes(url.protocol)&&!url.username&&!url.password?url.href:null;}catch{return null;}};
const short=value=>typeof value==='string'&&value.length>70?value.slice(0,67)+'…':display(value);
const makeStatus=(text,type='unknown')=>node('span',text,'status '+type);
const metric=(value,label)=>{const element=node('div',undefined,'metric');element.append(node('strong',value),node('span',label));return element;};
const diagnosticsOf=context=>context.diagnostics&&typeof context.diagnostics==='object'?context.diagnostics:{};
const deliveryOf=context=>context.delivery&&typeof context.delivery==='object'?context.delivery:{};
const completeOf=context=>context.delivery_complete===true;
const values=report.contexts;
let current=values[0];
function renderProvenance(record){
 const list=node('ul',undefined,'provenance');
 const items=Array.isArray(record.provenance)?record.provenance:[];
 for(const item of items){const row=node('li');const url=safeUrl(item.url);if(url){const link=node('a',item.url);link.href=url;link.target='_blank';link.rel='noopener noreferrer';row.append(link);}else if(item.url){row.append(node('p','Unlinked source reference: '+display(item.url),'source-unlinked'));}
 row.append(node('p','Locator: '+display(item.locator),'small'),node('p','Source SHA-256: '+display(item.source_sha256),'small mono'));
 const extra=Object.fromEntries(Object.entries(item).filter(([key])=>!['url','locator','source_sha256'].includes(key)));if(Object.keys(extra).length)row.append(details('Additional provenance',extra));list.append(row);}
 if(!items.length)list.append(node('li','No provenance was recorded. This record must not be treated as verified official evidence.'));
 return list;
}
function renderRecord(record){
 const element=node('details',undefined,'record');const summary=node('summary');summary.append(node('span',display(record.label),'record-title'));
 summary.append(node('div',display(record.kind)+' · '+display(record.id),'record-meta'));element.append(summary);
 const body=node('div',undefined,'record-body');body.append(node('h3','Exact retained text'),node('pre',typeof record.text==='string'?record.text:'No retained text.','source-text'));
 body.append(node('h3','Authority and review'),jsonBlock({authority:record.authority??null,review_status:record.review_status??null,assertion_status:record.assertion_status??null}));
 body.append(node('h3','Source provenance'),renderProvenance(record));body.append(details('Why this record was selected',{reasons:record.reasons??[],paths:record.paths??[]}));element.append(body);return element;
}
function renderRecords(){
 const records=Array.isArray(current.records)?current.records:[];const query=byId('record-search').value.toLocaleLowerCase('en-GB');const scope=byId('record-scope').value;
 const filtered=records.filter(record=>(scope==='all'||record.kind==='evidence')&&(!query||[record.label,record.id,record.text].some(value=>typeof value==='string'&&value.toLocaleLowerCase('en-GB').includes(query))));
 byId('record-count').textContent=numeric(filtered.length)+' of '+numeric(records.length)+' retained records shown';const list=byId('record-list');list.replaceChildren();
 if(!filtered.length)list.append(node('p',records.length?'No records match this search and record type.':'This context retained no readable records.','empty'));
 for(const record of filtered)list.append(renderRecord(record));
}
function selectContext(index){
 current=values[index];for(const row of document.querySelectorAll('[data-context-index]'))row.classList.toggle('selected-row',Number(row.dataset.contextIndex)===index);
 byId('selected-title').textContent=display(current.label??current.id);byId('selected-query').textContent=display(current.query);byId('selected-identity').textContent=display(current.context_id);
 const status=byId('selected-status');status.replaceChildren(makeStatus(display(current.evidence_status),current.evidence_status==='sufficient'?'complete':'warning'));
 const note=byId('evidence-boundary');note.textContent=current.evidence_status==='sufficient'?'The engine reports scoped sufficiency for this context. This is not specialist approval or an individual entitlement decision.':'The retained evidence has not established a complete answer. Verified delivery preserves this status and cannot supply missing evidence.';
 const metrics=byId('selected-metrics');metrics.replaceChildren(metric(numeric(current.selected_records),'selected records'),metric(numeric(current.relationships),'relationships'),metric(numeric(current.package_bytes)+' bytes','assembled package'),metric(completeOf(current)?'Verified complete':'Not established','delivery of requested values'));
 const delivery=deliveryOf(current);const calls=Array.isArray(current.receipt?.calls)?current.receipt.calls:[];const largest=calls.length?Math.max(...calls.map(call=>Number(call.response_bytes)||0)):null;
 const packageState=current.package_complete===true?'The whole assembled package was reconstructed and verified.':current.package_complete===false?'Only the requested values were verified; the whole package was not reconstructed.':'Whole-package reconstruction was not recorded.';
 byId('delivery-state').textContent=packageState+' Largest recorded response: '+numeric(delivery.max_response_bytes??largest)+' bytes.'+(Number.isFinite(delivery.max_value_json_bytes)?' Largest decoded value: '+numeric(delivery.max_value_json_bytes)+' bytes.':'')+' Calls: '+numeric(delivery.calls??calls.length)+'.';
 byId('truncation-state').textContent='Assembly truncation: '+display(current.assembly_truncated)+'. Retrieval truncation: '+display(current.retrieval_truncated)+'.'+(current.identity_kind==='graph-plan'?' Complete declared graph routes: '+display(current.retrieval_complete)+'.':'')+' These describe selection limits and omissions, independently of whether every requested byte was delivered.';
 const diagnostics=diagnosticsOf(current);const codes=[...new Set((Array.isArray(diagnostics.missing_evidence)?diagnostics.missing_evidence:[]).map(item=>item.code).filter(value=>typeof value==='string'))];const codeList=byId('diagnostic-codes');codeList.replaceChildren();for(const code of codes)codeList.append(node('span',code,'code'));
 const full=byId('full-diagnostics');full.replaceChildren(details('Reasons grouped for review',current.insufficiency_categories??[]),jsonBlock(diagnostics));const receipt=byId('delivery-receipt');receipt.replaceChildren(jsonBlock({delivery_complete:current.delivery_complete??null,package_complete:current.package_complete??null,package_sha256:current.package_sha256??null,delivery:current.delivery??null,receipt:current.receipt??null}));
 byId('record-search').value='';renderRecords();
}
function initialise(){
 const table=byId('context-rows');for(const [index,context] of values.entries()){
 const row=node('tr');row.dataset.contextIndex=String(index);const choice=node('th');choice.scope='row';const wrapper=node('div',undefined,'context-choice');const input=node('input');input.type='radio';input.name='context';input.id='context-'+index;input.value=String(index);input.checked=index===0;input.addEventListener('change',()=>selectContext(index));const label=node('label');label.htmlFor=input.id;label.append(node('span',display(context.label??context.id)),node('span',display(context.id),'small'));wrapper.append(input,label);choice.append(wrapper);row.append(choice);
 const status=node('td');status.append(makeStatus(display(context.evidence_status),context.evidence_status==='sufficient'?'complete':'warning'));row.append(status,node('td',numeric(context.selected_records)),node('td',numeric(context.relationships)),node('td',numeric(context.package_bytes)));
 const limits=node('td');limits.append(node('span','Assembly: '+display(context.assembly_truncated)),node('br'),node('span','Retrieval: '+display(context.retrieval_truncated)));row.append(limits);const delivered=node('td');delivered.append(makeStatus(completeOf(context)?'Verified complete':'Not established',completeOf(context)?'complete':'unknown'));row.append(delivered);table.append(row);}
 byId('record-search').addEventListener('input',renderRecords);byId('record-scope').addEventListener('change',renderRecords);
 const identity=byId('report-identity');identity.append(jsonBlock(report.identity??{}));const recovery=byId('recovery-plan');recovery.append(jsonBlock(report.recovery_plan??{}));const limitations=byId('limitations');for(const value of report.limitations??[])limitations.append(node('li',display(value)));
 if(values.length)selectContext(0);else{byId('context-detail').classList.add('hidden');byId('no-contexts').classList.remove('hidden');}
}
initialise();
`;

export function renderContextReview(report) {
  if (!report || typeof report !== 'object' || report.schema !== 'okf-dwp-context-review.v1'
    || typeof report.question !== 'string' || !Array.isArray(report.contexts)
    || !report.contexts.every(context => context && typeof context === 'object' && typeof context.id === 'string')
    || (report.limitations !== undefined && (!Array.isArray(report.limitations) || !report.limitations.every(value => typeof value === 'string')))) {
    throw new Error('Invalid context review report');
  }
  const data = embeddedJson(report);
  const csp = `default-src 'none'; base-uri 'none'; form-action 'none'; connect-src 'none'; img-src 'none'; style-src 'sha256-${hash(style)}'; script-src 'sha256-${hash(script)}'`;
  return `<!doctype html>
<html lang="en-GB"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="${escapeHtml(csp)}"><title>Evidence context review — OKF-DWP</title><style>${style}</style></head>
<body><a class="skip-link" href="#main">Skip to evidence review</a><header><div><div class="eyebrow">Independent experimental publication</div><h1>Evidence context review</h1><p class="question">${escapeHtml(report.question)}</p><span class="status">${escapeHtml(report.status ?? 'candidate-not-deployed')}</span></div></header>
<main id="main"><div class="boundary"><strong>An independent research candidate.</strong><p>Compare the graph-guided evidence, baseline, guarded query and bounded follow-up routes. Complete delivery and sufficient evidence are separate findings. This file reads only its embedded report; source links open only when you choose them.</p></div>
<noscript><p class="boundary">Enable JavaScript to inspect this embedded report. The inspector makes no network requests.</p></noscript>
<section class="panel" aria-labelledby="comparison-title"><h2 id="comparison-title">Compare the evidence sets</h2><div class="table-scroll"><table><caption class="small">Choose one context to inspect its retained passages, source identities and omissions.</caption><thead><tr><th scope="col">Context</th><th scope="col">Evidence status</th><th scope="col">Records</th><th scope="col">Relationships</th><th scope="col">Package bytes</th><th scope="col">Selection limits</th><th scope="col">Requested delivery</th></tr></thead><tbody id="context-rows"></tbody></table></div><p class="small comparison-note">Each context keeps its own query and content identity. Follow-up contexts are not merged into a new claim of completeness.</p><p id="no-contexts" class="empty hidden">No evidence contexts were recorded.</p></section>
<div id="context-detail"><section class="panel" aria-labelledby="selected-title"><h2 id="selected-title">Selected context</h2><div id="selected-status"></div><p id="evidence-boundary"></p><h3>Query used for this context</h3><p id="selected-query" class="query"></p><p class="small">Context identity</p><p id="selected-identity" class="identity-line mono"></p><div id="selected-metrics" class="metrics"></div><p id="delivery-state" class="small"></p><p id="truncation-state" class="small"></p><details class="block"><summary>Exact delivery receipt</summary><div id="delivery-receipt"></div></details></section>
<section class="panel" aria-labelledby="records-title"><h2 id="records-title">Inspect the retained source records</h2><p class="small">Open a record to read its complete retained text, provenance and selection path. Extracted text and project-authored interpretation keep their original authority and review status.</p><div class="toolbar"><div class="field"><label for="record-search">Search this context</label><input id="record-search" type="search" placeholder="Words, heading or record identifier" autocomplete="off"></div><div class="field scope"><label for="record-scope">Record type</label><select id="record-scope"><option value="evidence">Source evidence</option><option value="all">All retained records</option></select></div></div><p id="record-count" class="small" role="status" aria-live="polite"></p><div id="record-list" class="record-list"></div></section>
<section class="panel" aria-labelledby="diagnostics-title"><h2 id="diagnostics-title">Missing evidence and diagnostics</h2><p>Omissions, unresolved references, conflicts and unfulfilled requirements remain visible. A downloaded passage does not close an unmet legal or review obligation.</p><div id="diagnostic-codes" class="diagnostic-codes"></div><details class="block" open><summary>Complete retained diagnostics</summary><div id="full-diagnostics"></div></details></section></div>
<section class="panel" aria-labelledby="identity-title"><h2 id="identity-title">Report identity and recovery plan</h2><details class="block"><summary>Source, engine and policy identities</summary><div id="report-identity"></div></details><details class="block"><summary>Bounded recovery plan</summary><div id="recovery-plan"></div></details></section>
<section class="panel" aria-labelledby="limitations-title"><h2 id="limitations-title">Limits of this evaluation</h2><ul id="limitations" class="limitations"></ul><p class="small">No answer, award calculation or individual entitlement decision is generated by this inspector.</p></section></main>
<footer>OKF-DWP · Independent experimental research · British English · Offline evidence inspector</footer><script id="review-data" type="application/json">${data}</script><script>${script}</script></body></html>`;
}
