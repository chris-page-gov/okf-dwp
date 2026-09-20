// Public compact evidence reader acceptance. No interception, local substitution or model calls.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { createRequire } from 'node:module';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

export const sha256 = value => createHash('sha256').update(value).digest('hex');
export const MINIMUM_CALL_INTERVAL_MS = 750;
// One pacer is shared by all engines. Observe actual request starts, not click times.
export function createCallPacer({ now = () => performance.now(), sleep = ms => new Promise(resolve => setTimeout(resolve, ms)) } = {}) {
  let lastRequestAt = -Infinity;
  return {
    markRequest: () => {
      const started = now(), interval = Number.isFinite(lastRequestAt) ? started - lastRequestAt : null;
      lastRequestAt = started; return interval === null ? null : Math.round(interval * 1000) / 1000;
    },
    wait: async () => {
      let remaining;
      while ((remaining = MINIMUM_CALL_INTERVAL_MS - (now() - lastRequestAt)) > 0) await sleep(remaining);
    }
  };
}
const root = path.resolve(fileURLToPath(new URL('..', import.meta.url)));
const scriptPath = fileURLToPath(import.meta.url);
const sections = ['record_text', 'record_metadata', 'diagnostics', 'relationships', 'package'];
const engines = ['chrome', 'firefox', 'webkit'];
// Browser-native UTF-8 observation. The request, response and original fetch promise
// are returned unchanged; only a clone is read. No routing or response substitution.
export function installNativeResponseObserver() {
  const original = window.fetch;
  const state = { sequence: 0, last: null };
  Object.defineProperty(window, '__okfEvidenceObservation', { value: state });
  window.fetch = function (input, init) {
    const result = Reflect.apply(original, this, arguments);
    try {
      const target = new URL(typeof input === 'string' ? input : input.url, window.location.href);
      const method = init?.method ?? (typeof input === 'object' ? input.method : 'GET');
      if (target.origin !== window.location.origin || target.pathname !== '/okf/mcp' || method?.toUpperCase() !== 'POST') return result;
      const request = JSON.parse(init.body);
      const observation = { sequence: ++state.sequence, rpc_id: request.id, status: null, text: null, error: null, done: false };
      state.last = observation;
      result.then(async response => {
        try {
          observation.status = response.status;
          const text = await response.clone().text();
          if (new TextEncoder().encode(text).byteLength > 300000) throw new Error('Browser-native tool envelope exceeds observation limit');
          observation.text = text;
        } catch (error) { observation.error = String(error.message); }
        finally { observation.done = true; }
      }, error => { observation.error = String(error.message); observation.done = true; });
    } catch { /* The normal application still receives its original result. */ }
    return result;
  };
}
export function decodeTool(text) {
  assert.ok(Buffer.byteLength(text) <= 300000, 'Tool envelope exceeds the reader limit');
  const data = JSON.parse(text.trimStart().startsWith('{') ? text : text.split('\n').find(line => line.startsWith('data: '))?.slice(6) || 'null');
  assert.ok(data && !data.error && data.result?.isError !== true && data.result?.structuredContent, 'Tool returned no verified evidence');
  assert.deepEqual(JSON.parse(data.result.content[0].text), data.result.structuredContent, 'Tool text and structured result differ');
  return data.result.structuredContent;
}
export function checkContentSecurityPolicy(header) {
  assert.equal(typeof header, 'string', 'Missing content security policy');
  const directives = {};
  for (const part of header.split(';').map(value => value.trim()).filter(Boolean)) {
    const [name, ...values] = part.split(/\s+/);
    const directive = name.toLowerCase();
    assert.ok(!Object.hasOwn(directives, directive), 'Duplicate content security policy directive');
    directives[directive] = values.sort();
  }
  assert.deepEqual(directives, {
    'default-src': ["'none'"], 'script-src': ["'self'"], 'connect-src': ["'self'"],
    'style-src': ["'unsafe-inline'"], 'img-src': ['data:'], 'base-uri': ["'none'"],
    'form-action': ["'none'"], 'frame-ancestors': ["'none'"]
  }, 'Reader content security policy differs from the intended restricted directives');
}
export function checkCatalogue(catalogue, selected) {
  const expected = selected.map(({ record, reasons, paths }) => ({
    id: record.id, label: record.label, kind: record.kind, assertion_status: record.assertion_status,
    text_characters: record.text.length, text_sha256: sha256(record.text),
    source_url: record.provenance[0]?.url ?? '', source_locator: record.provenance[0]?.locator ?? '',
    authority_class: record.authority.class, review_status: record.review_status ?? 'not-declared',
    reasons: reasons.length, paths: paths.length
  }));
  assert.deepEqual(catalogue, expected, 'Catalogue metadata differs from the hash-verified full evidence package');
}
export function validateInputs(sdk, deployment, serviceURL) {
  const service = new URL(serviceURL);
  assert.equal(service.protocol, 'https:', 'Public acceptance requires HTTPS');
  assert.ok(!service.username && !service.password && !service.search && !service.hash && service.pathname === '/', 'Use a bare service origin');
  assert.equal(sdk.schema, 'okf-remote-mcp-sdk-verification.v1');
  assert.equal(deployment.schema, 'okf-compact-delivery-deployment.v1');
  assert.equal(sdk.passed, true, 'SDK acceptance must pass first');
  assert.equal(sdk.comparison_source_commit, deployment.runtime_commit);
  assert.equal(sdk.comparison_worker_sha256, deployment.runtime_worker_sha256);
  assert.match(deployment.runtime_commit, /^[a-f0-9]{40}$/);
  assert.match(deployment.runtime_worker_sha256, /^[a-f0-9]{64}$/);
  assert.equal(deployment.deployment.status, 'succeeded');
  const deployedURL = new URL(deployment.deployment.url);
  assert.ok(!deployedURL.username && !deployedURL.password && !deployedURL.search && !deployedURL.hash && deployedURL.pathname === '/', 'Deployment URL must be a credential-free origin');
  assert.equal(deployedURL.origin, service.origin);
  assert.equal(sdk.endpoint, service.origin + '/okf/mcp');
  const expected = sdk.compact_delivery;
  assert.ok(expected && expected.catalogue_matches_selected_records && expected.review_recipe_matches_context);
  assert.ok(expected.reconstructed_package_matches_direct_engine && expected.all_delivery_bounds_checked);
  assert.equal(expected.model_answer_present, false);
  assert.ok(Number.isSafeInteger(expected.selected_records) && expected.selected_records > 0 && expected.selected_records <= 200);
  const review = new URL(expected.review_url);
  assert.ok(!review.username && !review.password, 'Review URL must not contain credentials');
  assert.equal(review.origin, service.origin); assert.equal(review.pathname, '/review/'); assert.equal(review.search, '');
  const recipe = JSON.parse(Buffer.from(review.hash.slice(1), 'base64url').toString('utf8'));
  assert.equal(recipe.version, expected.bundle_version); assert.equal(recipe.context_id, expected.context_id);
  assert.match(recipe.context_id, /^urn:sha256:[a-f0-9]{64}$/);
  assert.equal(sha256(recipe.question), expected.question_sha256);
  assert.deepEqual(recipe.budget, expected.context_budget);
  for (const section of sections) {
    const read = expected.reads.find(item => item.section === section);
    assert.ok(read && read.reconstructed_hash_matches && read.contiguous_offsets && read.all_delivery_bounds_checked, `Missing verified ${section}`);
    assert.match(read.content_sha256, /^[a-f0-9]{64}$/);
    assert.ok(Number.isSafeInteger(read.characters) && read.characters >= 0 && read.characters <= 300000);
  }
  assert.equal(expected.reads.find(row => row.section === 'record_text').record_id, expected.reads.find(row => row.section === 'record_metadata').record_id);
  return { expected, recipe, origin: service.origin };
}
export function checkSlice(part, expected, contextId, offset) {
  assert.equal(part.context_id, contextId); assert.equal(part.section, expected.section);
  assert.equal(part.record_id, expected.record_id); assert.equal(part.offset, offset);
  assert.equal(part.content_sha256, expected.content_sha256); assert.equal(part.total_characters, expected.characters);
  assert.equal(typeof part.data, 'string'); assert.equal(part.end_offset, offset + part.data.length);
  assert.ok(part.end_offset <= part.total_characters);
  assert.equal(part.next_offset, part.end_offset < part.total_characters ? part.end_offset : null);
  assert.ok(part.next_offset === null || part.next_offset > offset, 'Pagination must progress');
  assert.equal(part.delivery.used_bytes, Buffer.byteLength(JSON.stringify(part)));
  assert.ok(part.delivery.used_bytes <= part.delivery.max_bytes && part.delivery.max_bytes <= 65536);
}
function options(argv, env) {
  const parsed = {};
  for (let i = 0; i < argv.length; i++) {
    const name = argv[i];
    assert.ok(['--explorer-root', '--service-url', '--sdk-receipt', '--deployment', '--output', '--engines', '--check-inputs', '--help'].includes(name), `Unknown argument ${name}`);
    if (['--check-inputs', '--help'].includes(name)) parsed[name] = true;
    else { assert.ok(argv[i + 1] && !argv[i + 1].startsWith('--'), `Missing value for ${name}`); parsed[name] = argv[++i]; }
  }
  return {
    checkout: parsed['--explorer-root'] || env.OKF_EXPLORER_CHECKOUT,
    service: parsed['--service-url'] || env.OKF_STAFF_SERVICE_URL,
    sdk: parsed['--sdk-receipt'] || env.OKF_STAFF_SDK_RECEIPT,
    deployment: parsed['--deployment'] || env.OKF_STAFF_DEPLOYMENT_RECEIPT,
    output: parsed['--output'] || env.OKF_STAFF_BROWSER_OUTPUT,
    engines: (parsed['--engines'] || env.OKF_STAFF_BROWSER_ENGINES || engines.join(',')).split(','),
    checkOnly: parsed['--check-inputs'], help: parsed['--help']
  };
}
const sanitise = message => String(message).replace(/https?:\/\/[^\s)]+/g, value => {
  try { const url = new URL(value); return url.origin + url.pathname; } catch { return '[URL]'; }
}).slice(0, 1500);

async function observe(engine, playwright, inputs, binding, out, pacer) {
  const { expected, recipe, origin } = inputs;
  const started = new Date().toISOString();
  const consoleErrors = [], calls = [], reads = [], responseObservations = [];
  const deadline = Date.now() + 12 * 60 * 1000;
  let droppedConsoleErrors = 0;
  const retainError = error => { if (consoleErrors.length < 128) consoleErrors.push(error); else droppedConsoleErrors++; };
  let browser, receipt = {
    schema: 'okf-staff-service-browser-observation.v1', started_at: started, browser: engine,
    url: expected.review_url, source_version: expected.bundle_version, question: recipe.question,
    context_id: expected.context_id, context_budget: recipe.budget, binding,
    functional_status: 'failed', strict_console_status: 'not_observed', overall_clean_browser_acceptance: false,
    calls, reads, response_observations: responseObservations, console_errors: consoleErrors,
    limitations: ['Actual public browser requests without interception or local source substitution; SDK and hosting receipts establish separate reference identities.',
      'One declared staff question and one source record per browser. This is not an accessibility audit, legal assessment, AI-answer test or whole-corpus semantic completeness claim.',
      'Full selected package hashes are compared with the SDK; no cookie, account data, raw network trace or model response is retained.',
      'Functional checks and strict browser-console acceptance are separate; any observed failure remains recorded.']
  };
  try {
    browser = await playwright[engine === 'chrome' ? 'chromium' : engine].launch(engine === 'chrome' ? { channel: 'chrome' } : {});
    receipt.browser_version = browser.version();
    const context = await browser.newContext({ viewport: { width: 1280, height: 1000 } });
    await context.addInitScript(installNativeResponseObserver);
    const page = await context.newPage();
    const expect = playwright.expect;
    page.on('pageerror', error => retainError({ type: 'pageerror', message: sanitise(error.message) }));
    page.on('console', message => { if (message.type() === 'error') retainError({ type: 'console', message: sanitise(message.text()) }); });
    page.on('request', request => {
      if (request.url() !== origin + '/okf/mcp') return;
      const interval = pacer.markRequest();
      const params = request.postDataJSON()?.params;
      calls.push({ tool: params?.name, milliseconds_since_previous_mcp_request: interval, section: params?.arguments?.section ?? null,
        record_id: params?.arguments?.record_id ?? null, offset: params?.arguments?.offset ?? 0 });
    });
    async function invoke(tool, action) {
      assert.ok(Date.now() < deadline && calls.length < 512, 'Browser observation time or call budget exhausted');
      await pacer.wait();
      const waiting = page.waitForResponse(response => response.url() === origin + '/okf/mcp'
        && response.request().postDataJSON()?.params?.name === tool, { timeout: 90000 });
      await action(); const response = await waiting; assert.equal(response.status(), 200);
      const rpcId = response.request().postDataJSON().id;
      await page.waitForFunction(id => window.__okfEvidenceObservation?.last?.rpc_id === id && window.__okfEvidenceObservation.last.done, rpcId, { timeout: 10000 });
      const observed = await page.evaluate(() => window.__okfEvidenceObservation.last);
      assert.equal(observed.rpc_id, rpcId); assert.equal(observed.status, response.status()); assert.equal(observed.error, null);
      const driverText = await response.text();
      responseObservations.push({ tool, rpc_id: rpcId, representation: 'browser-native Response.clone().text() UTF-8',
        native_bytes: Buffer.byteLength(observed.text), native_sha256: sha256(observed.text),
        driver_bytes: Buffer.byteLength(driverText), driver_sha256: sha256(driverText), driver_text_matches_native: driverText === observed.text });
      return decodeTool(observed.text);
    }
    const shell = await page.goto(expected.review_url, { waitUntil: 'load', timeout: 90000 });
    assert.equal(shell.status(), 200); assert.equal(new URL(page.url()).origin, origin);
    const headers = shell.headers();
    checkContentSecurityPolicy(headers['content-security-policy']);
    assert.ok(headers['cache-control']?.split(',').map(value => value.trim()).includes('no-transform'));
    receipt.shell = { status: shell.status(), cache_control: headers['cache-control'], content_security_policy: headers['content-security-policy'] };
    await expect(page.getByLabel('Approved source version')).toHaveValue(expected.bundle_version);
    await expect(page.getByLabel('General question')).toHaveValue(recipe.question);
    await expect(page.locator('#context')).toBeHidden(); assert.equal(calls.length, 0, 'Replay link must be inert until invoked');
    let manifest = await invoke('ask_okf_manifest', () => page.getByRole('button', { name: 'Recreate evidence', exact: true }).click());
    const catalogue = [], summary = manifest.summary;
    let offset = 0, pages = 0;
    while (true) {
      assert.equal(manifest.context_id, expected.context_id); assert.deepEqual(manifest.summary, summary);
      assert.equal(manifest.evidence_status, expected.evidence_status); assert.equal(summary.ai_answer, null);
      assert.equal(summary.selected_records, expected.selected_records); assert.equal(summary.relationships, expected.selected_relationships);
      assert.equal(manifest.delivery.offset, offset); assert.equal(manifest.delivery.returned, manifest.records.length);
      assert.equal(manifest.delivery.total, expected.selected_records);
      assert.equal(manifest.response_bytes, Buffer.byteLength(JSON.stringify(manifest)));
      assert.ok(manifest.response_bytes <= manifest.response_limit && manifest.response_limit <= 65536);
      catalogue.push(...manifest.records); pages++;
      assert.ok(pages <= 201 && catalogue.length <= expected.selected_records, 'Bounded catalogue');
      await expect(page.locator('#records article')).toHaveCount(catalogue.length);
      if (manifest.delivery.next_offset === null) break;
      assert.equal(manifest.delivery.next_offset, catalogue.length); assert.ok(manifest.delivery.next_offset > offset);
      offset = manifest.delivery.next_offset;
      manifest = await invoke('ask_okf_manifest', () => page.getByRole('button', { name: 'Show more records', exact: true }).click());
    }
    assert.equal(catalogue.length, expected.selected_records); assert.equal(new Set(catalogue.map(row => row.id)).size, catalogue.length);
    await expect(page.locator('#record-count')).toContainText(`${catalogue.length} of ${catalogue.length}`);
    await expect(page.locator('#identity')).toContainText(expected.context_id);
    await expect(page.locator('#boundary')).toContainText(expected.evidence_status.toUpperCase());
    await page.screenshot({ path: path.join(out, engine + '-catalogue.png') });
    receipt.catalogue = { records: catalogue.length, pages, ids: catalogue.map(row => row.id), summary };
    const sourceExpected = expected.reads.find(row => row.section === 'record_text');
    const selected = catalogue.find(row => row.id === sourceExpected.record_id); assert.ok(selected, 'SDK source record must be in the catalogue');
    const article = page.locator('#records article').filter({ has: page.getByText(selected.id, { exact: true }) });
    await expect(article.getByRole('link', { name: /^Original source/ })).toHaveAttribute('href', selected.source_url);
    const reconstructed = {};
    for (const section of sections) {
      const readExpected = expected.reads.find(row => row.section === section);
      const action = section === 'record_text' ? () => article.getByRole('button', { name: 'Read exact text', exact: true }).click()
        : section === 'record_metadata' ? () => article.getByRole('button', { name: 'Inspect provenance and inclusion reasons', exact: true }).click()
        : () => page.getByRole('button', { name: ({ diagnostics: 'Read gaps, scope and budgets', relationships: 'Read relationship paths', package: 'Read full machine package' })[section], exact: true }).click();
      let part = await invoke('read_okf_evidence', action), readOffset = 0, slices = 0;
      const chunks = [];
      while (true) {
        checkSlice(part, readExpected, expected.context_id, readOffset);
        await expect(page.locator('#read-status')).toContainText(`Characters ${part.offset}–${part.end_offset}`);
        await expect(page.locator('#read-status')).toContainText('This is source data, not an AI answer');
        await expect.poll(() => page.locator('#read-data').textContent()).toBe(part.data);
        chunks.push(await page.locator('#read-data').textContent()); slices++; assert.ok(slices <= 256, 'Bounded text pagination');
        if (slices === 1 && section === 'record_text') {
          await expect(page.locator('#read-source')).toContainText(selected.id);
          await expect(page.locator('#read-source a')).toHaveAttribute('href', selected.source_url);
          await page.locator('section[aria-labelledby="read-heading"]').screenshot({ path: path.join(out, engine + '-source-evidence.png') });
        }
        if (part.next_offset === null) break;
        readOffset = part.next_offset;
        part = await invoke('read_okf_evidence', () => page.getByRole('button', { name: 'Read next part', exact: true }).click());
      }
      const text = chunks.join(''); assert.equal(text.length, readExpected.characters); assert.equal(sha256(text), readExpected.content_sha256);
      reconstructed[section] = text;
      reads.push({ section, record_id: readExpected.record_id, slices, characters: text.length, rendered_sha256: sha256(text), matches_sdk: true });
    }
    const full = JSON.parse(reconstructed.package), metadata = JSON.parse(reconstructed.record_metadata);
    assert.equal(sha256(reconstructed.package), expected.package_canonical_sha256);
    checkCatalogue(catalogue, full.selected);
    receipt.catalogue.metadata_matches_verified_package = true;
    assert.equal(Buffer.byteLength(reconstructed.package), expected.reconstructed_package_bytes);
    assert.equal(full.ai_answer, null);
    const source = full.selected.find(item => item.record.id === selected.id); assert.ok(source);
    assert.equal(source.record.text, reconstructed.record_text); assert.deepEqual(metadata.record.provenance, source.record.provenance);
    assert.deepEqual(metadata.reasons, source.reasons); assert.deepEqual(metadata.paths, source.paths);
    assert.deepEqual(JSON.parse(reconstructed.relationships), full.relationships);
    const diagnostics = JSON.parse(reconstructed.diagnostics);
    assert.deepEqual(diagnostics.missing_evidence, full.missing_evidence); assert.deepEqual(diagnostics.budget, full.budget);
    receipt.record = { id: selected.id, source_url: selected.source_url, source_locator: selected.source_locator, provenance_visible: true };
    receipt.diagnostics = { keys: Object.keys(diagnostics), missing_evidence: full.missing_evidence.length, evidence_status: full.evidence_status, context_truncated: full.budget.truncated };
    receipt.functional_status = 'passed';
  } catch (error) { receipt.failure = { name: error.name, message: sanitise(error.message) }; }
  finally {
    if (browser) {
      try { await browser.close(); } catch (error) {
        receipt.functional_status = 'failed'; receipt.browser_close_error = sanitise(error.message);
      }
    }
  }
  receipt.completed_at = new Date().toISOString();
  receipt.dropped_console_errors = droppedConsoleErrors;
  receipt.strict_console_status = consoleErrors.length ? 'failed' : receipt.shell ? 'passed' : 'not_observed';
  receipt.overall_clean_browser_acceptance = receipt.functional_status === 'passed' && receipt.strict_console_status === 'passed';
  await writeFile(path.join(out, engine + '-receipt.json'), JSON.stringify(receipt, null, 2) + '\n');
  return receipt;
}
export async function main(argv = process.argv.slice(2), env = process.env) {
  const opts = options(argv, env);
  if (opts.help) {
    console.log('node scripts/check_staff_service_browser.mjs --explorer-root /checkout/okf-explorer --service-url https://service.example --sdk-receipt /path/sdk-receipt.json --deployment /path/deployment.json --output /new/output [--engines chrome,firefox,webkit] [--check-inputs]\nUse --check-inputs for offline receipt checks only. Existing output directories are never overwritten.'); return;
  }
  for (const key of ['service', 'sdk', 'deployment']) assert.ok(opts[key], `Supply ${key}`);
  const sdkBytes = await readFile(opts.sdk), deploymentBytes = await readFile(opts.deployment);
  const sdk = JSON.parse(sdkBytes), deployment = JSON.parse(deploymentBytes);
  const inputs = validateInputs(sdk, deployment, opts.service);
  if (opts.checkOnly) { console.log(JSON.stringify({ status: 'passed-inputs-only', network_used: false, context_id: inputs.expected.context_id, selected_records: inputs.expected.selected_records })); return; }
  assert.ok(opts.checkout && opts.output, 'Supply Explorer checkout and a fresh output directory');
  assert.ok(opts.engines.length > 0 && opts.engines.every(engine => engines.includes(engine)) && new Set(opts.engines).size === opts.engines.length, 'Use distinct supported browser engines');
  const playwright = createRequire(path.join(path.resolve(opts.checkout), 'apps/okf-explorer/package.json'))('@playwright/test');
  const out = path.resolve(opts.output); await mkdir(path.dirname(out), { recursive: true }); await mkdir(out);
  const relative = file => path.relative(root, path.resolve(file));
  const binding = {
    script: { path: path.relative(root, scriptPath), sha256: sha256(await readFile(scriptPath)) },
    sdk: { path: relative(opts.sdk), sha256: sha256(sdkBytes) }, deployment: { path: relative(opts.deployment), sha256: sha256(deploymentBytes) },
    runtime_commit: deployment.runtime_commit, runtime_worker_sha256: deployment.runtime_worker_sha256,
    site_version: deployment.site_version_number, sdk_reference_identity_is_not_browser_worker_attestation: true,
    response_observation: 'Read-only native fetch response cloning; no routing, request/response replacement or security-policy change. Driver/native digests recorded separately. Rendered text and full-package SDK hashes remain decisive.',
    request_pacing: { minimum_interval_ms: MINIMUM_CALL_INTERVAL_MS, scope: 'shared across all requested browser engines',
      measured_from: 'observed previous MCP request start', automatic_retries: false, rate_limit_response: 'retained as a functional failure' }
  };
  const results = [], pacer = createCallPacer();
  for (const engine of opts.engines) results.push(await observe(engine, playwright, inputs, binding, out, pacer));
  const summary = { schema: 'okf-staff-service-browser-run.v1', observed_at: new Date().toISOString(), binding,
    results: results.map(row => ({ browser: row.browser, functional_status: row.functional_status, strict_console_status: row.strict_console_status,
      overall_clean_browser_acceptance: row.overall_clean_browser_acceptance, receipt: row.browser + '-receipt.json' })),
    all_requested_engines_passed: results.every(row => row.overall_clean_browser_acceptance),
    all_three_engines_requested: engines.every(engine => opts.engines.includes(engine)),
    all_three_engines_observed: engines.every(engine => results.some(row => row.browser === engine && row.shell)),
    scope: 'Exact public compact evidence UI against separately retained SDK/deployment receipts; no AI-answer quality or specialist acceptance.' };
  await writeFile(path.join(out, 'run-summary.json'), JSON.stringify(summary, null, 2) + '\n');
  console.log(JSON.stringify(summary)); if (!summary.all_requested_engines_passed) process.exitCode = 1;
}
if (process.argv[1] && path.resolve(process.argv[1]) === scriptPath) main().catch(error => { console.error(sanitise(error.message)); process.exitCode = 1; });
