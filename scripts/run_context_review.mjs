#!/usr/bin/env node
/** Build an offline, source-bound comparison of independent evidence contexts. */
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdir, readFile, realpath, writeFile, readdir, lstat } from 'node:fs/promises';
import { dirname, resolve, sep } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { createContextRecovery } from './context_recovery.mjs';
import { createEvidenceSession } from './progressive_evidence_client.mjs';
import { renderContextReview } from './context_review_html.mjs';
import { categoriseInsufficiency } from './insufficiency_categories.mjs';
import { loadEvidenceRouteRuntime } from './load_evidence_route_runtime.mjs';
import { graphEvidenceManifest, readGraphEvidence, graphBytes, graphCanonical } from './graph_evidence_runtime.mjs';
import { collectGraphEvidence } from './graph_evidence_client.mjs';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const DEFAULT_OUTPUT = 'evaluation/truncation/review';
const DELIVERY_SHA256 = '5df92c0e7edf437f9ff23b25b9a812e947930dd2369f2e954104962f04c91d90';
const sha256 = value => createHash('sha256').update(value).digest('hex');
const json = value => JSON.stringify(value, null, 2) + '\n';

function parseArgs(args) {
  const options = {};
  for (let i = 0; i < args.length; i += 1) {
    const flag = args[i];
    if (flag === '--check') { assert(!options.check, 'Duplicate --check'); options.check = true; continue; }
    if (['--explorer-root', '--output-dir', '--question'].includes(flag)) {
      assert(args[i + 1] && !args[i + 1].startsWith('--'), `Missing value for ${flag}`);
      const key = flag.slice(2).replaceAll('-', '_');
      assert(!options[key], `Duplicate ${flag}`); options[key] = args[++i]; continue;
    }
    throw new Error(`Unknown argument: ${flag}`);
  }
  assert(options.explorer_root, 'Usage: node --experimental-strip-types scripts/run_context_review.mjs --explorer-root PATH [--question TEXT] [--output-dir PATH] [--check]');
  return options;
}

async function confinedFile(root, relative) {
  const full = await realpath(resolve(root, relative));
  assert(full.startsWith(root + sep), `Input leaves repository: ${relative}`);
  return readFile(full);
}

function contextRecord(context, label, query, collected) {
  const { catalogue, diagnostics, selected, relationships, summary, receipt } = collected;
  assert(summary.delivery_complete === true && summary.package_complete === true
    && typeof summary.package_sha256 === 'string', 'Progressive package collection did not verify complete delivery');
  assert.equal(summary.context_id, context.context_id);
  assert.equal(summary.evidence_status, context.evidence_status);
  assert.equal(summary.package_sha256, collected.receipt.completed_values[0].content_sha256);
  return {
    id: label.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, ''), label, query,
    context_id: context.context_id, evidence_status: context.evidence_status,
    assembly_truncated: context.budget.truncated,
    retrieval_truncated: context.retrieval?.truncated ?? false,
    selected_records: selected.length, relationships: relationships.length,
    package_bytes: catalogue.summary.full_package_bytes,
    delivery_complete: summary.delivery_complete, package_complete: summary.package_complete,
    package_sha256: summary.package_sha256,
    collection_artifact: `contexts/${label.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')}.json`,
    collection_sha256: sha256(json(collected)),
    delivery: summary.delivery, receipt, diagnostics,
    insufficiency_categories: categoriseInsufficiency([
      ...diagnostics.missing_evidence, ...(diagnostics.budget?.omissions ?? []), ...(diagnostics.retrieval?.omissions ?? []),
    ]),
    records: selected.map(row => ({ ...row.record, reasons: row.reasons, paths: row.paths })),
  };
}

async function collectContext(context, question, label, explorer) {
  const transport = {
    manifest: args => explorer.contextManifest(context, { offset: args.offset, max_bytes: args.delivery_bytes }),
    read: args => explorer.readContextEvidence(context, {
      context_id: args.context_id ?? context.context_id, section: args.section,
      ...(args.record_id === undefined ? {} : { record_id: args.record_id }),
      offset: args.offset, max_bytes: args.delivery_bytes,
    }),
  };
  const session = await createEvidenceSession({ transport, request: { question } });
  const collected = await session.collectPackage();
  return { review: contextRecord(context, label, question, collected), collectionText: json(collected) };
}

async function build(options) {
  const explorerRoot = await realpath(resolve(options.explorer_root));
  const engineDir = resolve(explorerRoot, 'apps/okf-explorer/src/lib/context');
  const deliveryPath = resolve(engineDir, 'delivery.ts');
  const deliveryRaw = await readFile(deliveryPath);
  assert.equal(sha256(deliveryRaw), DELIVERY_SHA256, 'Unsupported Explorer delivery.ts; review its protocol before import');
  const indexRaw = await readFile(resolve(engineDir, 'index.ts'));
  assert.equal(sha256(indexRaw), '689f8b8ab1cfb5ccc21b6dd9b5527fcad04de01f5876b44cbb2dc0240fceb010', 'Unsupported Explorer context engine index');
  const explorer = await import(pathToFileURL(deliveryPath).href);

  const policyRaw = await confinedFile(ROOT, 'domain-profile/context-recovery/policy.yamlld');
  const caseRaw = await confinedFile(ROOT, 'evaluation/out-of-sample/uc-disabled-child-supersession-001.json');
  const spec = JSON.parse(caseRaw);
  const question = options.question ?? spec.question;
  assert(typeof question === 'string' && question.trim().length > 0 && question.length <= 2000, 'Question must contain 1–2000 characters');
  const recovery = await createContextRecovery({ root: ROOT, explorerRoot });
  const assembled = await recovery.assemble(question, spec.observed_replay.budget);
  assert.equal(assembled.ai_answer, null); assert.equal(assembled.evidence_status, 'insufficient');

  const collections = [await collectContext(assembled.baseline, question, 'Baseline', explorer)];
  if (assembled.guarded) collections.push(await collectContext(assembled.guarded.context, question, 'Compound-alias guard', explorer));
  for (const route of assembled.followups) collections.push(await collectContext(route.context, route.query, `Follow-up: ${route.label}`, explorer));
  const graph = await loadEvidenceRouteRuntime({ root: ROOT, explorerRoot });
  const plan = await graph.runtime.plan(question);
  const wrap = value => ({ structuredContent: value, content: [{ type: 'text', text: JSON.stringify(value) }] });
  const sizer = value => graphBytes({ jsonrpc: '2.0', id: 'x'.repeat(128), result: wrap(value) });
  const graphCollection = await collectGraphEvidence({ question, expectedGraphSha256: graph.graphSha256, expectedEngineId: graph.engineId,
    transport: {
      manifest: async args => wrap(await graphEvidenceManifest(plan, { offset: args.offset, maxBytes: args.delivery_bytes }, sizer)),
      read: async args => wrap(await readGraphEvidence(plan, { ...args, maxBytes: args.delivery_bytes }, sizer)),
    } });
  const graphCollectionText = json(graphCollection);
  const { selected: _selected, relationships: _relationships, ...graphDiagnostics } = graphCollection.package;
  collections.unshift({ collectionText: graphCollectionText, review: {
    id: 'graph-guided-evidence', label: 'Graph-guided evidence', query: question,
    context_id: plan.plan_id, identity_kind: 'graph-plan', evidence_status: plan.evidence_status,
    assembly_truncated: false, retrieval_truncated: false, retrieval_complete: plan.retrieval_complete,
    selected_records: plan.selected.length, relationships: plan.relationships.length,
    package_bytes: Buffer.byteLength(graphCanonical(plan)), delivery_complete: graphCollection.summary.delivery_complete,
    package_complete: graphCollection.summary.package_complete, package_sha256: graphCollection.summary.package_sha256,
    collection_artifact: 'contexts/graph-guided-evidence.json', collection_sha256: sha256(graphCollectionText),
    delivery: graphCollection.summary.delivery, receipt: graphCollection.receipt,
    records: plan.selected.map(row => ({ ...row.record, reasons: row.reasons, paths: row.paths })),
    diagnostics: { ...graphDiagnostics, missing_evidence: plan.diagnostics }, insufficiency_categories: plan.insufficiency_categories,
  } });
  const contexts = collections.map(row => row.review);

  const scriptRaw = await readFile(fileURLToPath(import.meta.url));
  const clientRaw = await readFile(resolve(ROOT, 'scripts/progressive_evidence_client.mjs'));
  const adapterRaw = await readFile(resolve(ROOT, 'scripts/context_recovery.mjs'));
  const rendererRaw = await readFile(resolve(ROOT, 'scripts/context_review_html.mjs'));
  const output = {
    schema: 'okf-dwp-context-review.v1', question, status: 'candidate-not-deployed',
    identity: {
      case_id: options.question === undefined ? spec.id : null,
      budget_protocol_case_id: spec.id, case_sha256: sha256(caseRaw), policy_sha256: recovery.identity.policy_sha256,
      source_binding: recovery.identity.source_binding,
      engine: recovery.identity.engine, engine_index_sha256: sha256(indexRaw),
      explorer_delivery_sha256: sha256(deliveryRaw),
      runner_sha256: sha256(scriptRaw), progressive_client_sha256: sha256(clientRaw),
      adapter_sha256: sha256(adapterRaw),
      renderer_sha256: sha256(rendererRaw), question_sha256: sha256(question),
      insufficiency_classifier_sha256: sha256(await readFile(resolve(ROOT, 'scripts/insufficiency_categories.mjs'))),
      graph_engine_id: graph.engineId, graph_sha256: graph.graphSha256, graph_engine_admission: graph.engineAdmission,
      graph_client_sha256: sha256(await readFile(resolve(ROOT, 'scripts/graph_evidence_client.mjs'))),
    },
    recovery_plan: { ...recovery.plan(question), guarded_derivation: assembled.guarded?.derivation ?? null }, contexts,
    limitations: [
      'Independent local contexts are compared without combining their evidence into a new answer.',
      'Complete package delivery verifies integrity and identity; it does not establish legal applicability, evidence sufficiency or specialist approval.',
      'The original GOV.UK source, extracted text and project-authored interpretations retain their recorded authority and review status.',
      'This offline adapter makes no model or network calls and produces no individual entitlement decision or award calculation.',
    ],
    model_calls: 0, network_calls: 0, ai_answer: null,
  };
  const reportText = json(output);
  return { reportText, htmlText: renderContextReview(output), output,
    collectionFiles: Object.fromEntries(collections.map(row => [row.review.collection_artifact, row.collectionText])) };
}

const options = parseArgs(process.argv.slice(2));
const built = await build(options);
const outputDir = resolve(ROOT, options.output_dir ?? DEFAULT_OUTPUT);
const reportPath = resolve(outputDir, 'report.json');
const htmlPath = resolve(outputDir, 'index.html');
const expectedFiles = new Map([['report.json', built.reportText], ['index.html', built.htmlText], ...Object.entries(built.collectionFiles)]);
// Fresh output is deliberately required. A stale or foreign file must not be
// silently overwritten by an evaluation producer, or admitted by --check.
async function actualFiles(directory, prefix = '') {
  const files = [];
  for (const name of await readdir(directory)) {
    const relative = prefix + name, path = resolve(directory, name);
    const entry = await lstat(path);
    assert(!entry.isSymbolicLink(), 'Review artefact symlinks are forbidden');
    if (entry.isDirectory()) files.push(...await actualFiles(path, relative + '/'));
    else { assert(entry.isFile(), 'Review artefact must be a regular file'); files.push(relative); }
  }
  return files.sort();
}
if (options.check) {
  assert.deepEqual(await actualFiles(outputDir), [...expectedFiles.keys()].sort(), 'Unexpected or missing context review artefact');
  for (const [relative, expected] of expectedFiles) {
    assert.equal(await readFile(resolve(outputDir, relative), 'utf8'), expected, `Context review artefact is stale: ${relative}`);
  }
} else {
  try {
    assert.equal((await readdir(outputDir)).length, 0, 'Use a fresh output directory; existing review artefacts are preserved');
  } catch (error) { if (error.code !== 'ENOENT') throw error; }
  await mkdir(resolve(outputDir, 'contexts'), { recursive: true });
  for (const [relative, contents] of expectedFiles) await writeFile(resolve(outputDir, relative), contents, { flag: 'wx' });
}
process.stdout.write(json({ schema: built.output.schema, status: options.check ? 'current' : 'written',
  contexts: built.output.contexts.map(({ id, evidence_status, selected_records, relationships, package_bytes, package_sha256 }) =>
    ({ id, evidence_status, selected_records, relationships, package_bytes, package_sha256 })),
  model_calls: 0, network_calls: 0 }));
