# Independent source and projection checks

The manifest review checks the final 53,727-unit catalogue against frozen
extraction bytes, including every source span and the 75 preserved authored
units. It does not establish complete semantic segmentation.

The separate projection-retirement review covers the new fixed-root output
helper. Its reviewed caller hash predates the additive semantic integration;
the helper itself is unchanged. Installation is not transactional. A partial
write must pass a fresh build/check before publication. Neither review is a
remote deployment observation or specialist acceptance.
