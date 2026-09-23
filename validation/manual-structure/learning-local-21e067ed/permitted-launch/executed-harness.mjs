#!/usr/bin/env node
/** Local rendered-site checks. All browser requests are fulfilled from four supplied files. */
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {mkdir, readFile, writeFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
import {boundedFile} from '../../scripts/verify_learning_site_v2.mjs';

const [site, playwrightModule, output] = process.argv.slice(2);
assert(site && playwrightModule && output, 'Supply rendered site, installed Playwright module and fresh output directory');
const base = 'https://learning.okf.invalid/okf-dwp/';
const paths = ['index.html', 'docs/glossary.html', 'docs/semantic-closure-and-compact-delivery.html', 'assets/learning.css'];
const sha = raw => createHash('sha256').update(raw).digest('hex');
const files = new Map(await Promise.all(paths.map(async path => [path, await boundedFile(resolve(site, path), 2 * 1024 * 1024)])));
await mkdir(output);
const result = {schema: 'okf-learning-browser-regression.v1', outcome: 'failed', started_at: new Date().toISOString(),
  inputs: [...files].map(([path, raw]) => ({path, bytes: raw.length, sha256: sha(raw)})),
  harness_sha256: sha(await readFile(new URL(import.meta.url))), checks: [], requests: [], errors: [], warnings: [],
  external_requests: 0, scope: 'Local rendered-site regression, not public deployment verification or full accessibility acceptance.'};
let browser;
try {
  const {chromium} = await import(pathToFileURL(resolve(playwrightModule)).href);
  browser = await chromium.launch({channel: 'chrome', headless: true, timeout: 20000});
  result.browser = browser.version();
  for (const viewport of [{width: 1280, height: 900}, {width: 390, height: 844}]) {
    const context = await browser.newContext({viewport, serviceWorkers: 'block', acceptDownloads: false});
    context.setDefaultTimeout(10000);
    await context.route('**/*', async route => {
      const r = route.request(), path = r.url().startsWith(base) ? r.url().slice(base.length) : null;
      result.requests.push({url: r.url(), method: r.method()});
      if (r.method() !== 'GET' || !files.has(path) || result.requests.length > 64) {
        result.errors.push(`Unexpected request: ${r.url()}`); await route.abort(); return;
      }
      await route.fulfill({status: 200, contentType: path.endsWith('.css') ? 'text/css' : 'text/html', body: files.get(path)});
    });
    const page = await context.newPage();
    page.on('pageerror', e => result.errors.push(e.message));
    page.on('requestfailed', r => result.errors.push(`Failed request: ${r.url()}`));
    page.on('console', m => {if (m.type() === 'error') result.errors.push(m.text()); else if (m.type() === 'warning') result.warnings.push(m.text());});
    await page.goto(base + 'index.html');
    const glossary = page.getByRole('navigation', {name: 'Main'}).getByRole('link', {name: 'Glossary', exact: true});
    const before = await glossary.boundingBox();
    await page.keyboard.press('Tab');
    assert.equal(await page.locator(':focus').textContent(), 'Skip to content');
    const skip = await page.locator('.skip').boundingBox();
    assert(skip && skip.x >= 0 && skip.y >= 0 && skip.x + skip.width <= viewport.width, 'Focused skip link must be visible');
    assert.deepEqual(await glossary.boundingBox(), before, 'Skip focus must not move navigation before pointer activation');
    await glossary.click();
    await page.waitForURL(base + 'docs/glossary.html');
    result.checks.push({viewport, check: 'mixed-keyboard-pointer-glossary', status: 'passed'});

    await page.goto(base + 'index.html');
    await page.keyboard.press('Tab'); await page.keyboard.press('Enter');
    await page.waitForURL(base + 'index.html#main');
    result.checks.push({viewport, check: 'keyboard-skip-to-main', status: 'passed'});
    await page.goto(base + 'index.html');
    for (let i = 0; i < 3; i++) await page.keyboard.press('Tab');
    assert.equal(await page.locator(':focus').textContent(), 'Glossary');
    await page.keyboard.press('Enter'); await page.waitForURL(base + 'docs/glossary.html');
    result.checks.push({viewport, check: 'keyboard-glossary', status: 'passed'});

    await page.goto(base + 'docs/semantic-closure-and-compact-delivery.html');
    assert.equal(await page.locator('[style]').count(), 0, 'Rendered table must not need inline styles');
    assert(await page.locator('.table-align-right').count() > 0, 'Exercise the real aligned closure table');
    assert.equal(await page.locator('.table-align-right').first().evaluate(e => getComputedStyle(e).textAlign), 'right');
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    assert.equal(await page.locator('meta[http-equiv="Content-Security-Policy"]').getAttribute('content'),
      "default-src 'none'; style-src 'self'; img-src https:; base-uri 'none'; form-action 'none'");
    await page.screenshot({path: resolve(output, `closure-${viewport.width}.png`)});
    result.checks.push({viewport, check: 'aligned-table-with-original-csp', status: 'passed'});
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
