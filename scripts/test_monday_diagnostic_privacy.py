import json
import unittest
from project_monday_diagnostic_privacy import redact,produce


class PrivacyTests(unittest.TestCase):
    def test_dynamic_identifier_keys_are_hashed_even_when_identifier_shaped(self):
        value={'events':[{'fields':{'wire_tool_inputs':{'OpaqueIdentifierABC123':{'checksum':'int'}},'estimated_tokens':'int'}}]}
        result=redact(value)
        self.assertNotIn('OpaqueIdentifierABC123',json.dumps(result));self.assertIn('estimated_tokens',json.dumps(result))

    def test_projection_is_labelled_and_binds_original_without_values(self):
        raw=b'{"fields":{"wire_tool_inputs":{"toolu_fixture":{"input":"str"}}}}'
        result=json.loads(produce(raw));self.assertFalse(result['privacy_projection']['original_retained_publicly'])
        self.assertNotIn('toolu_fixture',json.dumps(result));self.assertEqual(result['privacy_projection']['original_bytes'],len(raw))


if __name__=='__main__':unittest.main()
