import unittest
from pdf_structure_alignment import align_blocks

class AlignmentControls(unittest.TestCase):
    def test_cross_page_unicode_keeps_exact_byte_locations(self):
        pages=[{'text':'Heading\nA1001 A claimant’s ﬁrst'}, {'text':' condition.\n'}]
        result=align_blocks(pages,[{'role':'H2','text':'Heading'}, {'role':'P','text':'A1001 A claimant’s first condition.'}])
        self.assertEqual(result['matched_count'],2)
        block=result['blocks'][1]
        raw=''.join(p['text'] for p in pages).encode()
        self.assertEqual(raw[block['start']:block['end']].decode(),'A1001 A claimant’s ﬁrst condition.')

    def test_unmatched_is_not_fuzzy_repaired(self):
        result=align_blocks([{'text':'A rule about claimants.'}],[{'role':'P','text':'A rule about payments.'}])
        self.assertEqual(result['matched_count'],0)
        self.assertEqual(len(result['unmatched']),1)

    def test_parent_does_not_consume_children(self):
        result=align_blocks([{'text':'One two'}],[{'role':'L','text':'One two'},{'role':'P','text':'One'},{'role':'P','text':'two'}])
        self.assertEqual(result['matched_count'],3)

    def test_reordered_ambiguous_text_remains_unknown(self):
        result=align_blocks([{'text':'Repeat repeat end'}],[{'role':'P','text':'end'},{'role':'P','text':'repeat'}])
        self.assertEqual(len(result['unmatched']),1)
