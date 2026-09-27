#!/usr/bin/env python3
"""Bind retained staff evidence to exact reading-help units without reassembling it."""
from __future__ import annotations
import argparse,hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CONFIG='domain-profile/reading-help/workbench-link.json'
BASE_MANIFEST='evaluation/evidence-workbench/tools-manifest.json'
OUTPUT='evaluation/evidence-workbench/reading-help-manifest.json'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def read(root,relative):
 path=(root/relative).resolve()
 if not path.is_relative_to(root.resolve()):raise ValueError('Reference escapes repository')
 return path.read_bytes()
def build(root=ROOT):
 config=json.loads(read(root,CONFIG));revision=config['catalogue_revision']
 if not re.fullmatch('[0-9a-f]{40}',revision):raise ValueError('Pin the reviewed catalogue commit')
 catalogue_raw=read(root,'reading-help-corpus/manifest.json')
 if sha(catalogue_raw)!=config['catalogue_sha256']:raise ValueError('Catalogue differs from approved binding')
 catalogue=json.loads(catalogue_raw);manifest=json.loads(read(root,BASE_MANIFEST))
 selected={};by_case={}
 for question in manifest['questions']:
  ref=question['package'];raw=read(root,'evaluation/evidence-workbench/'+ref['url'])
  if sha(raw)!=ref['sha256'] or len(raw)!=ref['bytes']:raise ValueError('Frozen package differs')
  by_case[question['id']]=set()
  for item in json.loads(raw)['selected']:
   record=item['record']
   if record['kind']=='evidence':
    previous=selected.get(record['id'])
    if previous is not None and previous!=record:raise ValueError('Conflicting retained records share an identifier')
    selected[record['id']]=record;by_case[question['id']].add(record['id'])
 targets=[];found=set()
 for doc in catalogue['documents']:
  raw=read(root,doc['path'])
  if len(raw)!=doc['bytes'] or sha(raw)!=doc['sha256']:raise ValueError('Document index differs')
  index=json.loads(raw)
  for passage in index['passages']:
   ident=passage['unit_id']
   if ident not in selected or ident in found:continue
   # Equality is literal, never inferred from a paragraph number or page.
   record=selected[ident];spans=record.get('evidence_unit',{}).get('spans',[])
   if not spans or any(s['source_sha256']!=index['source']['sha256'] or s['extraction_sha256']!=index['extraction']['sha256'] for s in spans):
    raise ValueError('Equal unit identifier has different source identity')
   found.add(ident);targets.append({'record_id':ident,'family':doc['family'],'document_id':doc['document_id'],'unit_id':ident})
 outputs={};references=[]
 for case_id,ids in by_case.items():
  if not re.fullmatch(r'staff-[0-9]{3}',case_id):raise ValueError('Invalid case identity')
  selected_targets=sorted([t for t in targets if t['record_id'] in ids],key=lambda r:r['record_id'])
  if len(selected_targets)>64:raise ValueError('Case target count exceeds bound')
  content={'schema':'okf-reading-help-workbench-targets.v1','case_id':case_id,'targets':selected_targets}
  body=(json.dumps(content,separators=(',',':'),ensure_ascii=False)+'\n').encode()
  if len(body)>32768:raise ValueError('Case targets exceed bound')
  relative='reading-help/'+case_id+'.json';outputs['evaluation/evidence-workbench/'+relative]=body
  references.append({'case_id':case_id,'url':relative,'sha256':sha(body),'bytes':len(body)})
 manifest['reading_help']={'catalogue':{'url':'https://raw.githubusercontent.com/chris-page-gov/okf-dwp/'+revision+'/reading-help-corpus/manifest.json','sha256':sha(catalogue_raw),'bytes':len(catalogue_raw)},'targets_by_case':references}
 raw=(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n').encode()
 if len(raw)>256*1024:raise ValueError('Augmented workbench manifest exceeds consumer cap')
 outputs[OUTPUT]=raw
 report={'schema':'okf-reading-help-workbench-link-report.v1','catalogue_revision':revision,'catalogue_sha256':sha(catalogue_raw),'questions':len(by_case),'selected_evidence_records':len(selected),'exact_reading_help_targets':len(found),'unmatched_records':sorted(set(selected)-found),'scope':'Navigation only; packages, requirements and evidence status unchanged.'}
 outputs['evaluation/reading-help-rollout/workbench-link-report.json']=(json.dumps(report,indent=2)+'\n').encode()
 return outputs,report
def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args();outputs,report=build()
 for path,raw in outputs.items():
  if a.check:
   if read(ROOT,path)!=raw:raise ValueError('Stale reading-help workbench projection '+path)
  else:
   target=ROOT/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
 print(json.dumps(report))
if __name__=='__main__':main()
