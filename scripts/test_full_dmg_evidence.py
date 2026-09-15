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


if __name__ == '__main__':
    unittest.main()
