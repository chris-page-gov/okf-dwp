#!/usr/bin/env node
/** Independently load every retained context through the bounded delivery contract. */
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const args = process.argv.slice(2);
const i = args.indexOf('--explorer-root');
assert(i >= 0 && args[i + 1], 'Usage: --explorer-root PATH [--delivery-root PATH]');
const explorer = resolve(args[i + 1]);
const j = args.indexOf('--delivery-root');
const deliveryRoot = j < 0 ? explorer : resolve(args[j + 1]);
const engineDir = resolve(explorer, 'apps/okf-explorer/src/lib/context');
const deliveryDir = resolve(deliveryRoot, 'apps/okf-explorer/src/lib/context');
const { reconstructContextPackage } = await import(pathToFileURL(resolve(deliveryDir, 'packageDelivery.ts')));
const { canonicalJson } = await import(pathToFileURL(resolve(engineDir, 'index.ts')));
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const output = resolve(root, 'evaluation/evidence-workbench');
const registry = JSON.parse(readFileSync(resolve(root, 'evaluation/staff-questions/cases.json')));
const manifest = JSON.parse(readFileSync(resolve(output, 'manifest.json')));
assert.equal(manifest.schema, 'okf-evidence-workbench.v1');
assert.equal(manifest.questions.length, 40);
assert.deepEqual(manifest.questions.map(row=>[row.id,row.question]),
  registry.cases.map(row=>[row.id,row.question]));
assert.equal(new Set(manifest.questions.map(row=>row.id)).size, 40);
for (const name of ['index.ts','corpus.ts','corpusV3.ts','types.ts'])
  assert.equal(manifest.source.engine_files[name], sha(readFileSync(resolve(engineDir,name))), `Engine drift: ${name}`);
assert.equal(manifest.source.delivery_sha256, sha(readFileSync(resolve(deliveryDir,'packageDelivery.ts'))), 'Delivery code drift');
assert.equal(manifest.source.registry_sha256, sha(readFileSync(resolve(root,manifest.source.registry))), 'Question registry drift');
assert.equal(manifest.source.corpus_sha256, sha(readFileSync(resolve(root,manifest.source.corpus))), 'Corpus drift');
const allowedPath = path => /^[a-z0-9._/-]+$/.test(path) && path.split('/').every(bit => bit && bit !== '.' && bit !== '..');
let parts=0,maxPart=0,totalRaw=0;
for (const row of manifest.questions) {
  assert(allowedPath(row.package.url) && row.package.url===`packages/${row.id}.json`);
  const raw = readFileSync(resolve(output,row.package.url));
  assert.equal(raw.length,row.package.bytes);
  assert.equal(sha(raw),row.package.sha256);
  assert(raw.length <= 524288);
  const pages=[];
  assert(row.package.parts.length > 0 && row.package.parts.length <= 128);
  for (const part of row.package.parts) {
    assert(allowedPath(part.url) && part.url.startsWith(`parts/${row.id}-`));
    const body=readFileSync(resolve(output,part.url));
    assert.equal(body.length,part.bytes);
    assert.equal(sha(body),part.sha256);
    assert(body.length <= 32768);
    maxPart=Math.max(maxPart,body.length);
    pages.push(JSON.parse(body)); parts++;
  }
  const reconstructed=await reconstructContextPackage(pages,row.package.sha256);
  assert.equal(reconstructed,raw.toString('utf8'));
  const context=JSON.parse(reconstructed);
  assert.equal(context.schema,'okf-governed-context.v1');
  assert.equal(context.question,row.question);
  assert.equal(context.ai_answer,null);
  assert.equal(context.evidence_status,'insufficient');
  assert.equal(canonicalJson(context),reconstructed);
  assert(context.selected.every(selection=>selection.record.access==='public'));
  assert.equal(context.binding.index_sha256,manifest.source.corpus_sha256);
  totalRaw+=raw.length;
}
console.log(JSON.stringify({status:'verified',cases:40,parts,max_part_bytes:maxPart,
  total_canonical_package_bytes:totalRaw,model_calls:0,network_calls:0}));
