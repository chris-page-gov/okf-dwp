# Retained source bytes for the earlier browser observations

The archive preserves the 261 distinct combined-Reader files actually observed
by the existing local and public browser runs. Its source is immutable content
commit `9de52acf1db84b27f8933d80480eaa850e74fa33`.

These bytes were archived on 20 September 2026 before rebuilding the new
household candidate. Each file was checked against that commit's Git blob
identity before packaging. Tar members use sorted paths, zero timestamps and
regular-file mode; gzip uses a zero timestamp. The manifest in
[retained-source.json](../retained-source.json) records every source size and
SHA-256 plus the archive fingerprint.

This is a later archival operation, not a new browser observation. The original
observation times, failures, response hashes, screenshots and context packages
are unchanged. The offline verifier checks them against these exact source
bytes, independently of today's `combined/` candidate. Its result explicitly
says that the current candidate was not checked. A new candidate requires new
browser observations in a fresh directory.

No extraction to disk occurs during verification. The reader rejects unexpected,
duplicate, linked, missing or oversized archive members and checks total limits.
The archive is about 21 MiB because many original response files are already
compressed. This one-off retention cost preserves reproducibility; clients do
not download it when asking a question or opening the Reader.
