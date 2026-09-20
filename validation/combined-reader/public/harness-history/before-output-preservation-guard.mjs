// Actual Explorer UI, with a local byte fixture or observed immutable HTTPS bytes.
// Public mode never installs routing/interception. No model calls.
// Usage: OKF_EXPLORER_CHECKOUT=/path/to/explorer node scripts/check_combined_reader_browser.mjs
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = path.resolve(fileURLToPath(new URL('..', import.meta.url)));
const corpus = path.join(root, 'combined');
const checkout = process.env.OKF_EXPLORER_CHECKOUT;
assert.ok(checkout, 'Supply OKF_EXPLORER_CHECKOUT with installed, pinned Explorer dependencies');
const modulePath = path.join(checkout, 'apps/okf-explorer/node_modules/@playwright/test/index.mjs');
const { chromium, firefox, webkit, expect: playwrightExpect } = await import(pathToFileURL(modulePath));
const { default: AxeBuilder } = await import(pathToFileURL(path.join(checkout, 'apps/okf-explorer/node_modules/@axe-core/playwright/dist/index.mjs')));
const appUrl = process.env.OKF_COMBINED_APP_URL || 'http://127.0.0.1:8014/explore/';
const engine = process.env.OKF_COMBINED_BROWSER || 'chrome';
const publicBundleUrl = process.env.OKF_COMBINED_BUNDLE_URL;
const expectedAppManifest = process.env.OKF_COMBINED_APP_MANIFEST_SHA256;
const expect = playwrightExpect.configure({ timeout: publicBundleUrl ? 60000 : 5000 });
if (publicBundleUrl) {
  assert.match(publicBundleUrl, /^https:\/\/raw\.githubusercontent\.com\/chris-page-gov\/okf-dwp\/[a-f0-9]{40}\/combined\/okf-explorer\.json$/, 'Public bundle must name the exact immutable DWP commit and combined descriptor');
  assert.equal(appUrl, 'https://chris-page-gov.github.io/okf-explorer/explore/', 'Public check must use the published Explorer application');
  assert.match(expectedAppManifest || '', /^[a-f0-9]{64}$/, 'Public check requires the expected application manifest digest');
}
const output = process.env.OKF_COMBINED_OUTPUT || path.join(root, publicBundleUrl ? 'validation/combined-reader/public' : 'validation/combined-reader/browser', engine);
const origin = 'https://combined-reader.fixture.test';
const bundleUrl = publicBundleUrl || origin + '/okf-explorer.json';
const publicBase = publicBundleUrl ? new URL('.', publicBundleUrl).href : null;
const hash = data => createHash('sha256').update(data).digest('hex');
const descriptorBytes = await readFile(path.join(corpus, 'okf-explorer.json'));
const descriptor = JSON.parse(descriptorBytes);
const facets = JSON.parse(await readFile(path.join(corpus, 'data/facets.json')));
const served = new Map();
const publicReadChecks = [];
const publicReadErrors = [];
const started = performance.now();
const timings = [];
const mark = phase => {
  const elapsed = Math.round(performance.now() - started);
  timings.push({ phase, elapsed_ms: elapsed, phase_ms: elapsed - (timings.at(-1)?.elapsed_ms || 0) });
};
const corpusPath = reference => {
  const target = path.resolve(corpus, reference);
  assert.ok(target.startsWith(corpus + path.sep), 'Bounded corpus path');
  return target;
};
const launchOptions = engine === 'chrome' ? { channel: 'chrome' } : {};
const browser = await ({ chrome: chromium, firefox, webkit }[engine]).launch(launchOptions);
const context = await browser.newContext({ viewport: { width: 1440, height: 1080 } });
const page = await context.newPage();
if (publicBundleUrl) page.setDefaultTimeout(60000);
const consoleErrors = [];
page.on('pageerror', error => consoleErrors.push(error.message));
page.on('console', message => { if (message.type() === 'error') consoleErrors.push(message.text()); });
if (publicBase) {
  page.on('response', response => {
    if (!response.url().startsWith(publicBase)) return;
    publicReadChecks.push((async () => {
      const reference = decodeURIComponent(response.url().slice(publicBase.length).split(/[?#]/)[0]);
      assert.equal(response.ok(), true, reference);
      const bytes = await response.body();
      const expected = await readFile(corpusPath(reference));
      assert.equal(bytes.length, expected.length, reference);
      assert.equal(hash(bytes), hash(expected), 'Published corpus response differs: ' + reference);
      served.set(reference, { path: reference, bytes: bytes.length, sha256: hash(bytes), url: response.url() });
    })().catch(error => publicReadErrors.push(String(error))));
  });
} else {
  await context.route(origin + '/**', async route => {
    const reference = decodeURIComponent(new URL(route.request().url()).pathname.slice(1));
    const bytes = await readFile(corpusPath(reference));
    served.set(reference, { path: reference, bytes: bytes.length, sha256: hash(bytes) });
    await route.fulfill({ status: 200, body: bytes, headers: { 'access-control-allow-origin': '*',
      'content-type': reference.endsWith('.gz') ? 'application/gzip' : 'application/json' } });
  });
}
await mkdir(output, { recursive: true });
try {
  const manifestUrl = new URL('../okf-explorer-build-manifest.json', appUrl).href;
  const response = await page.request.get(manifestUrl);
  assert.equal(response.ok(), true, 'Application manifest');
  if (publicBundleUrl) assert.equal(response.url(), manifestUrl, 'Published application manifest canonical URL');
  const manifestBytes = await response.body();
  if (expectedAppManifest) assert.equal(hash(manifestBytes), expectedAppManifest, 'Published application manifest differs');
  const appManifest = JSON.parse(manifestBytes);
  for (const row of appManifest.materials) {
    const material = await page.request.get(new URL(row.path, manifestUrl).href);
    assert.equal(material.ok(), true, row.path);
    const bytes = await material.body();
    assert.equal(bytes.length, row.bytes, row.path);
    assert.equal(hash(bytes), row.sha256, row.path);
  }
  mark('application_integrity_verified');
  if (publicBundleUrl) {
    const published = await page.request.get(publicBundleUrl);
    assert.equal(published.ok(), true, 'Public descriptor response');
    assert.equal(published.url(), publicBundleUrl, 'Public descriptor canonical URL');
    assert.equal(hash(await published.body()), hash(descriptorBytes), 'Public descriptor differs from local candidate');
  }
  mark('descriptor_verified');
  const url = (route = 'overview', suffix = '') => `${appUrl}?bundle=${encodeURIComponent(bundleUrl)}${suffix}#${route}`;
  await page.goto(url());
  await expect(page.locator('.title-block')).toContainText(descriptor.title);
  mark('initial_view_ready');
  const facet = page.locator('[data-facet-key="source_family"]');
  const toggle = facet.locator('.facet-toggle');
  await expect(toggle).toHaveAttribute('aria-expanded', /^(true|false)$/);
  if (await toggle.getAttribute('aria-expanded') !== 'true') await toggle.click();
  await facet.getByText('ADM', { exact: true }).click();
  await page.getByRole('button', { name: 'Keep highlighted', exact: true }).click();
  const admCount = facets.source_family.find(row => row.value === 'ADM').count;
  const scope = `0 highlighted / ${admCount.toLocaleString('en-GB')} in scope`;
  await expect(page.locator('.exploration-toolbar')).toContainText(scope);
  mark('adm_facet_reduction_ready');
  await page.getByLabel('Views').getByRole('button', { name: 'Graph', exact: true }).click();
  await expect(page.getByRole('group', { name: 'Large corpus graph', exact: true })).toBeVisible();
  await expect(page.locator('.exploration-toolbar')).toContainText(scope);
  mark('adm_graph_ready');
  await page.getByLabel('Views').getByRole('button', { name: 'Timeline', exact: true }).click();
  await expect(page.getByLabel('Primary date role')).toBeVisible();
  await expect(page.locator('.view-heading').filter({ hasText: 'Timeline' })).toContainText(`${admCount.toLocaleString('en-GB')} guidance records in current reduction`);
  await page.getByLabel('Primary date role').selectOption('source');
  const sourceSeries = await page.locator('.release-series').count();
  assert.equal(sourceSeries, 0, 'ADM capture dates must not become publication dates');
  await page.getByLabel('Primary date role').selectOption('audit');
  const auditSeries = await page.locator('.release-series').count();
  assert.ok(auditSeries > 0 && auditSeries <= 80);
  mark('adm_timeline_ready');
  await page.screenshot({ path: path.join(output, 'adm-timeline.png') });
  await page.goto(url('overview', '&q=P1001'));
  await expect(page.locator('input.search-input')).toHaveValue('P1001');
  await expect(page.locator('body')).toContainText('Chapter P1: Conditions of entitlement');
  await page.goto(url('page/adm/adm-chapter-p1/0002'));
  await expect(page.locator('body')).toContainText('P1001');
  await expect(page.locator('body')).toContainText('PDF page 2');
  const official = await page.locator('a[href*="assets.publishing.service.gov.uk"][href$="#page=2"]').count();
  assert.ok(official > 0, 'Exact official ADM PDF page link');
  mark('adm_source_page_ready');
  await page.screenshot({ path: path.join(output, 'adm-source-page.png') });
  await page.goto(url('staff-domain/pip', '&view=graph'));
  const graph = page.getByRole('group', { name: 'Large corpus graph', exact: true });
  await expect(graph).toBeVisible();
  await expect(page.locator('body')).toContainText('Relationships');
  await expect(graph).toContainText(/references|Conditions of entitlement|Daily Living/, { timeout: 30000 });
  const graphText = await graph.textContent();
  assert.ok(/Personal Independence Payment|PIP/.test(graphText));
  assert.ok(/references|Conditions of entitlement|Daily Living/.test(graphText), 'Authored concept has useful source relationship paths: ' + graphText);
  mark('pip_graph_ready');
  await page.screenshot({ path: path.join(output, 'pip-graph.png') });
  await page.getByRole('button', { name: 'Ask OKF', exact: true }).click();
  const question = 'What is the interaction between Child DLA and PIP?';
  await page.getByLabel('Question', { exact: true }).fill(question);
  await page.getByRole('button', { name: 'Build evidence package', exact: true }).click();
  await expect(page.locator('[data-evidence-status]')).toHaveText('Insufficient evidence', { timeout: 90000 });
  await page.getByRole('button', { name: 'Inspect package JSON', exact: true }).click();
  const evidence = JSON.parse(await page.getByLabel('Evidence package JSON', { exact: true }).inputValue());
  assert.equal(evidence.question, question);
  assert.equal(evidence.ai_answer, null);
  assert.ok(evidence.resolved_concepts.some(row => /PIP|Personal Independence/.test(row.label)));
  assert.ok(evidence.selected.some(row => row.record?.route?.startsWith('page/adm/') || row.route?.startsWith('page/adm/')), 'Ask retains ADM evidence');
  mark('desktop_ask_context_ready');
  await page.screenshot({ path: path.join(output, 'ask-staff-question.png') });
  const desktopAccessibility = await new AxeBuilder({ page }).include('.ask-okf').analyze();
  assert.deepEqual(desktopAccessibility.violations, [], 'Targeted desktop Ask accessibility');

  // Follow real Tab/Enter key events from a newly loaded narrow viewport.
  // A bounded loop fails if the named control is not keyboard reachable.
  await page.setViewportSize({ width: 390, height: 844 });
  await page.mouse.move(389, 843); // Keep the pointer clear of header tooltips.
  await page.goto(url());
  await expect(page.locator('.title-block')).toContainText(descriptor.title);
  let tabSteps = 0;
  const forwardKey = engine === 'webkit' ? 'Alt+Tab' : 'Tab';
  const backwardKey = engine === 'webkit' ? 'Alt+Shift+Tab' : 'Shift+Tab';
  async function tabTo(locator, key = forwardKey) {
    for (let step = 0; step < 500; step++) {
      if (await locator.evaluate(element => element === document.activeElement)) return;
      await page.keyboard.press(key); tabSteps++;
    }
    throw new Error('Named control was not reachable with 500 ' + key + ' presses: ' + await locator.getAttribute('aria-label') + ' / ' + await locator.textContent()
      + '; last focus=' + await page.evaluate(() => document.activeElement?.outerHTML.slice(0, 600)));
  }
  const panels = page.getByRole('navigation', { name: 'Workspace panels' });
  await tabTo(panels.getByRole('button', { name: 'Search & facets', exact: true }));
  await page.keyboard.press('Enter');
  await expect(page.getByRole('button', { name: 'Ask OKF', exact: true })).toBeVisible();
  // Return backwards into the newly visible panel. This avoids assuming that
  // forward Tab wraps through browser chrome identically in every engine.
  await tabTo(page.getByRole('button', { name: 'Ask OKF', exact: true }), backwardKey);
  await page.keyboard.press('Enter');
  const questionField = page.getByLabel('Question', { exact: true });
  await expect(questionField).toBeVisible();
  await tabTo(questionField);
  await page.keyboard.type(question);
  await tabTo(page.getByRole('button', { name: 'Build evidence package', exact: true }));
  await page.keyboard.press('Enter');
  await expect(page.locator('[data-evidence-status]')).toHaveText('Insufficient evidence', { timeout: 90000 });
  await tabTo(page.getByRole('button', { name: 'Inspect package JSON', exact: true }));
  await page.keyboard.press('Enter');
  await expect(page.locator('#ask-context-json summary')).toBeFocused();
  const mobileEvidence = JSON.parse(await page.getByLabel('Evidence package JSON', { exact: true }).inputValue());
  assert.equal(mobileEvidence.context_id, evidence.context_id, 'Narrow viewport and keyboard yield the same context');
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true, 'No page-level horizontal overflow at 390px');
  const mobileAccessibility = await new AxeBuilder({ page }).include('.ask-okf').include('.panel-footer').analyze();
  assert.deepEqual(mobileAccessibility.violations, [], 'Targeted narrow Ask and panel controls accessibility');
  mark('narrow_keyboard_ask_ready');
  await page.screenshot({ path: path.join(output, 'mobile-keyboard-ask.png') });
  await Promise.all(publicReadChecks);
  assert.deepEqual(publicReadErrors, [], 'Published corpus response integrity');
  if (publicBundleUrl) assert.ok(served.has('okf-explorer.json'), 'Published descriptor actually fetched by the application');
  assert.deepEqual(consoleErrors, []);
  await writeFile(path.join(output, 'context.json'), JSON.stringify(evidence, null, 2) + '\n');
  await writeFile(path.join(output, 'observation.json'), JSON.stringify({
    schema: 'okf-combined-reader-browser.v1', status: 'passed', observed_at: new Date().toISOString(), browser: engine,
    browser_version: browser.version(), browser_preferences: {},
    environment: publicBundleUrl ? 'published-browser-observation' : 'local-browser-candidate', app_url: appUrl,
    phase_timings: timings,
    ...(publicBundleUrl ? { bundle_url: publicBundleUrl, content_commit: publicBundleUrl.split('/')[5], network_mode: 'real-https-no-interception', public_response_integrity_errors: publicReadErrors } : {}),
    app: { manifest_sha256: hash(manifestBytes), tree_sha256: appManifest.tree_sha256, verified_materials: appManifest.materials.length },
    descriptor: { path: 'combined/okf-explorer.json', sha256: hash(descriptorBytes), snapshot: descriptor.snapshot },
    source_family_facet: { value: 'ADM', records: admCount, reader_graph_timeline_parity: true },
    timeline: { source_series: sourceSeries, audit_series: auditSeries },
    search: { query: 'P1001', exact_adm_page: 'page/adm/adm-chapter-p1/0002', official_page_links: official },
    semantic_graph: { focus: 'staff-domain/pip', text: graphText },
    ask: { question, context_id: evidence.context_id, evidence_status: evidence.evidence_status, budget: evidence.budget, selected_records: evidence.selected.length,
      relationships: evidence.relationships.length, ai_answer: evidence.ai_answer }, console_errors: consoleErrors,
    accessibility: { desktop_ask_violations: desktopAccessibility.violations, mobile_ask_and_panel_violations: mobileAccessibility.violations,
      mobile_viewport: { width: 390, height: 844 }, keyboard: { events: `${forwardKey}, ${backwardKey} and Enter only for navigation; keyboard typing for question`, tab_steps: tabSteps,
        json_summary_focus_verified: true, same_context_as_desktop: true }, page_horizontal_overflow: false },
    corpus_requests: [...served.values()].sort((a,b) => a.path.localeCompare(b.path)),
    limitations: [publicBundleUrl ? 'Observed immutable HTTPS corpus responses and published application bytes; no interception or local substitution.' : 'Local byte-bound corpus fixture, not a public deployment observation.',
      'Machine extraction and semantic interpretation remain unreviewed; the staff question remains insufficient.',
      'Accessibility automation covers the named controls, not a full audit or assistive-technology user acceptance.',
      'No physical mobile device or live screen-reader session was tested. Browser operation is not legal correctness certification.']
  }, null, 2) + '\n');
  console.log(JSON.stringify({ status: 'passed', browser: engine, output, context_id: evidence.context_id, corpus_requests: served.size }));
} catch (error) {
  if (publicBundleUrl) {
    await Promise.all(publicReadChecks);
    const failure = { schema: 'okf-combined-reader-browser-failure.v1', status: 'failed', recorded_at: new Date().toISOString(),
      browser: engine, environment: 'published-browser-observation', app_url: appUrl, bundle_url: publicBundleUrl,
      expected_app_manifest_sha256: expectedAppManifest, descriptor_sha256: hash(descriptorBytes),
      error_name: error?.name || 'Error', error_message: String(error?.message || error).slice(0, 4000),
      corpus_requests: [...served.values()].sort((a,b) => a.path.localeCompare(b.path)),
      phase_timings: timings,
      public_response_integrity_errors: publicReadErrors, console_errors: consoleErrors,
      limitations: ['Failed attempt, not an acceptance receipt. Requests listed only where response integrity completed.'] };
    const failures = path.join(root, 'validation/combined-reader/public/failed-attempts');
    await mkdir(failures, { recursive: true });
    const failureId = `${engine}-${Date.now()}`;
    failure.page_url = page.url();
    failure.toolbar_state = await page.locator('.exploration-toolbar').innerText({ timeout: 5000 }).catch(() => 'unavailable');
    failure.screenshot = await page.screenshot({ path: path.join(failures, `${failureId}.png`), timeout: 5000 }).then(() => `${failureId}.png`).catch(() => null);
    await writeFile(path.join(failures, `${failureId}.json`), JSON.stringify(failure, null, 2) + '\n');
  }
  throw error;
} finally { await browser.close(); }
