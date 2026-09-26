# Read two Chapter 60 passages with source-linked help

This independent reading aid covers paragraphs 60025 and 60033 of the frozen Decision makers’ guide (DMG) Chapter 60. It helps a beginner inspect abbreviations and local references. It does not decide entitlement or give an award, and it does not establish what the current law requires.

## Try the bounded example

Open the [Chapter 60 reading-help manifest](../reading-help-ch60.json) in a compatible Explorer reading-help view. The public Explorer route is provisional until the exact merged revision has been checked in a browser. In paragraph 60025, compare condition **5.**, the letters **FTE**, and the following printed **5**. The abbreviation list expands FTE to “Full-Time Education”; the raised 5 points to local reference 5 on PDF page 4; the parenthesised DMG range is another manual pointer. These are three different jobs.

Then compare condition **6.**, **GB** and its following **6**. GB expands to “Great Britain”. The residence or presence conditions are pointed to in Chapter 07 Part 2, outside this pilot. The note on page 4 points to paragraph 60033, which continues from page 4 onto page 5.

In paragraph 60033, **WDisP** expands to “War Disablement Pension”. The raised 6 points to a local reference to regulation 3(1)(d). The later note says its meaning is **prescribed** and carries marker 13, pointing to regulation 3(2). The abbreviation expansion does not supply that legal definition. The regulation text and its applicable version are absent here. The additional printed `2` after reference 11 and mixed reference 12 are shown as unresolved source defects, without a guessed correction.

The manifest binds every displayed occurrence to the frozen document SHA-256, PDF page, passage identity and exact UTF-8 span in the extracted page. That lets the viewer reject a changed source or a plausible term appearing in another context. The PDF remains the typography check because the extracted text does not encode superscripts.

## What the review changed

The original 219 vocabulary and 31 citation proposals remain intact and model-authored. A separate overlay limits the candidate view to two paragraphs. It records that the original “living with” explanation attached a Chapter 11 pointer from an adult-increase passage to a different Child Benefit context on page 19; that association is excluded. The “prescribed” explanation is split so the regulation 3(2) pointer belongs only to the WDisP note, not the residence/presence condition. The qualifying-young-person proposal stays outside this two-paragraph view. The overlay now binds the explicit Chapter 16 pointer in paragraph 60100 Note 2 on page 23 as exact source support; using it in a later card still needs separate scope and review.

The original proposal hashes, source hashes and review dispositions are recorded in [the authored overlay](../domain-profile/reading-help/ch60.json). The [returned validation record](../research/ch60-reading-help/validation.json) checks proposal integrity; it was not specialist acceptance. The earlier [manual guide](source-led-manual-guide.md) explains why a page number alone is not a complete passage identity.

## Reproduce and next checks

```sh
uv sync --locked
uv run --locked python scripts/build_reading_help.py --check
uv run --locked python -m unittest discover -s scripts -p test_reading_help.py
```

The tests reject changed hashes, duplicate passage identity and wrong-context occurrence anchors, including CA, AP, “living with” and “prescribed”. Before extending beyond this pilot, freeze a held-out passage set, test occurrence and citation selection independently, inspect the excluded corrections with a qualified reviewer, and verify the exact merged manifest and Explorer revision in a public browser. Broader passage structure and all 40 staff-question evidence obligations remain open work.
