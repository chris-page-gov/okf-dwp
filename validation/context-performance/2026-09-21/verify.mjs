import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
const root = path.dirname(fileURLToPath(import.meta.url));
const sha = data => createHash('sha256').update(data).digest('hex');
const manifest = JSON.parse(await readFile(path.join(root, 'artifacts.json')));
assert.equal(manifest.schema, 'okf-context-performance-artifacts.v1');
for (const [name, expected] of Object.entries(manifest.files)) {
  assert(!path.isAbsolute(name) && !name.split('/').includes('..'));
  const raw = await readFile(path.join(root, name));
  assert.equal(raw.length, expected.bytes, name);
  assert.equal(sha(raw), expected.sha256, name);
}
const report = JSON.parse(await readFile(path.join(root, 'comparison.json')));
assert.equal(report.inputs.runner_sha256, manifest.files['compare.mjs'].sha256);
assert.equal(report.inputs.overlay_sha256, manifest.files['overlay.json'].sha256);
assert.equal(report.inputs.registry_sha256, manifest.files['cases.json'].sha256);
assert.equal(report.inputs.manifest_sha256, manifest.files['manifest.json'].sha256);
for (const [name, digest] of Object.entries(report.inputs.current_engine_sha256)) {
  assert.equal(digest, manifest.files[`candidate/${name}`].sha256, name);
}
assert.equal(report.cases.length, 40);
assert.equal(report.cases.reduce((sum, row) => sum + row.before.hits.length, 0), 169);
assert.equal(report.cases.reduce((sum, row) => sum + row.after.hits.length, 0), 171);
assert.equal(report.cases.reduce((sum, row) => sum + row.after.expected, 0), 177);
assert.equal(report.cases.filter(row => row.identical_package).length, 38);
assert.deepEqual(report.summary.changed_cases, ['staff-008', 'staff-009']);
assert.equal(report.summary.ai_answers, 0);
for (const row of report.cases) for (const result of [row.before, row.after]) {
  assert.equal(result.evidence_status, 'insufficient');
  assert(result.bytes <= 524288);
}
assert.equal(report.timings.length, 30);
for (const row of report.timings) {
  assert.equal(row.peak_fetches, row.engine === 'before' ? 1 : 4);
  assert(row.elapsed_ms > 0 && row.package_bytes <= 524288);
}
console.log(`PASS: ${Object.keys(manifest.files).length} hash-bound files; 40 frozen comparisons; 30 artificial-delay timing observations.`);
