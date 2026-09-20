import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, mkdir, readFile, writeFile, rm, symlink } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { options, fresh, packageIdentity, sha } from './check_public_household_reader.mjs';
const env = { OKF_EXPLORER_CHECKOUT: '/isolated/explorer', OKF_PUBLIC_HOUSEHOLD_COMMIT: 'a'.repeat(40), OKF_PUBLIC_HOUSEHOLD_APP_SHA256: 'b'.repeat(64), OKF_PUBLIC_HOUSEHOLD_OUTPUT: '/fresh/output' };
test('public host, explicit commit, expected fingerprint and fresh output are mandatory', () => {
  assert.equal(options(env).app, 'https://chris-page-gov.github.io/okf-explorer/explore/');
  for (const key of Object.keys(env)) { const value = {...env}; delete value[key]; assert.throws(() => options(value)); }
  for (const value of ['main', 'a'.repeat(39), 'https://example.invalid']) assert.throws(() => options({...env, OKF_PUBLIC_HOUSEHOLD_COMMIT: value}));
});
test('existing directories, files and symbolic links cannot overwrite observations', async () => {
  const dir = await mkdtemp(path.join(os.tmpdir(), 'public-household-'));
  try {
    const old = path.join(dir,'old'); await mkdir(old); await writeFile(path.join(old,'receipt'), 'retained');
    const file = path.join(dir,'file'); await writeFile(file,'retained'); const link = path.join(dir,'link'); await symlink(old,link);
    for (const target of [old,file,link]) await assert.rejects(fresh(target), /Fresh output/);
    assert.equal(await readFile(path.join(old,'receipt'),'utf8'),'retained');
  } finally { await rm(dir,{recursive:true,force:true}); }
});
test('packages bind the immutable manifest and preserve limits and insufficient status', () => {
  const bytes = Buffer.from(JSON.stringify({semantic_source_snapshot:'reader',bundle:{snapshot:'context'}}));
  const value = { question:'Question', ai_answer:null, evidence_status:'insufficient',bundle:{snapshot:'context'},binding:{index_sha256:sha(bytes)},budget:{max_bytes:4096},selected:[],relationships:[] };
  packageIdentity(value,'Question',{snapshot:'reader'},bytes);
  for (const change of [x=>x.ai_answer='invented',x=>x.evidence_status='sufficient',x=>x.binding.index_sha256='0'.repeat(64),x=>x.budget.max_bytes=1]) {
    const changed=structuredClone(value);change(changed);assert.throws(()=>packageIdentity(changed,'Question',{snapshot:'reader'},bytes));
  }
});
