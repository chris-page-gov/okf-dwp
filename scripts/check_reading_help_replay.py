#!/usr/bin/env python3
"""Verify the retained 40-question non-regression receipt without re-running it."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ATTEMPT='evaluation/reading-help-rollout/replays/reading-help-20260927-01'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def read(path):return (ROOT/path).read_bytes()
def load(path):return json.loads(read(path))
def require(value,message):
 if not value:raise ValueError(message)
def check():
 protocol=load(ATTEMPT+'/protocol.json');report=load(ATTEMPT+'/report.json');prior=load('evaluation/evidence-workbench/manifest.json')
 require(protocol['source']==prior['source'],'Replay source differs from frozen workbench')
 require(protocol['source']['registry_sha256']==sha(read(protocol['source']['registry'])),'Staff registry differs')
 require(protocol['source']['corpus_sha256']==sha(read(protocol['source']['corpus'])),'Source scope differs')
 require(read(ATTEMPT+'/runner.mjs')==read('scripts/replay_reading_help_questions.mjs'),'Retained runner differs')
 require(all(report[k]==v for k,v in protocol.items()),'Protocol changed after execution')
 expected=[q['id'] for q in prior['questions']]
 require(len(expected)==40 and protocol['cases']==expected,'Case denominator differs')
 require(report['model_calls']==report['network_calls']==0,'Unexpected external calls')
 require(report['cases_passed']==40 and report['cases_failed']==[] and report['passed'] is True,'Retained failures require review')
 require([r['path'] for r in report['files']]==[c+'.json' for c in expected],'Case receipt inventory differs')
 cold=warm=0
 for q,ref in zip(prior['questions'],report['files']):
  raw=read(ATTEMPT+'/'+ref['path']);require(len(raw)==ref['bytes'] and sha(raw)==ref['sha256'],'Case receipt binding differs')
  case=json.loads(raw);require(case['case_id']==q['id'] and case['passed'] and case['failure'] is None,'Failed or wrong case')
  original=read('evaluation/evidence-workbench/'+q['package']['url']);require(sha(original)==q['package']['sha256'],'Original package differs')
  pack=json.loads(original)
  require(case['evidence_status']==pack['evidence_status'] and case['requirements']==pack['requirements'] and case['missing_evidence']==pack['missing_evidence'],'Obligations or status changed')
  evidence=[{'id':s['record']['id'],'text_sha256':sha(s['record']['text'].encode()),'relationship_paths':s['paths']} for s in pack['selected'] if s['record']['kind']=='evidence']
  require(case['selected_evidence']==evidence,'Retained text identity or traversal changed')
  require([r['temperature'] for r in case['measurements']]==['cold','warm'],'Missing paired measurement')
  for row in case['measurements']:
   require(row['package_sha256']==sha(original) and row['package_bytes']==len(original),'Observed package identity differs')
   require(row['latency_ms']>=0 and row['bytes_read']>=0 and row['files_read']>=0 and row['cache_hits']>=0,'Invalid performance observation')
  cold+=case['measurements'][0]['bytes_read'];warm+=case['measurements'][1]['bytes_read']
 require(cold==report['total_cold_bytes'] and warm==report['total_warm_bytes'],'Aggregate measurements differ')
 return {'status':'passed','retained_cases':40,'external_calls':0,'scope':'Receipt integrity and exact retained evidence, not legal answer completeness'}
if __name__=='__main__':print(json.dumps(check()))
