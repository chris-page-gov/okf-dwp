/** Governed local loader; the runtime itself remains portable to the Worker. */
import assert from 'node:assert/strict';
import { readFile, realpath } from 'node:fs/promises';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
import { validateRecoveryPolicy } from './context_recovery.mjs';
import { createGraphEvidenceRuntime, graphCanonical, graphSha } from './graph_evidence_runtime.mjs';

export async function loadEvidenceRouteRuntime({ root, explorerRoot }) {
  const directory = await realpath(resolve(root));
  const engine = resolve(await realpath(resolve(explorerRoot)), 'apps/okf-explorer/src/lib/context');
  const policy = validateRecoveryPolicy(JSON.parse(await readFile(resolve(directory, 'domain-profile/context-recovery/policy.yamlld'), 'utf8')));
  for (const [name, digest] of Object.entries(policy.engine.files)) {
    assert.equal(await graphSha(await readFile(resolve(engine, name), 'utf8')), digest, 'Graph resolver module drift: ' + name);
  }
  const resolver = await import(pathToFileURL(resolve(engine, 'index.ts')).href);
  const inputs = {};
  for (const name of ['graph_evidence_runtime.mjs', 'insufficiency_categories.mjs']) inputs[name] = await graphSha(await readFile(resolve(directory, 'scripts', name), 'utf8'));
  const engineAdmission = { schema: 'okf-graph-engine-admission.v1', modules: inputs, resolver: policy.engine };
  const engineId = 'urn:okf:graph-engine:sha256:' + await graphSha(graphCanonical(engineAdmission));
  const graphText = await readFile(resolve(directory, 'retrieval-graph/graph.json'), 'utf8');
  const graphSha256 = await graphSha(graphText);
  const runtime = await createGraphEvidenceRuntime({ graphText, graphSha256, engineId,
    resolveConcepts: resolver.resolveConcepts, validateContextIndex: resolver.validateContextIndex });
  return { runtime, graphText, graphSha256, engineId, engineAdmission };
}
