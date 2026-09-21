import assert from 'node:assert/strict';
import { test } from 'node:test';
import { mkdtemp, mkdir, writeFile, readFile, symlink, rm, realpath } from 'node:fs/promises';
import { execFileSync } from 'node:child_process';
import { tmpdir } from 'node:os';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { FILES, sha, admitEngines, boundedAt, exactTree, safeDirectory, safeName, fromGit } from './guards.mjs';
const here = path.dirname(fileURLToPath(import.meta.url));
async function fixture() {
  const root = await realpath(await mkdtemp(path.join(tmpdir(), 'okf-qualification-admission-'))), hashes = {};
  for (const stage of ['baseline','candidate']) {
    await mkdir(path.join(root,'engines',stage), { recursive: true }); hashes[stage] = {};
    for (const name of FILES) { const raw = `throw new Error('UNREVIEWED CODE EXECUTED');\n`; await writeFile(path.join(root,'engines',stage,name),raw); hashes[stage][name]=sha(raw); }
  }
  return { root, hashes };
}
test('engine digest admission rejects a changed module before an import can occur', async () => {
 const f=await fixture(); try { await writeFile(path.join(f.root,'engines/candidate/index.ts'),'changed'); await assert.rejects(admitEngines(f.root,f.hashes),/Engine digest mismatch before import/); } finally { await rm(f.root,{recursive:true}); }
});
test('exact reviewed engine set admits without executing module bodies', async () => {
 const f=await fixture(); try { await admitEngines(f.root,f.hashes); } finally { await rm(f.root,{recursive:true}); }
});
for (const target of ['root','parent','candidate']) test(`rejects ${target} directory symlinks`,async()=>{
 const f=await fixture(); const external=await realpath(await mkdtemp(path.join(tmpdir(),'okf-qualification-links-')));
 try {
  let selected=f.root;
  if(target==='root'){selected=path.join(external,'linked');await symlink(f.root,selected);}
  if(target==='parent'){await symlink(path.dirname(f.root),path.join(external,'linked'));selected=path.join(external,'linked',path.basename(f.root));}
  if(target==='candidate'){await rm(path.join(f.root,'engines/candidate'),{recursive:true});await symlink(path.join(f.root,'engines/baseline'),path.join(f.root,'engines/candidate'));}
  await assert.rejects(admitEngines(selected,f.hashes),/[Ss]ymlink/);
 } finally {await rm(f.root,{recursive:true});await rm(external,{recursive:true});}
});
test('rejects oversized and symlink files before reading them',async()=>{
 const f=await fixture();try{
  await writeFile(path.join(f.root,'too-large'),Buffer.alloc(17));await assert.rejects(boundedAt(f.root,'too-large',16),/Invalid retained file/);
  await symlink(path.join(f.root,'too-large'),path.join(f.root,'linked'));await assert.rejects(boundedAt(f.root,'linked',32),/Invalid retained file/);
 }finally{await rm(f.root,{recursive:true});}
});
test('archive allowlist rejects extra files and nested directories',async()=>{
 const f=await fixture();try{
  const approved=['baseline','candidate'].flatMap(s=>FILES.map(n=>`engines/${s}/${n}`));await exactTree(f.root,approved);
  await writeFile(path.join(f.root,'extra.mjs'),'extra');await assert.rejects(exactTree(f.root,approved),/Unapproved archive file/);
  await rm(path.join(f.root,'extra.mjs'));await mkdir(path.join(f.root,'extra'));await assert.rejects(exactTree(f.root,approved),/Unapproved archive directory/);
 }finally{await rm(f.root,{recursive:true});}
});
test('relative source paths and immutable commit syntax reject traversal or option injection',()=>{
 for(const name of ['../private.email.md','/absolute','a/../b','a\\b','a\0b'])assert.throws(()=>safeName(name),/Unsafe relative path/);
 assert.throws(()=>fromGit('/does-not-exist','--help','safe.json'),/exact commit/);
});
test('pending source protocol refuses before creating an output or executing engines',async()=>{
 const protocol=JSON.parse(await readFile(path.join(here,'protocol.json')));
 protocol.status='awaiting-final-source-commit';protocol.new_dwp_commit=null;
 const temp=await realpath(await mkdtemp(path.join(tmpdir(),'okf-qualification-pending-')));
 try{
  for(const name of ['compare.mjs','guards.mjs','metrics.mjs'])await writeFile(path.join(temp,name),await readFile(path.join(here,name)));
  await writeFile(path.join(temp,'protocol.json'),JSON.stringify(protocol));
  let failure;try{execFileSync(process.execPath,['--experimental-strip-types',path.join(temp,'compare.mjs'),'--dwp-root',temp,'--explorer-root',temp,'--output',path.join(temp,'attempt')],{encoding:'utf8',stdio:['ignore','pipe','pipe'],timeout:10000});}catch(error){failure=error;}
  assert(failure);assert.match(String(failure.stderr),/Protocol awaits final source approval/);await assert.rejects(safeDirectory(path.join(temp,'attempt')),/ENOENT/);
 }finally{await rm(temp,{recursive:true});}
});
test('fresh-output admission refuses existing directories, files and symlinks before engine imports',async()=>{
 const protocol=JSON.parse(await readFile(path.join(here,'protocol.json')));protocol.status='ready-for-frozen-source-comparison';protocol.new_dwp_commit='a'.repeat(40);
 const temp=await realpath(await mkdtemp(path.join(tmpdir(),'okf-qualification-existing-')));
 try{
  for(const name of ['compare.mjs','guards.mjs','metrics.mjs'])await writeFile(path.join(temp,name),await readFile(path.join(here,name)));
  await writeFile(path.join(temp,'protocol.json'),JSON.stringify(protocol));
  const directory=path.join(temp,'existing-directory'),file=path.join(temp,'existing-file'),linked=path.join(temp,'existing-link');
  await mkdir(directory);await writeFile(file,'preserved');await symlink(directory,linked);
  for(const selected of [directory,file,linked]){
   let failure;try{execFileSync(process.execPath,['--experimental-strip-types',path.join(temp,'compare.mjs'),'--dwp-root',temp,'--explorer-root',temp,'--output',selected],{encoding:'utf8',stdio:['ignore','pipe','pipe'],timeout:10000});}catch(error){failure=error;}
   assert(failure);assert.match(String(failure.stderr),/EEXIST/);assert(!String(failure.stderr).includes('engines'));
  }
  assert.equal(await readFile(file,'utf8'),'preserved');
 }finally{await rm(temp,{recursive:true});}
});
