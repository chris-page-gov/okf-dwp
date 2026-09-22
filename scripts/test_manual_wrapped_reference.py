"""Frozen source regression for a wrapped citation mistaken for a paragraph.

The expected complete77161 span was frozen from source during concurrent repair
work; the first control failed against the pre-repair parser.
This tests one original page in isolation without changing its text. It does not
assert that paragraph77164 exists or establish any legal applicability.
"""
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = {'source_path': 'source/pages/dmg-vol13-ch77.json',
 'pages_sha256': 'f7c34c30310a5e1f4700fb00b291e2bdec89554a89d4c244a9762c16c7448f19',
 'pdf_sha256': '0528f2fb95ac3bd71bdff0d91cdaba5df76ab4260396ca99608c840004ff5708',
 'page': 28,
 'start_utf8': 185,
 'end_utf8': 822,
 'literal_sha256': '5a6734652466acc31368f1cfcb7ffbafcd7687cca531d3dbf68e4c93e2dcc58a',
 'literal': '77161 For the purposes of SPC, unless any of the exceptions in DMG 77117 - 77130 apply, '
            'the mixed-age\n'
            'couple, including parties to a polygamous marriage, would normally be treated as members '
            'of the same\n'
            '\n'
            'household, and therefore excluded from claiming SPC1. Instead, the UC rules apply so that, '
            'from the date\n'
            '\n'
            'on which any of the circumstances in DMG 77160 apply, the claimant may claim SPC 2. See '
            'DMG 77162 -\n'
            '77164 for further details.\n'
            '\n'
            '\n'
            'Note: See DMG 77100 – 77131 for detailed guidance on membership of the household.\n'
            '\n'
            '\n'
            '                                                                           1 SPC Regs, reg '
            '5(1)-(2); reg 5(5)\n'
            '\n'
            '\n',
 'false_body_line': '77164 for further details.',
 'expected_numbered_labels': ['77161', '77170', '77171'],
 'basis': 'Independent frozen-source reading before wrapped-reference parser repair. The source line '
          'continues See DMG77162-77164; following actual standalone reserved range is77162-77169.'}


class WrappedReferenceSourceControls(unittest.TestCase):
    def source(self):
        raw = (ROOT / FIXTURE['source_path']).read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), FIXTURE['pages_sha256'])
        extraction = json.loads(raw)
        self.assertEqual(extraction['source_sha256'], FIXTURE['pdf_sha256'])
        return extraction['pages'][FIXTURE['page']-1]['text']

    def test_source_identity_and_complete_expected_span(self):
        text = self.source()
        literal = text.encode()[FIXTURE['start_utf8']:FIXTURE['end_utf8']]
        self.assertEqual(literal.decode(), FIXTURE['literal'])
        self.assertEqual(hashlib.sha256(literal).hexdigest(), FIXTURE['literal_sha256'])
        self.assertIn('77164 for further details.', literal.decode())
        self.assertIn('Note: See DMG 77100', literal.decode())
        self.assertIn('reg 5(1)-(2); reg 5(5)', literal.decode())

    def test_wrapped_reference_is_not_a_new_numbered_body(self):
        from manual_structure import segment_source
        text = self.source()
        # One unchanged original source page, locally numbered1 for a bounded
        # parser control; provenance above retains its real PDF page28 identity.
        units, _ = segment_source('dmg', {'chapter':'77'}, [{'page':1,'text':text}])
        labels = [label for unit in units for label in unit['paragraph_labels']]
        self.assertEqual(labels, FIXTURE['expected_numbered_labels'])
        first = next(unit for unit in units if unit['paragraph_labels']==['77161'])
        self.assertEqual(first['text'],FIXTURE['literal'])
        self.assertEqual(''.join(unit['text'] for unit in units),text)


if __name__ == '__main__':
    unittest.main()
