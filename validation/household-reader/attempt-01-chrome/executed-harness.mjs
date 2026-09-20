// Local candidate browser observation only. Never overwrites a previous attempt.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdir, readFile, realpath, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = path.resolve(fileURLToPath(new URL('..', import.meta.url)));
export const sha256 = bytes => createHash('sha256').update(bytes).digest('hex');
export function validateOptions(env) {
  const checkout = env.OKF_EXPLORER_CHECKOUT;
  assert.ok(checkout, 'Supply OKF_EXPLORER_CHECKOUT');
  const engine = env.OKF_HOUSEHOLD_BROWSER || 'chrome';
  assert.ok(['chrome', 'firefox', 'webkit'].includes(engine), 'Unknown browser');
  const appUrl = env.OKF_HOUSEHOLD_APP_URL || 'http://127.0.0.1:8015/explore/';
  const parsed = new URL(appUrl);
  assert.ok(parsed.protocol === 'http:' && parsed.hostname === '127.0.0.1' && parsed.pathname === '/explore/' &&
    !parsed.username && !parsed.password && !parsed.search && !parsed.hash, 'Local loopback Explorer URL required');
  assert.match(env.OKF_HOUSEHOLD_APP_MANIFEST_SHA256 || '', /^[a-f0-9]{64}$/, 'Expected app manifest SHA-256 required');
  assert.match(env.OKF_HOUSEHOLD_SNAPSHOT || '', /^dwp-combined-[a-f0-9]{20}$/, 'Expected combined snapshot required');
  assert.ok(env.OKF_HOUSEHOLD_OUTPUT, 'A fresh explicit output directory is required');
  return { checkout: path.resolve(checkout), engine, appUrl, output: path.resolve(env.OKF_HOUSEHOLD_OUTPUT),
    expectedApp: env.OKF_HOUSEHOLD_APP_MANIFEST_SHA256, expectedSnapshot: env.OKF_HOUSEHOLD_SNAPSHOT };
}
export async function createFreshOutput(output) {
  await mkdir(path.dirname(output), { recursive: true });
  try { await mkdir(output); } catch (error) {
    if (error.code === 'EEXIST') throw new Error('Fresh output directory required; existing evidence was not changed');
    throw error;
  }
}
export function inspectPackage(evidence, question, descriptor, manifestBytes) {
  assert.equal(evidence.question, question);
  assert.equal(evidence.ai_answer, null);
  assert.equal(evidence.evidence_status, 'insufficient');
  assert.equal(evidence.bundle.snapshot, descriptor.snapshot);
  assert.equal(evidence.binding.index_sha256, sha256(manifestBytes));
  assert.ok(evidence.budget.max_bytes <= 524288);
  const bytes = Buffer.byteLength(JSON.stringify(evidence));
  assert.ok(bytes <= evidence.budget.max_bytes, 'Whole package byte budget');
  return { context_id: evidence.context_id, evidence_status: evidence.evidence_status, budget: evidence.budget,
    compact_json_bytes: bytes, selected_records: evidence.selected.length, relationships: evidence.relationships.length,
    ambiguities: evidence.ambiguities, ai_answer: evidence.ai_answer };
}

async function main() {
  const options = validateOptions(process.env);
  await createFreshOutput(options.output); // Before dependency import or browser launch.
  const output = options.output;
  const write = (name, value) => writeFile(path.join(output, name), typeof value === 'string' || Buffer.isBuffer(value) ? value : JSON.stringify(value, null, 2) + '\n', { flag: 'wx' });
  const harness = await readFile(fileURLToPath(import.meta.url));
  await write('executed-harness.mjs', harness);
  const corpus = await realpath(path.join(root, 'combined'));
  const inputBindings = [];
  async function input(relative) {
    const file = path.resolve(root, relative);
    assert.ok(file.startsWith(root + path.sep));
    const bytes = await readFile(file);
    inputBindings.push({ path: relative, bytes: bytes.length, sha256: sha256(bytes) });
    return bytes;
  }
  const descriptorBytes = await input('combined/okf-explorer.json');
  const descriptor = JSON.parse(descriptorBytes);
  assert.equal(descriptor.snapshot, options.expectedSnapshot);
  const contextManifestBytes = await input('combined/context/corpus/manifest.json');
  const overlay = JSON.parse(await input('domain-profile/legal-bodies/context-overlay.json'));
  const questions = JSON.parse(await input('evaluation/staff-questions/cases.json')).cases;
  const careQuestion = questions.find(row => row.id === 'staff-012').question;
  const sdaQuestion = questions.find(row => row.id === 'staff-008').question;
  const baseIndex = JSON.parse(await input('combined/context/assembly-index.json'));
  const headingPage = baseIndex.records.find(row => row.kind === 'evidence' && /78088/.test(row.text) && /Claimants who have no partner/.test(row.text));
  assert.ok(headingPage, 'Source page includes the controlling heading');
  const facets = JSON.parse(await input('combined/data/facets.json'));
  const statutoryCount = facets.source_family.find(row => row.value === 'Legislation').count;
  assert.equal(statutoryCount, overlay.records.length);
  assert.equal(statutoryCount, 20, 'Declared household candidate statutory scope');
  const { chromium, firefox, webkit, expect: baseExpect } = await import(pathToFileURL(path.join(options.checkout, 'apps/okf-explorer/node_modules/@playwright/test/index.mjs')));
  const { default: AxeBuilder } = await import(pathToFileURL(path.join(options.checkout, 'apps/okf-explorer/node_modules/@axe-core/playwright/dist/index.mjs')));
  const expect = baseExpect.configure({ timeout: 15000 });
  const browser = await ({ chrome: chromium, firefox, webkit }[options.engine]).launch(options.engine === 'chrome' ? { channel: 'chrome' } : {});
  const context = await browser.newContext({ viewport: { width: 1440, height: 1080 } });
  const page = await context.newPage();
  const errors = [], served = new Map(), checks = {}, timings = [];
  const start = performance.now();
  const mark = phase => timings.push({ phase, elapsed_ms: Math.round(performance.now() - start) });
  const origin = 'https://household-reader.fixture.test';
  const bundleUrl = origin + '/okf-explorer.json';
  const url = (route = 'overview', suffix = '') => `${options.appUrl}?bundle=${encodeURIComponent(bundleUrl)}${suffix}#${route}`;
  page.on('pageerror', error => errors.push(error.message));
  page.on('console', event => { if (event.type() === 'error') errors.push(event.text()); });
  await context.route(origin + '/**', async route => {
    const relative = decodeURIComponent(new URL(route.request().url()).pathname.slice(1));
    const file = await realpath(path.resolve(corpus, relative));
    assert.ok(file.startsWith(corpus + path.sep), 'Corpus fixture path confinement');
    const bytes = await readFile(file);
    served.set(relative, { path: relative, bytes: bytes.length, sha256: sha256(bytes) });
    await route.fulfill({ status: 200, body: bytes, headers: { 'access-control-allow-origin': '*',
      'content-type': relative.endsWith('.gz') ? 'application/gzip' : 'application/json' } });
  });
  let app;
  try {
    const manifestUrl = new URL('../okf-explorer-build-manifest.json', options.appUrl).href;
    const manifestResponse = await page.request.get(manifestUrl);
    assert.equal(manifestResponse.ok(), true);
    const appBytes = await manifestResponse.body();
    assert.equal(sha256(appBytes), options.expectedApp);
    const appManifest = JSON.parse(appBytes);
    for (const material of appManifest.materials) {
      const response = await page.request.get(new URL(material.path, manifestUrl).href);
      assert.equal(response.ok(), true);
      const bytes = await response.body();
      assert.equal(bytes.length, material.bytes); assert.equal(sha256(bytes), material.sha256);
    }
    app = { manifest_sha256: sha256(appBytes), tree_sha256: appManifest.tree_sha256, verified_materials: appManifest.materials.length };
    mark('application_integrity');
    await page.goto(url());
    await expect(page.locator('.title-block')).toContainText(descriptor.title);
    const facet = page.locator('[data-facet-key="source_family"]');
    if (await facet.locator('.facet-toggle').getAttribute('aria-expanded') !== 'true') await facet.locator('.facet-toggle').click();
    await facet.getByText('Legislation', { exact: true }).click();
    await page.getByRole('button', { name: 'Keep highlighted', exact: true }).click();
    const scope = `0 highlighted / ${statutoryCount} in scope`;
    await expect(page.locator('.exploration-toolbar')).toContainText(scope);
    await page.getByLabel('Views').getByRole('button', { name: 'Graph', exact: true }).click();
    await expect(page.getByRole('group', { name: 'Large corpus graph', exact: true })).toBeVisible();
    await expect(page.locator('.exploration-toolbar')).toContainText(scope);
    await page.getByLabel('Views').getByRole('button', { name: 'Timeline', exact: true }).click();
    await expect(page.locator('.view-heading').filter({ hasText: 'Timeline' })).toContainText(`${statutoryCount} guidance records in current reduction`);
    await page.getByLabel('Primary date role').selectOption('source');
    assert.equal(await page.locator('.release-series').count(), 0, 'Requested version is not a publication event');
    await page.screenshot({ path: path.join(output, 'statutory-source-timeline.png') });
    await page.getByLabel('Primary date role').selectOption('audit');
    await expect(page.locator('.release-series').first()).toBeVisible();
    checks.facets_and_timeline = { statutory_units: statutoryCount, reader_graph_timeline_parity: true, source_series: 0,
      audit_series: await page.locator('.release-series').count(), requested_version_is_publication: false };
    mark('statutory_facet_and_timeline');
    checks.literal_bodies = [];
    for (const record of overlay.records) {
      await page.goto(url(record.route, '&view=narrative'));
      const narrative = page.locator('.record-narrative-body');
      await expect(narrative).toBeVisible();
      await expect(narrative).toContainText(record.scope);
      const literal = await narrative.locator('pre code').textContent();
      assert.equal(literal?.replace(/\n$/, ''), record.text.replace(/\n$/, ''), record.route + ' literal body');
      const official = narrative.locator('a').filter({ hasText: record.provenance[0].locator });
      assert.equal(await official.getAttribute('href'), record.provenance[0].url);
      assert.match(record.provenance[0].url, /^https:\/\/www\.legislation\.gov\.uk\/.+\/2026-09-20$/);
      checks.literal_bodies.push({ route: record.route, literal_sha256: sha256(record.text), source_url: record.provenance[0].url,
        requested_source_version: '2026-09-20', status: 'derived-unreviewed', exact_visible_literal: true });
    }
    mark('twenty_statutory_bodies');
    const focus = 'legal-body/uksi/2002/1792/regulation/5';
    await page.goto(url(focus, '&view=narrative'));
    await page.screenshot({ path: path.join(output, 'statutory-reader.png') });
    await page.goto(url(focus, '&view=graph'));
    const graph = page.getByRole('group', { name: 'Large corpus graph', exact: true });
    await expect(graph).toBeVisible();
    await expect(graph.locator('.edge-hit').first()).toBeVisible();
    const graphControls = page.locator('.graph-toolbar');
    await expect(graphControls).toContainText('from focus');
    await expect(graphControls).toContainText('to focus');
    const edgeLabels = await graph.locator('.edge-hit').evaluateAll(elements => elements.map(element => element.getAttribute('aria-label')));
    assert.ok(edgeLabels.some(label => label.includes('uksi/2013/376/regulation/3')), 'Visible statutory routing to UC couple definition');
    checks.statutory_graph = { focus, edge_labels: edgeLabels, incoming_and_outgoing_visible: true };
    await page.screenshot({ path: path.join(output, 'statutory-graph.png') });
    mark('statutory_graph');
    async function ask(question) {
      await page.getByRole('button', { name: 'Ask OKF', exact: true }).click();
      await page.getByLabel('Question', { exact: true }).fill(question);
      await page.getByRole('button', { name: 'Build evidence package', exact: true }).click();
      await expect(page.locator('[data-evidence-status]')).toHaveText('Insufficient evidence', { timeout: 90000 });
      await page.getByRole('button', { name: 'Inspect package JSON', exact: true }).click();
      return JSON.parse(await page.getByLabel('Evidence package JSON', { exact: true }).inputValue());
    }
    const care = await ask(careQuestion);
    checks.care_home = inspectPackage(care, careQuestion, descriptor, contextManifestBytes);
    const selectedHeading = care.selected.find(item => item.record.id === headingPage.id);
    checks.care_home.controlling_heading = { record_id: headingPage.id, selected: Boolean(selectedHeading), visible: false };
    if (selectedHeading) {
      assert.equal(selectedHeading.record.text, headingPage.text, 'No-partner scope retained in selected whole page');
      const item = page.locator('.evidence-item').filter({ has: page.getByRole('heading', { name: selectedHeading.record.label, exact: true }) });
      await item.locator('.source-passage summary').click();
      await expect(item.locator('.evidence-text')).toContainText('Claimants who have no partner');
      checks.care_home.controlling_heading.visible = true;
    }
    await write('care-home-context.json', care);
    await page.screenshot({ path: path.join(output, 'care-home-ask.png') });
    mark('care_home_ask');
    const sda = await ask(sdaQuestion);
    checks.sda = inspectPackage(sda, sdaQuestion, descriptor, contextManifestBytes);
    const ambiguity = sda.ambiguities.find(row => row.phrase === 'SDA');
    assert.ok(ambiguity && ambiguity.candidates.length === 2);
    assert.ok(ambiguity.candidates.every(id => !sda.resolved_concepts.some(row => row.id === id)));
    assert.ok(ambiguity.candidates.every(id => sda.selected.some(item => item.paths.some(route => route.seed === id))));
    await expect(page.locator('.ask-okf')).toContainText('No meaning has been selected');
    assert.ok(await page.locator('.alternative-meaning').count() >= 2);
    checks.sda.alternative_labels = await page.locator('.alternative-meaning').allTextContents();
    await write('sda-context.json', sda);
    await page.screenshot({ path: path.join(output, 'sda-alternatives.png') });
    const desktopAxe = await new AxeBuilder({ page }).include('.ask-okf').analyze();
    assert.deepEqual(desktopAxe.violations, []);
    mark('sda_ask');
    await page.setViewportSize({ width: 390, height: 844 });
    await page.mouse.move(389, 843);
    await page.goto(url());
    await expect(page.locator('.title-block')).toContainText(descriptor.title);
    const forward = options.engine === 'webkit' ? 'Alt+Tab' : 'Tab';
    const backward = options.engine === 'webkit' ? 'Alt+Shift+Tab' : 'Shift+Tab';
    let keys = 0;
    async function tabTo(locator, key = forward) {
      for (let step = 0; step < 500; step++) {
        if (await locator.evaluate(element => element === document.activeElement)) return;
        await page.keyboard.press(key); keys++;
      }
      throw new Error('Control not keyboard reachable in 500 presses');
    }
    await tabTo(page.getByRole('navigation', { name: 'Workspace panels' }).getByRole('button', { name: 'Search & facets', exact: true }));
    await page.keyboard.press('Enter');
    await tabTo(page.getByRole('button', { name: 'Ask OKF', exact: true }), backward);
    await page.keyboard.press('Enter');
    await tabTo(page.getByLabel('Question', { exact: true }));
    await page.keyboard.type(sdaQuestion);
    await tabTo(page.getByRole('button', { name: 'Build evidence package', exact: true }));
    await page.keyboard.press('Enter');
    await expect(page.locator('[data-evidence-status]')).toHaveText('Insufficient evidence', { timeout: 90000 });
    await tabTo(page.getByRole('button', { name: 'Inspect package JSON', exact: true }));
    await page.keyboard.press('Enter');
    await expect(page.locator('#ask-context-json summary')).toBeFocused();
    const narrow = JSON.parse(await page.getByLabel('Evidence package JSON', { exact: true }).inputValue());
    assert.equal(narrow.context_id, sda.context_id);
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    const mobileAxe = await new AxeBuilder({ page }).include('.ask-okf').include('.panel-footer').analyze();
    assert.deepEqual(mobileAxe.violations, []);
    checks.accessibility = { desktop_ask_violations: [], narrow_ask_and_panel_violations: [], viewport: { width: 390, height: 844 },
      keys: [forward, backward, 'Enter'], tab_presses: keys, json_focus: true, same_context_id: true, page_overflow: false };
    await page.screenshot({ path: path.join(output, 'narrow-keyboard-sda.png') });
    mark('narrow_keyboard');
    assert.deepEqual(errors, []);
    assert.equal(sha256(await readFile(path.join(corpus, 'okf-explorer.json'))), sha256(descriptorBytes), 'Candidate changed during observation');
    await write('observation.json', { schema: 'okf-household-reader-browser.v1', status: 'passed', observed_at: new Date().toISOString(),
      environment: 'local-browser-candidate', browser: options.engine, browser_version: browser.version(), app_url: options.appUrl,
      app, descriptor: { sha256: sha256(descriptorBytes), snapshot: descriptor.snapshot }, harness_sha256: sha256(harness),
      inputs: inputBindings, checks, timings, console_errors: errors, corpus_requests: [...served.values()].sort((a,b) => a.path.localeCompare(b.path)),
      limitations: ['Local hash-bound corpus interception, not a public deployment observation.',
        'Exact visible text means parity with the retained normalised extraction, not verification against original HTTP bytes or a specialist legal assessment.',
        'The 20 selected statutory units do not constitute the full legislation. Both questions remain insufficient and no AI answer is generated.',
        'Automated named-control checks only; no physical mobile device, human screen-reader session or full accessibility audit.'] });
    console.log(JSON.stringify({ status: 'passed', engine: options.engine, output, checks: Object.keys(checks), care_heading: checks.care_home.controlling_heading, sda_context_id: sda.context_id }));
  } catch (error) {
    await page.screenshot({ path: path.join(output, 'failure.png'), timeout: 5000 }).catch(() => {});
    await write('failure.json', { schema: 'okf-household-reader-browser-failure.v1', status: 'failed', observed_at: new Date().toISOString(),
      browser: options.engine, app, descriptor_sha256: sha256(descriptorBytes), snapshot: descriptor.snapshot,
      harness_sha256: sha256(harness), error: String(error.message || error), current_url: page.url(), checks, timings, console_errors: errors,
      corpus_requests: [...served.values()].sort((a,b) => a.path.localeCompare(b.path)), limitation: 'Failed attempt, not acceptance evidence.' });
    throw error;
  } finally { await browser.close(); }
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) await main();
