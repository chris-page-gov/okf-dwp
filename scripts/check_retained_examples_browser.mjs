#!/usr/bin/env node
/** Source-bound public archive browser acceptance; invoked only after publication. */
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { mkdir, writeFile, lstat, readdir } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { BASE, boundedFile, strictJson, safePath } from './verify_learning_site_v2.mjs';
const HERE = fileURLToPath(import.meta.url);
export const LIMITS = Object.freeze({ archive_bytes: 8388608, archive_files: 1024, requests: 512,
  response_bytes: 1048576, transferred_bytes: 16777216, action_ms: 20000, overall_ms: 180000, retries: 0 });
const sha = raw => createHash('sha256').update(raw).digest('hex');
const requiredCases = ['current-care-home', 'unknown-control', 'historical-care-home'];
const requireValue = (value, message) => { if (!value) throw new Error(message); };
function same(raw, ref) { requireValue(raw.length === ref.bytes && sha(raw) === ref.sha256, 'Immutable file binding differs'); }
export async function captureRuntime(repo, commit, local = { harness: HERE, helper: resolve(dirname(HERE), 'verify_learning_site_v2.mjs') }) {
  requireValue(/^[a-f0-9]{40}$/.test(commit), 'Invalid runtime commit');
  const captured = {};
  for (const [key, path] of [['harness', 'scripts/check_retained_examples_browser.mjs'], ['helper', 'scripts/verify_learning_site_v2.mjs']]) {
    const raw = await boundedFile(local[key], 1048576);
    const tree = execFileSync('git', ['ls-tree', commit, '--', path], { cwd: repo, maxBuffer: 4096 }).toString().trim();
    const match = /^100644 blob ([a-f0-9]{40})\t(.+)$/.exec(tree);
    requireValue(match && match[2] === path, 'Executed material is not a regular immutable Git blob');
    const blob = createHash('sha1').update(Buffer.from(`blob ${raw.length}\0`)).update(raw).digest('hex');
    requireValue(blob === match[1], 'Executed harness or helper differs from the supplied commit');
    captured[key] = { path, local: local[key], raw, bytes: raw.length, sha256: sha(raw), git_blob: blob };
  }
  return captured;
}
export function archiveRequest(url, method, plan) {
  const parsed = new URL(url);
  requireValue(method === 'GET' && parsed.origin === new URL(BASE).origin && !parsed.username && !parsed.password
    && !parsed.search && !parsed.hash && url.startsWith(plan.base), 'Request escaped the fixed archive');
  const path = url.slice(plan.base.length);
  requireValue(plan.assets.has(path) && new URL(path, plan.base).href === url, 'Request is not an approved archive asset');
  return path;
}
export async function loadPlan(repo, commit, releaseId) {
  requireValue(/^[a-f0-9]{40}$/.test(commit) && /^[a-z0-9][a-z0-9-]{0,63}$/.test(releaseId), 'Invalid immutable source or release ID');
  const tree = execFileSync('git', ['ls-tree', '-rz', commit], { cwd: repo, maxBuffer: 16 * 1024 * 1024 }).toString();
  const entries = new Map(tree.split('\0').filter(Boolean).map(x => { const [meta, path] = x.split('\t'); return [path, meta.split(' ')]; }));
  const inputs = new Map();
  function read(path, cap = LIMITS.response_bytes) {
    safePath(path); const entry = entries.get(path);
    requireValue(entry?.[0] === '100644' && entry[1] === 'blob', 'Input is not an immutable regular Git blob');
    const size = Number(execFileSync('git', ['cat-file', '-s', entry[2]], { cwd: repo, maxBuffer: 64 }));
    requireValue(Number.isSafeInteger(size) && size <= cap, 'Immutable input exceeds bound');
    const raw = execFileSync('git', ['cat-file', 'blob', entry[2]], { cwd: repo, maxBuffer: cap + 1024 });
    requireValue(raw.length === size, 'Immutable input size changed'); inputs.set(path, { path, bytes: size, sha256: sha(raw), git_blob: entry[2] }); return raw;
  }
  const approval = strictJson(read('evidence-examples/registry.json', 65536));
  requireValue(approval.schema === 'okf-dwp-retained-evidence-publication.v1', 'Wrong publication approval');
  const declarations = approval.releases.filter(x => x.id === releaseId); requireValue(declarations.length === 1, 'Release must have one declaration');
  const release = declarations[0], prefix = `evidence-examples/${releaseId}`;
  requireValue(release.approved_publication === true && release.archive_root === prefix
    && release.artifact_manifest.path === `${prefix}/artifact-manifest.json` && release.registry.path.startsWith('evaluation/'), 'Release is not explicitly approved');
  const manifestRaw = read(release.artifact_manifest.path); same(manifestRaw, release.artifact_manifest);
  const registryRaw = read(release.registry.path, 65536); same(registryRaw, release.registry);
  const inventory = strictJson(manifestRaw), registry = strictJson(registryRaw);
  requireValue(inventory.schema === 'okf-context-archive-artifacts.v1' && registry.schema === 'okf-context-archive-registry.v1'
    && inventory.registry_sha256 === sha(registryRaw) && Array.isArray(inventory.files)
    && inventory.files.length <= LIMITS.archive_files, 'Invalid archive inventory');
  assert.deepEqual(inventory.exporter_files, release.exporter.files, 'Exporter declaration differs');
  const assets = new Map(), bytes = new Map(); let aggregate = manifestRaw.length;
  for (const ref of inventory.files) {
    requireValue(/^(?:index\.(?:html|json)|reader\.(?:mjs|css)|shared\.mjs|[a-f0-9]{64}\/(?:descriptor\.json|package\.json|data\/[a-f0-9]{64}\.json))$/.test(ref.path)
      && !assets.has(ref.path) && Number.isSafeInteger(ref.bytes) && ref.bytes > 0 && ref.bytes <= LIMITS.response_bytes
      && /^[a-f0-9]{64}$/.test(ref.sha256), 'Invalid archive file binding');
    const raw = read(`${prefix}/${ref.path}`); same(raw, ref); aggregate += raw.length;
    requireValue(aggregate <= LIMITS.archive_bytes, 'Archive aggregate exceeds bound'); assets.set(ref.path, ref); bytes.set(ref.path, raw);
  }
  assets.set('artifact-manifest.json', { path: 'artifact-manifest.json', bytes: manifestRaw.length, sha256: sha(manifestRaw) });
  const expectedPaths = new Set([...assets.keys()].map(path => `${prefix}/${path}`));
  assert.deepEqual([...entries.keys()].filter(path => path.startsWith(prefix + '/')).sort(), [...expectedPaths].sort(), 'Archive file census differs from immutable tree');
  const index = strictJson(bytes.get('index.json'));
  requireValue(index.schema === 'okf-context-archive-index.v1' && index.registry_sha256 === sha(registryRaw), 'Wrong index binding');
  assert.deepEqual(index.cases.map(x => x.id), requiredCases, 'Exactly the three named acceptance cases are required');
  assert.deepEqual(registry.cases.map(x => x.id), requiredCases, 'Registry cases differ');
  const cases = index.cases.map((row, i) => {
    const entry = registry.cases[i]; requireValue(entry.approved_publication === true && entry.observation_kind === 'public', 'Case lacks public approval');
    requireValue(row.path === `${row.package_sha256}/descriptor.json` && row.package_sha256 === entry.package.canonical_sha256, 'Wrong fixed descriptor path');
    const descriptorRaw = bytes.get(row.path); same(descriptorRaw, row.descriptor); const descriptor = strictJson(descriptorRaw);
    const raw = bytes.get(`${row.package_sha256}/package.json`); same(raw, { bytes: descriptor.package_bytes, sha256: row.package_sha256 });
    const context = strictJson(raw);
    requireValue(descriptor.schema === 'okf-context-archive.v1' && context.schema === 'okf-governed-context.v1'
      && descriptor.id === row.id && descriptor.title === row.title && descriptor.question === context.question
      && descriptor.context_id === context.context_id && descriptor.evidence_status === 'insufficient'
      && context.evidence_status === 'insufficient' && context.ai_answer === null && descriptor.ai_answer === null
      && descriptor.observation_kind === entry.observation_kind && descriptor.package_sha256 === row.package_sha256
      && descriptor.source_version === entry.source_version && descriptor.engine_id === entry.engine_id
      && descriptor.original_engine_id === entry.original_engine_id, 'Descriptor/package identity or boundary differs');
    assert.deepEqual(descriptor.input_receipt, entry.receipt); same(read(entry.receipt.path, 2097152), entry.receipt);
    requireValue(context.selected.length <= 200 && context.relationships.length <= 1000, 'Case exceeds UI census bounds');
    assert.deepEqual(descriptor.counts, { records: context.selected.length, relationships: context.relationships.length });
    if (row.id === 'unknown-control') requireValue(context.selected.length === 0 && context.relationships.length === 0, 'Unknown control is not empty');
    else requireValue(context.selected.length > 0 && context.relationships.length > 0, 'Substantive case lacks retained evidence');
    if (row.id === 'historical-care-home') requireValue(descriptor.original_engine_id === null, 'Historical original engine must remain unknown');
    return { ...row, descriptor, context, raw };
  });
  return { commit, release_id: releaseId, base: BASE + prefix + '/', assets, cases,
    archive_sha256: sha(manifestRaw), archive_bytes: aggregate, inputs: [...inputs.values()] };
}
export function relationshipText(context) {
  const names = new Map(context.selected.map(x => [x.record.id, x.record.label]));
  return context.relationships.map(row => `${names.get(row.source) || row.source} → ${row.label} → ${names.get(row.target) || row.target}; ${row.predicate}; ${row.assertion_status}; ${row.authority.label}`);
}
export function expectedMetadata(item) {
  const { text, ...record } = item.record;
  return { ...item, record: { ...record, text_reference: { section: 'record_text', characters: text.length, sha256: sha(Buffer.from(text)) } } };
}
export function verifyResponse(raw, response, plan) {
  const path = archiveRequest(response.url, 'GET', plan), ref = plan.assets.get(path);
  requireValue(response.status === 200 && response.redirected !== true && raw.length <= LIMITS.response_bytes, 'Public response failed or redirected');
  same(raw, ref); return { path, url: response.url, http_status: response.status, bytes: raw.length, sha256: sha(raw), status: 'matched' };
}
async function freshDirectory(output) {
  for (let path = dirname(resolve(output)); ; path = dirname(path)) {
    requireValue((await lstat(path)).isDirectory(), 'Output parent is not a regular directory'); if (dirname(path) === path) break;
  }
  await mkdir(resolve(output));
}
export async function run({ repo, commit, releaseId, playwrightModule, output }) {
  await freshDirectory(output);
  const started = new Date().toISOString(), errors = [], warnings = [], requests = [], responses = [], checks = [], caseResults = [];
  const report = { schema: 'okf-retained-examples-public-browser.v1', started_at: started, source_commit: commit,
    release_id: releaseId, outcome: 'failed', model_calls: 0, limits: LIMITS, errors, warnings, requests, responses, checks, cases: caseResults,
    limitations: ['Point-in-time Chrome checks; no cross-browser or exhaustive accessibility acceptance.', 'Delivery and presentation checks do not establish legal applicability, evidence sufficiency or AI answer correctness.'] };
  report.limitations.push('Playwright supplies complete response bodies for hashing. Announced sizes are checked before capture and actual captured sizes afterwards; this is not a hard streaming transfer ceiling inside Chrome. Request count and elapsed-time limits are enforced separately.');
  let plan, runtime, browser, page, context, deadlineTimer, transferred = 0, finishing = false; const pending = new Set();
  const deadline = performance.now() + LIMITS.overall_ms;
  const timely = () => requireValue(performance.now() <= deadline, 'Overall browser deadline exceeded');
  try {
    runtime = await captureRuntime(resolve(repo), commit);
    report.executed_materials = Object.values(runtime).map(({ raw, local, ...identity }) => identity);
    plan = await loadPlan(resolve(repo), commit, releaseId); report.archive_manifest_sha256 = plan.archive_sha256;
    report.base_url = plan.base; report.immutable_inputs = plan.inputs;
    const modulePath = resolve(playwrightModule); const moduleBytes = await boundedFile(modulePath, 1048576);
    report.playwright_entry_sha256 = sha(moduleBytes);
    const { chromium } = await import(pathToFileURL(modulePath).href);
    browser = await chromium.launch({ channel: 'chrome', headless: true, timeout: LIMITS.action_ms }); report.browser = browser.version();
    context = await browser.newContext({ viewport: { width: 1100, height: 850 }, serviceWorkers: 'block', acceptDownloads: false });
    context.setDefaultTimeout(LIMITS.action_ms);
    deadlineTimer = setTimeout(() => { errors.push('Overall browser deadline exceeded'); void context?.close(); }, Math.max(1, deadline - performance.now()));
    await context.route('**/*', async route => {
      const request = route.request(), row = { url: request.url(), method: request.method() }; requests.push(row);
      try { timely(); requireValue(requests.length <= LIMITS.requests, 'Browser request count exceeded');
        row.path = archiveRequest(row.url, row.method, plan); row.status = 'allowed'; await route.continue();
      } catch (error) { row.status = 'blocked'; row.error = error.message; errors.push(error.message); await route.abort(); }
    });
    page = await context.newPage();
    context.on('page', popup => { errors.push('Unexpected additional page blocked'); void popup.close(); });
    page.on('pageerror', error => errors.push(error.message));
    page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); else if (message.type() === 'warning') warnings.push(message.text()); });
    page.on('requestfailed', request => { if (!finishing) errors.push('Request failed: ' + request.url() + ' ' + (request.failure()?.errorText || 'unknown')); });
    page.on('response', response => {
      const task = (async () => { const row = { url: response.url(), status: 'failed' }; responses.push(row);
        try { const announced = response.headers()['content-length'];
          requireValue(announced === undefined || /^\d+$/.test(announced) && Number(announced) <= LIMITS.response_bytes,
            'Announced browser response exceeds capture bound');
          const raw = await response.body(); transferred += raw.length; timely();
          requireValue(transferred <= LIMITS.transferred_bytes, 'Browser response aggregate exceeded');
          Object.assign(row, verifyResponse(raw, { url: response.url(), status: response.status() }, plan));
        } catch (error) { row.error = error.message; errors.push(error.message); }
      })(); pending.add(task); void task.finally(() => pending.delete(task));
    });
    await page.goto(plan.base + 'index.html', { waitUntil: 'domcontentloaded', timeout: LIMITS.action_ms });
    await page.getByRole('link', { name: plan.cases[0].title, exact: true }).waitFor();
    await page.keyboard.press('Tab'); assert.equal(await page.evaluate(() => document.activeElement?.textContent), 'Skip to evidence');
    checks.push('Keyboard Tab reaches the skip link');
    const detail = page.getByRole('region', { name: 'Verified evidence detail' });
    for (const entry of plan.cases) {
      timely(); await page.getByRole('link', { name: entry.title, exact: true }).click();
      await page.getByRole('heading', { name: entry.title, level: 2, exact: true }).waitFor();
      await page.getByRole('button', { name: 'Verify complete machine package', exact: true }).waitFor();
      assert.equal(new URL(page.url()).origin, new URL(plan.base).origin); assert.equal(new URL(page.url()).hash, '#' + entry.id);
      assert.match(await page.locator('#example').textContent(), /Evidence insufficient/);
      assert.equal(await page.getByRole('button', { name: /^Read evidence:/ }).count(), entry.context.selected.length);
      const identities = await page.locator('.identity').evaluate(dl => Object.fromEntries([...dl.querySelectorAll('dt')].map(dt => [dt.textContent, dt.nextElementSibling?.textContent])));
      assert.equal(identities['Source version'], entry.descriptor.source_version); assert.equal(identities['Context identifier'], entry.context.context_id);
      assert.equal(identities['Bundle snapshot'], entry.context.bundle.snapshot);
      assert.equal(identities['Whole-package SHA-256'], entry.package_sha256);
      assert.equal(identities['Recorded assembler'], entry.descriptor.engine_id || 'Unknown');
      assert.equal(identities['Original assembler'], entry.descriptor.original_engine_id || 'Unknown; a compatible reconstruction does not establish the original engine');
      const result = { id: entry.id, selected_records: entry.context.selected.length, relationships: entry.context.relationships.length,
        evidence_status: 'insufficient', context_id: entry.context.context_id, package_sha256: entry.package_sha256 };
      if (entry.context.selected.length) {
        const item = entry.context.selected.find(x => x.record.kind === 'evidence') || entry.context.selected[0];
        await page.getByRole('button', { name: `Read evidence: ${item.record.label}`, exact: true }).click();
        await page.getByText('Complete selected value verified against its retained hash.', { exact: true }).waitFor();
        assert.equal(await detail.locator('pre').first().textContent(), item.record.text);
        assert.deepEqual(JSON.parse(await detail.locator('details pre').textContent()), expectedMetadata(item));
        for (const source of item.record.provenance) {
          assert.ok((await detail.textContent()).includes('Captured: ' + source.captured_at));
          assert.ok((await detail.textContent()).includes(`${source.source_date_kind || 'Source date'}: ${source.source_date || 'Not declared'}`));
          assert.ok((await detail.textContent()).includes('source SHA-256: ' + source.source_sha256));
          assert.ok((await detail.locator('a').evaluateAll(links => links.map(a => a.href))).includes(new URL(source.url).href));
        }
        result.record_id = item.record.id; result.record_literal_sha256 = sha(Buffer.from(item.record.text)); result.provenance_matches = true;
      } else await page.getByText('No records selected. This empty result does not answer the question.', { exact: true }).waitFor();
      await page.getByRole('button', { name: 'Read directed relationships', exact: true }).click();
      await detail.getByRole('heading', { name: 'Directed relationships', exact: true }).waitFor();
      assert.deepEqual(await detail.locator('li').allTextContents(), relationshipText(entry.context));
      result.directed_relationships_match = true;
      const button = page.getByRole('button', { name: 'Verify complete machine package', exact: true }); await button.focus(); await page.keyboard.press('Enter');
      await detail.getByRole('heading', { name: 'Complete machine package', exact: true }).waitFor();
      const rendered = Buffer.from(await detail.locator('pre').textContent()); assert.equal(sha(rendered), entry.package_sha256); assert.ok(rendered.equals(entry.raw));
      assert.equal(await page.evaluate(() => document.activeElement?.textContent), 'Complete machine package');
      result.complete_package_matches = true; result.keyboard_activation_matches = true; caseResults.push(result);
      await page.screenshot({ path: resolve(output, entry.id + '.png') });
    }
    await page.setViewportSize({ width: 390, height: 844 }); await page.getByRole('link', { name: plan.cases[0].title, exact: true }).click();
    await page.getByRole('heading', { name: plan.cases[0].title, level: 2, exact: true }).waitFor();
    await page.getByRole('button', { name: 'Read directed relationships', exact: true }).waitFor();
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    await page.locator('#example-heading').scrollIntoViewIfNeeded(); await page.screenshot({ path: resolve(output, 'current-care-home-mobile.png') });
    checks.push('390px mobile viewport has no horizontal overflow', 'All three cases preserve original package bytes and evidence boundaries');
    await Promise.all([...pending]); timely(); assert.deepEqual(errors, []);
    requireValue(requests.every(x => x.status === 'allowed') && responses.every(x => x.status === 'matched') && responses.length === requests.length, 'Network census differs');
    report.outcome = 'passed';
  } catch (error) {
    report.failure = { name: error.name, message: error.message };
    if (page) { report.failure_state = { url: page.url(), status: await page.locator('#status').textContent().catch(() => null) }; await page.screenshot({ path: resolve(output, 'failure.png') }).catch(() => {}); }
  } finally {
    finishing = true; clearTimeout(deadlineTimer); await browser?.close(); await Promise.allSettled([...pending]);
    if (runtime) {
      for (const material of Object.values(runtime)) {
        try { same(await boundedFile(material.local, 1048576), material); }
        catch { errors.push('Executed material changed during observation: ' + material.path); }
      }
    }
    if (report.outcome === 'passed' && (errors.length || requests.length !== responses.length
      || requests.some(x => x.status !== 'allowed') || responses.some(x => x.status !== 'matched') || performance.now() > deadline)) {
      report.outcome = 'failed'; report.failure = { name: 'ObservationError', message: 'Final response census, deadline or error checks failed' };
    }
    report.completed_at = new Date().toISOString(); report.transferred_bytes = transferred;
    report.executed_harness_sha256 = runtime?.harness.sha256 ?? null; report.helper_sha256 = runtime?.helper.sha256 ?? null;
    if (runtime) {
      await writeFile(resolve(output, 'executed-harness.mjs'), runtime.harness.raw, { flag: 'wx' });
      await writeFile(resolve(output, 'verification-helper.mjs'), runtime.helper.raw, { flag: 'wx' });
    }
    await writeFile(resolve(output, 'observation.json'), JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
    const files = [];
    for (const name of (await readdir(output)).sort()) { const raw = await boundedFile(resolve(output, name), 16 * 1024 * 1024); files.push({ path: name, bytes: raw.length, sha256: sha(raw) }); }
    await writeFile(resolve(output, 'artifact-manifest.json'), JSON.stringify({ schema: 'okf-retained-examples-browser-artifacts.v1', files }, null, 2) + '\n', { flag: 'wx' });
  }
  return report;
}
if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  const args = process.argv.slice(2); assert.equal(args.length, 10, 'Use --repo DIR --commit SHA --release-id ID --playwright-module FILE --output FRESH_DIR');
  assert.deepEqual([args[0], args[2], args[4], args[6], args[8]], ['--repo', '--commit', '--release-id', '--playwright-module', '--output']);
  const result = await run({ repo: args[1], commit: args[3], releaseId: args[5], playwrightModule: args[7], output: args[9] });
  console.log(JSON.stringify({ outcome: result.outcome, cases: result.cases.length, requests: result.requests.length, errors: result.errors.length, failure: result.failure }));
  if (result.outcome !== 'passed') process.exitCode = 1;
}
