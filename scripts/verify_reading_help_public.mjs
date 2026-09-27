#!/usr/bin/env node
/** Public browser/data acceptance only. No PDF, law, service or model requests.
 * Example (after Pages deployment): node scripts/verify_reading_help_public.mjs
 *   --data-root /path/to/okf-dwp --data-commit <40-hex>
 *   --workbench-commit <40-hex> --explorer-commit <40-hex>
 *   --explorer-root /path/to/okf-explorer --output /private/tmp/new-receipt.json
 * Optional --chapter60-revision defaults to --workbench-commit.
 */
import { createHash } from 'node:crypto';
import { readFile, realpath, lstat, writeFile } from 'node:fs/promises';
import { createRequire } from 'node:module';
import { join, resolve, sep } from 'node:path';
import { performance } from 'node:perf_hooks';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { gunzipSync } from 'node:zlib';

const EXPLORER = 'https://chris-page-gov.github.io/okf-explorer/';
const RAW = 'https://raw.githubusercontent.com/chris-page-gov/okf-dwp/';
const HEX40 = /^[a-f0-9]{40}$/;
const allowedDataRevisions = new Set();
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const insist = (condition, message) => { if (!condition) throw Error(message); };
const parse = bytes => JSON.parse(bytes.toString('utf8'));
async function boundedResponse(response, max) {
  insist(response.body && Number.isSafeInteger(max) && max > 0, 'Invalid response bound');
  const reader = response.body.getReader(), chunks = [];
  let size = 0;
  try {
    for (;;) {
      const part = await reader.read();
      if (part.done) break;
      size += part.value.byteLength;
      insist(size <= max, 'Public response exceeds its declared byte bound');
      chunks.push(Buffer.from(part.value));
    }
  } finally { await reader.cancel().catch(() => {}); }
  return Buffer.concat(chunks, size);
}
const result = { schema: 'okf-reading-help-public-verification.v1', status: 'failed', started_at: new Date().toISOString(), inputs: {}, checks: [], requests: [], errors: [], screenshots: [] };

function args() {
  const values = {};
  const accepted = new Set(['data-root', 'data-commit', 'workbench-commit', 'explorer-commit', 'explorer-root', 'output', 'chapter60-revision']);
  for (let n = 2; n < process.argv.length; n += 2) {
    const key = process.argv[n];
    insist(key?.startsWith('--') && accepted.has(key.slice(2)) && process.argv[n + 1] && !values[key.slice(2)], `Invalid or duplicate argument: ${key}`);
    values[key.slice(2)] = process.argv[n + 1];
  }
  for (const key of ['data-root', 'data-commit', 'workbench-commit', 'explorer-commit', 'explorer-root', 'output']) insist(values[key], `Missing --${key}`);
  for (const key of ['data-commit', 'workbench-commit', 'explorer-commit', 'chapter60-revision']) if (values[key]) insist(HEX40.test(values[key]), `Invalid --${key}`);
  values['chapter60-revision'] ??= values['workbench-commit'];
  return values;
}

async function within(root, relative) {
  insist(typeof relative === 'string' && relative && !relative.startsWith('/') && !relative.includes('\\') && !relative.split('/').some(x => !x || x === '.' || x === '..'), `Unsafe local path: ${relative}`);
  const base = await realpath(root), target = await realpath(join(base, relative));
  insist(target.startsWith(base + sep), `Local path escapes data root: ${relative}`);
  return target;
}
async function local(root, relative, binding) {
  const bytes = await readFile(await within(root, relative));
  if (binding) insist(bytes.length === binding.bytes && sha(bytes) === binding.sha256, `Local binding differs: ${relative}`);
  return bytes;
}
async function remote(url, binding, label) {
  const parsed = new URL(url);
  insist(parsed.protocol === 'https:' && !parsed.username && !parsed.password && !parsed.search && !parsed.hash && parsed.hostname === 'raw.githubusercontent.com', `Unapproved data URL: ${url}`);
  const started = performance.now();
  const response = await fetch(parsed, { redirect: 'error', signal: AbortSignal.timeout(15000) });
  insist(response.ok, `${label}: HTTP ${response.status}`);
  const advertised = Number(response.headers.get('content-length'));
  if (Number.isFinite(advertised) && advertised > 0) insist(advertised <= binding.bytes, `${label}: advertised bytes exceed binding`);
  const bytes = await boundedResponse(response, binding.bytes);
  const observed = { label, url: parsed.href, bytes: bytes.length, sha256: sha(bytes), elapsed_ms: Math.round(performance.now() - started) };
  result.requests.push(observed);
  insist(bytes.length === binding.bytes && observed.sha256 === binding.sha256, `${label}: public bytes differ from bound SHA-256`);
  return bytes;
}
async function check(name, operation, receipt = x => x) {
  const started = performance.now();
  try { const detail = await operation(); result.checks.push({ name, passed: true, elapsed_ms: Math.round(performance.now() - started), detail: receipt(detail) }); return detail; }
  catch (error) { const message = `${name}: ${error?.stack || error}`; result.checks.push({ name, passed: false, elapsed_ms: Math.round(performance.now() - started), error: String(error) }); result.errors.push(message); return null; }
}
function corpusRoute(catalogue, family, document, unit, extra = {}) {
  const page = new URL('reading-help/corpus/', EXPLORER);
  for (const [key, value] of Object.entries({ catalogue, family, document, unit, ...extra })) if (value !== undefined && value !== '') page.searchParams.set(key, String(value));
  return page.href;
}
function indexFor(catalogue, family, document) {
  const row = catalogue.documents.find(x => x.family === family && x.document_id === document);
  insist(row, `No catalogue document ${family}/${document}`);
  return row;
}
async function sourceSample(root, catalogue, family, document, needle) {
  const ref = indexFor(catalogue, family, document);
  const index = parse(await local(root, ref.path, ref));
  const passage = index.passages.find(x => x.label?.includes(needle) && x.role === 'paragraph');
  insist(passage, `No ${needle} source passage`);
  const leaf = index.leaves.find(x => x.url === passage.leaf_url);
  insist(leaf && leaf.sha256 === passage.leaf_sha256, 'Passage leaf is unbound');
  const compressed = await local(root, leaf.url, leaf);
  const decoded = gunzipSync(compressed, { maxOutputLength: leaf.decoded_bytes });
  insist(decoded.length === leaf.decoded_bytes && sha(decoded) === leaf.decoded_sha256, 'Decoded leaf differs');
  const row = parse(decoded).passages.find(x => x.id === passage.unit_id);
  insist(row && row.source_spans.length && row.segment.text, 'Selected source row is absent or empty');
  const extraction = parse(await local(root, index.extraction.path, index.extraction));
  const span = row.source_spans[0];
  const page = extraction.pages.find(x => x.page === span.page);
  insist(page?.text, 'Frozen extraction page is unavailable');
  const literal = Buffer.from(page.text, 'utf8').subarray(span.start_utf8, span.end_utf8).toString('utf8');
  insist(sha(Buffer.from(literal)) === span.literal_sha256, 'Frozen source span differs');
  return { ref, index, passage, row, leaf, literal };
}
async function browserCheck(browser, name, url, operation, output) {
  return check(name, async () => {
    const page = await browser.newPage();
    const failures = [];
    page.on('pageerror', error => failures.push(String(error)));
    page.on('console', message => { if (message.type() === 'error') failures.push(message.text()); });
    await page.route('**/*', route => {
      const request = route.request(), uri = new URL(request.url());
      // Only public Explorer assets and immutable DWP raw blobs are needed.
      const revision = uri.pathname.match(/^\/chris-page-gov\/okf-dwp\/([a-f0-9]{40})\//)?.[1];
      if (uri.protocol === 'https:' && !uri.username && !uri.password &&
          (uri.hostname === 'chris-page-gov.github.io' && uri.pathname.startsWith('/okf-explorer/') ||
           uri.hostname === 'raw.githubusercontent.com' && !uri.search && !uri.hash && revision && allowedDataRevisions.has(revision) && !/\.pdf$/i.test(uri.pathname))) return route.continue();
      return route.abort();
    });
    const started = performance.now();
    try {
      await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 25000 });
      const detail = await operation(page);
      insist(!failures.length, `Browser errors: ${failures.join('; ')}`);
      return { url: page.url(), chrome: browser.version(), elapsed_ms: Math.round(performance.now() - started), ...detail };
    } catch (error) {
      const shot = output.replace(/\.json$/i, '') + `-${name.replace(/[^a-z0-9]+/gi, '-')}.png`;
      try { await page.screenshot({ path: shot, fullPage: true }); result.screenshots.push(shot); } catch {}
      throw error;
    } finally { await page.close(); }
  });
}

async function main() {
  const opt = args();
  const root = await realpath(opt['data-root']);
  const explorerRoot = await realpath(opt['explorer-root']);
  const output = resolve(opt.output), allowed = [await realpath('/private/tmp')];
  try { allowed.push(await realpath('/Users/crpage/tmp')); } catch {}
  const outputParent = await realpath(resolve(output, '..'));
  insist(allowed.some(base => outputParent === base || outputParent.startsWith(base + sep)), 'Output must be under /private/tmp or the authorised ExtSSD tmp root');
  try { await lstat(output); throw Error('Output already exists; supply a new receipt path'); }
  catch (error) { if (error.code !== 'ENOENT') throw error; }
  result.inputs = { data_root: root, data_commit: opt['data-commit'], workbench_commit: opt['workbench-commit'], chapter60_revision: opt['chapter60-revision'], explorer_commit: opt['explorer-commit'], explorer_root: explorerRoot, output };
  result.script_sha256 = sha(await readFile(fileURLToPath(import.meta.url)));
  result.invocation = process.argv.slice(2);
  for (const revision of [opt['data-commit'], opt['workbench-commit'], opt['chapter60-revision']]) allowedDataRevisions.add(revision);
  let browser;
  try {
    const require = createRequire(pathToFileURL(join(explorerRoot, 'package.json')));
    const { chromium } = require(join(explorerRoot, 'apps/okf-explorer/node_modules/@playwright/test'));
    const identity = await check('public Explorer identity', async () => {
      const url = new URL('okf-publication-identity.json', EXPLORER).href;
      const response = await fetch(url, { redirect: 'error', signal: AbortSignal.timeout(15000) });
      insist(response.ok, `Identity HTTP ${response.status}`);
      const bytes = await boundedResponse(response, 1024 * 1024);
      const value = parse(bytes);
      insist(value.commit === opt['explorer-commit'], `Explorer Pages commit ${value.commit} does not equal expected ${opt['explorer-commit']}`);
      result.requests.push({ label: 'Explorer identity', url, bytes: bytes.length, sha256: sha(bytes) });
      return { url, commit: value.commit, sha256: sha(bytes) };
    });
    if (!identity) return;

    const catalogue = await check('immutable corpus catalogue', async () => {
      const bytes = await local(root, 'reading-help-corpus/manifest.json');
      const value = parse(bytes);
      insist(value.schema === 'okf-reading-help-catalogue.v1' && value.documents.length === 513, 'Catalogue census differs');
      const url = `${RAW}${opt['data-commit']}/reading-help-corpus/manifest.json`;
      await remote(url, { bytes: bytes.length, sha256: sha(bytes) }, 'corpus catalogue');
      return { value, url, sha256: sha(bytes), bytes: bytes.length };
    }, x => ({ url: x.url, sha256: x.sha256, bytes: x.bytes, documents: x.value.documents.length }));
    if (!catalogue) return;

    const workbench = await check('40 bound workbench sidecars', async () => {
      const path = 'evaluation/evidence-workbench/reading-help-manifest.json';
      const bytes = await local(root, path), value = parse(bytes);
      insist(value.schema === 'okf-evidence-workbench.v1' && value.questions.length === 40, 'Workbench question census differs');
      const refs = value.reading_help?.targets_by_case;
      insist(Array.isArray(refs) && refs.length === 40 && new Set(refs.map(x => x.case_id)).size === 40, 'Sidecar census differs');
      await remote(`${RAW}${opt['workbench-commit']}/${path}`, { bytes: bytes.length, sha256: sha(bytes) }, 'workbench manifest');
      const boundCatalogue = value.reading_help.catalogue;
      insist(boundCatalogue.sha256 === catalogue.sha256 && boundCatalogue.bytes === catalogue.bytes, 'Workbench catalogue binding differs');
      const boundUrl = new URL(boundCatalogue.url);
      insist(boundUrl.hostname === 'raw.githubusercontent.com' && /^\/chris-page-gov\/okf-dwp\/[a-f0-9]{40}\/reading-help-corpus\/manifest\.json$/.test(boundUrl.pathname), 'Workbench catalogue URL is not an immutable corpus snapshot');
      allowedDataRevisions.add(boundUrl.pathname.split('/')[3]);
      await remote(boundCatalogue.url, boundCatalogue, 'workbench-bound catalogue');
      const loaded = new Map();
      let targets = 0;
      for (const ref of refs) {
        insist(value.questions.some(x => x.id === ref.case_id), `Unknown case ${ref.case_id}`);
        const relative = `evaluation/evidence-workbench/${ref.url}`;
        const sidecar = parse(await local(root, relative, ref));
        await remote(`${RAW}${opt['workbench-commit']}/${relative}`, ref, `sidecar ${ref.case_id}`);
        insist(sidecar.schema === 'okf-reading-help-workbench-targets.v1' && sidecar.case_id === ref.case_id && Array.isArray(sidecar.targets), `Invalid sidecar ${ref.case_id}`);
        for (const target of sidecar.targets) {
          const doc = indexFor(catalogue.value, target.family, target.document_id);
          let idx = loaded.get(doc.path);
          if (!idx) { idx = parse(await local(root, doc.path, doc)); loaded.set(doc.path, idx); }
          insist(target.record_id === target.unit_id && idx.passages.some(p => p.unit_id === target.unit_id), `Unbound target ${ref.case_id}: ${target.record_id}`);
          targets++;
        }
      }
      return { url: `${RAW}${opt['workbench-commit']}/${path}`, cases: refs.length, targets, distinct_document_indexes: loaded.size, catalogue_sha256: boundCatalogue.sha256, staff016: parse(await local(root, 'evaluation/evidence-workbench/reading-help/staff-016.json', refs.find(x => x.case_id === 'staff-016'))) };
    }, x => ({ url: x.url, cases: x.cases, targets: x.targets, distinct_document_indexes: x.distinct_document_indexes, catalogue_sha256: x.catalogue_sha256 }));
    if (!workbench) return;
    const briefSource = x => ({ document_id: x.ref.document_id, unit_id: x.passage.unit_id, source_span_sha256: x.row.source_spans[0].literal_sha256 });
    const dmg = await check('local Chapter 60 source controls', async () => sourceSample(root, catalogue.value, 'dmg', 'dmg-vol10-ch60', '60025'), briefSource);
    const adm = await check('local ADM source controls', async () => sourceSample(root, catalogue.value, 'adm', 'adm-chapter-a1', 'A1001'), briefSource);
    const abbrev = await check('printed 166-literal table control', async () => {
      const ref = indexFor(catalogue.value, 'dmg', 'dmg-abbreviations-0db6c476b0');
      const index = parse(await local(root, ref.path, ref));
      const row = index.passages.find(p => p.abbreviations?.length === 166);
      insist(row, 'Printed 166-literal source table is absent');
      const segments = index.passages.filter(x => x.unit_id === row.unit_id).sort((a, b) => a.segment_ordinal - b.segment_ordinal);
      insist(segments.length === row.segment_count && segments.every((x, i) => x.segment_ordinal === i), 'Printed table continuation is incomplete');
      const passageRows = [];
      for (const segment of segments) {
        const leaf = index.leaves.find(x => x.url === segment.leaf_url && x.sha256 === segment.leaf_sha256);
        insist(leaf, 'Printed table leaf is unbound');
        const decoded = gunzipSync(await local(root, leaf.url, leaf), { maxOutputLength: leaf.decoded_bytes });
        insist(sha(decoded) === leaf.decoded_sha256 && decoded.length === leaf.decoded_bytes, 'Printed table leaf decoded binding differs');
        const passage = parse(decoded).passages.find(x => x.id === row.unit_id && x.segment.ordinal === segment.segment_ordinal);
        insist(passage, 'Printed table segment missing');
        passageRows.push(passage);
      }
      insist(passageRows.every(p => JSON.stringify(p.source_spans) === JSON.stringify(passageRows[0].source_spans)), 'Continued table segments do not share one complete source-span list');
      const extraction = parse(await local(root, index.extraction.path, index.extraction));
      const literals = passageRows[0].source_spans.map(span => {
        const page = extraction.pages.find(x => x.page === span.page);
        insist(page?.text, 'Printed table extraction page missing');
        const literal = Buffer.from(page.text, 'utf8').subarray(span.start_utf8, span.end_utf8).toString('utf8');
        insist(sha(Buffer.from(literal)) === span.literal_sha256, 'Printed table source span differs');
        return literal;
      });
      insist(passageRows.map(p => p.segment.text).join('') === literals.join('\n'), 'Continued table text differs from all exact frozen source spans');
      return { ref, row, literals, segment_count: segments.length };
    }, x => ({ document_id: x.ref.document_id, unit_id: x.row.unit_id, abbreviation_literals: x.row.abbreviations.length, source_spans: x.literals.length }));
    const gap = await check('explicit ADM extraction gap control', async () => {
      const ref = indexFor(catalogue.value, 'adm', 'adm-chapter-a2');
      const index = parse(await local(root, ref.path, ref));
      insist(index.extraction_blocked_pages.includes(10), 'ADM page 10 extraction gap missing');
      return { ref, page: 10 };
    }, x => ({ document_id: x.ref.document_id, page: x.page }));
    if (!dmg || !adm || !abbrev || !gap) return;

    browser = await chromium.launch({ channel: 'chrome', headless: true });
    result.chrome_version = browser.version();
    const route = (sample, extra = {}) => corpusRoute(catalogue.url, sample.ref.family, sample.ref.document_id, sample.passage.unit_id, { catalogue_sha256: catalogue.sha256, catalogue_bytes: catalogue.bytes, ...extra });
    await browserCheck(browser, 'DMG 60025 source and cache', route(dmg), async page => {
      const coldStarted = performance.now();
      await page.getByRole('heading', { name: 'Selected source passage' }).waitFor();
      const selected = page.getByRole('region', { name: 'Selected source passage' });
      insist((await selected.locator('.source-page pre').first().textContent()) === dmg.literal, 'Displayed 60025 source differs from exact frozen UTF-8 span');
      insist((await selected.textContent()).includes(dmg.passage.unit_id), 'Selected unit identity missing');
      const cold = (await selected.textContent()).match(/Selected load: ([\d,]+) files and ([\d,]+) bytes fetched; ([\d,]+) verified cache hits/);
      insist(cold && Number(cold[1].replaceAll(',', '')) > 0 && Number(cold[2].replaceAll(',', '')) > 0, 'Cold load metrics absent');
      const coldElapsed = Math.round(performance.now() - coldStarted);
      const button = page.getByRole('region', { name: 'Choose passage' }).getByRole('button', { name: /60025/ }).first();
      const warmStarted = performance.now();
      await button.click();
      await page.waitForFunction(() => /Selected load: 0 files and 0 bytes fetched; [1-9][\d,]* verified cache hits/.test(document.querySelector('.passage')?.textContent || ''), undefined, { timeout: 15000 });
      const warm = (await selected.textContent()).match(/Selected load: ([\d,]+) files and ([\d,]+) bytes fetched; ([\d,]+) verified cache hits/);
      const warmElapsed = Math.round(performance.now() - warmStarted);
      insist(warm && Number(warm[1].replaceAll(',', '')) === 0 && Number(warm[2].replaceAll(',', '')) === 0 && Number(warm[3].replaceAll(',', '')) > 0, 'Warm cache metrics absent');
      const occurrence = page.locator(`.passage [data-occurrence-id="${dmg.row.cards[0].occurrence_id}"]`);
      await occurrence.focus(); await page.keyboard.press('Enter');
      await page.getByText('Candidate status:', { exact: false }).first().waitFor();
      insist((await page.locator('aside.help').textContent()).includes('This is not reviewed guidance'), 'Candidate status label missing');
      await page.getByRole('button', { name: 'Close reading help' }).click();
      insist(await occurrence.evaluate(el => el === document.activeElement), 'Close did not return keyboard focus');
      const numbers = match => ({ fetched_files: Number(match[1].replaceAll(',', '')), fetched_bytes: Number(match[2].replaceAll(',', '')), cache_hits: Number(match[3].replaceAll(',', '')) });
      return { source_span_sha256: dmg.row.source_spans[0].literal_sha256, cold: { ...numbers(cold), elapsed_ms: coldElapsed }, warm: { ...numbers(warm), elapsed_ms: warmElapsed }, occurrence_id: await occurrence.getAttribute('data-occurrence-id') };
    }, output);
    await browserCheck(browser, 'ADM source passage', route(adm), async page => {
      await page.getByRole('heading', { name: 'Selected source passage' }).waitFor();
      const displayed = await page.locator('.passage .source-page pre').first().textContent();
      insist(displayed === adm.literal, 'Displayed ADM source differs from frozen UTF-8 span');
      insist((await page.locator('.passage').textContent()).includes('Candidate meanings and legal applicability remain unreviewed'), 'ADM boundary label missing');
      return { source_span_sha256: adm.row.source_spans[0].literal_sha256, unit_id: adm.passage.unit_id };
    }, output);
    await browserCheck(browser, 'printed table and extraction gap', corpusRoute(catalogue.url, 'dmg', abbrev.ref.document_id, abbrev.row.unit_id), async page => {
      await page.getByRole('heading', { name: 'Selected source passage' }).waitFor();
      const visible = await page.locator('.passage .source-page pre').allTextContents();
      insist(visible.length === abbrev.literals.length && visible.every((text, i) => text === abbrev.literals[i]), 'Printed 166-literal table differs from exact frozen source spans');
      return { abbreviation_literals: abbrev.row.abbreviations.length, unit_id: abbrev.row.unit_id, source_spans: visible.length };
    }, output);
    await browserCheck(browser, 'ADM extraction gap', corpusRoute(catalogue.url, 'adm', gap.ref.document_id, ''), async page => {
      const disclosure = page.getByText('Machine-extraction gaps', { exact: false }).first();
      await disclosure.waitFor(); await disclosure.click();
      insist((await page.getByRole('link', { name: 'Open source PDF at page 10' }).count()) === 1, 'ADM extraction gap is not visible');
      return { document_id: gap.ref.document_id, page: gap.page };
    }, output);
    const chapter = async (file, name, paired) => browserCheck(browser, name, new URL(`reading-help/?manifest=${encodeURIComponent(`${RAW}${opt['chapter60-revision']}/${file}`)}&passage=dmg-60025`, EXPLORER).href, async page => {
      await page.getByRole('heading', { name: /60025/ }).waitFor();
      const marker = page.locator('[data-occurrence-id="60025-fte-marker-5"]');
      if (paired) {
        insist(await marker.count() === 1, 'Paired footer marker missing');
        await marker.click();
        insist((await page.locator('#reading-help-panel').textContent()).includes('Other occurrences for this reference'), 'Footer pairing unavailable');
        await page.locator('#reading-help-panel button').filter({ hasText: '5 s 70(3)' }).click();
        const footer = page.locator('[data-occurrence-id="60025-marker-5-reference-row"]');
        insist(await footer.evaluate(el => el === document.activeElement), 'Paired footer navigation did not focus the exact row');
      } else {
        const term = page.locator('[data-occurrence-id="60025-fte"]');
        await term.click();
        insist((await page.locator('#reading-help-panel').textContent()).includes('Project reading help'), 'Original v1 card unavailable');
        await page.getByRole('button', { name: 'Close reading help' }).click();
        insist(await term.evaluate(el => el === document.activeElement), 'Original v1 close did not restore focus');
      }
      return { manifest: file, paired_marker: paired };
    }, output);
    await check('immutable Chapter 60 v1 manifests', async () => {
      for (const file of ['reading-help-ch60.json', 'reading-help-ch60-references.json', 'reading-help-ch60-law.json']) {
        const bytes = await local(root, file);
        await remote(`${RAW}${opt['chapter60-revision']}/${file}`, { bytes: bytes.length, sha256: sha(bytes) }, file);
      }
      return { revision: opt['chapter60-revision'] };
    });
    await chapter('reading-help-ch60.json', 'original Chapter 60 v1 fallback', false);
    await chapter('reading-help-ch60-references.json', 'paired Chapter 60 footer', true);
    await browserCheck(browser, 'dated Chapter 60 provision link', new URL(`reading-help/?manifest=${encodeURIComponent(`${RAW}${opt['chapter60-revision']}/reading-help-ch60-law.json`)}&passage=dmg-60025`, EXPLORER).href, async page => {
      const localLaw = parse(await local(root, 'reading-help-ch60-law.json'));
      const card = localLaw.cards.find(x => x.id === '60025-marker-5');
      insist(card?.target?.url?.includes('/2026-09-20'), 'Dated local provision binding absent');
      const marker = page.locator('[data-occurrence-id="60025-fte-marker-5"]');
      await marker.waitFor(); await marker.click();
      const link = page.locator('#reading-help-panel a').filter({ hasText: 'Open dated official provision' }).first();
      insist(await link.getAttribute('href') === card.target.url, 'Displayed dated provision differs from bound candidate card');
      return { candidate_card: card.id, dated_url: card.target.url, statutory_document_fetched: false };
    }, output);
    await browserCheck(browser, 'staff-016 bound reading-help link', new URL(`evidence/?manifest=${encodeURIComponent(`${RAW}${opt['workbench-commit']}/evaluation/evidence-workbench/reading-help-manifest.json`)}&case=staff-016&record=${encodeURIComponent(workbench.staff016.targets[0].record_id)}&tab=passage`, EXPLORER).href, async page => {
      const link = page.getByRole('link', { name: 'Read this passage in the source-linked reading help' });
      await link.waitFor();
      const href = new URL(await link.getAttribute('href'), page.url());
      insist(href.pathname.endsWith('/reading-help/corpus/'), 'Workbench reading-help destination differs');
      insist(href.searchParams.get('catalogue_sha256') === catalogue.sha256 && href.searchParams.get('catalogue_bytes') === String(catalogue.bytes), 'Workbench catalogue binding missing');
      insist(href.searchParams.get('unit') === workbench.staff016.targets[0].unit_id, 'Workbench exact record target differs');
      return { record_id: workbench.staff016.targets[0].record_id, link: href.href };
    }, output);
  } catch (error) {
    result.errors.push(`Fatal verifier failure: ${error?.stack || error}`);
  } finally {
    try { await browser?.close(); } catch (error) { result.errors.push(`Browser cleanup failed: ${error}`); }
    result.finished_at = new Date().toISOString();
    const required = ['public Explorer identity', 'immutable corpus catalogue', '40 bound workbench sidecars', 'DMG 60025 source and cache', 'ADM source passage', 'printed table and extraction gap', 'ADM extraction gap', 'immutable Chapter 60 v1 manifests', 'original Chapter 60 v1 fallback', 'paired Chapter 60 footer', 'dated Chapter 60 provision link', 'staff-016 bound reading-help link'];
    for (const name of required) if (!result.checks.some(x => x.name === name && x.passed)) result.errors.push(`Required check did not pass: ${name}`);
    result.status = result.errors.length ? 'failed' : 'passed';
    await writeFile(output, JSON.stringify(result, null, 2) + '\n', { flag: 'wx', mode: 0o600 });
    console.log(`${result.status}: ${result.checks.filter(x => x.passed).length}/${result.checks.length} checks; receipt ${output}`);
    if (result.errors.length) process.exitCode = 1;
  }
}
main().catch(error => { console.error(error?.stack || error); process.exitCode = 1; });
