"""Offline budget and failure controls; no network or model calls."""
import io
import unittest
from unittest.mock import patch
from acquire_reading_help_law import Acquisition, MAX_RESPONSE, MAX_TOTAL, NoRedirect

class Response(io.BytesIO):
    def __init__(self, data, code=200, headers=None):
        super().__init__(data); self.code=code; self.url='https://www.legislation.gov.uk/ukpga/1992/4/section/70/2026-09-20/data.xml'
        self.headers={} if headers is None else headers
class Opener:
    def __init__(self, factory): self.factory=factory;self.calls=0
    def open(self, *args, **kwargs): self.calls+=1;return self.factory()
URL='https://www.legislation.gov.uk/ukpga/1992/4/section/70/2026-09-20/data.xml'

class AcquisitionTests(unittest.TestCase):
    def test_exact_success(self):
        a=Acquisition(Opener(lambda:Response(b'<xml/>',headers={'Content-Length':'6'})))
        data,r=a.fetch(URL);self.assertEqual(data,b'<xml/>');self.assertEqual(a.total,6);self.assertEqual(r['status'],'observed')
    def test_hard_aggregate_includes_failed_bodies(self):
        a=Acquisition(Opener(lambda:Response(b'abcdefgh',code=503)))
        with patch('acquire_reading_help_law.MAX_TOTAL',10):
            self.assertIsNone(a.fetch(URL)[0]);self.assertEqual(a.total,8)
            self.assertIsNone(a.fetch(URL)[0]);self.assertEqual(a.total,10)
            self.assertEqual(a.fetch(URL)[1]['status'],'not-requested');self.assertEqual(a.opener.calls,2)
    def test_response_limit_never_reads_probe_byte(self):
        a=Acquisition(Opener(lambda:Response(b'abcdefgh')))
        with patch('acquire_reading_help_law.MAX_RESPONSE',4):
            data,r=a.fetch(URL);self.assertIsNone(data);self.assertEqual(a.total,4);self.assertIn('completeness',r['error'])
    def test_advertised_excess_no_body_read(self):
        a=Acquisition(Opener(lambda:Response(b'abc',headers={'Content-Length':str(MAX_RESPONSE+1)})))
        self.assertIsNone(a.fetch(URL)[0]);self.assertEqual(a.total,0)
    def test_truncated_length_rejected(self):
        a=Acquisition(Opener(lambda:Response(b'abc',headers={'Content-Length':'9'})))
        self.assertIsNone(a.fetch(URL)[0]);self.assertEqual(a.total,3)
    def test_request_limit_no_retry(self):
        a=Acquisition(Opener(lambda:Response(b'error',code=503)))
        for _ in range(5):self.assertIsNone(a.fetch(URL)[0])
        with self.assertRaisesRegex(ValueError,'Five-request'):a.fetch(URL)
        self.assertEqual(a.opener.calls,5)
    def test_no_redirect_or_unsafe_url(self):
        self.assertIsNone(NoRedirect().redirect_request(None,None,302,'',{},'https://attacker.test'))
        a=Acquisition(Opener(lambda:Response(b'x')))
        with self.assertRaises(ValueError):a.fetch('https://attacker.test/data.xml')
        self.assertEqual(a.opener.calls,0)
    def test_encoded_body_not_admitted(self):
        a=Acquisition(Opener(lambda:Response(b'x',headers={'Content-Encoding':'gzip'})))
        self.assertIsNone(a.fetch(URL)[0])

if __name__=='__main__':unittest.main()

from project_reading_help_law import project, complete_text
from unittest.mock import patch
class ProjectionTests(unittest.TestCase):
    def test_all_territorial_variants_keep_distinct_dated_urls(self):
        target='ukpga/1992/4/section/70';prefix='http://www.legislation.gov.uk/'
        xml='<Legislation>'
        for region in ['england+wales','scotland']:
            xml+='<P1 IdURI="'+prefix+'id/'+target+'" DocumentURI="'+prefix+target+'/'+region+'/2026-09-20"><Pnumber>70</Pnumber><P1para><Text>Condition '+region+' except when absent.</Text><AppendText>;</AppendText></P1para></P1>'
        xml+='</Legislation>'
        with patch('project_reading_help_law.legislative_metadata',return_value={'document_identifier':prefix+target+'/2026-09-20'}):
            d=project(xml.encode(),target)
            self.assertEqual(len(d['units']),2)
            self.assertEqual({u['variant'] for u in d['units']},{'england+wales','scotland'})
            self.assertTrue(all(u['body_text'].endswith('\n;') for u in d['units']))
            self.assertTrue(all('except when absent' in u['body_text'] for u in d['units']))
            self.assertEqual(len({u['version_url'] for u in d['units']}),2)
    def test_ambiguous_duplicate_variant_rejected(self):
        target='uksi/1976/409/regulation/3';prefix='http://www.legislation.gov.uk/'
        unit='<P1 IdURI="'+prefix+'id/'+target+'" DocumentURI="'+prefix+target+'/2026-09-20"><Text>condition</Text></P1>'
        with patch('project_reading_help_law.legislative_metadata',return_value={'document_identifier':prefix+target+'/2026-09-20'}):
            with self.assertRaisesRegex(ValueError,'duplicate'):project(('<Legislation>'+unit*2+'</Legislation>').encode(),target)
