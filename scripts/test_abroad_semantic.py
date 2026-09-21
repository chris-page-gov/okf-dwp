"""Whole-passage and scope controls for the additive international routes.

The frozen guidance is not a finding of current legal applicability. These
controls preserve its conditions and citations rather than grade an AI answer.
"""
import json
import unittest
from pathlib import Path

from build_bundle import ROOT, BASE, digest, load_yaml


class AbroadSemanticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.author=load_yaml(ROOT/'domain-profile/staff-semantic/concepts.yamlld')
        cls.nodes={n['key']:n for n in cls.author['@graph']}
        cls.index=json.loads((ROOT/'evaluation/semantic-expansion/assembly-index.json').read_bytes())
        cls.records={r['id']:r for r in cls.index['records']}
        cls.profiles=load_yaml(ROOT/'domain-profile/staff-semantic/profiles.yamlld')['profiles']
        cls.pages=json.loads((ROOT/'source/full-dmg-2026-09-15/pages/dmg-vol2-ch7-part6.json').read_bytes())['pages']

    def text(self,page):
        return self.pages[page-1]['text']

    def test_reuses_prior_identifiers_and_preserves_all_whole_pages(self):
        prior=json.loads((ROOT/'context/corpus/base-index.json').read_bytes())
        old={r['id']:r for r in prior['records']}
        keys=('intl-spc-claimant-absence','intl-spc-household-absence',
              'intl-spc-absence-transition-2016','intl-spc-non-export')
        for key in keys:
            iri=BASE+'id/term/'+key
            self.assertIn(iri,old)
            node=self.nodes[key]
            self.assertEqual(node['@id'],iri)
            self.assertEqual(self.records[iri]['assertion_status'],'model-derived')
            self.assertEqual(self.records[iri]['review_status'],'unreviewed-specialist-review-required')
        required=set().union(*(set(self.nodes[k]['required_source_ids']) for k in keys))
        self.assertEqual(required,{BASE+f'id/page/dmg-vol2-ch7-part6/{n:04d}' for n in range(8,15)})
        for n in range(8,15):
            record=self.records[BASE+f'id/page/dmg-vol2-ch7-part6/{n:04d}']
            self.assertEqual(record['text'],self.text(n))
            self.assertTrue(all(p['literal_sha256']==digest(self.text(n).encode()) for p in record['provenance']))
            self.assertEqual(record['assertion_status'],'normalized')

    def test_whole_claimant_conditions_include_cut_sentences_and_exceptions(self):
        self.assertTrue(self.text(8).rstrip().endswith('As Jason’s'))
        self.assertTrue(self.text(9).startswith('period abroad was not expected to exceed 4 weeks'))
        self.assertIn('not expected to exceed 8 weeks',self.text(9))
        self.assertIn('the Secretary of State considers',self.text(9))
        self.assertIn('is solely in connection with',self.text(9))
        self.assertIn('provided the partner, child or qualifying young person had that illness',self.text(10))
        self.assertIn('did not go abroad for the sole purpose',self.text(10))
        self.assertTrue(self.text(11).startswith('form of treatment which is similar to'))
        definition=self.nodes['intl-spc-claimant-absence']['definition']
        for term in ('Other entitlement conditions must continue','expected duration',
                     'Secretary of State','solely','pre-existing-condition',
                     'unknown','DMG 04642'):
            self.assertIn(term,definition)

    def test_household_and_young_person_continuations_are_distinct(self):
        self.assertIn('077005 A person is treated as being a member',self.text(11))
        self.assertIn('077007 The temporary absence',self.text(11))
        self.assertTrue(self.text(12).startswith('      1.2 medically approved convalescence'))
        self.assertIn('077008 A qualifying young person',self.text(12))
        self.assertIn('077010 The education or training',self.text(13))
        self.assertIn('not a qualifying young person if they are receiving UC',self.text(13))
        self.assertIn('separate question from the claimant-payment provision',
                      self.nodes['intl-spc-household-absence']['definition'])
        self.assertIn('Do not transfer the claimant’s list of people',
                      self.nodes['intl-spc-household-absence']['definition'])

    def test_historical_transition_and_other_benefit_boundary_remain_explicit(self):
        self.assertIn('28.7.16',self.text(13))
        self.assertIn('All further absences will be subject to the new rules',self.text(13))
        self.assertIn('Reg (EC) No. 883/04',self.text(14))
        self.assertIn('077026 SPC is not within the scope',self.text(14))
        self.assertIn('077027 An overseas resident',self.text(14))
        self.assertIn('dated source-described transition',self.nodes['intl-spc-absence-transition-2016']['definition'])
        self.assertIn('different benefit',self.nodes['intl-spc-non-export']['definition'])
        self.assertIn('no post-exit or present-day legal applicability',self.nodes['intl-spc-non-export']['definition'])

    def test_only_explicit_pension_credit_abroad_profile_requires_spc_closure(self):
        changed=[p for p in self.profiles if 'intl-spc-claimant-absence' in p.get('qualification_concepts',[])]
        self.assertEqual([p['id'] for p in changed],['staff-023'])
        self.assertEqual(changed[0]['when_all'],['pension-credit','abroad'])
        requirement=next(r for r in self.index['requirements'] if r['id'].endswith('/staff-023'))
        paths=requirement['required_paths']
        edges={e['id']:e for e in self.index['assertions']}
        for n in range(8,15):
            target=BASE+f'id/page/dmg-vol2-ch7-part6/{n:04d}'
            path=next(p for p in paths if p['records'][-1]==target and
                      any(edges[e]['predicate'].endswith('/requires') for e in p['assertions']))
            self.assertIn(path['seed'],requirement['when_all'])
            for j,e in enumerate(path['assertions']):
                self.assertEqual((edges[e]['source'],edges[e]['target']),tuple(path['records'][j:j+2]))
        self.assertLessEqual(len(paths),100)
        self.assertLessEqual(len(requirement['required']),200)
        self.assertLessEqual(max(len(p['assertions']) for p in paths),8)
        profiles=json.loads((ROOT/'evaluation/semantic-expansion/profiles.json').read_bytes())
        self.assertEqual(len(profiles['obligations']),203)
        self.assertTrue(all(p['evidence_status']=='insufficient' for p in profiles['profiles']))

    def test_no_bare_absence_holiday_or_universal_credit_alias_is_invented(self):
        aliases=self.nodes['abroad']['aliases']
        self.assertIn('overseas',aliases)
        for value in ['temporary absence','holiday','absence','Universal Credit','UC']:
            self.assertNotIn(value,aliases)
        definition=self.nodes['abroad']['definition']
        self.assertIn('Domestic temporary absence',definition)
        self.assertIn('not interchangeable territorial tests',definition)
        self.assertIn('does not establish',definition)


if __name__=='__main__':
    unittest.main()
