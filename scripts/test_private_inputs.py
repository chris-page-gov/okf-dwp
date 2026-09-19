from pathlib import Path
import subprocess
import tempfile
import unittest

from check_private_inputs import check


class PrivateInputTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.git('init', '--quiet')
        self.git('config', 'user.name', 'Private-input test')
        self.git('config', 'user.email', 'fixture@example.invalid')
        (self.root / '.gitignore').write_text('.email.md\n')
        self.git('add', '.gitignore')

    def git(self, *arguments):
        return subprocess.run(['git', '-C', str(self.root), *arguments], check=True, capture_output=True)

    def email(self, relative):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('Synthetic fixture only.\n')

    def test_ignored_untracked_root_and_nested_email_are_allowed(self):
        self.email('.email.md')
        self.email('nested/deeper/.email.md')
        self.assertEqual(check(self.root), [])

    def test_force_staged_root_and_nested_email_are_rejected(self):
        for relative in ('.email.md', 'nested/.email.md'):
            with self.subTest(path=relative):
                self.email(relative)
                self.git('add', '-f', relative)
                self.assertIn(f'Private correspondence is in the Git index: {relative}', check(self.root))

    def test_committed_email_is_rejected(self):
        self.email('nested/.email.md')
        self.git('add', '-f', 'nested/.email.md')
        self.git('-c', 'commit.gpgsign=false', 'commit', '--quiet', '-m', 'Synthetic fixture')
        self.assertIn('Private correspondence is in the Git index: nested/.email.md', check(self.root))

    def test_missing_ignore_rule_is_rejected(self):
        (self.root / '.gitignore').write_text('# No private-input rule\n')
        self.assertTrue(check(self.root))

    def test_root_only_ignore_rule_is_rejected(self):
        (self.root / '.gitignore').write_text('/.email.md\n')
        self.assertTrue(check(self.root))

    def test_later_root_negation_is_rejected(self):
        (self.root / '.gitignore').write_text('.email.md\n!.email.md\n')
        self.assertTrue(any('not ignored' in error for error in check(self.root)))

    def test_nested_tracked_ignore_override_is_rejected(self):
        (self.root / 'nested').mkdir()
        (self.root / 'nested/.gitignore').write_text('!.email.md\n')
        self.git('add', 'nested/.gitignore')
        self.assertIn('Private correspondence is not ignored at: nested/.email.md', check(self.root))


if __name__ == '__main__':
    unittest.main()
