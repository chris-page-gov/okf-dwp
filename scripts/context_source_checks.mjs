/** Exact source identity includes URL and capture time, not only the bytes. */
export function assertSourceProvenance(record, expected) {
  if (record.provenance.length !== expected.length) throw new Error(`Unexpected source provenance count: ${record.id}`);
  for (const required of expected) {
    const matches = record.provenance.filter((row) => Object.entries(required).every(([key, value]) => row[key] === value)
      && ['source_date', 'source_date_kind'].every((key) => Object.hasOwn(required, key) || !Object.hasOwn(row, key)));
    if (matches.length !== 1) throw new Error(`Source URL, capture date, locator or digest differs from frozen identity: ${record.id}`);
  }
}
