#!/usr/bin/env node
/** Verify frozen DWP passages, then execute the reusable Explorer context engine. */
import { readFile, writeFile, mkdir, realpath } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { assertSourceProvenance } from './context_source_checks.mjs';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const options = {};
const args = process.argv.slice(2);
for (let ordinal = 0; ordinal < args.length; ordinal += 1) {
  if (args[ordinal] === '--check') options.check = true;
  else if (['--explorer-root', '--case', '--output'].includes(args[ordinal])) {
    if (!args[ordinal + 1] || args[ordinal + 1].startsWith('--')) throw new Error(`Missing value for ${args[ordinal]}`);
    options[args[ordinal].slice(2)] = args[++ordinal];
  } else throw new Error(`Unknown option ${args[ordinal]}`);
}
const sha256 = (value) => createHash('sha256').update(value).digest('hex');
const bindings = new Map();
const cache = new Map();
async function frozenFile(relative) {
  if (typeof relative !== 'string' || path.isAbsolute(relative)) throw new Error('Source path must be repository-relative');
  const full = await realpath(path.resolve(ROOT, relative));
  if (!full.startsWith(ROOT + path.sep)) throw new Error('Source path leaves the repository');
  if (!cache.has(relative)) {
    const bytes = await readFile(full);
    cache.set(relative, bytes);
    bindings.set(relative, sha256(bytes));
  }
  return cache.get(relative);
}
const readJson = async (relative) => JSON.parse(await frozenFile(relative));
function requireValue(condition, message) { if (!condition) throw new Error(message); }
function pointer(document, selector) {
  if (selector === '') return document;
  requireValue(selector.startsWith('/'), 'Invalid metadata JSON pointer');
  let value = document;
  for (const part of selector.slice(1).split('/')) {
    requireValue(!/~[^01]|~$/.test(part), 'Invalid pointer escape');
    const key = part.replaceAll('~1', '/').replaceAll('~0', '~');
    requireValue(value !== null && typeof value === 'object' && Object.hasOwn(value, key), `Missing pointer ${selector}`);
    value = value[key];
  }
  return value;
}

const indexPath = 'full-dmg/context/assembly-index.json';
const selectorsPath = 'evaluation/context-assembly/source-selectors.json';
const index = await readJson(indexPath);
const selectors = await readJson(selectorsPath);
requireValue(selectors.schema === 'okf-dwp-context-source-selectors.v1', 'Unsupported source selector schema');
const inventory = await readJson(selectors.inventory);
const documents = new Map(inventory.documents.map((row) => [row.id, row]));
const sourceRoutes = await readJson(selectors.source_routes);
const routes = new Map();
const chapterRoutes = new Map(sourceRoutes.documents.map((source) => [source.route, source.id]));
for (const source of sourceRoutes.documents) source.page_routes.forEach((route, ordinal) => routes.set(route, { document_id: source.id, page: ordinal + 1 }));
const metadata = new Map(selectors.metadata_records.map((row) => [row.record_id, row]));
const census = await readJson(selectors.census);
const checks = [];
const verifiedDocuments = new Set();
for (const record of index.records.filter((row) => row.kind === 'evidence' || (row.kind === 'scope' && chapterRoutes.has(row.route)))) {
  const route = routes.get(record.route);
  let expectedText;
  let sourceHash;
  let sourcePath;
  let expectedProvenance;
  if (record.kind === 'scope' && chapterRoutes.has(record.route)) {
    const doc = documents.get(chapterRoutes.get(record.route));
    requireValue(Boolean(doc), `Unknown chapter metadata for ${record.id}`);
    requireValue(sha256(await frozenFile(doc.pdf_path)) === doc.sha256, `Chapter PDF hash mismatch: ${doc.id}`);
    expectedText = doc.title;
    sourceHash = sha256(await frozenFile(selectors.inventory));
    sourcePath = selectors.inventory;
    const ordinal = inventory.documents.findIndex((row) => row.id === doc.id);
    expectedProvenance = [
      { url: doc.url, source_sha256: doc.sha256, captured_at: doc.observed_at,
        locator: 'Frozen document identity; chapter metadata, not passage evidence' },
      { url: `https://github.com/chris-page-gov/okf-dwp/blob/main/${selectors.inventory}`,
        source_sha256: sourceHash, captured_at: doc.observed_at, locator: `/documents/${ordinal}/title`,
        literal_sha256: sha256(Buffer.from(expectedText, 'utf8')) }
    ];
  } else if (route) {
    const doc = documents.get(route.document_id);
    requireValue(Boolean(doc), `Unknown source document for ${record.id}`);
    if (!verifiedDocuments.has(doc.id)) {
      requireValue(sha256(await frozenFile(doc.pdf_path)) === doc.sha256, `PDF hash mismatch: ${doc.id}`);
      requireValue(sha256(await frozenFile(doc.pages_path)) === doc.pages_sha256, `Page artefact hash mismatch: ${doc.id}`);
      verifiedDocuments.add(doc.id);
    }
    const pages = await readJson(doc.pages_path);
    requireValue(pages.source_sha256 === doc.sha256 && pages.document_id === doc.id, `Page artefact identity mismatch: ${doc.id}`);
    const page = pages.pages[route.page - 1];
    requireValue(page.page === route.page, `PDF page ordinal mismatch: ${record.id}`);
    expectedText = page.text;
    sourceHash = doc.sha256;
    sourcePath = doc.pages_path;
    const literal = sha256(Buffer.from(expectedText, 'utf8'));
    expectedProvenance = [
      { url: `${doc.url}#page=${route.page}`, source_sha256: doc.sha256,
        captured_at: doc.observed_at, literal_sha256: literal },
      { url: `https://github.com/chris-page-gov/okf-dwp/blob/main/${doc.pages_path}`,
        source_sha256: doc.pages_sha256, captured_at: doc.observed_at,
        locator: `pages[${route.page - 1}].text`, literal_sha256: literal }
    ];
  } else {
    const selector = metadata.get(record.id);
    requireValue(Boolean(selector), `Evidence lacks a frozen source selector: ${record.id}`);
    const bytes = await frozenFile(selector.path);
    requireValue(sha256(bytes) === selector.sha256, `Metadata artefact hash mismatch: ${record.id}`);
    const captured = JSON.parse(bytes);
    expectedText = pointer(captured, selector.pointer);
    requireValue(typeof expectedText === 'string', `Selected metadata must be exact text: ${record.id}`);
    sourceHash = selector.sha256;
    sourcePath = selector.path;
    requireValue(typeof captured.base_path === 'string' && captured.base_path.startsWith('/government/'), 'Unexpected captured GOV.UK metadata path');
    expectedProvenance = [{ url: `https://www.gov.uk${captured.base_path}`, source_sha256: sourceHash,
      captured_at: census.retrieved_to, locator: selector.pointer,
      literal_sha256: sha256(Buffer.from(expectedText, 'utf8')),
      ...(selector.source_date_pointer ? { source_date: pointer(captured, selector.source_date_pointer),
        source_date_kind: selector.source_date_kind } : {}) }];
  }
  requireValue(record.text === expectedText, `Evidence text differs from frozen source: ${record.id}`);
  const literal = sha256(Buffer.from(expectedText, 'utf8'));
  requireValue(record.provenance.some((row) => row.source_sha256 === sourceHash && row.literal_sha256 === literal), `Evidence provenance differs from frozen bytes: ${record.id}`);
  assertSourceProvenance(record, expectedProvenance);
  checks.push({ record_id: record.id, route: record.route, source_path: sourcePath, source_sha256: sourceHash,
    literal_sha256: literal, verified_provenance: expectedProvenance, status: 'passed-exact-frozen-source' });
}
requireValue(checks.length > 0, 'No evidence records verified');
await frozenFile('scripts/evaluate_context_assembly.mjs');
await frozenFile('scripts/context_source_checks.mjs');
const sourceReceipt = {
  schema: 'okf-dwp-context-source-validation.v1', status: 'passed-exact-frozen-source-checks',
  method: 'Rehash original PDFs, page artefacts and metadata; compare whole page text, chapter inventory title or exact JSON-pointer text with each context source record. No new acquisition or legal grading.',
  index_sha256: bindings.get(indexPath), checks,
  inputs: [...bindings].sort(([left], [right]) => left.localeCompare(right)).map(([file, sha]) => ({ path: file, sha256: sha })),
  limitations: ['Exact source bytes do not establish current applicability, complete law or specialist acceptance.']
};
const sourceReceiptPath = path.join(ROOT, 'evaluation/context-assembly/source-check.json');
const sourceBytes = JSON.stringify(sourceReceipt, null, 2) + '\n';
if (options.check) requireValue(await readFile(sourceReceiptPath, 'utf8') === sourceBytes, 'Context source receipt is stale');
else { await mkdir(path.dirname(sourceReceiptPath), { recursive: true }); await writeFile(sourceReceiptPath, sourceBytes); }

const explorerRoot = path.resolve(options['explorer-root'] || path.join(ROOT, '../okf-explorer'));
const casePath = path.resolve(options.case || path.join(ROOT, 'evaluation/context-assembly/imprisonment-case.json'));
const outputPath = path.resolve(options.output || path.join(ROOT, 'evaluation/context-assembly/imprisonment-execution.json'));
const command = ['--experimental-strip-types', path.join(explorerRoot, 'scripts/run_context_evaluation.mjs'),
  '--index', path.join(ROOT, indexPath), '--case', casePath, '--output', outputPath];
if (options.check) command.push('--check');
const run = spawnSync(process.execPath, command, { cwd: explorerRoot, stdio: 'inherit', env: process.env });
if (run.error) throw run.error;
if (run.status === 0) {
  const receipt = JSON.parse(await readFile(outputPath, 'utf8'));
  requireValue(receipt.execution.inputs.index_sha256 === sourceReceipt.index_sha256,
    'The assembled index differs from the source-verified index; rerun after the producer is stable');
}
process.exitCode = run.status ?? 1;
