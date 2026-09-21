"""Source and conditional-branch controls for the household authoring increment.

These controls read authored inputs and frozen evidence without writing outputs.
The regular staff compiler checks projection identities, hashes and the byte cap.
"""
import json
import unittest

from build_bundle import ROOT, load_yaml, digest


class HouseholdSemanticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.authoring=load_yaml(ROOT/'domain-profile/staff-semantic/concepts.yamlld')
        cls.nodes={n['key']:n for n in cls.authoring['@graph']}
        cls.profiles={p['id']:p for p in load_yaml(ROOT/'domain-profile/staff-semantic/profiles.yamlld')['profiles']}
        cls.inventory={d['id']:d for d in json.loads((ROOT/'source/full-dmg-2026-09-15/inventory.json').read_text())['documents']}
        cls.registry=json.loads((ROOT/'evaluation/staff-questions/cases.json').read_text())

    def evidence(self,key):
        return {(x['document_id'],x['page']):x for x in self.nodes[key].get('additional_sources',[])}

    def text(self,doc,page):
        return json.loads((ROOT/self.inventory[doc]['pages_path']).read_text())['pages'][page-1]['text']

    def test_no_partner_heading_and_whole_qualifications(self):
        source=self.text('dmg-vol13-ch78',25)
        self.assertLess(source.index('Claimants who have no partner'),source.index('78088'))
        self.assertLess(source.index('78088'),source.index('Claimants who have a partner'))
        definition=self.nodes['no-partner-disability-addition']['definition']
        for condition in ('no partner','all conditions','must actually be in payment',
                          'not a universal cash-payment test','transitional-protection exception',
                          'does not consolidate','funding status alone does not settle'):
            self.assertIn(condition,definition)
        selected=self.evidence('no-partner-disability-addition')
        for page in [11,12,15,16,17,21,22,23,25]:self.assertIn(('dmg-vol13-ch78',page),selected)
        self.assertIn('no-partner',self.nodes['severe-disability-addition']['definition'])

    def test_receipt_rule_keeps_award_period_and_partner_patient_qualifications(self):
        first=self.text('dmg-vol13-ch78',16);second=self.text('dmg-vol13-ch78',17)
        self.assertIn('before an award is made but in respect of which the allowance is awarded',first)
        self.assertIn('not covered by an award but in respect of which a payment is made in lieu of an award',first)
        self.assertIn('in the case of a claimant who has a partner',first)
        self.assertIn('but for being a patient for over 28 days',second)
        self.assertIn('which the award is first paid',second)
        definition=self.nodes['no-partner-disability-addition']['definition']
        self.assertIn('periods before an award is made but in respect of which it is awarded',definition)
        self.assertIn('periods not covered by an award but with payment in lieu of an award',definition)
        self.assertIn('in respect of caring for the claimant or partner, must actually be in payment',definition)
        self.assertIn('expressly concerns a claimant who has a partner',definition)
        self.assertIn('must not be transferred to a no-partner care-home case',definition)
        for page,anchor in [(16,'78060'),(17,'which the award is first paid')]:
            evidence=self.evidence('no-partner-disability-addition')[('dmg-vol13-ch78',page)]
            self.assertEqual(evidence['anchor'],anchor)
        source=self.text('dmg-vol13-ch78',15)
        self.assertIn('CA/UC carer element',source)
        self.assertIn('has to actually be in payment before it affects',source)

    def test_dated_receipt_support_is_required_without_consolidating_memo_terms(self):
        base='https://chris-page-gov.github.io/okf-dwp/id/page/'
        node=self.nodes['no-partner-disability-addition']
        memo_sources=[('dmg-memo-02-25-e03b36ce3e',5),('dmg-memo-06-25-5fee4f859a',3),
                      ('dmg-memo-06-25-5fee4f859a',9),('dmg-memo-01-26-0605724317',3)]
        for doc,page in memo_sources:
            self.assertIn((doc,page),self.evidence(node['key']))
            self.assertIn(base+doc+'/'+str(page).zfill(4),node['required_source_ids'])
        self.assertIn('21.10.24',self.text(memo_sources[0][0],5))
        self.assertIn('21.3.25',self.text(memo_sources[1][0],3))
        text=self.text(memo_sources[3][0],3)
        self.assertIn('15.03.26',text)
        self.assertIn('carer support component',text)
        self.assertIn('carer\n\nsupport payment component',text)
        self.assertFalse(self.nodes['severe-disability-addition'].get('required_concepts'))
        self.assertNotIn('Dated Scottish-benefit memoranda amend dependencies',
                         self.nodes['severe-disability-addition']['definition'])

    def test_one_and_both_partners_are_separate_conditional_branches(self):
        n=self.nodes['household-separation']
        for term in ('one partner','both enter permanently','non-exhaustive','none is decisive alone','not that an award automatically follows'):
            self.assertIn(term,n['definition'])
        for page in [7,19,21,23,24,25]:self.assertIn(('dmg-vol13-ch77',page),self.evidence('household-separation'))
        self.assertIn('77130',self.text('dmg-vol13-ch77',24))

    def test_temporary_housing_cost_conditions_have_continuations(self):
        for page in [53,54,55,56,57]:self.assertIn(('dmg-vol13-ch78',page),self.evidence('care-home-housing-costs'))
        n=self.nodes['care-home-housing-costs']
        for term in ('not the whole','intention to return','normally occupied part of the home not being let or sublet','52 weeks','temporary'):
            self.assertIn(term,n['definition'])
        self.assertEqual(n['source_candidates'],['source-c030'])
        self.assertIn('not allowed for claimants in a care home',n['definition'])
        self.assertIn('does not establish payment of care-home fees',n['definition'])
        for page in [24,25]:self.assertIn(('dmg-vol13-ch78',page),self.evidence('temporary-care-home'))
        self.assertIn('DLA payability ceases',self.nodes['temporary-care-home']['definition'])

    def test_mixed_age_rule_retains_migration_exception_and_dates(self):
        n=self.nodes['mixed-age-pension-credit']
        for phrase in ('15 May 2019','14 May 2019','8 June 2024','within three months','migration notice','not a general right'):
            self.assertIn(phrase,n['definition'])
        for page in [26,27,28,29,30]:self.assertIn(('dmg-vol13-ch77',page),self.evidence(n['key']))
        self.assertIn(('dmg-memo-04-24-282c3cef22',5),self.evidence(n['key']))
        self.assertIn('within 3 months',self.text('dmg-memo-04-24-282c3cef22',5))

    def test_scottish_dependencies_keep_dated_component_wording_uncertainty(self):
        n=self.nodes['scottish-disability-carer-dependencies']
        for phrase in ('21 October 2024','21 March 2025','15 March 2026','different component wording','requiring legal reconciliation'):
            self.assertIn(phrase,n['definition'])
        raw=self.text('dmg-memo-01-26-0605724317',3)
        self.assertIn('carer support component',raw)
        self.assertIn('carer\n\nsupport payment component',raw)

    def test_neutral_income_support_retains_case_sensitive_is(self):
        n=self.nodes['income-support']
        self.assertEqual(n['aliases'],[{'label':'IS','case_sensitive':True}])
        self.assertEqual(n['label'],'Income Support')
        self.assertEqual(self.authoring['alias_reassignments']['term/is-prisoner-applicable-amount'],['IS','Income Support'])
        self.assertIn('Note 2',n['definition'])
        self.assertNotEqual(n['@id'].split('/id/')[-1],'term/is-prisoner-applicable-amount')
        frozen=json.loads((ROOT/'context/corpus/base-index.json').read_text())
        old=next(r for r in frozen['records'] if r['route']=='term/is-prisoner-applicable-amount')
        self.assertIn('24212',old['text']);self.assertIn('24214',old['text'])

    def test_six_previously_unreachable_candidates_have_authored_paths(self):
        cases={c['id']:c for c in self.registry['cases']}
        expected={'staff-005':['source-c036','source-c039'],'staff-020':['source-c011'],
                  'staff-024':['source-c032'],'staff-025':['source-c034','source-c042']}
        for cid,targets in expected.items():
            seeds=self.profiles[cid]['when_all'];seen=set(seeds)
            for _ in range(2):
                seen|={r['target'] for r in self.authoring['relationships'] if r['source'] in seen}
            acquired={c for key in seen for c in self.nodes[key]['source_candidates']}
            for candidate in targets:
                self.assertIn(candidate,cases[cid]['candidate_ids'])
                self.assertIn(candidate,acquired,(cid,candidate))
        rea=next(r for r in self.authoring['relationships'] if r['source']=='iidb' and r['target']=='rea')
        self.assertIn('historical branch',rea['statement']);self.assertIn('5 April 1987',rea['statement'])
        self.assertIn('does not establish that IIDB ceases',rea['statement'])
        overlap=next(r for r in self.authoring['relationships'] if r['source']=='iidb' and r['target']=='overlap')
        self.assertIn('exact component and direction',overlap['statement'])

    def test_every_authored_extra_source_is_exact_and_hash_bound(self):
        checked=set()
        for node in self.nodes.values():
            for item in node.get('additional_sources',[]):
                if item['family']!='dmg':continue
                doc=self.inventory[item['document_id']]
                if doc['id'] not in checked:
                    self.assertEqual(digest((ROOT/doc['pdf_path']).read_bytes()),doc['sha256'])
                    self.assertEqual(digest((ROOT/doc['pages_path']).read_bytes()),doc['pages_sha256'])
                    checked.add(doc['id'])
                self.assertIn(item['anchor'],self.text(doc['id'],item['page']))

    def test_profile_refinement_does_not_close_review_or_invent_scope(self):
        cases={c['id']:c for c in self.registry['cases']}
        for cid in ['staff-012','staff-013','staff-014','staff-017','staff-018','staff-020']:
            p=self.profiles[cid]
            self.assertEqual(p['candidate_ids'],cases[cid]['candidate_ids'])
            self.assertEqual(p['ambiguities'],cases[cid]['ambiguities'])
            categories={o['category'] for o in p['obligations']}
            self.assertEqual(categories,{'evidence_closure_unverified','applicability_unresolved','legal_version_unreconciled','independent_review_pending','question_scope_unresolved'})
            self.assertEqual(next(o for o in p['obligations'] if o['category']=='independent_review_pending')['status'],'not-reviewed')
            self.assertEqual(next(o for o in p['obligations'] if o['category']=='evidence_closure_unverified')['status'],'candidate-evidence-only')


if __name__=='__main__':unittest.main()
