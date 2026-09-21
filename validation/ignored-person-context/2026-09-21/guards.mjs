import assert from 'node:assert/strict';
import { open, lstat, realpath, readdir } from 'node:fs/promises';
import { constants } from 'node:fs';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import path from 'node:path';
export const FILES = ['index.ts', 'corpus.ts', 'types.ts'];
export const sha = raw => createHash('sha256').update(raw).digest('hex');
export function exactFields(value, keys) {
  assert(value && typeof value === 'object' && !Array.isArray(value), 'Invalid object');
  assert.deepEqual(Object.keys(value).sort(), [...keys].sort(), 'Unrecognised manifest fields');
}
export function safeName(name) {
  assert(typeof name === 'string' && name && !path.isAbsolute(name) && !/[\\\0]/.test(name) && name.split('/').every(p => p && p !== '.' && p !== '..'), 'Unsafe relative path');
  return name;
}
export async function safeDirectory(directory) {
  const absolute = path.resolve(directory), root = path.parse(absolute).root;
  let current = root;
  for (const part of absolute.slice(root.length).split(path.sep).filter(Boolean)) {
    current = path.join(current, part); const stat = await lstat(current);
    assert(stat.isDirectory() && !stat.isSymbolicLink(), 'Directory or parent is a symlink or not a directory');
  }
  return absolute;
}
export async function boundedAt(directory, name, limit) {
  await safeDirectory(directory);
  const full = path.join(directory, safeName(name)); await safeDirectory(path.dirname(full));
  const stat = await lstat(full);
  assert(stat.isFile() && !stat.isSymbolicLink() && stat.size <= limit, 'Invalid retained file');
  assert((await realpath(full)).startsWith((await realpath(directory)) + path.sep), 'File escaped directory');
  const handle = await open(full, constants.O_RDONLY | constants.O_NOFOLLOW);
  try {
    const opened = await handle.stat(); assert(opened.isFile() && opened.size <= limit && opened.ino === stat.ino && opened.dev === stat.dev, 'Changed retained file');
    const buffer = Buffer.alloc(limit + 1); let length = 0;
    while (length < buffer.length) { const result = await handle.read(buffer, length, buffer.length - length, length); if (!result.bytesRead) break; length += result.bytesRead; }
    assert(length <= limit && length === opened.size, 'Retained file grew or changed during read');
    return buffer.subarray(0, length);
  } finally { await handle.close(); }
}
export function fromGit(repo, commit, name, limit = 32 * 1024 * 1024) {
  assert(/^[a-f0-9]{40}$/.test(commit), 'Source must be an exact commit');
  const ref = `${commit}:${safeName(name)}`;
  const size = Number(execFileSync('git', ['cat-file', '-s', ref], { cwd: repo, maxBuffer: 1024 }).toString().trim());
  assert(Number.isSafeInteger(size) && size >= 0 && size <= limit, 'Git blob exceeds byte limit');
  const raw = execFileSync('git', ['show', ref], { cwd: repo, maxBuffer: Math.max(1, size + 1) });
  assert.equal(raw.length, size); return raw;
}
export async function exactTree(directory, approved) {
  const found = [];
  async function walk(prefix = '') {
    await safeDirectory(path.join(directory, prefix));
    for (const name of await readdir(path.join(directory, prefix))) {
      const relative = prefix ? prefix + '/' + name : name, stat = await lstat(path.join(directory, relative));
      assert(!stat.isSymbolicLink(), 'Symlink in archive');
      if (stat.isDirectory()) { assert(approved.some(p => p.startsWith(relative + '/')), 'Unapproved archive directory'); await walk(relative); }
      else { assert(stat.isFile(), 'Invalid archive member'); found.push(relative); }
    }
  }
  await walk(); assert.deepEqual(found.sort(), [...approved].sort(), 'Unapproved archive file');
}
export async function admitEngines(directory, hashes) {
  exactFields(hashes, ['baseline', 'candidate']);
  for (const stage of ['baseline', 'candidate']) {
    exactFields(hashes[stage], FILES);
    for (const name of FILES) {
      assert(/^[a-f0-9]{64}$/.test(hashes[stage][name]), 'Invalid engine hash');
      assert.equal(sha(await boundedAt(directory, `engines/${stage}/${name}`, 2 * 1024 * 1024)), hashes[stage][name], 'Engine digest mismatch before import');
    }
  }
}
