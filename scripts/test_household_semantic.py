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

    def test_partner_lower_rate_conditions_keep_both_page_continuations(self):
        p12=self.text('dmg-vol13-ch78',12);p13=self.text('dmg-vol13-ch78',13)
        p14=self.text('dmg-vol13-ch78',14)
        self.assertLess(p12.index('Claimants who have a partner'),p12.index('78045'))
        self.assertIn('for only one of the partners',p12)
        self.assertIn('the other partner is certified as blind or severely sight impaired',p13)
        self.assertIn('but for being a patient for over 28 days',p13)
        self.assertTrue(p13.lstrip().startswith('1.5 AFIP and'))
        self.assertTrue(p14.lstrip().startswith('3.2 who the partners normally reside with'))
        # Do not silently harmonise this literal restriction with the wider benefit list.
        self.assertIn('the partner who is receiving “AA” or DLA as in 1.',p13)
        self.assertIn('the partner who is receiving “AA” or DLA as in 1.',p14)
        node=self.nodes['partner-disability-addition']
        for page in range(12,18):self.assertIn(('dmg-vol13-ch78',page),self.evidence(node['key']))

    def test_partner_higher_rate_reference_keeps_patient_item_and_footnote_distinct(self):
        source=self.text('dmg-vol13-ch78',14)
        self.assertIn('does not apply to claimants who have no partner',source)
        self.assertIn('either partner',source)
        self.assertIn('DMG 78060 2.1.',source)  # Captured flattened superscript is preserved.
        self.assertIn('lower rate of additional amount should be considered',source)
        definition=self.nodes['partner-disability-addition']['definition']
        self.assertIn('partner-patient provision in 78060(2)',definition)
        self.assertIn('does not exclude every form of treated receipt',definition)
        self.assertIn('CA/UC actual-payment qualification in 78057, in respect of caring for the claimant or partner',definition)
        self.assertIn('does not establish that partner status persists after care-home admission',definition)
        self.assertIn('in the case of a claimant who has a partner',self.text('dmg-vol13-ch78',16))
        self.assertIn('which the award is first paid',self.text('dmg-vol13-ch78',17))

    def test_partner_support_scope_matches_component_questions_and_keeps_unbounded_case_open(self):
        cases={c['id']:c for c in self.registry['cases']}
        for cid in ('staff-014','staff-017'):
            self.assertIn('rate/component effects',' '.join(cases[cid]['required_evidence']))
            self.assertEqual(self.profiles[cid]['qualification_concepts'],['partner-disability-addition'])
            obligation=self.profiles[cid]['obligations'][0]
            self.assertIn('qualifying disability-benefit receipt, residence and caring facts remain unknown',obligation['label'])
            self.assertIn('does not establish entitlement',obligation['label'])
        self.assertNotIn('qualification_concepts',self.profiles['staff-018'])
        self.assertTrue(any('all scenarios' in a.lower() for a in self.profiles['staff-018']['ambiguities']))

    def test_ignored_presence_is_distinct_from_normal_residence_and_couple_membership(self):
        ignored=self.nodes['severe-disability-ignored-persons']
        residence=self.nodes['severe-disability-normal-residence']
        self.assertIn('not a finding that a person is absent from the household for every purpose',ignored['definition'])
        self.assertIn('Assess normal residence separately',ignored['definition'])
        self.assertIn('separate from ignoring a person’s presence',residence['definition'])
        self.assertIn('from deciding whether partners remain one household',residence['definition'])
        self.assertIn('All residence and contractual facts remain unknown',residence['definition'])
        source=self.text('dmg-vol13-ch78',25)
        self.assertIn('do not normally reside with',source)
        self.assertNotIn('78087',ignored['definition'])
        for key in ('no-partner-disability-addition','partner-disability-addition'):
            self.assertEqual(self.nodes[key]['required_concepts'],['severe-disability-ignored-persons'])
        self.assertEqual(ignored['required_concepts'],['severe-disability-normal-residence'])
        self.assertFalse(residence.get('required_concepts'))
        for n in (ignored,residence):
            self.assertEqual(n['review_status'],'unreviewed-specialist-review-required')
            self.assertFalse(set(n['aliases'])&{'SDA','carer','child','partner','residence','household','non-dependant'})

    def test_ignored_carer_and_young_person_categories_keep_their_qualifications(self):
        n=self.nodes['severe-disability-ignored-persons'];text=n['definition']
        for phrase in ('a person aged under 18','highest- or middle-rate DLA care',
                       'standard- or enhanced-rate PIP or ADP daily living',
                       'consultant ophthalmologist','28 weeks after regained eyesight',
                       'engaged by a charitable or voluntary organisation which charges',
                       'that carer’s partner','a source-defined qualifying young person, or a child for Child Benefit purposes',
                       'neither education alone nor being under 20 is enough'):
            self.assertIn(phrase,text)
        source=' '.join(self.text('dmg-vol13-ch78',22).split())
        self.assertIn('lives with the claimant in order to care for the claimant or partner and',source)
        self.assertIn('makes a charge to the claimant or partner',source)
        self.assertIn('not a public authority or LA',self.text('dmg-vol13-ch78',6))
        for page in (9,10,11):self.assertIn(('dmg-vol13-ch77',page),self.evidence(n['key']))
        self.assertIn('receiving UC, JSA, IS or ESA',self.text('dmg-vol13-ch77',10))
        self.assertIn('will not satisfy the condition in DMG 77025',self.text('dmg-vol13-ch77',11))

    def test_first_time_carer_qualification_keeps_immediate_prior_condition_and_twelve_weeks(self):
        text=self.nodes['severe-disability-ignored-persons']['definition']
        for phrase in ('first joining the household to care for the claimant or partner',
                       'satisfying the additional-amount conditions immediately beforehand',
                       'first 12 weeks after joining'):
            self.assertIn(phrase,text)
        self.assertIn('joins the claimant’s household for the first time',self.text('dmg-vol13-ch78',22))
        self.assertIn('immediately before joining',self.text('dmg-vol13-ch78',22))
        self.assertIn('first twelve weeks',self.text('dmg-vol13-ch78',23))

    def test_commercial_and_joint_occupation_rules_keep_both_directions_and_date_exception(self):
        text=self.nodes['severe-disability-ignored-persons']['definition']
        for phrase in ('not a close relative','from that person to the claimant or partner',
                       'from the claimant or partner to that person','membership of that person’s household',
                       'legal liability','broadly comparable to a lodger’s',
                       'joint liability to the same landlord','person’s-partner branch',
                       'satisfying DMG 78078(3) or (4) as well as the timing condition',
                       'before 11 April 1988 or, if later, on or before first occupation',
                       'right-to-occupy date, not a later moving-in date'):
            self.assertIn(phrase,text)
        source=' '.join(self.text('dmg-vol13-ch78',23).split())
        self.assertIn('is a close relative who satisfies 3. or 4.',source)
        self.assertIn('before 11.4.88 or',source)
        self.assertIn('date they had the right to occupy the dwelling',source)
        self.assertIn('legal relationship not the blood',self.text('dmg-vol13-ch77',7))

    def test_shared_lives_and_padp_keep_exclusion_completion_and_specific_amendment(self):
        text=self.nodes['severe-disability-ignored-persons']['definition']
        self.assertIn('exclusion where other people cannot be ignored',text)
        self.assertIn('not a general award rule or a current rate',text)
        self.assertIn('Memo 02/25 paragraph 15',text)
        self.assertIn('21 October 2024',text)
        self.assertIn('separately from the memo’s claimant/partner and housing-deduction propositions',text)
        self.assertIn('Scottish Adult Disability Living Allowance wording requiring separate legal reconciliation',text)
        self.assertIn('partner-patient item must not be transferred automatically to a third person',text)
        self.assertIn('who cannot be ignored',self.text('dmg-vol13-ch78',23))
        self.assertIn('household facilities',self.text('dmg-vol13-ch78',24))
        self.assertIn('£395/week',self.text('dmg-vol13-ch78',24))
        memo=self.text('dmg-memo-02-25-e03b36ce3e',5)
        paragraph=memo[memo.index('15. DMG 78077'):memo.index('Deductions for non-dependants')]
        self.assertIn('From 21.10.24 PADP is added',paragraph)

    def test_normal_residence_has_complete_sharing_liability_and_overnight_carer_evidence(self):
        n=self.nodes['severe-disability-normal-residence'];text=n['definition']
        self.assertEqual(set(self.evidence(n['key'])),{('dmg-vol13-ch78',p) for p in range(17,22)})
        for phrase in ('temporary absence does not itself change the normal home',
                       'degree of sharing','only a bathroom, lavatory or communal area',
                       'same landlord','personal items are stored or meals prepared',
                       'merely passing through to a self-contained flat',
                       'contractual capacity and intention to create legal relations',
                       'connection between non-payment and ending the licence or lease',
                       'another liability to a third party','England-and-Wales scope',
                       'separate address, actual use and frequency, postal address and Council Tax registration'):
            self.assertIn(phrase,text)
        self.assertIn('A kitchen is not shared if a person',self.text('dmg-vol13-ch78',19))
        self.assertIn('the liability has to be to the same landlord',self.text('dmg-vol13-ch78',20))
        self.assertIn('what address the carer is registered at for CT purposes',self.text('dmg-vol13-ch78',21))

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
