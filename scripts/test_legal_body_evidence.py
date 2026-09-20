"""Offline controls for bounded statutory body extraction and publication."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from acquire_legal_bodies import project_xml, public_ref, OPAQUE, validate_url, pretty
from build_legal_body_evidence import ROOT, SOURCE, AUTHORING, build, sha, verify_manifest, verify_unit, verify_version, extent, read_safe

TARGET='uksi/2002/1792/regulation/5'
SEED={'target':TARGET,'units':[TARGET]}

def fixture(ref='note-one'):
    return ('<Legislation xmlns="http://www.legislation.gov.uk/namespaces/legislation" RestrictExtent="E+W+S">'
        '<Secondary><Body><P1group><Title>Claimants who have no partner</Title>'
        '<P1 IdURI="http://www.legislation.gov.uk/id/'+TARGET+'"><Pnumber>5</Pnumber><P1para>'
        '<Text>If permanently resident, except during a temporary absence <CommentaryRef Ref="'+ref+'"/>with conditions.</Text>'
        '</P1para></P1></P1group></Body></Secondary>'
        '<Commentaries><Commentary id="'+ref+'" Type="F"><Para><Text>Editorial amendment.</Text></Para></Commentary></Commentaries>'
        '</Legislation>').encode()

class LegalBodyTests(unittest.TestCase):
    def test_complete_unit_qualifications_and_heading(self):
        d=project_xml(fixture(),SEED,'2026-09-20');u=d['units'][0]
        self.assertIn('except during a temporary absence with conditions.',u['body_text'])
        self.assertEqual(u['ancestor_headings_nearest_first'],['Claimants who have no partner'])
        self.assertEqual(extent(u),['E+W+S']);verify_unit(u)
        self.assertEqual(d['selected_commentaries'][0]['text'],'Editorial amendment.')
        self.assertNotIn('Editorial amendment.',u['body_text'])

    def test_opaque_commentary_identifier_digest_not_literal(self):
        ref='key-'+'a'*32;d=project_xml(fixture(ref),SEED,'2026-09-20')
        self.assertFalse(OPAQUE.search(pretty(d).decode()))
        self.assertEqual(d['units'][0]['commentary_ids'],[public_ref(ref)])
        self.assertEqual(d['selected_commentaries'][0]['id'],public_ref(ref))
        self.assertTrue(any(x['value_sha256']==sha(ref.encode()) for x in d['omitted_attributes']))

    def test_wrong_canonical_target_rejected(self):
        with self.assertRaisesRegex(ValueError,'canonical'): project_xml(fixture(),{'target':'uksi/2002/1792/regulation/99','units':[]},'2026-09-20')

    def test_dtd_entity_rejected(self):
        for text in [b'<!DOCTYPE x>'+fixture(),b'<!ENTITY bad "x">'+fixture()]:
            with self.assertRaisesRegex(ValueError,'DTD'): project_xml(text,SEED,'2026-09-20')

    def test_missing_unit_is_partial_not_complete(self):
        d=project_xml(fixture(),{'target':TARGET,'units':[TARGET+'/99']},'2026-09-20')
        self.assertEqual(d['status'],'partial-selected-units');self.assertEqual(d['missing_units'],[TARGET+'/99'])

    def test_text_tree_or_hash_tamper_rejected(self):
        u=project_xml(fixture(),SEED,'2026-09-20')['units'][0]
        for field,value in [('body_text','Unconditional outcome'),('body_text_sha256','0'*64)]:
            changed=copy.deepcopy(u);changed[field]=value
            with self.assertRaisesRegex(ValueError,'binding'):verify_unit(changed)

    def test_unknown_extent_stays_unknown(self):
        d=project_xml(fixture().replace(b' RestrictExtent="E+W+S"',b''),SEED,'2026-09-20')
        self.assertEqual(extent(d['units'][0]),[])
        self.assertIn('absence-is-unknown',d['metadata']['extent_assessment'])

    def test_only_explicit_official_https_destinations(self):
        for url in ['http://www.legislation.gov.uk/x','https://attacker.test/x','https://name:secret@www.legislation.gov.uk/x','https://www.legislation.gov.uk:443/x']:
            with self.assertRaises(ValueError):validate_url(url)
        validate_url('https://www.legislation.gov.uk/uksi/2002/1792/regulation/5/2026-09-20/data.xml')

    def test_manifest_hash_and_exact_census(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name);directory=root/'source';directory.mkdir();data=b'{"evidence":"public"}\n';(directory/'record.json').write_bytes(data)
            (directory/'manifest.json').write_bytes(pretty({'files':[{'path':'record.json','bytes':len(data),'sha256':sha(data)}]}))
            verify_manifest(root,'source')
            (directory/'unexpected.json').write_text('{}')
            with self.assertRaisesRegex(ValueError,'census'):verify_manifest(root,'source')
            (directory/'unexpected.json').unlink();(directory/'record.json').write_text('{"evidence":"changed"}\n')
            with self.assertRaisesRegex(ValueError,'binding'):verify_manifest(root,'source')

    def test_path_escape_and_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name);(root/'record.json').write_text('{}');(root/'link.json').symlink_to(root/'record.json')
            for path in ['../record.json','/tmp/record.json','link.json']:
                with self.assertRaises(ValueError):read_safe(root,path)

    def test_retained_acquisition_and_six_cases_fail_closed(self):
        outputs=build();overlay=json.loads(outputs[AUTHORING+'/context-overlay.json']);coverage=json.loads(outputs[AUTHORING+'/coverage.json'])
        self.assertEqual(len(overlay['records']),20);self.assertEqual(len(overlay['assertions']),43)
        self.assertEqual(coverage['requested_provisions'],16)
        self.assertEqual({x['case_id'] for x in coverage['cases']},{'staff-012','staff-013','staff-014','staff-017','staff-018','staff-020'})
        self.assertTrue(all(x['evidence_status']=='insufficient' and x['selected_body_ids'] for x in coverage['cases']))
        self.assertIn('s 5 and s 12(2)(d) remain unresolved',' '.join(coverage['unresolved_literal_policy']))
        self.assertTrue(all(x['assertion_status']=='normalized' for x in overlay['records']+overlay['assertions']))
        self.assertTrue(all(x['review_status']=='unreviewed' for x in overlay['records']))
        self.assertTrue(all(x['authority']['class']=='derived' and x['authority']['source'].startswith('https://') for x in overlay['records']+overlay['assertions']))
        self.assertTrue(all(x['predicate']=='http://purl.org/dc/terms/references' for x in overlay['assertions']))
        self.assertEqual(sum(x['extent_status']=='unknown' for x in coverage['units']),12)
        self.assertFalse(OPAQUE.search(b''.join(outputs.values()).decode()))

    def test_linked_data_direct_triples_match_reified_navigation(self):
        from build_bundle import load_yaml
        outputs=build();overlay=json.loads(outputs[AUTHORING+'/context-overlay.json'])
        with tempfile.TemporaryDirectory() as name:
            path=Path(name)/'evidence.yamlld';path.write_bytes(outputs[AUTHORING+'/evidence.yamlld']);graph=load_yaml(path)['@graph']
        predicate='http://purl.org/dc/terms/references'
        direct={(row['@id'],target['@id']) for row in graph for target in row.get(predicate,[])}
        self.assertEqual(direct,{(row['source'],row['target']) for row in overlay['assertions']})

    def test_requested_date_must_match_observed_document_and_unit(self):
        d=json.loads((ROOT/SOURCE/'provisions/uksi--2002--1792--regulation--5.json').read_text())
        verify_version(d,'2026-09-20')
        for where in ['metadata','unit']:
            changed=copy.deepcopy(d)
            if where=='metadata':changed['metadata']['document_identifier']=changed['metadata']['document_identifier'].replace('2026-09-20','2025-01-01')
            else:changed['units'][0]['body_tree']['attributes']['DocumentURI']=changed['units'][0]['body_tree']['attributes']['DocumentURI'].replace('2026-09-20','2025-01-01')
            with self.assertRaisesRegex(ValueError,'version identity'):verify_version(changed,'2026-09-20')

    def test_preserved_failed_attempt_and_reused_successes(self):
        first=json.loads((ROOT/'source/legal-bodies-2026-09-21/request-census.json').read_text())
        second=json.loads((ROOT/SOURCE/'request-census.json').read_text())
        self.assertEqual((first['count'],second['count'],len(second['reused_prior_projections'])),(18,13,5))
        failed=[json.loads(p.read_text()) for p in (ROOT/'source/legal-bodies-2026-09-21/provisions').glob('*.json')]
        self.assertEqual(sum(x['status']=='parse-failed' for x in failed),13)
        self.assertEqual(second['automatic_retries'],0)

if __name__=='__main__':unittest.main()
