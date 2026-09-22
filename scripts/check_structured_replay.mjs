#!/usr/bin/env node
/** Replay the explicitly accepted local context trial; no network/model calls. */
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {dirname,resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const args=process.argv.slice(2);assert.equal(args.length,2);assert.equal(args[0],'--explorer-root');
const current=JSON.parse(readFileSync(resolve(root,'evaluation/manual-structure/context-probe/current.json')));
assert.equal(current.schema,'okf-dwp-context-probe-current.v1');assert.match(current.attempt,/^[a-z0-9-]{1,60}$/);
assert.equal(current.status,'accepted-with-recorded-limitations');
execFileSync(process.execPath,['--experimental-strip-types',resolve(root,'scripts/evaluate_structured_context.mjs'),
 '--explorer-root',resolve(args[1]),'--attempt',current.attempt,'--check'],{stdio:'inherit',cwd:root});
