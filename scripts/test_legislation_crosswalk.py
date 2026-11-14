#!/usr/bin/env python3
"""Regression tests for the deterministic legislation crosswalk."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from build_legislation_crosswalk import (
    CATALOGUE_MANIFEST,
    CHECKSUMS,
    CatalogueReader,
    CrosswalkError,
    ROOT,
    build_crosswalk,
)

LEGISLATION_ROOT: Path | None = None


class LegislationCrosswalkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.legislation_root = LEGISLATION_ROOT or (Path(os.environ['OKF_LEGISLATION_ROOT'])
            if os.environ.get('OKF_LEGISLATION_ROOT') else None)
        if cls.legislation_root is None:
            raise unittest.SkipTest('Supply --legislation-root or OKF_LEGISLATION_ROOT for the pinned crosswalk integration tests')
        cls.report = build_crosswalk(ROOT, cls.legislation_root)

    def test_current_hash_bound_crosswalk_and_explicit_limits(self):
        report = self.report
        self.assertEqual(report['schema'], 'okf-dwp-statutory-reference-crosswalk.v1')
        self.assertEqual(report['identities']['legislation_commit'],
                         report['identities']['expected_legislation_commit'])
        self.assertEqual(report['counts']['unique_exact_catalogue_work_records'], 20)
        self.assertEqual(report['counts']['unique_statutory_provision_targets'], 53)
        self.assertEqual(report['counts']['original_obligations_closed'], 0)
        self.assertEqual(report['obligation_policy']['closed_by_metadata_match'], False)
        self.assertTrue(report['identities']['catalogue_manifest']['verified_by_bundle_checksum'])
        self.assertTrue(all(row['matches_immutable_git_object']
                            for row in report['identities']['catalogue_selected_files']))
        self.assertTrue(all(row['path'].startswith('bundle/')
                            and row['git_commit'] == report['identities']['legislation_commit']
                            for row in report['identities']['catalogue_selected_files']))
        self.assertTrue(report['identities']['dwp_source_files'])
        self.assertTrue(all(row['git_commit'] == report['identities']['dwp_commit']
                            for row in report['identities']['dwp_source_files']))

    def test_work_metadata_is_not_provision_body(self):
        work = next(row for row in self.report['works']
                    if row['work_path'] == 'ukpga/2002/16')
        self.assertFalse(work['provision_body_present_in_work_record'])
        target = next(row for row in self.report['provisions']
                      if row['target'] == 'ukpga/2002/16/section/1')
        self.assertFalse(target['catalogue_has_provision_record_for_target'])
        capture = target['dwp_provision_capture']
        self.assertTrue(capture['captured'])
        self.assertTrue(capture['projection_only'])
        self.assertFalse(capture['raw_official_response_publicly_retained'])
        self.assertEqual(target['specialist_review_status'], 'not-approved-by-this-crosswalk')
        self.assertNotEqual(capture['status'], 'catalogue-work-body-captured')

    def test_case_law_stays_excluded_and_unresolved(self):
        case_law = self.report['case_law_excluded']
        self.assertGreater(case_law['existing_tribunal_decision_metadata'].__len__(), 0)
        self.assertTrue(all(row['judgment_body_acquired'] is False
                            for row in case_law['existing_tribunal_decision_metadata']))
        self.assertTrue(all(row['status'] == 'case-law-string-excluded-from-statutory-work-crosswalk'
                            for row in case_law['literal_mentions_in_source_citations']))
        self.assertTrue(all(row['status'] == 'case-law-unresolved-excluded-from-statutory-work-match'
                            for row in case_law['explicit_unresolved_notes']))
        self.assertFalse(any('R(' in row['target'] or 'R(' in row['work_path']
                             for row in self.report['provisions']))

    def test_invalid_work_id_rejected(self):
        reader = CatalogueReader(self.legislation_root)
        for invalid in ('ukpga/2002', 'ukpga/2002/not-a-number', 'https://example.test/ukpga/2002/16'):
            with self.subTest(invalid=invalid), self.assertRaises(CrosswalkError):
                reader.work(invalid)

    def test_catalogue_manifest_hash_mismatch_rejected(self):
        source = self.legislation_root
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for relative in (CATALOGUE_MANIFEST, CHECKSUMS):
                src = source / (f'bundle/{relative}' if relative.startswith('data/') else relative)
                dst = root / (f'bundle/{relative}' if relative.startswith('data/') else relative)
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(src, dst)
            manifest = root / 'bundle' / CATALOGUE_MANIFEST
            manifest.write_bytes(manifest.read_bytes() + b' ')
            subprocess.run(['git', 'init', '-q', str(root)], check=True)
            subprocess.run(['git', '-C', str(root), 'config', 'user.email', 'crosswalk-test@example.invalid'], check=True)
            subprocess.run(['git', '-C', str(root), 'config', 'user.name', 'Crosswalk test'], check=True)
            subprocess.run(['git', '-C', str(root), 'add', 'bundle'], check=True)
            subprocess.run(['git', '-C', str(root), 'commit', '-qm', 'fixture'], check=True)
            with self.assertRaisesRegex(CrosswalkError, 'differs from bundle/checksums.json'):
                CatalogueReader(root, expected_commit=None, verify_git_objects=False)

    def test_generated_json_is_byte_deterministic(self):
        encoded = json.dumps(self.report, ensure_ascii=False, indent=2) + '\n'
        output = ROOT / 'evaluation/retrieval-gate/legislation-crosswalk.json'
        self.assertEqual(output.read_text(encoding='utf-8'), encoded)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--legislation-root', type=Path, required=True)
    args = parser.parse_args()
    LEGISLATION_ROOT = args.legislation_root
    unittest.main(argv=[sys.argv[0]])
