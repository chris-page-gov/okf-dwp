# Chapter 60: reading-help examples

**Review draft — all explanations and display proposals are model-authored and unreviewed.** These examples explain vocabulary and navigation in the supplied frozen publications. They do not decide a claim or establish present legal applicability.

Exact source extracts appear in code blocks. They preserve the supplied extraction’s wording, spacing and line breaks. Its baseline digits do not encode superscript formatting: where a raised marker is shown separately below, that is a **visual transcription of the checked PDF**, not a substituted source quotation. Each source key resolves to its PDF path and SHA-256 in the source register at the end; page numbers are one-based physical PDF pages.

## 1. GB and its superscript: two different jobs

**Exact source — DMG abbreviations, PDF page 6, abbreviation table; exact key GB** (quote ex-01; source key `dmg-abbreviations-0db6c476b0`):

```text
GB      Great Britain
```

**Exact source — Chapter 60, PDF page 3, 60025, condition 6** (quote ex-02; source key `dmg-vol10-ch60`):

```text
6. satisfies prescribed conditions of residence or presence in GB6 (see DMG Chapter 07 Part 2).
```

**Exact source — Chapter 60, PDF page 4, 60025, local reference 6** (quote ex-03; source key `dmg-vol10-ch60`):

```text
6 s 70(4)
```


**Proposed reading help:** **GB** expands to **Great Britain**. On the PDF the following **⁶** is a raised source marker, not part of the abbreviation. The leading **6.** numbers the condition; the raised **⁶** points to local reference 6 on the continuation page. These numbering systems happen to use the same digit here.

Reference 6 prints only `s 70(4)`. Carrying the Act title from reference 1 into it is a proposed navigation normalisation: `SS CB Act 92, s 70(4)`. The text in parentheses is a separate **manual** cross-reference, to DMG Chapter 07 Part 2. Neither the full section nor that chapter part is supplied, so the residence/presence conditions are not reconstructed.

## 2. FTE: expand the letters, then retain the distinction

**Exact source — DMG abbreviations, PDF page 5, abbreviation table; exact key FTE** (quote ex-04; source key `dmg-abbreviations-0db6c476b0`):

```text
FTE        Full-Time Education
```

**Exact source — Chapter 60, PDF page 3, 60025, condition 5** (quote ex-05; source key `dmg-vol10-ch60`):

```text
5. is not in FTE5 (see DMG 60068 - 60081) and
```

**Exact source — Chapter 60, PDF page 4, 60025, local reference 5** (quote ex-06; source key `dmg-vol10-ch60`):

```text
5 s 70(3)
```


**Proposed reading help:** **Full-Time Education** is the exact dictionary expansion. The checked PDF shows **FTE⁵**. That 5 points to the fifth reference, `s 70(3)`; it does **not** mean “regulation 5”. The separate manual link leads to paragraphs 60068–60081.

Expansion is not a complete definition. The chapter distinguishes receiving FTE from being **treated as** receiving FTE. Keep the discussion of evidence, course descriptions, exceptions and the treated-as calculation together; do not reduce it to one abbreviated threshold. Those passages are in the pack, but the underlying legislative text is not.

## 3. WDisP: a supported expansion and a missing definition

**Exact source — DMG abbreviations, PDF page 16, abbreviation table; exact key WDisP** (quote ex-07; source key `dmg-abbreviations-0db6c476b0`):

```text
WDisP       War Disablement Pension
```

**Exact source — Chapter 60, PDF page 4, 60033, numbered alternative 3.4** (quote ex-08; source key `dmg-vol10-ch60`):

```text
3.4 a WDisP6 or
```

**Exact source — Chapter 60, PDF page 5, 60033, local reference 6** (quote ex-09; source key `dmg-vol10-ch60`):

```text
6 reg 3(1)(d)
```

**Exact source — Chapter 60, PDF page 5, 60033, note** (quote ex-10; source key `dmg-vol10-ch60`):

```text
Note: The meaning of WDisP is prescribed13.
```

**Exact source — Chapter 60, PDF page 5, 60033, local reference 13** (quote ex-11; source key `dmg-vol10-ch60`):

```text
13 SS (ICA) Regs, reg 3(2)
```


**Proposed reading help:** The exact expansion is **War Disablement Pension**. The PDF shows **WDisP⁶** in alternative 3.4, but **prescribed¹³** in the note. Marker 6 and marker 13 perform different navigation jobs: the former points to `reg 3(1)(d)`; the latter identifies `SS (ICA) Regs, reg 3(2)` as the definition dependency.

For reference 6, supplying `SS (ICA) Regs` from reference 3 is a **proposed inherited-title normalisation**, not an official expanded quotation. The text of regulation 3(2) is absent. Display “prescribed definition not included”, rather than treating the expansion as the full legal meaning. The entire paragraph 60033 spans pages 4–5, including the later payability/rate qualification.

## 4. Prescribed: a prompt to find the defining provision

**Exact source — Chapter 60, PDF page 5, 60033, note** (quote ex-12; source key `dmg-vol10-ch60`):

```text
Note: The meaning of WDisP is prescribed13.
```


**Proposed reading help:** Here, **prescribed** sends the reader to a meaning specified in the referenced provision. It is not permission to substitute an everyday definition. Use the adjacent source marker to locate that provision; show the absence of its text explicitly.

The residence/presence use in 60025 and the hospital-period use in 60050 have different dependencies. No general official definition of the word itself is supplied, and this proposed reading help does not create one.

## 5. SS CB Act 92: identify the document before the locator

**Exact source — DMG statutes, PDF page 3, full title / abbreviation table; SS CB Act 92** (quote ex-13; source key `dmg-statutes-23bca4e6a8`):

```text
Social Security Contributions and Benefits Act 1992                   SS CB Act 92
```

**Exact source — Chapter 60, PDF page 4, 60025, local reference 1** (quote ex-14; source key `dmg-vol10-ch60`):

```text
1 SS CB Act 92, s 70(1)
```


**Proposed reading help:** The title list supplies **Social Security Contributions and Benefits Act 1992** for **SS CB Act 92**. Treat the title and the following `s 70(1)` as separate components: the document, then the place within it. The title list is not the text of section 70(1), and it does not establish the applicable amended version.

## 6. s: preserve the table’s capitalisation

**Exact source — DMG abbreviations, PDF page 13, abbreviation table; exact key S** (quote ex-15; source key `dmg-abbreviations-0db6c476b0`):

```text
S        Section (of an Act)
```

**Exact source — Chapter 60, PDF page 4, 60025, local reference 6** (quote ex-16; source key `dmg-vol10-ch60`):

```text
6 s 70(4)
```


**Proposed reading help:** In this Act-reference context, read lower-case **s** as a section locator. The DMG table actually prints **S**, with the expansion **Section (of an Act)**. Matching the chapter’s lower-case form to that entry is a **proposed surface normalisation**, not a rewritten table quotation. The `(4)` remains part of the locator.

## 7. reg and Regs: a locator is not a title

**Exact source — DMG abbreviations, PDF page 12, abbreviation table; exact key Reg(s)** (quote ex-17; source key `dmg-abbreviations-0db6c476b0`):

```text
Reg(s)   Regulation(s)
```

**Exact source — Chapter 60, PDF page 5, 60033, local reference 13** (quote ex-18; source key `dmg-vol10-ch60`):

```text
13 SS (ICA) Regs, reg 3(2)
```


**Proposed reading help:** The table supplies **Regulation(s)** for **Reg(s)**. Here **Regs** forms part of the shortened instrument title, while **reg 3(2)** locates the cited provision within it. Lower-case singular `reg` and title-form `Regs` are proposed case/number surface matches to the table entry. Keep their different roles visible.

The statutory-instrument list names *The Social Security (Invalid Care Allowance) Regulations 1976 No. 409*. Do not replace the historical words “Invalid Care Allowance” in that title with the current chapter heading, and do not claim to have read the regulation’s text.

## 8. Sch: retain the parent document

**Exact source — DMG abbreviations, PDF page 13, abbreviation table; exact key Sch** (quote ex-19; source key `dmg-abbreviations-0db6c476b0`):

```text
Sch      Schedule (as in an Act)
```

**Exact source — Chapter 60, PDF page 2, 60003, reference 1** (quote ex-20; source key `dmg-vol10-ch60`):

```text
SS (C&P) Regs, reg 22(3) & Sch 6
```


**Proposed reading help:** **Schedule (as in an Act)** is the exact wording in the DMG table. The chapter also uses **Sch** after a regulations title, as this example shows. Therefore the display should retain the parent reference rather than assuming every Sch points into an Act. Do not rewrite the dictionary qualification to conceal that scope issue.

## 9. para: helpful navigation, but no supplied dictionary entry

**Exact source — Chapter 60, PDF page 2, 60003, reference 2** (quote ex-21; source key `dmg-vol10-ch60`):

```text
SS CB Act 92, s 70(9) & Sch 4, Part III, para 4
```


**Proposed reading help:** In this nested citation, **para 4** is proposed to be read as a paragraph locator within the named Schedule/Part. The attached DMG and ADM abbreviation lists do not provide an explicit **para** entry, so an “official expansion” field must remain empty.

This is different from **DMG 60025**, which identifies a paragraph in the manual. Keep the manual paragraph number and the legislation’s internal locator separate; neither substitutes for the other.

## 10. AP: the same letters, different manuals

**Exact source — DMG abbreviations, PDF page 1, abbreviation table; exact key AP** (quote ex-22; source key `dmg-abbreviations-0db6c476b0`):

```text
AP            Additional Pension
```

**Exact source — ADM abbreviations, PDF page 1, abbreviation table; exact key AP** (quote ex-23; source key `adm-list-of-abbreviations`):

```text
AP                 Assessment period
```


**Proposed reading help:** In the supplied **DMG** list, AP means **Additional Pension**. In the supplied **ADM** list, it means **Assessment period**. Choose the dictionary by manual and context; do not show a universal AP expansion. This is a comparison example, not a claim that AP occurs in the Chapter 60 inventory.

## A further scope check: quotation marks around AA

**Exact source — DMG abbreviations, PDF page 1, abbreviation table; exact key AA** (quote ex-24; source key `dmg-abbreviations-0db6c476b0`):

```text
AA            Attendance Allowance paid under s 64 of the SS (CB) Act 92
```

**Exact source — DMG abbreviations, PDF page 1, abbreviation table; exact key "AA"** (quote ex-25; source key `dmg-abbreviations-0db6c476b0`):

```text
"AA"          Attendance Allowance as defined in IS (Gen) Regs, reg 2(1) or JSA, reg 1(3)
```

**Exact source — ADM abbreviations, PDF page 1, abbreviation table; exact key “AA”** (quote ex-26; source key `adm-list-of-abbreviations`):

```text
“AA”               “Attendance Allowance” as defined in Reg 2 of the UC Regs
```


**Proposed reading help:** Preserve the quoted/unquoted form and the benefit/regulation qualifications. The quoted DMG entry points to IS/JSA definition provisions; the quoted ADM entry points to UC regulations. Those provisions are absent. The difference must remain visible rather than being collapsed into a single AA definition. Ordinary punctuation around a mention should not, by itself, be taken to establish the specially defined quoted sense.

## Reusable wording: preserve the qualification

**Exact source — Chapter 60, PDF page 6, 60040** (quote ex-27; source key `dmg-vol10-ch60`):

```text
60040 The claimant’s statement that the required number of hours are spent in caring should be
accepted without further enquiry unless there is good reason to doubt it.
```


**Proposed reading help for “unless”:** Keep the exception attached to the instruction. Here the text contains both a starting position and a reason for departing from it; displaying only “should be accepted” would omit part of the sentence.

**Exact source — Chapter 60, PDF page 5, 60033, concluding qualification; depends on the preceding alternatives** (quote ex-28; source key `dmg-vol10-ch60`):

```text
is payable provided that it is payable at a weekly rate of at least that specified in legislation 12.
```


**Proposed reading help for “provided that”:** Introduces a condition that remains attached to the preceding alternatives. Do not turn the preceding list into an unconditional statement, or supply the missing rate from another source.

**Exact source — Chapter 60, PDF page 20, 60089, purpose restriction** (quote ex-29; source key `dmg-vol10-ch60`):

```text
For CA purposes occupational

and personal pensions and PPF periodic payments should be regarded as earnings 1.
```


**Proposed reading help for “for CA purposes”:** Restricts the treatment to the stated purpose. It is not a statement about every benefit or an ordinary-language definition of earnings. The calculation guidance is outside this pack.

**Exact source — Chapter 60, PDF page 21, 60090, opening clause; historical savings provision** (quote ex-30; source key `dmg-vol10-ch60`):

```text
60090 Where, at 6.4.03, entitlement to CDI exists but is not payable for any reason, e.g. CDI is not
payable because of a spouse’s or civil partners earnings, payment of the CDI can be reinstated
```


**Proposed reading help for “entitlement” versus “payable”:** The source itself distinguishes entitlement existing from payment being available. Keep those states separate. This opening clause continues into conditions about reinstatement; it must not be used as a stand-alone rule, and its historical date is not a current-applicability finding.

## Do not hide the citation defects

**Exact source — Chapter 60, PDF page 5, 60033, end of local reference list** (quote ex-31; source key `dmg-vol10-ch60`):

```text
11 AJ v SSWP CG/1346/2018; 2
  Art.5 of Reg (EC) 883/2004; 12 reg 3(1) SS CB Act 92, Sch 4, Part V, para 2(a); 13 SS (ICA) Regs, reg 3(2)
```


**Review flags, not repairs:** An extra numbered **2** follows reference 11. It has no unambiguous separate body anchor and conflicts with the earlier reference 2. Reference **12** joins `reg 3(1)` to an Act reference without a clear separator or regulation parent. Retain both raw strings; do not renumber the extra entry, merge it into 11, or invent an instrument for 12. The Orders in references 9–10 retain their printed `reg` locators. The final `or` in alternative 8 also remains as printed.

Paragraph numbering has another collision: **60082** and **60083** each occur in the education section on PDF page 17 and again in the child-increase section on page 19. A safe navigation target therefore needs **source hash + PDF page + section + paragraph**, not the paragraph number alone.

## Source register

The listed dates are capture or publication-listing metadata only, never legal effective dates. The supporting PDF paths are relative to the original source ZIP. No source links were followed. Each quote’s provenance is also recorded in `coverage.json`, under `example_quote_provenance`.

### `dmg-vol10-ch60`

DMG Vol 10 Ch 60: Carer’s Allowance. File: `sources/dmg-vol10-ch60/pdf.pdf`. SHA-256: `ab9fed933c167b4ac18039204c3853c425731ffb4239022a11b41884caaee22a`.

### `dmg-abbreviations-0db6c476b0`

DMG abbreviations. File: `sources/dmg-abbreviations-0db6c476b0/pdf.pdf`. SHA-256: `aaa72d19e16b8817b5af5d90f3f7bdeb9921f4d226a929313641deae784b439b`.

### `dmg-statutes-23bca4e6a8`

DMG abbreviations for statutes. File: `sources/dmg-statutes-23bca4e6a8/pdf.pdf`. SHA-256: `505a5ef2f6b74af8f5d0ed2fc4e3e3ce6a5b904b22f3ead09a2e6c63beac4dce`.

### `dmg-si-abbreviations-eeb52291df`

DMG abbreviations for statutory instruments. File: `sources/dmg-si-abbreviations-eeb52291df/pdf.pdf`. SHA-256: `ee8edbb1927dbd798c9d7fb3bb120347447193008e21101c11341aa0ef2e8dad`.

### `adm-list-of-abbreviations`

List of abbreviations. File: `sources/adm-list-of-abbreviations/pdf.pdf`. SHA-256: `b7ca118176a5bb78d0892d08549f61787bd463930b9975b9d84e8af943ff4100`.


## Publication gate

These cards are proposals, not approved glossary entries. Review the source selection, the scope of each sense, all inherited-reference normalisations and missing dependencies before publication. Frequency is a prioritisation aid only: this pilot has not reproduced the inventory counts or made any finding about legal importance.
