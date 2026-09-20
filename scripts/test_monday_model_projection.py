"""Lossless repeated-value factoring controls; no providers or web retrieval."""
import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch
import project_monday_model_contexts as projection
from project_monday_model_contexts import REF,expand,factor,raw


class ProjectionTests(unittest.TestCase):
    def test_preserves_all_literals_conditions_governance_and_diagnostics(self):
        provenance={'url':'https://example.test/source','scope':'Only if the claimant has no partner. '*10}
        original={'selected':[{'record':{'id':str(i),'text':'Heading\nNo partner\nLiteral £1 and emoji 🏠','status':'unreviewed','provenance':provenance}} for i in range(5)],'ambiguities':['two variants'],'requirements':[provenance],'budget':{'truncated':True},'missing_evidence':['no full continuation']}
        context,pool=factor(original)
        self.assertTrue(pool);self.assertEqual(raw(expand(context,pool)),raw(original))
        self.assertLess(len(raw({'context':context,'values':pool})),len(raw(original)))

    def test_nested_references_and_dictionary_are_deterministic(self):
        shared={'long':'source scope '*40};original={'x':[shared,shared],'y':[shared,shared]}
        a=factor(original);self.assertEqual(a,factor(original));self.assertEqual(expand(*a),original)

    def test_reserved_input_and_missing_cycles_or_extra_values_rejected(self):
        with self.assertRaises(ValueError):factor({REF:'untrusted'})
        for context,pool in [({REF:'absent'},{}),({REF:'x'},{'x':{REF:'x'}}),({'text':'same'},{'unused':'extra'})]:
            with self.subTest(pool=pool),self.assertRaises(ValueError):expand(context,pool)

    def test_frozen_input_cannot_escape_or_exceed_byte_bound(self):
        with tempfile.TemporaryDirectory() as d,patch.object(projection,'ORIGINAL',Path(d)/'frozen'):
            root=Path(d);projection.ORIGINAL.mkdir();(root/'private').write_bytes(b'private')
            (projection.ORIGINAL/'link').symlink_to(root/'private')
            (projection.ORIGINAL/'large').write_bytes(b'large')
            for name,limit in [('../private',100),('link',100),('large',2)]:
                with self.subTest(name=name),self.assertRaises(ValueError):projection.frozen_bytes(name,limit)


if __name__=='__main__':unittest.main()
