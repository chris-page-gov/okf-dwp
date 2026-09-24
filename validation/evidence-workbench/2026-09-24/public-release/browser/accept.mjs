import { createRequire } from 'node:module';
import { readFileSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { createHash } from 'node:crypto';
const out='/Users/crpage/tmp/okf-workbench-public-acceptance/final-pages-7eeded763';
const explorerRoot='/Users/crpage/tmp/okf-explorer-evidence-integration';
const require=createRequire(resolve(explorerRoot,'apps/okf-explorer/package.json'));
const {chromium}=require('@playwright/test');
const app='https://chris-page-gov.github.io/okf-explorer';
const pin='7eeded763042ddd0070f4fed834c6074149e8e2f';
const raw=`https://raw.githubusercontent.com/chris-page-gov/okf-dwp/${pin}`;
const manifestUrl='https://chris-page-gov.github.io/okf-dwp/evaluation/evidence-workbench/manifest.json';
const descriptorUrl=`${raw}/structured-context/evidence-connect-explorer.json`;
const sha=b=>createHash('sha256').update(b).digest('hex');
const receipt={schema:'okf-workbench-public-candidate-acceptance.v1',accepted_at:new Date().toISOString(),surface:'PUBLIC EXPLORER + MERGED DWP PAGES',app_url:app,merged_dwp_git_sha:pin,manifest_url:manifestUrl,descriptor_url:descriptorUrl,app_http:{},dwp_pages_http:{},dwp_http:{},cases:[],reader_ask:null,console_errors:[],page_errors:[],failed_requests:[],http_errors:[],screenshots:[]};
const browser=await chromium.launch({channel:'chrome',headless:true});
const context=await browser.newContext({viewport:{width:1440,height:900},acceptDownloads:true});
const page=await context.newPage();
const tracked=[];
page.on('console',m=>{if(m.type()==='error')receipt.console_errors.push(m.text())});
page.on('pageerror',e=>receipt.page_errors.push(String(e)));
page.on('requestfailed',r=>receipt.failed_requests.push({url:r.url(),failure:r.failure()?.errorText||''}));
page.on('response',r=>{const u=r.url();if(r.status()>=400)receipt.http_errors.push({url:u,status:r.status()});if((u.startsWith(raw)||u.startsWith('https://chris-page-gov.github.io/okf-dwp/'))&&(/manifest\.json$|descriptor\.json$|evidence-connect-explorer\.json$|\/parts\//.test(u)))tracked.push({url:u,status:r.status()});});
function headers(r){return {url:r.url(),status:r.status(),content_type:r.headers()['content-type']||null,cache_control:r.headers()['cache-control']||null,etag:r.headers()['etag']||null,last_modified:r.headers()['last-modified']||null,access_control_allow_origin:r.headers()['access-control-allow-origin']||null};}
try{
  const appResponse=await context.request.get(`${app}/evidence/`,{timeout:30000});
  const buildResponse=await context.request.get(`${app}/okf-explorer-build-manifest.json`,{timeout:30000});
  const siteResponse=await context.request.get('https://chris-page-gov.github.io/okf-dwp/site-manifest.json',{timeout:30000});
  const siteBytes=await siteResponse.body();const siteManifest=JSON.parse(siteBytes);receipt.dwp_pages_http.site_manifest=headers(siteResponse);receipt.dwp_pages_http.site_manifest_sha256=sha(siteBytes);receipt.dwp_pages_http.source_commit=siteManifest.source_commit;receipt.dwp_pages_http.schema=siteManifest.schema;
  const manifestResponse=await context.request.get(manifestUrl,{timeout:30000});
  receipt.app_http.evidence=headers(appResponse);receipt.app_http.build_manifest=headers(buildResponse);receipt.dwp_http.manifest=headers(manifestResponse);
  const buildBytes=await buildResponse.body();receipt.app_http.build_manifest_sha256=sha(buildBytes);receipt.app_http.build_tree_sha256=JSON.parse(buildBytes).tree_sha256;
  const manifestBytes=await manifestResponse.body();receipt.dwp_http.manifest_sha256=sha(manifestBytes);receipt.dwp_pages_http.workbench_manifest_entry=siteManifest.files.find(row=>row.path==='evaluation/evidence-workbench/manifest.json');receipt.dwp_pages_http.manifest_hash_matches=receipt.dwp_pages_http.workbench_manifest_entry?.sha256===sha(manifestBytes);const manifest=JSON.parse(manifestBytes);receipt.question_count=manifest.questions.length;
  const target=new URL(`${app}/evidence/`);target.search=new URLSearchParams({manifest:manifestUrl,case:'staff-001'}).toString();
  await page.goto(target.href,{waitUntil:'domcontentloaded',timeout:30000});
  await page.getByRole('heading',{name:manifest.questions[0].question,exact:true}).waitFor({timeout:45000});
  for(const id of ['staff-001','staff-018','staff-023']){
    const entry=manifest.questions.find(row=>row.id===id);if(!entry)throw Error(`Missing ${id}`);
    if(id!=='staff-001'){await page.locator(`.cases nav a[href*="case=${id}"]`).click();await page.getByRole('heading',{name:entry.question,exact:true}).waitFor({timeout:45000});}
    if(!(await page.getByRole('heading',{name:'Original question review brief'}).isVisible()))throw Error(`${id} review brief missing`);
    const briefItems=[...(entry.ambiguities||[]),...(entry.required_evidence||[]),...(entry.scope_gaps||[])];
    for(const note of briefItems)if(!(await page.locator('.review-brief').getByText(note,{exact:true}).isVisible()))throw Error(`${id} brief note missing`);
    const fullPackage=page.getByRole('link',{name:/Open full machine-readable evidence package/});
    if(!(await fullPackage.isVisible())||!(await fullPackage.getAttribute('href'))?.endsWith(`packages/${id}.json`))throw Error(`${id} package link missing`);
    let selectedKind=await page.locator('.record-list nav a.current small').textContent();
    if(!selectedKind?.startsWith('evidence')){await page.locator('.record-list nav a').filter({has:page.locator('small',{hasText:/^evidence/})}).first().click();selectedKind=await page.locator('.record-list nav a.current small').textContent();}
    await page.getByRole('link',{name:'Original source'}).click();
    const sourceHref=await page.getByRole('link',{name:/Open original document and cited page/}).getAttribute('href');
    const fallback=page.getByRole('link',{name:'Open PDF in a new tab if the embedded viewer is unavailable'});
    if(!sourceHref?.startsWith('https://')||!(await fallback.isVisible())||await fallback.getAttribute('href')!==sourceHref)throw Error(`${id} source fallback missing`);
    await page.getByRole('link',{name:'Complete passage'}).click();const passage=await page.locator('.inspector pre').first().textContent();if(!passage?.trim())throw Error(`${id} passage missing`);
    await page.getByRole('link',{name:'Concepts and relationships'}).click();if(!(await page.getByRole('heading',{name:'Concepts and relationships'}).isVisible()))throw Error(`${id} ontology missing`);
    await page.getByRole('link',{name:'Retrieval trace'}).click();if(!(await page.getByRole('heading',{name:'Question retrieval trace'}).isVisible()))throw Error(`${id} trace missing`);
    const screen=`${id}-public-trace.png`;await page.screenshot({path:resolve(out,screen),fullPage:false});receipt.screenshots.push(screen);
    receipt.cases.push({id,question:entry.question,review_brief_items:briefItems.length,selected_records:await page.locator('.record-list nav a').count(),selected_kind:selectedKind,source_href:sourceHref,passage_characters:passage.length,declared_evidence_status:await page.locator('.case-heading p').filter({hasText:'Declared evidence status:'}).textContent(),package_url:await fullPackage.getAttribute('href')});
  }
  await page.setViewportSize({width:390,height:844});await page.screenshot({path:resolve(out,'staff-023-public-narrow.png'),fullPage:false});receipt.screenshots.push('staff-023-public-narrow.png');receipt.narrow={scroll_width:await page.evaluate(()=>document.documentElement.scrollWidth),client_width:await page.evaluate(()=>document.documentElement.clientWidth)};
  await page.getByRole('link',{name:'Review proposal'}).click();await page.getByLabel('Evidence and suggested change').fill('Public candidate acceptance: check the cited source and review dependency.');const downloadPromise=page.waitForEvent('download');await page.getByRole('button',{name:'Download review proposal'}).click();const download=await downloadPromise;const reviewPath=resolve(out,download.suggestedFilename());await download.saveAs(reviewPath);const review=JSON.parse(readFileSync(reviewPath));receipt.review_export={filename:download.suggestedFilename(),authority:review.authority,question_id:review.question_id,record_id:review.record_id};
  receipt.dwp_http.workbench_requests={manifest:tracked.filter(r=>r.url===manifestUrl).length,parts:tracked.filter(r=>r.url.includes('/parts/')).length,raw_packages:tracked.filter(r=>r.url.includes('/packages/')).length,non_200:tracked.filter(r=>r.status!==200)};
  receipt.workbench_passed=receipt.question_count===40&&receipt.cases.length===3&&receipt.cases.every(c=>c.review_brief_items>0&&c.passage_characters>0)&&receipt.review_export.question_id==='staff-023'&&receipt.review_export.authority==='local-unreviewed-proposal'&&receipt.narrow.scroll_width===receipt.narrow.client_width;
  const reader=await context.newPage();
  reader.on('console',m=>{if(m.type()==='error')receipt.console_errors.push(`Reader: ${m.text()}`)});
  reader.on('pageerror',e=>receipt.page_errors.push(`Reader: ${String(e)}`));
  reader.on('requestfailed',r=>receipt.failed_requests.push({url:r.url(),failure:r.failure()?.errorText||''}));
  reader.on('response',r=>{if(r.status()>=400)receipt.http_errors.push({url:r.url(),status:r.status()})});
  const descriptorResponse=await context.request.get(descriptorUrl,{timeout:30000});const descriptorBytes=await descriptorResponse.body();receipt.dwp_http.descriptor=headers(descriptorResponse);receipt.dwp_http.descriptor_sha256=sha(descriptorBytes);
  await reader.goto(`${app}/explore/`,{waitUntil:'domcontentloaded',timeout:30000});
  await reader.getByPlaceholder('Bundle or descriptor URL').fill(descriptorUrl);await reader.getByRole('button',{name:'Load',exact:true}).click();await reader.getByText('DWP guidance: source-led evidence connect research',{exact:true}).first().waitFor({timeout:45000});
  await reader.getByRole('button',{name:'Ask OKF',exact:true}).click();await reader.getByRole('heading',{name:'Ask OKF',exact:true}).waitFor();
  const question='Can Pension Credit treat capital as still held after someone has got rid of it, and are there exceptions?';await reader.getByLabel('Question',{exact:true}).fill(question);await reader.getByText('Evidence limits',{exact:true}).click();await reader.getByLabel('Records',{exact:true}).fill('64');await reader.getByLabel('Relationships',{exact:true}).fill('128');await reader.getByLabel('Traversal depth',{exact:true}).fill('6');await reader.getByLabel('Package bytes',{exact:true}).fill('524288');await reader.getByRole('button',{name:'Build evidence package'}).click();await reader.getByRole('heading',{name:'Evidence package',exact:true}).waitFor({timeout:60000});await reader.getByRole('button',{name:'Inspect package JSON'}).click();const packageValue=JSON.parse(await reader.getByLabel('Evidence package JSON').inputValue());
  const u07=packageValue.selected.find(row=>row.record.id.endsWith('/pc-capital-u07'));const dep=packageValue.selected.find(row=>row.record.id.endsWith('/source-0000200424-000-606242ace072'));const link=packageValue.relationships.find(row=>row.source===u07?.record.id&&row.target===dep?.record.id);
  receipt.reader_ask={question,context_id:packageValue.context_id,evidence_status:packageValue.evidence_status,budget:packageValue.budget,selected_count:packageValue.selected.length,relationship_count:packageValue.relationships.length,u07_selected:!!u07,source_84861_selected:!!dep,direct_dependency_selected:!!link,dependency_label:link?.label||null};
  await reader.screenshot({path:resolve(out,'reader-ask-public-capital.png'),fullPage:false});receipt.screenshots.push('reader-ask-public-capital.png');
  receipt.reader_passed=!!u07&&!!dep&&!!link&&packageValue.budget.max_nodes===64&&packageValue.budget.max_relationships===128&&packageValue.budget.max_depth===6&&packageValue.budget.max_bytes===524288;
  receipt.passed=receipt.workbench_passed&&receipt.reader_passed&&receipt.dwp_pages_http.source_commit===pin&&receipt.dwp_pages_http.manifest_hash_matches&&receipt.page_errors.length===0&&receipt.console_errors.length===0&&receipt.http_errors.length===0;
}catch(error){receipt.error=String(error);process.exitCode=1;}finally{receipt.completed_at=new Date().toISOString();writeFileSync(resolve(out,'receipt.json'),JSON.stringify(receipt,null,2)+'\n');console.log(JSON.stringify({passed:receipt.passed,error:receipt.error,app_http:receipt.app_http,dwp_http:receipt.dwp_http,question_count:receipt.question_count,cases:receipt.cases,review_export:receipt.review_export,reader_ask:receipt.reader_ask,console_errors:receipt.console_errors,page_errors:receipt.page_errors,failed_requests:receipt.failed_requests,http_errors:receipt.http_errors,receipt:resolve(out,'receipt.json')},null,2));await browser.close();}
