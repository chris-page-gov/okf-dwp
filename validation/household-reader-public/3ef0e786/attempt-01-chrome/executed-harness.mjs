// Real public Chrome observation. No response routing, replacement or MCP calls.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
const root = path.resolve(fileURLToPath(new URL('..', import.meta.url)));
export const sha = bytes => createHash('sha256').update(bytes).digest('hex');
export function options(env) {
  assert.ok(env.OKF_EXPLORER_CHECKOUT, 'Isolated Explorer dependencies required');
  assert.match(env.OKF_PUBLIC_HOUSEHOLD_COMMIT || '', /^[a-f0-9]{40}$/, 'Immutable DWP commit required');
  assert.match(env.OKF_PUBLIC_HOUSEHOLD_APP_SHA256 || '', /^[a-f0-9]{64}$/, 'Expected application manifest required');
  assert.ok(env.OKF_PUBLIC_HOUSEHOLD_OUTPUT, 'Explicit fresh output required');
  return { checkout: path.resolve(env.OKF_EXPLORER_CHECKOUT), commit: env.OKF_PUBLIC_HOUSEHOLD_COMMIT,
    expectedApp: env.OKF_PUBLIC_HOUSEHOLD_APP_SHA256, output: path.resolve(env.OKF_PUBLIC_HOUSEHOLD_OUTPUT),
    app: 'https://chris-page-gov.github.io/okf-explorer/explore/' };
}
export async function fresh(output) {
  await mkdir(path.dirname(output), { recursive: true });
  try { await mkdir(output); } catch (error) {
    if (error.code === 'EEXIST') throw new Error('Fresh output directory required; retained evidence was not changed');
    throw error;
  }
}
export function packageIdentity(value, question, descriptor, manifestRaw) {
  const manifest = JSON.parse(manifestRaw);
  assert.equal(value.question, question); assert.equal(value.ai_answer, null);
  assert.equal(value.evidence_status, 'insufficient');
  assert.equal(manifest.semantic_source_snapshot, descriptor.snapshot);
  assert.equal(value.bundle.snapshot, manifest.bundle.snapshot);
  assert.equal(value.binding.index_sha256, sha(manifestRaw));
  assert.ok(value.budget.max_bytes <= 524288);
  const bytes = Buffer.byteLength(JSON.stringify(value));
  assert.ok(bytes <= value.budget.max_bytes);
  return { context_id: value.context_id, snapshot: value.bundle.snapshot, evidence_status: value.evidence_status,
    budget: value.budget, compact_json_bytes: bytes, selected_records: value.selected.length,
    relationships: value.relationships.length, truncation: value.truncation, ai_answer: null };
}
async function main() {
  const opt = options(process.env); await fresh(opt.output);
  const write = (name, value) => writeFile(path.join(opt.output, name), Buffer.isBuffer(value) || typeof value === 'string' ? value : JSON.stringify(value, null, 2) + '\n', { flag: 'wx' });
  const harness = await readFile(fileURLToPath(import.meta.url)); await write('executed-harness.mjs', harness);
  const bound = new Map();
  function source(relative) {
    assert.match(relative, /^(combined|domain-profile|evaluation)\/[a-zA-Z0-9_./-]+$/);
    assert.ok(!relative.split('/').includes('..'));
    const bytes = execFileSync('git', ['show', `${opt.commit}:${relative}`], { cwd: root, maxBuffer: 8 * 1024 * 1024, timeout: 10000 });
    bound.set(relative, { path: relative, bytes: bytes.length, sha256: sha(bytes) }); return bytes;
  }
  const descriptorRaw = source('combined/okf-explorer.json'), descriptor = JSON.parse(descriptorRaw);
  const contextManifest = source('combined/context/corpus/manifest.json');
  const base = JSON.parse(source('combined/context/assembly-index.json'));
  const facets = JSON.parse(source('combined/data/facets.json'));
  const legal = JSON.parse(source('domain-profile/legal-bodies/context-overlay.json')).records;
  const questions = JSON.parse(source('evaluation/staff-questions/cases.json')).cases;
  const careQuestion = questions.find(x => x.id === 'staff-012').question;
  const sdaQuestion = questions.find(x => x.id === 'staff-008').question;
  const heading = base.records.find(x => x.kind === 'evidence' && x.text.includes('78088') && x.text.includes('Claimants who have no partner'));
  const focus = legal.find(x => x.route === 'legal-body/uksi/2002/1792/regulation/5');
  assert.ok(heading && focus);
  const bundle = `https://raw.githubusercontent.com/chris-page-gov/okf-dwp/${opt.commit}/combined/okf-explorer.json`;
  const publicBase = new URL('.', bundle).href;
  const appManifestUrl = new URL('../okf-explorer-build-manifest.json', opt.app).href;
  const { chromium, expect: baseExpect } = await import(pathToFileURL(path.join(opt.checkout, 'apps/okf-explorer/node_modules/@playwright/test/index.mjs')));
  const expect = baseExpect.configure({ timeout: 60000 });
  const browser = await chromium.launch({ channel: 'chrome' });
  const context = await browser.newContext({ viewport: { width: 1440, height: 1080 }, serviceWorkers: 'block' });
  const page = await context.newPage(); page.setDefaultTimeout(60000);
  const start = performance.now(), checks = {}, timings = [], errors = [], networkErrors = [], corpus = new Map(), requests = [];
  const expectedMaterials = new Map(), loadedMaterials = new Map();
  let responseCount = 0, responseBytes = 0, app;
  const mark = phase => timings.push({ phase, elapsed_ms: Math.round(performance.now() - start) });
  const url = (route = 'overview', suffix = '') => `${opt.app}?bundle=${encodeURIComponent(bundle)}${suffix}#${route}`;
  page.on('pageerror', e => errors.push(e.message));
  page.on('console', e => { if (e.type() === 'error') errors.push(e.text()); });
  page.on('requestfailed', req => networkErrors.push({ url: req.url(), error: req.failure()?.errorText }));
  page.on('response', response => {
    if (expectedMaterials.has(response.url())) {
      requests.push((async () => {
        const expected = expectedMaterials.get(response.url());
        assert.equal(response.status(), 200, response.url());
        const bytes = await response.body();
        assert.equal(bytes.length, expected.bytes); assert.equal(sha(bytes), expected.sha256);
        loadedMaterials.set(response.url(), { url: response.url(), bytes: bytes.length, sha256: sha(bytes), status: response.status() });
      })().catch(e => networkErrors.push({ error: String(e.message || e) })));
    }
    if (!response.url().startsWith(publicBase)) return;
    requests.push((async () => {
      assert.ok(++responseCount <= 1024, 'Public corpus response count exceeded');
      const reference = decodeURIComponent(response.url().slice(publicBase.length));
      assert.match(reference, /^[a-zA-Z0-9_./-]+$/);
      assert.ok(!reference.split('/').includes('..')); assert.equal(response.status(), 200, reference);
      assert.equal(response.request().redirectedFrom(), null, 'No corpus redirect');
      const bytes = await response.body(); responseBytes += bytes.length;
      assert.ok(bytes.length <= 8 * 1024 * 1024 && responseBytes <= 64 * 1024 * 1024, 'Observed response-body bounds exceeded');
      const expected = source('combined/' + reference);
      assert.equal(bytes.length, expected.length, reference); assert.equal(sha(bytes), sha(expected), reference);
      corpus.set(reference, { path: reference, url: response.url(), status: response.status(), bytes: bytes.length, sha256: sha(bytes) });
    })().catch(e => networkErrors.push({ error: String(e.message || e) })));
  });
  const deadline = setTimeout(() => browser.close(), 8 * 60 * 1000);
  const summary = () => ({ schema: 'okf-public-household-reader.v1', observed_at: new Date().toISOString(),
    environment: 'published-browser-observation', network_mode: 'real-https-no-interception', browser: 'chrome', browser_version: browser.version(),
    app_url: opt.app, bundle_url: bundle, content_commit: opt.commit, expected_app_manifest_sha256: opt.expectedApp, app,
    descriptor: { sha256: sha(descriptorRaw), snapshot: descriptor.snapshot, records: descriptor.counts.records },
    harness_sha256: sha(harness), inputs: [...bound.values()].sort((a,b) => a.path.localeCompare(b.path)), checks, timings,
    console_errors: errors, network_errors: networkErrors, corpus_response_count: responseCount, corpus_response_bytes: responseBytes,
    corpus_requests: [...corpus.values()].sort((a,b) => a.path.localeCompare(b.path)),
    browser_loaded_app_materials: [...loadedMaterials.values()].sort((a,b) => a.url.localeCompare(b.url)),
    limitations: ['One public Chrome observation, not cross-browser or assistive-technology acceptance.',
      'Response-body size checks are observational bounds after browser receipt, not a hard network transfer ceiling.',
      'The app manifest and all listed assets are fetched independently; one statutory literal is checked here, with all twenty covered in separate local observations.',
      'Extracted source text and proposed relationships are unreviewed. Both questions remain insufficient; no AI answer, service MCP call or entitlement decision.'] });
  try {
    const manifestResponse = await page.request.get(appManifestUrl, { timeout: 30000 });
    assert.equal(manifestResponse.status(), 200); assert.equal(manifestResponse.url(), appManifestUrl);
    const raw = await manifestResponse.body(); assert.equal(sha(raw), opt.expectedApp);
    const manifest = JSON.parse(raw); assert.equal(manifest.materials.length, 21);
    const materials = [];
    for (const item of manifest.materials) {
      const target = new URL(item.path, appManifestUrl).href;
      assert.ok(target.startsWith('https://chris-page-gov.github.io/okf-explorer/'));
      expectedMaterials.set(target, item);
      const response = await page.request.get(target, { timeout: 30000 });
      assert.equal(response.status(), 200); assert.equal(response.url(), target);
      const bytes = await response.body(); assert.equal(bytes.length, item.bytes); assert.equal(sha(bytes), item.sha256);
      materials.push({ url: target, status: response.status(), bytes: bytes.length, sha256: sha(bytes) });
    }
    app = { manifest_url: appManifestUrl, manifest_sha256: sha(raw), tree_sha256: manifest.tree_sha256, verified_materials: materials };
    await write('app-manifest.json', raw); mark('application_integrity');
    await page.goto(url()); await expect(page.locator('.title-block')).toContainText(descriptor.title); mark('initial_reader_ready');
    await page.getByLabel('Facet visibility', { exact: true }).getByRole('button', { name: 'All', exact: true }).click();
    async function reduce(key, value) {
      const facet = page.locator(`[data-facet-key="${key}"]`); await expect(facet).toBeVisible();
      if (await facet.locator('.facet-toggle').getAttribute('aria-expanded') !== 'true') await facet.locator('.facet-toggle').click();
      const search = facet.getByRole('textbox'); if (await search.count()) await search.fill(value);
      await facet.locator('.facet-value').filter({ has: page.getByText(value, { exact: true }) }).click();
      await page.getByRole('button', { name: 'Keep highlighted', exact: true }).click();
      const count = facets[key].find(x => x.value === value).count;
      await expect(page.locator('.exploration-toolbar')).toContainText(`0 highlighted / ${count.toLocaleString('en-GB')} in scope`);
      return count;
    }
    const concept = 'Pension Credit household separation and care-home residence';
    checks.concept_facet = { value: concept, count: await reduce('concept', concept), role: 'Authored concept references; not legal applicability' };
    await page.screenshot({ path: path.join(opt.output, 'concept-facet.png') }); mark('concept_facet_ready');
    await page.getByRole('button', { name: 'Reset view', exact: true }).click();
    await expect(page.locator('.exploration-toolbar')).toContainText(`${descriptor.counts.records.toLocaleString('en-GB')} in scope`);
    const count = await reduce('source_family', 'Legislation'); assert.equal(count, legal.length);
    await page.getByLabel('Views').getByRole('button', { name: 'Graph', exact: true }).click();
    await expect(page.getByRole('group', { name: 'Large corpus graph', exact: true })).toBeVisible();
    await expect(page.locator('.exploration-toolbar')).toContainText(`0 highlighted / ${count} in scope`);
    await page.getByLabel('Views').getByRole('button', { name: 'Timeline', exact: true }).click();
    await expect(page.locator('.view-heading').filter({ hasText: 'Timeline' })).toContainText(`${count} guidance records in current reduction`);
    await page.getByLabel('Primary date role').selectOption('source'); assert.equal(await page.locator('.release-series').count(), 0);
    await page.screenshot({ path: path.join(opt.output, 'statutory-source-timeline.png') });
    await page.getByLabel('Primary date role').selectOption('audit'); await expect(page.locator('.release-series').first()).toBeVisible();
    checks.source_family_and_timeline = { value: 'Legislation', count, reader_graph_timeline_parity: true, source_series: 0, audit_series: await page.locator('.release-series').count(), requested_source_version_is_publication: false }; mark('statutory_facet_and_timeline_ready');
    await page.goto(url(focus.route, '&view=narrative'));
    const narrative = page.locator('.record-narrative-body'); await expect(narrative).toContainText(focus.scope);
    assert.equal((await narrative.locator('pre code').textContent()).replace(/\n$/, ''), focus.text.replace(/\n$/, ''));
    const official = narrative.locator('a').filter({ hasText: focus.provenance[0].locator });
    assert.equal(await official.getAttribute('href'), focus.provenance[0].url);
    checks.statutory_literal = { route: focus.route, source_url: focus.provenance[0].url, requested_source_version: '2026-09-20', literal_sha256: sha(focus.text), exact_visible_literal: true };
    await page.screenshot({ path: path.join(opt.output, 'statutory-reader.png') }); mark('statutory_literal_ready');
    await page.goto(url(focus.route, '&view=graph'));
    const graph = page.getByRole('group', { name: 'Large corpus graph', exact: true }); await expect(graph.locator('.edge-hit').first()).toBeVisible();
    const controls = page.locator('.graph-toolbar'); await controls.getByRole('button', { name: /^Relationships \(/ }).click();
    await expect(controls).toContainText('from focus'); await expect(controls).toContainText('to focus');
    const labels = await graph.locator('.edge-hit').evaluateAll(rows => rows.map(x => x.getAttribute('aria-label')));
    assert.ok(labels.some(x => x.includes('uksi/2013/376/regulation/3')));
    checks.statutory_graph = { focus: focus.route, incoming_and_outgoing_visible: true, edge_labels: labels };
    await page.screenshot({ path: path.join(opt.output, 'statutory-graph.png') }); mark('statutory_graph_ready');
    async function ask(question) {
      await page.getByRole('button', { name: 'Ask OKF', exact: true }).click(); await page.getByLabel('Question', { exact: true }).fill(question);
      await page.getByRole('button', { name: 'Build evidence package', exact: true }).click();
      await expect(page.locator('[data-evidence-status]')).toHaveText('Insufficient evidence', { timeout: 60000 });
      await page.getByRole('button', { name: 'Inspect package JSON', exact: true }).click();
      return JSON.parse(await page.getByLabel('Evidence package JSON', { exact: true }).inputValue());
    }
    const care = await ask(careQuestion); checks.care_home = packageIdentity(care, careQuestion, descriptor, contextManifest);
    const selected = care.selected.find(x => x.record.id === heading.id);
    checks.care_home.controlling_heading = { record_id: heading.id, selected: Boolean(selected), visible: false };
    if (selected) {
      assert.equal(selected.record.text, heading.text);
      const item = page.locator('.evidence-item').filter({ has: page.getByRole('heading', { name: selected.record.label, exact: true }) });
      await item.locator('.source-passage summary').click(); await expect(item.locator('.evidence-text')).toContainText('Claimants who have no partner');
      checks.care_home.controlling_heading.visible = true;
    }
    await write('care-home-context.json', care); await page.screenshot({ path: path.join(opt.output, 'care-home-ask.png') }); mark('care_home_ask_ready');
    const sda = await ask(sdaQuestion); checks.sda = packageIdentity(sda, sdaQuestion, descriptor, contextManifest);
    const ambiguity = sda.ambiguities.find(x => x.phrase === 'SDA'); assert.equal(ambiguity.candidates.length, 2);
    assert.ok(ambiguity.candidates.every(id => !sda.resolved_concepts.some(x => x.id === id)));
    assert.ok(ambiguity.candidates.every(id => sda.selected.some(x => x.paths.some(p => p.seed === id))));
    await expect(page.locator('.ask-okf')).toContainText('No meaning has been selected');
    assert.ok(await page.locator('.alternative-meaning').count() >= 2);
    checks.sda.alternative_labels = await page.locator('.alternative-meaning').allTextContents();
    await write('sda-context.json', sda); await page.screenshot({ path: path.join(opt.output, 'sda-alternatives.png') }); mark('sda_ask_ready');
    await Promise.all(requests); assert.deepEqual(errors, []); assert.deepEqual(networkErrors, []);
    assert.ok([...loadedMaterials.keys()].some(value => value.endsWith('.js')), 'Actual browser-loaded application script integrity');
    const required = ['okf-explorer.json', 'context/corpus/manifest.json'];
    for (const name of required) assert.ok(corpus.has(name), 'Browser observed required source: ' + name);
    await write('observation.json', { ...summary(), status: 'passed' });
    console.log(JSON.stringify({ status: 'passed', corpus_files: corpus.size, responses: responseCount, checks: Object.keys(checks), timings }));
  } catch (error) {
    await Promise.all(requests); await page.screenshot({ path: path.join(opt.output, 'failure.png'), timeout: 5000 }).catch(() => {});
    await write('failure.json', { ...summary(), status: 'failed', error: String(error.message || error).slice(0, 6000), current_url: page.url(), toolbar: await page.locator('.exploration-toolbar').innerText({ timeout: 5000 }).catch(() => 'unavailable') }); throw error;
  } finally { clearTimeout(deadline); await browser.close(); }
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) await main();
