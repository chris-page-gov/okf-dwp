import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync,mkdirSync,readFileSync,writeFileSync,existsSync,rmSync,symlinkSync,readdirSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {spawnSync} from 'node:child_process';
const source=readFileSync(resolve(dirname(fileURLToPath(import.meta.url)),'evaluate_original_acceptance.mjs'));
function fixture(){
 const root=mkdtempSync(resolve(tmpdir(),'okf-original-control-'));
 mkdirSync(resolve(root,'scripts'));writeFileSync(resolve(root,'scripts/evaluate_original_acceptance.mjs'),source);
 const prefix=resolve(root,'evaluation/manual-structure/original-acceptance');mkdirSync(prefix,{recursive:true});
 writeFileSync(resolve(prefix,'protocol.json'),JSON.stringify({schema:'okf-dwp-original-acceptance-protocol.v1',status:'draft-awaiting-source-freeze'}));
 return {root,prefix,run:(attempt='control')=>spawnSync(process.execPath,[resolve(root,'scripts/evaluate_original_acceptance.mjs'),'--explorer-root',root,'--attempt',attempt],{encoding:'utf8'})};
}
test('unfrozen protocol fails before importing engine or assembling context and retains failure',()=>{
 const f=fixture();try{const r=f.run();assert.notEqual(r.status,0);
  const failed=JSON.parse(readFileSync(resolve(f.prefix,'runs/control/failure.json')));
  assert.match(failed.error,/Freeze final source/);assert.deepEqual(failed.completed_rows,[]);
  assert.equal(failed.current.phase,'preflight');
 }finally{rmSync(f.root,{recursive:true,force:true});}
});
test('existing attempt is never overwritten by a new run',()=>{
 const f=fixture();try{const attempt=resolve(f.prefix,'runs/control');mkdirSync(attempt,{recursive:true});
  const marker=resolve(attempt,'retained.txt');writeFileSync(marker,'old receipt');
  const r=f.run();assert.notEqual(r.status,0);assert.equal(readFileSync(marker,'utf8'),'old receipt');
  assert.equal(existsSync(resolve(attempt,'evaluator.mjs')),false);
 }finally{rmSync(f.root,{recursive:true,force:true});}
});
test('attempt cannot escape the retained output directory',()=>{
 const f=fixture();try{const r=f.run('../outside');assert.notEqual(r.status,0);assert.equal(existsSync(resolve(f.prefix,'runs')),false);
 }finally{rmSync(f.root,{recursive:true,force:true});}
});
test('symlinked output parent is rejected before writing any receipt',()=>{
 const f=fixture(),external=mkdtempSync(resolve(tmpdir(),'okf-original-external-'));
 try{
  symlinkSync(external,resolve(f.prefix,'runs'),'dir');const r=f.run();
  assert.notEqual(r.status,0);assert.match(r.stderr,/Output ancestor must be a real directory/);
  assert.deepEqual(readdirSync(external),[]);
 }finally{rmSync(f.root,{recursive:true,force:true});rmSync(external,{recursive:true,force:true});}
});
