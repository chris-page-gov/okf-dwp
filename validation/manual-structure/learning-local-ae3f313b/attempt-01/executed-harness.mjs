#!/usr/bin/env node
/** Observe the rendered beginner journey offline, using an installed browser. */
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {mkdir, readFile, writeFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
import {boundedFile} from '../../scripts/verify_learning_site_v2.mjs';

const [site, playwrightModule, output] = process.argv.slice(2);
assert(site && playwrightModule && output, 'Supply rendered site, installed Playwright module and fresh output directory');
const base = 'https://learning.okf.invalid/okf-dwp/';
const paths = ['docs/learning-path.html', 'docs/source-led-manual-guide.html',
  'docs/source-led-results.html', 'docs/source-led-demonstration.html', 'assets/learning.css'];
const sha = raw => createHash('sha256').update(raw).digest('hex');
const files = new Map(await Promise.all(paths.map(async path => [path, await boundedFile(resolve(site, path), 2 * 1024 * 1024)])));
await mkdir(output);
const result = {schema: 'okf-source-led-learning-observation.v1', outcome: 'failed',
  started_at: new Date().toISOString(), inputs: [...files].map(([path, raw]) => ({path, bytes: raw.length, sha256: sha(raw)})),
  harness_sha256: sha(await readFile(new URL(import.meta.url))), checks: [], requests: [], errors: [], warnings: [],
  external_requests: 0, scope: 'Local rendered-site journey, not public deployment or full accessibility acceptance.'};
let browser;
try {
  const {chromium} = await import(pathToFileURL(resolve(playwrightModule)).href);
  browser = await chromium.launch({channel: 'chrome', headless: true, timeout: 20000});
  result.browser = browser.version();
  for (const viewport of [{width: 1280, height: 900}, {width: 390, height: 844}]) {
    const context = await browser.newContext({viewport, serviceWorkers: 'block', acceptDownloads: false});
    context.setDefaultTimeout(10000);
    await context.route('**/*', async route => {
      const request = route.request(), path = request.url().startsWith(base) ? request.url().slice(base.length) : null;
      result.requests.push({url: request.url(), method: request.method()});
      if (request.method() !== 'GET' || !files.has(path) || result.requests.length > 64) {
        result.errors.push(`Unexpected request: ${request.url()}`); await route.abort(); return;
      }
      await route.fulfill({status: 200, contentType: path.endsWith('.css') ? 'text/css' : 'text/html', body: files.get(path)});
    });
    const page = await context.newPage();
    page.on('pageerror', error => result.errors.push(error.message));
    page.on('requestfailed', request => result.errors.push(`Failed request: ${request.url()}`));
    page.on('console', message => {
      if (message.type() === 'error') result.errors.push(message.text());
      else if (message.type() === 'warning') result.warnings.push(message.text());
    });
    await page.goto(base + 'docs/learning-path.html');
    await page.getByRole('link', {name: 'source-led manual guide', exact: true}).click();
    await page.waitForURL(base + 'docs/source-led-manual-guide.html');
    assert.equal(await page.getByRole('heading', {level: 1}).textContent(), 'From a manual to inspectable evidence');
    assert.match(await page.locator('article').innerText(), /DMG.*Decision makers' guide/s);
    assert.match(await page.locator('article').innerText(), /ADM.*Advice for decision making/s);
    const machineGuide = page.locator('article a').filter({hasText: 'machine-readable manual guide'});
    const guideURL = await machineGuide.getAttribute('href');
    assert.match(guideURL, /^https:\/\/github\.com\/chris-page-gov\/okf-dwp\/blob\/[0-9a-f]{40}\/manual-guide\/guide\.json$/);
    result.checks.push({viewport, check: 'beginner-route-and-immutable-guide-link', status: 'passed'});
    await page.getByRole('link', {name: 'source-led results and remaining work', exact: true}).click();
    await page.waitForURL(base + 'docs/source-led-results.html');
    assert.match(await page.locator('article').innerText(), /203 open obligations/);
    assert.match(await page.locator('article').innerText(), /all 40|All 40/);
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    await page.screenshot({path: resolve(output, `results-${viewport.width}.png`)});
    result.checks.push({viewport, check: 'results-table-and-explicit-limits-fit-viewport', status: 'passed'});
    await page.getByRole('link', {name: 'Demonstration script', exact: true}).click();
    await page.waitForURL(base + 'docs/source-led-demonstration.html');
    assert.match(await page.locator('article').innerText(), /Inspect package JSON/);
    assert.match(await page.locator('article').innerText(), /524288/);
    assert.match(await page.locator('.notice').innerText(), /Not an official DWP service/);
    result.checks.push({viewport, check: 'demonstration-has-evidence-inspection-and-budget', status: 'passed'});
    await page.goBack();
    await page.waitForURL(base + 'docs/source-led-results.html');
    result.checks.push({viewport, check: 'back-navigation-retains-results-route', status: 'passed'});
    await context.close();
  }
  assert.deepEqual(result.errors, []); assert.deepEqual(result.warnings, []);
  result.outcome = 'passed';
} catch (error) { result.failure = {name: error.name, message: error.message}; }
finally {
  await browser?.close();
  result.completed_at = new Date().toISOString();
  await writeFile(resolve(output, 'observation.json'), JSON.stringify(result, null, 2) + '\n');
  await writeFile(resolve(output, 'executed-harness.mjs'), await readFile(new URL(import.meta.url)));
}
console.log(JSON.stringify({outcome: result.outcome, checks: result.checks.length, errors: result.errors.length, failure: result.failure}));
if (result.outcome !== 'passed') process.exitCode = 1;
