# Reader endpoint catalogue boundary

The native Edge Reader rejected the frozen structured descriptor before loading:
108,412 endpoint labels exceeded the existing 100,000-entry limit. The
[failure record](failure.json) binds the observed descriptor, label catalogue and
producer. No source evidence was lost; the failing projection is retained in
commit `159da46e09c06d11e300a7d1d2568983e54025ee`.

The producer had copied every per-unit discovery alias into generic tags, which
also created a separate endpoint object. The correction preserves aliases in the
exact discovery card and a separate `discovery_aliases` field, and indexes them
in the existing navigation-metadata channel (mask 32). Source text remains in
mask 8. Result tags now contain the actual tags, while source headings and
concept facets remain unchanged. No alias becomes an asserted domain concept.

The producer now checks the consumer's existing 100,000-entry and 48 MiB retained
UTF-16-text ceilings before emitting a release. It reports the bound census;
it does not truncate rows or increase the limits. Fifteen synthetic Reader
controls pass, including exact alias/card/posting retention, a 100,001-entry
refusal and the text ceiling. A fresh complete projection and actual browser
observation remain required before declaring the repair delivered.
