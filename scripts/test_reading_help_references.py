"""Source-identity controls for independent footer selection and navigation."""
import copy
import json
import unittest
from unittest.mock import patch
from build_reading_help_references import AUTHOR, ROOT, build, read_safe

class ReferenceTests(unittest.TestCase):
    def test_all_pairs_preserve_baseline_and_unresolved_meanings(self):
        old=json.loads(read_safe(ROOT,'reading-help-ch60.json'));new=json.loads(build())
        self.assertEqual(new['schema'],old['schema']);self.assertEqual(new['passages'],old['passages'])
        self.assertEqual(new['sources'],old['sources']);self.assertEqual(len(new['occurrences'])-len(old['occurrences']),20)
        self.assertEqual(new['occurrences'][:len(old['occurrences'])],old['occurrences'])
        cards={c['id']:c for c in new['cards']}
        for c in old['cards']:
            self.assertEqual(cards[c['id']]['body'],c['body']);self.assertEqual(cards[c['id']]['target'],c['target']);self.assertEqual(cards[c['id']]['review_status'],c['review_status'])
        self.assertEqual(cards['60033-extra-2']['occurrence_ids'],['60033-extra-2'])
        self.assertEqual(cards['60033-marker-12']['target']['status'],'unresolved')
    def test_equal_digits_are_different_occurrences(self):
        cards={c['id']:c for c in json.loads(build())['cards']}
        a=set(cards['60025-marker-6']['occurrence_ids']);b=set(cards['60033-marker-6']['occurrence_ids'])
        self.assertEqual(len(a),2);self.assertEqual(len(b),2);self.assertFalse(a&b)
    def test_swapped_same_digit_footer_rejected(self):
        a=json.loads(read_safe(ROOT,AUTHOR));x=next(x for x in a['links'] if x['card_id']=='60025-marker-6');y=next(x for x in a['links'] if x['card_id']=='60033-marker-6');x['footer_support']=copy.deepcopy(y['footer_support'])
        original=read_safe
        with patch('build_reading_help_references.read_safe',side_effect=lambda root,path: json.dumps(a).encode() if path==AUTHOR else original(root,path)):
            with self.assertRaisesRegex(ValueError,'existing exact support'):build()
    def test_changed_source_byte_offset_rejected(self):
        a=json.loads(read_safe(ROOT,AUTHOR));a['links'][0]['footer_support']['page_start_utf8']+=1
        original=read_safe
        with patch('build_reading_help_references.read_safe',side_effect=lambda root,path: json.dumps(a).encode() if path==AUTHOR else original(root,path)):
            with self.assertRaises(ValueError):build()

if __name__=='__main__':unittest.main()
