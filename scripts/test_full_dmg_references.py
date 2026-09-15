import unittest
from reconcile_full_dmg_references import paragraph_starts, resolution


class ReferenceReconciliationTests(unittest.TestCase):
    def test_body_labels_preserve_width_and_reject_contents_ranges(self):
        self.assertEqual(paragraph_starts('071700 This is the source paragraph.\n071701 - 071799\n07170 Wrong width for chapter 7.\n', 7), [('071700', 0)])

    def test_chapter_and_reference_mentions_do_not_become_body_anchors(self):
        self.assertEqual(paragraph_starts('84351 Source body refers to DMG 85001.\n85001 Different chapter.\n', 84), [('84351', 0)])
        self.assertEqual(paragraph_starts('Please see DMG 84351.\n84351 - 84356\n', 84), [])

    def test_multiple_targets_remain_ambiguous(self):
        self.assertEqual(resolution([]), 'no-acquired-location-resolved')
        self.assertEqual(resolution([{}]), 'single-acquired-location-candidate')
        self.assertEqual(resolution([{}, {}]), 'ambiguous-acquired-locations')

    def test_wrapped_reference_continuations_are_not_paragraph_starts(self):
        self.assertEqual(paragraph_starts('42610 et seq).\n42611 for guidance about the source.\n', 42), [])
        self.assertEqual(paragraph_starts('48048 et seq. The amount is discussed elsewhere.\n', 48), [])


if __name__ == '__main__':
    unittest.main()
