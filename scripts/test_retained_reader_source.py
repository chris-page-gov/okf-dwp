"""Keep old browser observations verifiable when the current candidate changes."""
import gzip
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest

from build_bundle import digest
from check_combined_reader_observations import retained_source


class RetainedSourceTests(unittest.TestCase):
    def fixture(self, root, *, duplicate=False, missing=False, link=False):
        directory = root / 'validation/combined-reader'
        target = directory / 'source-snapshots'
        target.mkdir(parents=True)
        buffer = io.BytesIO()
        rows = [{'path':'okf-explorer.json','bytes':2,'sha256':digest(b'{}')}]
        with tarfile.open(fileobj=buffer, mode='w') as archive:
            for _ in range(2 if duplicate else 1):
                if missing: continue
                entry = tarfile.TarInfo('okf-explorer.json')
                entry.size = 2
                if link: entry.type = tarfile.SYMTYPE; entry.linkname = '/etc/passwd'
                archive.addfile(entry, io.BytesIO(b'{}'))
        raw = gzip.compress(buffer.getvalue(), mtime=0)
        (target/'fixture.tar.gz').write_bytes(raw)
        binding = {'schema':'okf-combined-reader-retained-source.v1','source_commit':'a'*40,
                   'archive':'source-snapshots/fixture.tar.gz','archive_bytes':len(raw),
                   'archive_sha256':digest(raw),'source_files':rows}
        (directory/'retained-source.json').write_text(json.dumps(binding))
        return target/'fixture.tar.gz'

    def test_exact_archive_does_not_read_current_candidate(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); self.fixture(root)
            (root/'combined').mkdir();(root/'combined/okf-explorer.json').write_text('NEW CANDIDATE')
            _, files=retained_source(root)
            self.assertEqual(files['okf-explorer.json'],b'{}')

    def test_changed_archive_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);path=self.fixture(root);path.write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'archive changed'):retained_source(root)

    def test_missing_duplicate_and_link_members_rejected(self):
        for options in [{'missing':True},{'duplicate':True},{'link':True}]:
            with self.subTest(options=options), tempfile.TemporaryDirectory() as d:
                root=Path(d);self.fixture(root,**options)
                with self.assertRaises(ValueError):retained_source(root)


if __name__=='__main__': unittest.main()
