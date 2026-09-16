import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { assertSourceProvenance } from './context_source_checks.mjs';

const root = new URL('../', import.meta.url);
const json = async (path) => JSON.parse(await readFile(new URL(path, root), 'utf8'));
const index = await json('full-dmg/context/assembly-index.json');
const inventory = await json('source/full-dmg-2026-09-15/inventory.json');
const record = index.records.find((row) => row.route === 'page/dmg-vol3-ch12/0002');
const document = inventory.documents.find((row) => row.id === 'dmg-vol3-ch12');
const expected = [
  { url: `${document.url}#page=2`, source_sha256: document.sha256, captured_at: document.observed_at },
  { url: `https://github.com/chris-page-gov/okf-dwp/blob/main/${document.pages_path}`,
    source_sha256: document.pages_sha256, captured_at: document.observed_at, locator: 'pages[1].text' }
];

test('the actual frozen source URLs and capture times are accepted', () => {
  assert.doesNotThrow(() => assertSourceProvenance(record, expected));
});
for (const ordinal of [0, 1]) {
  for (const [field, value] of [['url', 'https://example.invalid/not-the-dmg.pdf#page=999'], ['captured_at', '2000-01-01T00:00:00Z']]) {
    test(`changed ${field} on actual provenance entry ${ordinal} is rejected despite unchanged text and digests`, () => {
      const mutant = structuredClone(record);
      mutant.provenance[ordinal][field] = value;
      assert.throws(() => assertSourceProvenance(mutant, expected), /differs from frozen identity/);
    });
  }
}
test('capture time cannot be repurposed as a source publication date', () => {
  const mutant = structuredClone(record);
  mutant.provenance[0].source_date = document.observed_at;
  mutant.provenance[0].source_date_kind = 'publication';
  assert.throws(() => assertSourceProvenance(mutant, expected), /differs from frozen identity/);
});
