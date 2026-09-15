import unittest

from discover_full_dmg_evidence import page_candidates


class EvidenceBoundaryTests(unittest.TestCase):
    def test_revision_is_not_publication_or_commencement(self):
        text = 'Amendment 44 – Oct 2019\nExample: on 6 April 2026 a claimant applies.\n'
        dates = page_candidates(text)
        self.assertEqual([(d['value'], d['kind']) for d in dates], [('2019-10', 'stated-revision-date'), ('2026-04-06', 'date-mention')])
        self.assertTrue(all(not d['legal_effective_date_established'] and not d['source_publication_date_established'] for d in dates))

    def test_month_precision_and_conflicting_statements_survive(self):
        dates = page_candidates('Amendment 1 June 2016\nAmendment 2 February 2017')
        self.assertEqual([d['value'] for d in dates], ['2016-06', '2017-02'])
        self.assertEqual({d['precision'] for d in dates}, {'month'})

    def test_exact_spans_and_unresolved_citations(self):
        text = 'See DMG 84351–84356 and DMG Memo 11/20.\n 1 SPC Act 02, s 15; SPC Regs, Sch V\n'
        rows = page_candidates(text)
        self.assertEqual({r['kind'] for r in rows}, {'dmg-paragraph-reference', 'dmg-memo-reference', 'legal-reference-line-candidate'})
        self.assertTrue(all(text[r['start']:r['end']] == r['quote'] for r in rows))
        self.assertTrue(all('unresolved' in r['status'] for r in rows))

    def test_invalid_dates_and_capture_labels_do_not_become_revision(self):
        rows = page_candidates('31 February 2026\nCaptured 15 September 2026\n')
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['kind'], 'date-mention')

    def test_amendment_mentioned_in_prose_does_not_relabel_an_effective_date(self):
        rows = page_candidates('Amendment 15 contains a change effective from 1 April 2026.\nAmendment 16 – 6 May 2026')
        self.assertEqual([(r['kind'], r['value']) for r in rows], [('date-mention', '2026-04-01'), ('stated-revision-date', '2026-05-06')])

    def test_six_digit_chapter_seven_and_range_are_preserved(self):
        rows = page_candidates('See DMG 072791 and DMG 071756-071758.')
        self.assertEqual([(r['target_label'], r['range_end']) for r in rows], [('072791', None), ('071756', '071758')])
        self.assertTrue(all(r['kind'] == 'dmg-paragraph-reference' for r in rows))

    def test_concatenated_footnote_digits_are_not_truncated(self):
        rows = page_candidates('DMG 843511 and DMG 0717561 and DMG 071756-0717581')
        self.assertEqual([r['quote'] for r in rows], ['DMG 843511', 'DMG 0717561', 'DMG 071756-0717581'])
        self.assertTrue(all(r['kind'] == 'dmg-unresolved-digit-reference' for r in rows))

    def test_slash_memo_label_does_not_become_a_paragraph(self):
        rows = page_candidates('See DMG 05/25 and DMG Memo 11/20.')
        self.assertTrue(all(r['kind'] == 'dmg-memo-reference' for r in rows))


if __name__ == '__main__':
    unittest.main()
