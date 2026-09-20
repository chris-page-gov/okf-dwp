"""Tamper controls for the offline critique verifier; no provider, network or Git."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
import check_monday_compact_critique as check


class CritiqueIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reader=check.Reader(check.ROOT);cls.seed={}
        for name in check.LIMITS:
            try:cls.seed[name]=reader.read(name)
            except FileNotFoundError:pass

    def fixture(self, root):
        for name,raw in self.seed.items():
            target=root/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)

    def change(self, root, path, mutation):
        target=root/path;value=json.loads(target.read_bytes());mutation(value)
        target.write_text(json.dumps(value,ensure_ascii=False))

    def test_actual_retained_critique_has_exact_census_and_one_failed_source_pair(self):
        result=check.validate()
        self.assertEqual(result['accepted_answers_checked'],7)
        self.assertEqual(result['claim_reviews_checked'],14)
        self.assertEqual(result['citation_diagnostics_checked'],21)
        self.assertEqual(result['additional_selected_records_checked'],4)
        self.assertEqual(result['retained_invalid_source_pairs'],1)
        self.assertFalse(result['semantic_opinions_validated']);self.assertFalse(result['specialist_accepted'])

    def test_changed_freeze_context_answer_results_receipt_or_helper_rejected(self):
        names=[check.FREEZE, check.ORIGINAL+'/contexts/staff-012.json',
            check.OUTPUT+'/codex-subscription/staff-012/attempt-01/answer.json',check.RESULTS,
            check.OUTPUT+'/codex-subscription/staff-012/attempt-01/receipt.json',
            'scripts/run_monday_compact_trials.py']
        for name in names:
            with self.subTest(name=name),TemporaryDirectory() as tmp:
                root=Path(tmp);self.fixture(root);target=root/name;target.write_bytes(target.read_bytes()+b' ')
                with self.assertRaisesRegex(ValueError,'fingerprint|hash|digest'):check.validate(root)

    def test_claim_and_review_census_paths_and_bindings_cannot_be_changed(self):
        changes=[lambda x:x['reviews'].pop(),lambda x:x['reviews'].__setitem__(0,x['reviews'][1]),
            lambda x:x['reviews'][1]['claim_reviews'].pop(),
            lambda x:x['reviews'][1]['claim_reviews'][0].__setitem__('claim_id','invented'),
            lambda x:x['reviews'][1].__setitem__('answer_path','.email.md'),
            lambda x:x['reviews'][1].__setitem__('context_sha256','0'*64),
            lambda x:x['reviews'][1].__setitem__('mechanical_status','failed-mechanical-controls')]
        for change in changes:
            with self.subTest(change=changes.index(change)),TemporaryDirectory() as tmp:
                root=Path(tmp);self.fixture(root);self.change(root,check.CRITIQUE,change)
                with self.assertRaises(ValueError):check.validate(root)

    def test_each_literal_diagnostic_is_recomputed_without_repairing_failed_locator(self):
        changes=[('exact_quote',False),('whitespace_normalised_match',False),('record_text_sha256','0'*64),
                 ('source_url','https://example.invalid/'),('locator','invented'),('source_provenance',[]),('exact_quote',1)]
        for field,value in changes:
            with self.subTest(field=field,value=value),TemporaryDirectory() as tmp:
                root=Path(tmp);self.fixture(root)
                self.change(root,check.CRITIQUE,lambda x:x['reviews'][1]['claim_reviews'][0]['citation_diagnostics'][0].__setitem__(field,value))
                with self.assertRaisesRegex(ValueError,'diagnostic'):check.validate(root)
        with TemporaryDirectory() as tmp:
            root=Path(tmp);self.fixture(root)
            self.change(root,check.CRITIQUE,lambda x:x['reviews'][2]['claim_reviews'][0]['citation_diagnostics'][3].__setitem__('source_pair_in_package',True))
            with self.assertRaisesRegex(ValueError,'diagnostic'):check.validate(root)

    def test_additional_evidence_must_be_selected_and_retain_its_hash_and_authority(self):
        for field,value in [('text_sha256','0'*64),('record_id','not-selected'),('authority',{'class':'official'}),('assertion_status','official'),('provenance',[])]:
            with self.subTest(field=field),TemporaryDirectory() as tmp:
                root=Path(tmp);self.fixture(root)
                self.change(root,check.CRITIQUE,lambda x:x['reviews'][2]['additional_selected_evidence_reviewed'][0].__setitem__(field,value))
                with self.assertRaisesRegex(ValueError,'Additional|additional'):check.validate(root)

    def test_human_acceptance_and_scalar_quality_scores_cannot_be_promoted(self):
        changes=[lambda x:x.__setitem__('human_review','accepted'),lambda x:x.__setitem__('specialist_accepted',True),
                 lambda x:x.__setitem__('answer_quality_score',0.99),lambda x:x.__setitem__('unsupported_claim_rate',0),
                 lambda x:x['reviews'][1].__setitem__('human_review','accepted'),
                 lambda x:x['reviews'][1]['claim_reviews'][0].__setitem__('human_acceptance','accepted'),
                 lambda x:x['reviews'][1]['claim_reviews'][0].__setitem__('quality_score',1)]
        for change in changes:
            with self.subTest(change=changes.index(change)),TemporaryDirectory() as tmp:
                root=Path(tmp);self.fixture(root);self.change(root,check.CRITIQUE,change)
                with self.assertRaises(ValueError):check.validate(root)

    def test_rebound_results_still_require_nine_attempts_and_truthful_pair_census(self):
        for change in [lambda x:x['attempts'].pop(),lambda x:x['pairs'][0].__setitem__('both_responses_retained',True)]:
            with TemporaryDirectory() as tmp:
                root=Path(tmp);self.fixture(root);self.change(root,check.RESULTS,change)
                digest=check.sha((root/check.RESULTS).read_bytes())
                self.change(root,check.CRITIQUE,lambda x:x.__setitem__('results_sha256',digest))
                with self.assertRaisesRegex(ValueError,'census'):check.validate(root)

    def test_prose_is_not_mistaken_for_machine_validated_semantic_truth(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp);self.fixture(root)
            self.change(root,check.CRITIQUE,lambda x:x['reviews'][1]['claim_reviews'][0].__setitem__('explanation','Changed fallible model opinion; requires human review.'))
            result=check.validate(root)
            self.assertFalse(result['semantic_opinions_validated']);self.assertEqual(result['human_review'],'pending')
            self.assertIsNone(result['answer_quality_score'])

    def test_missing_oversized_and_symlinked_files_rejected(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp);self.fixture(root);target=root/check.CRITIQUE;target.unlink()
            with self.assertRaises(FileNotFoundError):check.validate(root)
            target.symlink_to(root/check.RESULTS)
            with self.assertRaisesRegex(ValueError,'symlinks'):check.Reader(root).read(check.CRITIQUE)
            target.unlink()
            with target.open('wb') as stream:stream.truncate(check.LIMITS[check.CRITIQUE]+1)
            with patch.object(check.os,'open') as opened:
                with self.assertRaisesRegex(ValueError,'byte bound'):check.Reader(root).read(check.CRITIQUE)
                opened.assert_not_called()

    def test_root_parent_and_nested_directory_symlinks_rejected_before_read(self):
        with TemporaryDirectory() as tmp:
            base=Path(tmp);actual=base/'actual';actual.mkdir();child=actual/'child';child.mkdir();link=base/'link';link.symlink_to(actual,target_is_directory=True)
            for root in [link,link/'child']:
                with patch.object(check.os,'open') as opened:
                    with self.assertRaisesRegex(ValueError,'symlinks'):check.Reader(root)
                    opened.assert_not_called()
            (actual/'validation').symlink_to(child,target_is_directory=True)
            with self.assertRaisesRegex(ValueError,'symlinks'):check.Reader(actual).read(check.CRITIQUE)

    def test_unlisted_paths_rejected_before_open(self):
        reader=check.Reader(check.ROOT)
        for name in ['.email.md','../outside','/absolute',check.OUTPUT+'/other/answer.json']:
            with patch.object(check.os,'open') as opened:
                with self.assertRaisesRegex(ValueError,'allowlist'):reader.read(name)
                opened.assert_not_called()


if __name__ == '__main__':unittest.main()
