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
        declarations=[edges[identity] for identity in self.catalogue['qualification_assertion_ids']]
        self.assertEqual(len(declarations),8)
        self.assertEqual({(e['source'],e['target']) for e in declarations},
                         {(care,household)}|{(household,page) for page in pages})
        for edge in declarations:
            self.assertEqual(edge['predicate'],DCT+'requires')
            self.assertEqual(edge['assertion_status'],'model-derived')
            self.assertEqual(edge['authority']['class'],'model-assisted')
            self.assertTrue(edge['provenance'][0]['locator'].endswith('/qualification-dependencies'))
        profiles={p['id']:p for p in self.profiles['profiles']}
        requirements={r['id']:r for r in self.index['requirements']}
        for cid in ('staff-012','staff-013'):
            profile=profiles[cid];requirement=requirements[profile['requirement_id']]
            self.assertEqual(set(profile['qualification_evidence_ids']),pages)
            self.assertEqual(profile['qualification_concept_ids'],[household])
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
