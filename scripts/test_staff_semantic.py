"""Control stale sources, fabricated governance, missing profiles and alias regressions."""
from copy import deepcopy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from build_bundle import ROOT, digest, load_yaml
from build_staff_semantic import (AUTHORING, OUTPUT, BASE_INDEX, DCT, SKOS,
    compile_staff_semantic, check_statutory_governance, qualification_dependencies)


class StaffSemanticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.outputs=compile_staff_semantic()
        cls.index=json.loads(cls.outputs[OUTPUT+'assembly-index.json'])
        cls.catalogue=json.loads(cls.outputs[OUTPUT+'catalogue.json'])
        cls.profiles=json.loads(cls.outputs[OUTPUT+'profiles.json'])

    def test_reproducible_and_additive(self):
        for name,raw in self.outputs.items():self.assertEqual((ROOT/name).read_bytes(),raw)
        old=json.loads((ROOT/BASE_INDEX).read_bytes())
        self.assertLessEqual(len(self.outputs[OUTPUT+'assembly-index.json']),8*1024*1024)
        self.assertTrue({r['id'] for r in old['records']} <= {r['id'] for r in self.index['records']})
        self.assertTrue({r['id'] for r in old['assertions']} <= {r['id'] for r in self.index['assertions']})
        old_evidence={r['id']:r for r in old['records'] if r['kind']=='evidence'}
        now={r['id']:r for r in self.index['records']}
        for key,row in old_evidence.items():self.assertEqual(row,now[key])

    def test_all_source_pages_bound_to_exact_pdf_and_text(self):
        records={r['id']:r for r in self.index['records']}
        self.assertIn('adm',{p['family'] for p in self.catalogue['source_pages']})
        for binding in self.catalogue['source_pages']:
            raw=(ROOT/binding['pages_path']).read_bytes()
            self.assertEqual(digest(raw),binding['pages_sha256'])
            page=json.loads(raw)['pages'][binding['page']-1]
            self.assertEqual(page['url'],binding['source_url'])
            self.assertEqual(records[binding['id']]['text'],page['text'])
            self.assertEqual(digest(page['text'].encode()),binding['literal_sha256'])
            self.assertEqual(records[binding['id']]['assertion_status'],'normalized')

    def test_every_occurrence_and_duplicate_preserved(self):
        registry=json.loads((ROOT/'evaluation/staff-questions/cases.json').read_bytes())
        self.assertEqual(len(self.profiles['profiles']),40)
        self.assertEqual(len({p['question'] for p in self.profiles['profiles']}),39)
        for case,profile in zip(registry['cases'],self.profiles['profiles']):
            for k in ('id','question','duplicate_of','candidate_ids','ambiguities','required_evidence'):
                self.assertEqual(case[k],profile[k])

    def test_obligations_are_labelled_absence_not_evidence(self):
        ids={r['id'] for r in self.index['records']}
        obligations={r['@id']:r for r in self.profiles['obligations']}
        for p in self.profiles['profiles']:
            self.assertEqual(p['evidence_status'],'insufficient')
            self.assertTrue(p['obligation_ids'])
            for iri in p['obligation_ids']:
                self.assertNotIn(iri,ids)
                self.assertFalse(obligations[iri]['is_source_evidence'])
                self.assertTrue(obligations[iri]['category'])
                self.assertTrue(obligations[iri]['resolution'])

    def test_household_qualification_group_and_trigger_paths(self):
        base='https://chris-page-gov.github.io/okf-dwp/id/'
        care=base+'staff-domain/care-home';household=base+'staff-domain/household-separation'
        pages={base+'page/77/'+str(n).zfill(4) for n in (7,19,21,23,24,25)}|{base+'page/78/0025'}
        edges={row['id']:row for row in self.index['assertions']}
        all_declarations=[edges[identity] for identity in self.catalogue['qualification_assertion_ids']]
        self.assertEqual(len(all_declarations),29)
        declarations=[edge for edge in all_declarations if edge['source'] in {care,household}]
        self.assertEqual(len(declarations),8)
        self.assertEqual({(e['source'],e['target']) for e in declarations},
                         {(care,household)}|{(household,page) for page in pages})
        for edge in all_declarations:
            self.assertEqual(edge['predicate'],DCT+'requires')
            self.assertEqual(edge['assertion_status'],'model-derived')
            self.assertEqual(edge['authority']['class'],'model-assisted')
            self.assertTrue(edge['provenance'][0]['locator'].endswith('/qualification-dependencies'))
        profiles={p['id']:p for p in self.profiles['profiles']}
        requirements={r['id']:r for r in self.index['requirements']}
        for cid in ('staff-012','staff-013'):
            profile=profiles[cid];requirement=requirements[profile['requirement_id']]
            self.assertTrue(pages<=set(profile['qualification_evidence_ids']))
            self.assertIn(household,profile['qualification_concept_ids'])
            self.assertTrue(pages|{household}<=set(requirement['required']))
            for page in pages:
                path=next(p for p in profile['qualification_paths'] if p['records'][-1]==page)
                self.assertEqual(path['seed'],care)
                self.assertIn(path['seed'],requirement['when_all'])
                self.assertEqual(path['records'],[care,household,page])
                self.assertIn(path,requirement['required_paths'])
                self.assertTrue(all(edges[i]['predicate']==DCT+'requires' for i in path['assertions']))
        self.assertEqual({p['id'] for p in profiles.values() if p.get('qualification_concept_ids')},
                         {'staff-012','staff-013'})

    def test_component_dependencies_keep_temporary_scope_separate(self):
        base='https://chris-page-gov.github.io/okf-dwp/id/'
        care=base+'staff-domain/care-home';housing=base+'staff-domain/care-home-housing-costs'
        temporary=base+'staff-domain/temporary-care-home'
        pages={base+'page/78/'+str(n).zfill(4) for n in (53,55,56,57,58)}
        edges={row['id']:row for row in self.index['assertions']}
        dependencies=[edges[identity] for identity in self.catalogue['qualification_assertion_ids']]
        self.assertEqual({e['target'] for e in dependencies if e['source']==housing},pages)
        self.assertEqual({e['target'] for e in dependencies if e['source']==temporary},
                         {base+'page/78/0024',base+'page/78/0025'})
        self.assertFalse(any(e['source']==care and e['target']==temporary for e in dependencies))
        node=next(n for n in self.catalogue['concepts'] if n['key']=='care-home-housing-costs')
        self.assertIn(base+'page/78/0054',node['evidence_ids'])
        self.assertNotIn(base+'page/78/0054',node['required_source_ids'])
        requirements={r['id']:r for r in self.index['requirements']}
        for profile in self.profiles['profiles']:
            if profile['id'] not in ('staff-012','staff-013'):continue
            required=requirements[profile['requirement_id']]
            self.assertEqual(set(profile['qualification_concept_ids']),
                             {base+'staff-domain/household-separation',housing,
                              base+'staff-domain/severe-disability-addition',
                              base+'staff-domain/no-partner-disability-addition'})
            self.assertTrue(pages<=set(profile['qualification_evidence_ids']))
            self.assertNotIn(temporary,required['required'])
            self.assertNotIn(base+'page/78/0024',required['required'])
            for page in pages:
                path=next(p for p in profile['qualification_paths'] if p['records'][-1]==page)
                self.assertEqual(path['records'],[care,housing,page])
                self.assertIn(path['seed'],required['when_all'])
                self.assertEqual(edges[path['assertions'][-1]]['predicate'],DCT+'requires')
                self.assertIn(path,required['required_paths'])

    def test_disability_support_keeps_the_overview_small_and_receipt_complete(self):
        base='https://chris-page-gov.github.io/okf-dwp/id/'
        overview=base+'staff-domain/severe-disability-addition'
        branch=base+'staff-domain/no-partner-disability-addition'
        overview_pages={base+'page/78/'+str(n).zfill(4) for n in (11,12,25)}|{
            base+'page/dmg-vol10-ch57/0005'}
        branch_pages={base+'page/78/'+str(n).zfill(4) for n in (11,12,15,16,17,25)}|{
            base+'page/dmg-memo-02-25-e03b36ce3e/0005',
            base+'page/dmg-memo-06-25-5fee4f859a/0003',
            base+'page/dmg-memo-06-25-5fee4f859a/0009',
            base+'page/dmg-memo-01-26-0605724317/0003'}
        records={r['id']:r for r in self.index['records']}
        declarations=[e for e in self.index['assertions'] if e['id'] in
                      set(self.catalogue['qualification_assertion_ids'])]
        for concept,pages in [(overview,overview_pages),(branch,branch_pages)]:
            actual=[e for e in declarations if e['source']==concept]
            self.assertEqual({e['target'] for e in actual},pages)
            self.assertEqual(len(actual),len(pages))
            self.assertTrue(all(records[e['target']]['kind']=='evidence' for e in actual))
        self.assertEqual(len(overview_pages|branch_pages),11)
        # No intermediary concept dependencies can pull every branch into the overview.
        self.assertFalse(any(e['source']==overview and records[e['target']]['kind']=='concept'
                             for e in declarations))
        for page in (21,22,23,24):
            self.assertNotIn(base+'page/78/'+str(page).zfill(4),branch_pages)
        node=next(c for c in self.catalogue['concepts'] if c['key']=='no-partner-disability-addition')
        self.assertTrue({base+'page/78/'+str(n).zfill(4) for n in (21,22,23)}<=set(node['evidence_ids']))

    def test_disability_profile_paths_are_conditional_investigation_not_claimant_facts(self):
        base='https://chris-page-gov.github.io/okf-dwp/id/'
        care=base+'staff-domain/care-home'
        keys=('severe-disability-addition','no-partner-disability-addition')
        nodes={n['key']:n for n in self.catalogue['concepts']}
        edges={e['id']:e for e in self.index['assertions']}
        requirements={r['id']:r for r in self.index['requirements']}
        frozen=json.loads((ROOT/'evaluation/model-comparison/household-2026-09-21/frozen/input-snapshots/assembly-index.json').read_bytes())
        previous={r['id']:r for r in frozen['requirements']}
        for row in self.index['requirements']:
            self.assertEqual(row['when_all'],previous[row['id']]['when_all'])
        for profile in self.profiles['profiles']:
            if profile['id'] not in ('staff-012','staff-013'):continue
            requirement=requirements[profile['requirement_id']]
            self.assertEqual(requirement['when_all'],[base+'term/pension-credit',care])
            self.assertTrue(any('Conditional branch investigation only' in v and
                                'does not establish that the claimant has no partner' in v
                                for v in requirement['limitations']))
            self.assertEqual(profile['evidence_status'],'insufficient')
            self.assertEqual(len(profile['obligation_ids']),5)
            for key in keys:
                concept=nodes[key]['@id']
                for page in nodes[key]['required_source_ids']:
                    expected=[care,concept,page]
                    path=next(p for p in profile['qualification_paths'] if p['records']==expected)
                    self.assertIn(path,requirement['required_paths'])
                    self.assertIn(path['seed'],requirement['when_all'])
                    self.assertEqual([edges[i]['predicate'] for i in path['assertions']],
                                     [SKOS+'related',DCT+'requires'])

    def test_new_receipt_pages_preserve_literal_bytes_and_sda_ambiguity(self):
        base='https://chris-page-gov.github.io/okf-dwp/id/'
        rows={r['id']:r for r in self.index['records']}
        for number,expected in [(16,'d460401ebba54c108a6211f3e2eaa02e8dffb75177de1efacc17b70b4996f293'),
                                (17,'8b22b67c0956490c0b399c262554da6cd8a8e781875f497b72fc42d53c89b706')]:
            row=rows[base+'page/78/'+str(number).zfill(4)]
            self.assertEqual(digest(row['text'].encode()),expected)
            self.assertEqual(row['assertion_status'],'normalized')
            self.assertEqual(row['authority']['class'],'derived')
        candidates=[r['id'] for r in self.index['records']
                    if {'label':'SDA','case_sensitive':True} in r.get('aliases',[])]
        self.assertEqual(set(candidates),{base+'staff-domain/sda',base+'staff-domain/severe-disability-addition'})
        # The current addition does not reinterpret any earlier whole-page evidence.
        frozen=json.loads((ROOT/'evaluation/model-comparison/household-2026-09-21/frozen/input-snapshots/assembly-index.json').read_bytes())
        for before in frozen['records']:
            if before['kind']=='evidence':self.assertEqual(rows[before['id']],before)

    def test_receipt_continuation_rejects_an_invented_paragraph_anchor(self):
        def mutation(data):
            node=next(n for n in data['@graph'] if n['key']=='no-partner-disability-addition')
            page=next(x for x in node['additional_sources'] if x['document_id']=='dmg-vol13-ch78' and x['page']==17)
            page['anchor']='78060'
        self.mutate_authoring('concepts.yamlld',mutation,'Source anchor absent')

    def test_component_wording_preserves_source_subject_and_heading(self):
        base='https://chris-page-gov.github.io/okf-dwp/id/'
        rows={row['id']:row for row in self.index['records']}
        housing=rows[base+'staff-domain/care-home-housing-costs']['text']
        self.assertNotIn('expenditure met by Housing Benefit',housing)
        self.assertNotIn('permits a trial stay',housing)
        self.assertIn('an element for which Housing Benefit may be payable',housing)
        self.assertIn('allows treatment as living in the former home, with housing costs allowed',housing)
        self.assertIn('any element for which HB may be payable',rows[base+'page/78/0058']['text'])
        temporary=rows[base+'staff-domain/temporary-care-home']['text']
        self.assertTrue(temporary.startswith('For a claimant with no partner whose normal home circumstances'))
        self.assertIn('residential care exceeds 28 days and DLA payability ceases',temporary)
        page=rows[base+'page/78/0024']['text']
        self.assertLess(page.index('Claimants who have no partner'),page.index('78084'))
        self.assertLess(page.index('78084'),page.index('Claimants who have a partner'))
        self.assertIn('The lower rate EASD is not appropriate',rows[base+'page/78/0025']['text'])

    def test_qualification_pages_preserve_both_partner_scope_and_continuation(self):
        base='https://chris-page-gov.github.io/okf-dwp/id/page/77/'
        pages={r['id']:r for r in self.index['records']}
        self.assertIn('Where both partners',pages[base+'0023']['text'])
        self.assertIn('Where one of a couple',pages[base+'0024']['text'])
        self.assertIn('But both partners',pages[base+'0024']['text'])
        self.assertIn('None of these facts on their own are',pages[base+'0024']['text'])
        self.assertIn('R(IS) 1/99',pages[base+'0024']['text'])
        self.assertTrue(pages[base+'0025']['text'].startswith('Bill and Agnes are members of the same household.'))
        self.assertIn('They do not have a domestic establishment',pages[base+'0025']['text'])

    def test_qualification_addition_preserves_all_open_obligations_and_candidate_ids(self):
        frozen=ROOT/'evaluation/model-comparison/household-2026-09-21/frozen/input-snapshots/assembly-index.json'
        previous={r['id']:r for r in json.loads(frozen.read_bytes())['requirements']}
        prefix='https://chris-page-gov.github.io/okf-dwp/id/obligation/'
        self.assertEqual(len(self.profiles['obligations']),203)
        for row in self.index['requirements']:
            before=previous[row['id']]
            self.assertEqual([i for i in row['required'] if i.startswith(prefix)],
                             [i for i in before['required'] if i.startswith(prefix)])
            if not row['id'].endswith(('/staff-012','/staff-013')):
                self.assertEqual(row['required'],before['required'])
        node=next(c for c in self.catalogue['concepts'] if c['key']=='household-separation')
        self.assertIn('https://chris-page-gov.github.io/okf-dwp/id/page/77/0020',node['evidence_ids'])
        self.assertNotIn('https://chris-page-gov.github.io/okf-dwp/id/page/77/0020',node['required_source_ids'])

    def test_rejects_invalid_qualification_source_selection(self):
        def node(data):return next(n for n in data['@graph'] if n['key']=='household-separation')
        for value,message in [
            ('not-a-list','Invalid required source IDs'),
            (['https://example.test/missing'],'outside the concept source selection'),
            (['https://chris-page-gov.github.io/okf-dwp/id/staff-domain/household-separation'],'outside the concept source selection'),
            (['https://chris-page-gov.github.io/okf-dwp/id/page/77/0024']*2,'Duplicate required source IDs')]:
            with self.subTest(value=value):
                self.mutate_authoring('concepts.yamlld',lambda d:node(d).update(required_source_ids=value),message)

    def test_rejects_unknown_or_unbacked_required_concept(self):
        for key,message in [('invented','Unknown required concept'),
                            ('household-separation','lacks an existing source-backed relationship')]:
            with self.subTest(key=key):
                self.mutate_authoring('concepts.yamlld',
                    lambda d:next(n for n in d['@graph'] if n['key']=='household-separation').update(required_concepts=[key]),message)

    def test_rejects_cyclic_or_non_evidence_qualification_dependency(self):
        nodes=[{'key':'a','@id':'urn:a','evidence_ids':['urn:e'],'required_concepts':['b']},
               {'key':'b','@id':'urn:b','evidence_ids':['urn:e'],'required_concepts':['a']}]
        edges={str(n):{'source':s,'target':t,'predicate':SKOS+'related'}
               for n,(s,t) in enumerate([('urn:a','urn:b'),('urn:b','urn:a')])}
        with self.assertRaisesRegex(ValueError,'Cyclic qualification dependency'):
            qualification_dependencies(nodes,edges,{'urn:e':{'kind':'evidence'}})
        nodes=[{'key':'a','@id':'urn:a','evidence_ids':['urn:e'],'required_source_ids':['urn:e']}]
        with self.assertRaisesRegex(ValueError,'Required source must be verified evidence'):
            qualification_dependencies(nodes,{}, {'urn:e':{'kind':'scope'}})

    def test_rejects_invalid_or_unreachable_profile_qualification(self):
        def case(data):return next(p for p in data['profiles'] if p['id']=='staff-012')
        for value,message in [(['missing'],'Unknown profile qualification concept'),
                              (['household-separation']*2,'Duplicate profile qualification concepts'),
                              (['partner'],'has no explicit dependencies')]:
            with self.subTest(value=value):
                self.mutate_authoring('profiles.yamlld',lambda d:case(d).update(qualification_concepts=value),message)
        self.mutate_authoring('profiles.yamlld',lambda d:case(d).update(when_all=['pip-daily-living']),
                              'unreachable from profile triggers')

    def test_source_backed_meanings_never_promoted(self):
        rows={r['id']:r for r in self.index['records']}
        assertions={r['id']:r for r in self.index['assertions']}
        for c in self.catalogue['concepts']:
            self.assertEqual(c['assertion_status'],'model-derived')
            self.assertTrue(c['evidence_ids'])
            self.assertTrue(all(rows[i]['kind']=='evidence' for i in c['evidence_ids']))
        for i in self.catalogue['new_assertion_ids']:
            self.assertEqual(assertions[i]['assertion_status'],'model-derived')
            self.assertEqual(assertions[i]['authority']['class'],'model-assisted')
            self.assertGreater(len(assertions[i]['provenance']),1)

    def test_legal_links_are_not_substantive_evidence(self):
        rows={r['id']:r for r in self.index['records']}
        self.assertEqual(len(self.catalogue['legal_reference_ids']),44)
        self.assertEqual(len(self.catalogue['legal_assertion_ids']),62)
        required={i for r in self.index['requirements'] for i in r['required']}
        for identifier in self.catalogue['legal_reference_ids']:
            self.assertEqual(rows[identifier]['kind'],'scope')
            self.assertEqual(rows[identifier]['review_status'],'reference-only-unreviewed')
            self.assertNotIn(identifier,required)
            self.assertIn('statutory text and applicability are not established',rows[identifier]['text'])

    def test_all_statutory_bodies_and_links_integrate_without_changes(self):
        overlay=json.loads((ROOT/'domain-profile/legal-bodies/context-overlay.json').read_bytes())
        records={r['id']:r for r in self.index['records']}; assertions={a['id']:a for a in self.index['assertions']}
        self.assertEqual(len(self.catalogue['statutory_body_ids']),20)
        self.assertEqual(len(self.catalogue['statutory_body_assertion_ids']),43)
        self.assertEqual(set(self.catalogue['statutory_body_ids']),{r['id'] for r in overlay['records']})
        self.assertEqual(set(self.catalogue['statutory_body_assertion_ids']),{a['id'] for a in overlay['assertions']})
        for row in overlay['records']:
            self.assertEqual(records[row['id']],row)
            check_statutory_governance(row,record=True)
        for row in overlay['assertions']:
            self.assertEqual(assertions[row['id']],row)
            self.assertIn(row['source'],records);self.assertIn(row['target'],records)
            check_statutory_governance(row)

    def test_missing_prior_staff_reference_is_separately_source_bound(self):
        identifier='https://chris-page-gov.github.io/okf-dwp/id/legal/ukpga/2002/16/section/4'
        self.assertEqual(self.catalogue['statutory_supplementary_reference_ids'],[identifier])
        record=next(r for r in self.index['records'] if r['id']==identifier)
        self.assertEqual(record['kind'],'scope');self.assertEqual(record['authority']['class'],'derived')
        self.assertEqual(record['review_status'],'reference-only-unreviewed')
        projection=ROOT/'source/legal-bodies-2026-09-21-v2/provisions/ukpga--2002--16--section--4.json'
        self.assertEqual(record['provenance'][0]['source_sha256'],digest(projection.read_bytes()))
        self.assertIn('http://www.legislation.gov.uk/ukpga/2002/16/section/4/2026-09-20',record['text'])
        self.assertNotIn(identifier,{i for r in self.index['requirements'] for i in r['required']})

    def test_six_case_body_census_preserves_every_obligation(self):
        coverage=json.loads((ROOT/'domain-profile/legal-bodies/coverage.json').read_bytes())
        profiles={p['id']:p for p in self.profiles['profiles']}
        self.assertEqual(len(self.profiles['obligations']),203)
        self.assertEqual(len(coverage['cases']),6)
        for case in coverage['cases']:
            profile=profiles[case['case_id']]
            self.assertEqual(profile['statutory_body_ids'],case['selected_body_ids'])
            self.assertEqual(profile['evidence_status'],'insufficient')
            self.assertTrue(profile['obligation_ids'])
        categories={o['category'] for o in self.profiles['obligations']}
        self.assertTrue({'independent_review_pending','legal_version_unreconciled','applicability_unresolved'}<=categories)

    def test_rejects_statutory_authority_or_provenance_promotion(self):
        body=json.loads((ROOT/'domain-profile/legal-bodies/context-overlay.json').read_bytes())
        for record in (True,False):
            source=body['records' if record else 'assertions'][0]
            mutations=[lambda r:r.update(assertion_status='official'),
                lambda r:r['authority'].update(**{'class':'legislation'}),
                lambda r:r['authority'].update(source='OKF-DWP'),
                lambda r:r['authority'].update(source='https://name:password@example.test/'),
                lambda r:r.update(provenance=[]),
                lambda r:r['provenance'][0].update(source_sha256=''),
                lambda r:r['provenance'][0].update(locator='')]
            if record:
                mutations += [lambda r:r.update(review_status='human-reviewed'),
                    lambda r:r['provenance'][0].update(literal_sha256='0'*64)]
            else: mutations += [lambda r:r.update(predicate='http://example.test/appliesTo')]
            for mutation in mutations:
                with self.subTest(record=record,mutation=mutation):
                    changed=deepcopy(source);mutation(changed)
                    with self.assertRaises(ValueError):check_statutory_governance(changed,record=record)

    def mutate_body_output(self,path,mutate,message):
        import build_legal_body_evidence
        from build_context_discovery import Inputs
        outputs=build_legal_body_evidence.build();changed=deepcopy(outputs)
        data=json.loads(changed[path]);mutate(data)
        changed[path]=(json.dumps(data,sort_keys=True,indent=2)+'\n').encode()
        original=Inputs.read
        def fake_read(inputs,relative,expected=None,size=None):
            raw=original(inputs,relative,expected,size)
            return changed[relative] if relative==path else raw
        with patch('build_legal_body_evidence.build',return_value=changed),patch.object(Inputs,'read',fake_read):
            with self.assertRaisesRegex(ValueError,message):compile_staff_semantic()

    def test_rejects_unverified_supplementary_endpoint(self):
        def changed(data):
            data['assertions'][0]['source']='https://chris-page-gov.github.io/okf-dwp/id/legal/unverified/invented'
        self.mutate_body_output('domain-profile/legal-bodies/context-overlay.json',changed,'not the verified provision identity')

    def test_rejects_absent_case_body_id(self):
        self.mutate_body_output('domain-profile/legal-bodies/coverage.json',
            lambda d:d['cases'][0]['selected_body_ids'].append('https://example.test/missing'),
            'Statutory profile references absent evidence')

    def test_rejects_changed_statutory_source_projection(self):
        target=ROOT/'source/legal-bodies-2026-09-21-v2/provisions/uksi--2002--1792--regulation--5.json'
        original=Path.read_bytes
        def changed(path):
            raw=original(path);return raw+b' ' if path==target else raw
        with patch.object(Path,'read_bytes',changed):
            with self.assertRaisesRegex(ValueError,'File changed|manifest binding'):compile_staff_semantic()

    def test_scope_compaction_preserves_specialised_scopes(self):
        old={r['id']:r for r in json.loads((ROOT/BASE_INDEX).read_bytes())['assertions']}
        current={r['id']:r for r in self.index['assertions']}
        compact=self.catalogue['scope_compaction']
        for identifier,row in old.items():
            if identifier in compact['assertion_ids']:
                self.assertEqual(row['scope'],compact['before'])
                expected=deepcopy(row);expected['scope']=compact['after']
                self.assertEqual(expected,current[identifier])
            else:self.assertEqual(row,current[identifier])

    def test_rejects_alias_reassignment_of_absent_phrase(self):
        self.mutate_authoring('concepts.yamlld',lambda d:d['alias_reassignments']['term/pc-prisoner-credit-rates'].append('invented phrase'),'Alias reassignment must exactly match')

    def mutate_authoring(self,filename,mutate,message):
        original=load_yaml
        def changed(path):
            result=deepcopy(original(path))
            if Path(path)==ROOT/AUTHORING/filename:mutate(result)
            return result
        with patch('build_staff_semantic.load_yaml',changed):
            with self.assertRaisesRegex(ValueError,message):compile_staff_semantic()

    def test_rejects_invented_source_anchor(self):
        self.mutate_authoring('concepts.yamlld',lambda d:next(x for x in d['@graph'] if x.get('additional_sources'))['additional_sources'][0].update(anchor='unrepresented invented anchor'),'Source anchor absent')

    def test_rejects_removed_case(self):
        self.mutate_authoring('profiles.yamlld',lambda d:d['profiles'].pop(),'cover all question')

    def test_rejects_unknown_trigger(self):
        self.mutate_authoring('profiles.yamlld',lambda d:d['profiles'][0]['when_all'].append('invented'),'Unknown/duplicate profile trigger')

    def test_rejects_fake_completed_review(self):
        self.mutate_authoring('profiles.yamlld',lambda d:d['profiles'][0]['obligations'][0].update(status='official-approved'),'Unknown or promoted obligation')

    def test_rejects_silent_review_gate_removal(self):
        self.mutate_authoring('profiles.yamlld',lambda d:d['profiles'][0].update(obligations=[o for o in d['profiles'][0]['obligations'] if o['category']!='independent_review_pending']),'silently close independent review')

    def test_rejects_official_authority(self):
        self.mutate_authoring('concepts.yamlld',lambda d:d.update(assertion_status='official'),'cannot acquire official authority')

    def test_rejects_changed_frozen_extraction(self):
        target=ROOT/self.catalogue['source_pages'][0]['pages_path'];original=Path.read_bytes
        def changed(path):
            raw=original(path)
            return raw+b' ' if path==target else raw
        with patch.object(Path,'read_bytes',changed):
            with self.assertRaisesRegex(ValueError,'Input digest mismatch'):compile_staff_semantic()


if __name__=='__main__':unittest.main()
