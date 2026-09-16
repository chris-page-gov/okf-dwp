"""Execute exact frozen provenance corruption controls in the ordinary suite."""
from pathlib import Path
import subprocess
import unittest


class ContextSourceIdentityTests(unittest.TestCase):
    def test_actual_source_identity_corruption_controls(self):
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run(
            ['node', '--test', 'scripts/context_source_checks.test.mjs'],
            cwd=root, text=True, capture_output=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
