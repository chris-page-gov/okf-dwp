#!/usr/bin/env node
/** Public, read-only passage workbench observation. No request routing or fixtures. */
import { createHash } from 'node:crypto';
import { createRequire } from 'node:module';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const DWP_COMMIT = '65924955745c4ed1b8ce66252c4748902b5403ba';
const DEFAULT_MANIFEST = `https://raw.githubusercontent.com/chris-page-gov/okf-dwp/${DWP_COMMIT}/evaluation/passage-boundary-review/manifest.json`;
const DEFAULT_EXPLORER = 'https://chris-page-gov.github.io/okf-explorer/';
const EXPECTED_APP_TREE = '5dda237278ebbc52a3a3140dbd3b53af82a43b9140af9a41953417fbed6dfbd1';
const MAX_MANIFEST_BYTES = 512 * 1024;
const MAX_CASE_BYTES = 512 * 1024;
const MAX_APP_FILES = 512;
const MAX_APP_BYTES = 64 * 1024 * 1024;
const MAX_APP_FILE_BYTES = 16 * 1024 * 1024;
const CASE_TIMEOUT = 30_000;
const RUN_TIMEOUT = 12 * 60_000;
const require = createRequire(import.meta.url);

function argument(name, fallback) {
  const at = process.argv.indexOf(name);
  return at < 0 ? fallback : process.argv[at + 1];
}
function insist(condition, message) { if (!condition) throw new Error(message); }
function sha(bytes) { return createHash('sha256').update(bytes).digest('hex'); }
function iso() { return new Date().toISOString(); }
function safeName(value) { return value.replace(/[^a-z0-9-]/gi, '-').slice(0, 70); }

async function boundedFetch(url, limit) {
  const response = await fetch(url, {
    redirect: 'manual', cache: 'no-store', credentials: 'omit',
    signal: AbortSignal.timeout(30_000), headers: { 'cache-control': 'no-cache' }
  });
  insist(response.ok && response.url === url.href, `Public source failed or redirected: ${url.href} (${response.status})`);
  insist(Number(response.headers.get('content-length') || 0) <= limit, `Public source exceeds ${limit} bytes: ${url.href}`);
  const reader = response.body?.getReader();
  insist(reader, `Empty public response: ${url.href}`);
  const chunks = []; let length = 0;
  try {
    while (true) {
      const next = await reader.read();
      if (next.done) break;
      length += next.value.byteLength;
      insist(length <= limit, `Public source exceeds ${limit} bytes: ${url.href}`);
      chunks.push(next.value);
    }
  } catch (error) { await reader.cancel().catch(() => {}); throw error; }
  finally { reader.releaseLock(); }
  return Buffer.concat(chunks.map(chunk => Buffer.from(chunk)), length);
}

async function checkedCase(reference, manifestUrl) {
  const url = new URL(reference.url, manifestUrl);
  insist(url.origin === manifestUrl.origin && url.pathname.startsWith(manifestUrl.pathname.slice(0, manifestUrl.pathname.lastIndexOf('/') + 1)), `Case path escapes the immutable manifest: ${reference.id}`);
  const bytes = await boundedFetch(url, MAX_CASE_BYTES);
  insist(bytes.length === reference.bytes && sha(bytes) === reference.sha256, `Case reference bytes/hash differ: ${reference.id}`);
  const value = JSON.parse(bytes.toString('utf8'));
  insist(value.id === reference.id && value.label === reference.label, `Case identity differs: ${reference.id}`);
  return value;
}

function checkedAppMaterials(manifest) {
  insist(manifest && typeof manifest === 'object' && !Array.isArray(manifest), 'App build manifest must be an object.');
  insist(JSON.stringify(Object.keys(manifest).sort()) === JSON.stringify(['schema', 'algorithm', 'file_count', 'tree_sha256', 'materials'].sort()), 'App build manifest has unexpected fields.');
  insist(manifest.schema === 'okf-explorer-app-build-manifest.v1' && manifest.algorithm === 'sha256-canonical-json-materials-v1', 'App build manifest schema or algorithm differs.');
  insist(Array.isArray(manifest.materials) && manifest.materials.length > 0 && manifest.materials.length <= MAX_APP_FILES, 'App build manifest exceeds the 512-file limit or has no files.');
  insist(manifest.file_count === manifest.materials.length, 'App build manifest file count differs.');
  const materials = [];
  let total = 0;
  let previous = '';
  for (const [index, item] of manifest.materials.entries()) {
    insist(item && typeof item === 'object' && !Array.isArray(item) && JSON.stringify(Object.keys(item).sort()) === JSON.stringify(['path', 'bytes', 'sha256'].sort()), `App material ${index} has unexpected fields.`);
    insist(typeof item.path === 'string' && item.path.length <= 4096 && item.path.split('/').every(part => /^[A-Za-z0-9._-]+$/.test(part) && part !== '.' && part !== '..'), `App material ${index} has an unsafe path.`);
    insist(index === 0 || previous < item.path, `App material ${index} is duplicated or out of order.`);
    insist(Number.isSafeInteger(item.bytes) && item.bytes > 0 && item.bytes <= MAX_APP_FILE_BYTES, `App material ${index} exceeds the 16 MiB per-file limit or has invalid length.`);
    insist(typeof item.sha256 === 'string' && /^[0-9a-f]{64}$/.test(item.sha256), `App material ${index} has an invalid SHA-256.`);
    total += item.bytes;
    insist(total <= MAX_APP_BYTES, 'App materials exceed the 64 MiB total limit.');
    materials.push({ path: item.path, bytes: item.bytes, sha256: item.sha256 });
    previous = item.path;
  }
  insist(materials.some(item => item.path === 'index.html'), 'App materials omit index.html.');
  const tree = sha(Buffer.from(`${JSON.stringify(materials)}\n`, 'utf8'));
  insist(manifest.tree_sha256 === tree, 'App manifest tree hash differs from its canonical materials.');
  insist(tree === EXPECTED_APP_TREE, `Published app tree ${tree} differs from the reviewed tree ${EXPECTED_APP_TREE}.`);
  return { materials, total, tree };
}

async function verifyPublicApp(explorerBase, receipt) {
  const manifestUrl = new URL('okf-explorer-build-manifest.json', explorerBase);
  const manifestBytes = await boundedFetch(manifestUrl, MAX_MANIFEST_BYTES);
  const manifest = JSON.parse(manifestBytes.toString('utf8'));
  const { materials, total, tree } = checkedAppMaterials(manifest);
  receipt.app_build = {
    status: 'checking', manifest_url: manifestUrl.href,
    manifest_sha256: sha(manifestBytes), expected_tree_sha256: EXPECTED_APP_TREE,
    observed_tree_sha256: tree, declared_files: materials.length,
    declared_bytes: total, verified_files: 0, verified_bytes: 0
  };
  for (const item of materials) {
    const url = new URL(item.path, explorerBase);
    insist(url.origin === explorerBase.origin && url.pathname.startsWith(explorerBase.pathname), `App material escaped publication root: ${item.path}`);
    const bytes = await boundedFetch(url, Math.min(item.bytes, MAX_APP_FILE_BYTES));
    insist(bytes.length === item.bytes && sha(bytes) === item.sha256, `Published app material differs from build manifest: ${item.path}`);
    receipt.app_build.verified_files++;
    receipt.app_build.verified_bytes += bytes.length;
  }
  receipt.app_build.status = 'passed';
}

async function inkPixels(canvas) {
  return canvas.evaluate(element => {
    const context = element.getContext('2d');
    if (!context || !element.width || !element.height) return 0;
    const data = context.getImageData(0, 0, element.width, element.height).data;
    let dark = 0;
    for (let at = 0; at < data.length; at += 64) {
      if (data[at] < 180 || data[at + 1] < 180 || data[at + 2] < 180) dark++;
    }
    return dark;
  });
}

async function previewImpact(page) {
  await page.getByText('Preview passed', { exact: true }).waitFor({ state: 'visible', timeout: CASE_TIMEOUT });
  const status = page.locator('section.preview div[role="status"]');
  const result = await status.locator('dl').evaluate(dl => {
    const pairs = [...dl.querySelectorAll('dt')].map(dt => {
      const raw = dt.nextElementSibling?.querySelector('pre')?.textContent;
      return [dt.textContent?.trim(), raw ? JSON.parse(raw) : null];
    });
    return Object.fromEntries(pairs);
  });
  insist(result.document?.full_units_after === 'unknown', 'Preview claimed a full-document after-count.');
  insist(result.corpus?.isolated_projection_units_after === 'unknown', 'Preview claimed a full-corpus after-count.');
  insist(Number.isSafeInteger(result.document?.affected_unit_delta), 'Preview omitted the exact local unit delta.');
  const effects = result.downstream?.correction_effects;
  for (const key of ['dependencies', 'discovery_records', 'question_packages', 'budget_omissions']) {
    insist(effects?.[key] === 'unknown', `Edited correction claimed ${key} downstream effects.`);
  }
  insist(Object.hasOwn(result.downstream ?? {}, 'supplied_producer_case_evidence'), 'Producer case evidence was not separately labelled.');
  insist(Object.hasOwn(result.corpus ?? {}, 'supplied_producer_candidate_census'), 'Producer corpus census was not separately labelled.');
  return {
    affected_unit_delta: result.document.affected_unit_delta,
    original_passage_source_bytes: result.document.original_passage_source_bytes,
    explicitly_added_source_bytes: result.document.explicitly_added_source_bytes,
    full_document_after: result.document.full_units_after,
    full_corpus_after: result.corpus.isolated_projection_units_after,
    downstream_effects: effects
  };
}

async function main() {
  const explorerCommit = argument('--explorer-commit');
  const browserName = argument('--browser', 'chromium');
  const explorerBase = new URL(argument('--explorer-base', DEFAULT_EXPLORER));
  const manifestUrl = new URL(argument('--dwp-manifest', DEFAULT_MANIFEST));
  const outputArgument = argument('--output');
  insist(typeof outputArgument === 'string' && outputArgument.length > 0, 'Pass --output with a new observation directory whose parent already exists.');
  const output = resolve(outputArgument);
  insist(/^[0-9a-f]{40}$/.test(explorerCommit ?? ''), 'Pass --explorer-commit with the exact 40-character public Site commit.');
  insist(['chromium', 'firefox', 'webkit'].includes(browserName), 'Browser must be chromium, firefox or webkit.');
  insist(explorerBase.protocol === 'https:' && explorerBase.pathname.endsWith('/'), 'Explorer base must be an HTTPS publication root.');
  insist(manifestUrl.href === DEFAULT_MANIFEST, 'DWP manifest must be the exact immutable reviewed GitHub source URL.');
  // Exclusive creation prevents overwriting an earlier observation.
  await mkdir(output, { recursive: false });

  const modulePath = process.env.PLAYWRIGHT_PACKAGE ?? 'playwright';
  const playwright = require(modulePath);
  const playwrightVersion = require(`${modulePath}/package.json`).version;
  const runnerSha256 = sha(await readFile(fileURLToPath(import.meta.url)));
  const receipt = {
    schema: 'okf-public-passage-workbench-observation.v1',
    started_at: iso(), completed_at: null, status: 'running',
    public_explorer: explorerBase.href, expected_explorer_commit: explorerCommit,
    dwp_manifest: manifestUrl.href, expected_dwp_commit: DWP_COMMIT,
    browser: browserName, playwright_version: playwrightVersion, runner_sha256: runnerSha256,
    publication_identity: null, app_build: null, manifest_sha256: null,
    cases_expected: 28, cases_checked: [], pdf: null, case_014: null,
    case_019: null, export: null, screenshots: [], failures: [], page_errors: []
  };
  let browser;
  let page;
  let stage = 'publication-identity';
  const deadline = setTimeout(() => { receipt.failures.push({ step: 'overall-timeout', error: 'Observation exceeded 12 minutes.' }); void browser?.close(); }, RUN_TIMEOUT);
  async function check(step, action, screenshot = false) {
    try { return await action(); }
    catch (cause) {
      receipt.failures.push({ step, error: cause instanceof Error ? cause.message : String(cause) });
      if (screenshot && page) {
        const name = `failure-${safeName(step)}.png`;
        try { await page.screenshot({ path: resolve(output, name), fullPage: true, timeout: 5_000 }); receipt.screenshots.push(name); } catch { /* Keep the original failure. */ }
      }
      return null;
    }
  }
  try {
    const identityUrl = new URL('okf-publication-identity.json', explorerBase);
    const identityBytes = await boundedFetch(identityUrl, 64 * 1024);
    const identity = JSON.parse(identityBytes.toString('utf8'));
    insist(identity.schema === 'okf-publication-deployment-identity.v1' && identity.commit === explorerCommit,
      `Explorer publication identity is ${identity.commit ?? 'missing'}, expected ${explorerCommit}.`);
    receipt.publication_identity = { url: identityUrl.href, sha256: sha(identityBytes), commit: identity.commit };

    stage = 'public-app-build';
    await verifyPublicApp(explorerBase, receipt);

    stage = 'immutable-dwp-manifest';
    const manifestBytes = await boundedFetch(manifestUrl, MAX_MANIFEST_BYTES);
    const manifest = JSON.parse(manifestBytes.toString('utf8'));
    insist(manifest.schema === 'okf-passage-boundary-review-manifest.v1' && manifest.cases?.length === 28, 'Immutable DWP manifest is not the reviewed 28-case profile.');
    receipt.manifest_sha256 = sha(manifestBytes);
    const references = new Map(manifest.cases.map(row => [row.id, row]));
    insist(references.size === 28 && [...Array(28)].every((_, index) => references.has(`case-${String(index + 1).padStart(3, '0')}`)), 'Expected case IDs 001–028 are missing or duplicated.');

    stage = 'browser-observation';
    browser = await playwright[browserName].launch({ headless: true });
    const context = await browser.newContext({ acceptDownloads: true, viewport: { width: 1440, height: 960 }, locale: 'en-GB', timezoneId: 'Europe/London' });
    page = await context.newPage();
    page.setDefaultTimeout(15_000);
    page.on('pageerror', cause => receipt.page_errors.push(String(cause)));
    const publicUrl = new URL('evidence/passages/', explorerBase);
    publicUrl.searchParams.set('manifest', manifestUrl.href);
    await page.goto(publicUrl.href, { waitUntil: 'domcontentloaded', timeout: CASE_TIMEOUT });
    await page.getByText('28 cases').waitFor({ state: 'visible', timeout: CASE_TIMEOUT });
    insist(new URL(page.url()).pathname === publicUrl.pathname, `Public route redirected to ${page.url()}`);

    const first = await checkedCase(references.get('case-001'), manifestUrl);
    await check('first-case-PDF', async () => {
      const firstPage = first.before[0].spans[0].page;
      await page.locator('main h2').waitFor({ state: 'visible', timeout: CASE_TIMEOUT });
      insist((await page.locator('main h2').textContent())?.trim() === first.label, 'First case label differs.');
      await page.getByText('PDF SHA-256 verified against frozen source evidence.').waitFor({ state: 'visible', timeout: CASE_TIMEOUT });
      const canvas = page.locator(`canvas[data-rendered-page="${firstPage}"]`);
      await canvas.waitFor({ state: 'visible', timeout: CASE_TIMEOUT });
      const ink = await inkPixels(canvas);
      insist(ink > 100, `Verified PDF canvas appears blank (${ink} sampled dark pixels).`);
      const selector = page.getByLabel('Source page');
      const nextPage = first.pages.find(row => row.number !== firstPage)?.number;
      insist(nextPage, 'First case has no second page for synchronisation check.');
      await selector.selectOption(String(nextPage));
      await page.locator(`canvas[data-rendered-page="${nextPage}"]`).waitFor({ state: 'visible', timeout: CASE_TIMEOUT });
      await page.getByText(`Page ${nextPage}, UTF-8 bytes`, { exact: false }).waitFor({ state: 'visible', timeout: CASE_TIMEOUT });
      await selector.selectOption(String(firstPage));
      await canvas.waitFor({ state: 'visible', timeout: CASE_TIMEOUT });
      await page.getByText('How this passage was built').click();
      await page.getByText(first.document.parser.settings_text, { exact: true }).waitFor({ state: 'visible', timeout: CASE_TIMEOUT });
      receipt.pdf = { case_id: first.id, first_page: firstPage, synchronised_page: nextPage, sampled_dark_pixels: ink, verified_sha256: first.document.pdf.sha256, parser_settings_sha256: first.document.parser.settings_sha256 };
      const name = 'case-001-verified-pdf.png';
      await page.screenshot({ path: resolve(output, name), fullPage: true }); receipt.screenshots.push(name);
    }, true);

    for (let number = 1; number <= 28; number++) {
      const id = `case-${String(number).padStart(3, '0')}`;
      const reference = references.get(id);
      const result = await check(id, async () => {
        if (number !== 1) await page.getByRole('button', { name: reference.label, exact: true }).click();
        await page.locator('main h2').waitFor({ state: 'visible', timeout: CASE_TIMEOUT });
        insist((await page.locator('main h2').textContent())?.trim() === reference.label, `${id} navigation label differs.`);
        await page.getByRole('button', { name: 'Preview correction' }).click();
        const impact = await previewImpact(page);
        if (number === 14 || number === 19) {
          const item = await checkedCase(reference, manifestUrl);
          if (number === 14) {
            insist(item.technical_outcome?.status === 'unresolved', 'Case 014 source outcome is not unresolved.');
            await page.getByText('Successor target boundary:', { exact: false }).waitFor({ state: 'visible', timeout: CASE_TIMEOUT });
            insist((await page.locator('main').innerText()).includes(item.observation.uncertainty), 'Case 014 uncertainty is not displayed.');
            receipt.case_014 = { outcome: item.technical_outcome.status, uncertainty_visible: true };
          } else {
            insist(item.successor_after?.some(unit => unit.role === 'reference-table'), 'Case 019 lacks the source-bound successor reference table.');
            await page.getByRole('heading', { name: 'Narrowed successor units' }).waitFor({ state: 'visible', timeout: CASE_TIMEOUT });
            insist((await page.locator('main').innerText()).includes('reference-table'), 'Case 019 reference table is not visible.');
            receipt.case_019 = { successor_reference_table: true, source_page: item.successor_after.find(unit => unit.role === 'reference-table').spans[0].page };
          }
          const name = `${id}-source-boundary.png`;
          await page.screenshot({ path: resolve(output, name), fullPage: true }); receipt.screenshots.push(name);
        }
        return { id, preview: 'passed', impact };
      }, true);
      if (result) receipt.cases_checked.push(result);
    }

    await check('local-review-export', async () => {
      insist((await page.locator('main h2').textContent())?.trim() === references.get('case-028').label, 'Export is not bound to case 028.');
      await page.getByLabel('Reviewer').fill('Public observation reviewer');
      await page.getByLabel('Review date').fill(new Date().toISOString().slice(0, 10));
      await page.getByLabel('Reason').fill('Local browser observation only; requires independent source review.');
      const wait = page.waitForEvent('download', { timeout: CASE_TIMEOUT });
      await page.getByRole('button', { name: 'Download review JSON' }).click();
      const download = await wait;
      insist(download.suggestedFilename() === 'passage-review-case-028.json', 'Review download filename differs.');
      const file = resolve(output, 'passage-review-case-028.json');
      await download.saveAs(file);
      const value = JSON.parse(await readFile(file, 'utf8'));
      insist(value.case_id === 'case-028' && value.manifest_sha256 === receipt.manifest_sha256 && value.preview?.accepted === true, 'Review export is not bound to the active manifest and accepted preview.');
      insist(sha(Buffer.from(value.correction_text, 'utf8')) === value.correction_text_sha256, 'Review export correction text hash differs.');
      insist(value.preview.impact?.document?.full_units_after === 'unknown', 'Review export claims a full-document after-count.');
      receipt.export = { file: 'passage-review-case-028.json', sha256: sha(await readFile(file)), authority: value.authority };
    }, true);
    insist(receipt.cases_checked.length === 28, `Only ${receipt.cases_checked.length}/28 cases passed.`);
    insist(receipt.page_errors.length === 0, `${receipt.page_errors.length} uncaught browser page errors occurred.`);
  } catch (cause) {
    receipt.failures.push({ step: stage, error: cause instanceof Error ? cause.message : String(cause) });
    if (page) {
      const name = 'failure-setup-or-finish.png';
      try { await page.screenshot({ path: resolve(output, name), fullPage: true, timeout: 5_000 }); receipt.screenshots.push(name); } catch { /* Preserve the original failure. */ }
    }
  } finally {
    clearTimeout(deadline);
    await browser?.close().catch(() => {});
    receipt.completed_at = iso();
    receipt.status = receipt.failures.length ? 'failed' : 'passed';
    const file = resolve(output, 'observation.json');
    await writeFile(file, `${JSON.stringify(receipt, null, 2)}\n`);
    process.stdout.write(`${receipt.status}: ${receipt.cases_checked.length}/28 cases; receipt ${file}\n`);
    if (receipt.failures.length) process.exitCode = 1;
  }
}

await main();
