from pathlib import Path
import argparse,json,hashlib,re
from datetime import datetime,timezone
ROOT=Path('/Users/crpage/repos/okf-dwp');OUT=ROOT/'evaluation/full-dmg-behavioural'
def sha(b):return hashlib.sha256(b).hexdigest()
def now():return datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
def canon(x):return (json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
ap=argparse.ArgumentParser();ap.add_argument('--batch',required=True);ap.add_argument('--chapters');ap.add_argument('--part',default='all');args=ap.parse_args()
registryraw=(OUT/'case-registry.json').read_bytes();reg=json.loads(registryraw); selected=[c for c in reg['cases'] if c['batch']==args.batch and (not args.chapters or c['source_unit']['chapter'] in [int(v) for v in args.chapters.split(',')])]
invraw=(ROOT/'source/full-dmg-2026-09-15/inventory.json').read_bytes();inv=json.loads(invraw);docs={d['id']:d for d in inv['documents']};cache={};reads=[];cases=[];started=now()
for c in selected:
 ev=c['expected_evidence']; guided=False
 if not ev or all(not e.get('locator') and not e.get('quote') for e in ev):
  positive=next(p for p in reg['cases'] if p['source_unit']['id']==c['source_unit']['id'] and p['batch']==c['batch'] and p['kind']=='source-grounding')
  ev=positive['expected_evidence'];guided=True
 ids=[]
 for e in ev:
  route=e['page'];docid=e['source_identity']['document_id'];d=docs[docid]
  if docid not in cache:
   raw=(ROOT/d['pages_path']).read_bytes();assert sha(raw)==d['pages_sha256'];cache[docid]=json.loads(raw)['pages']
  page=int(route.split('/')[-1]);text=cache[docid][page-1]['text'];label=(e.get('locator') or '').removeprefix('DMG ').split('–')[0]
  if not label and e.get('quote'):
   match=re.match(r'\s*(\d{5,6})\b',e['quote']);label=match[1] if match else ''
  if label:
   m=re.search(rf'^\s*{re.escape(label)}\s+(?=[A-Z‘“(\[])',text,re.M);assert m,(route,label)
   start=m.start()+len(m[0])-len(m[0].lstrip());n=re.search(r'^\s*\d{5,6}\s+(?=[A-Z‘“(\[])',text[m.end():],re.M)
   end=m.end()+n.start() if n else len(text);excerpt=text[start:end].rstrip()
  else:excerpt=text
  rid=route+'#'+(label or 'whole-page');ids.append(rid)
  if any(r['id']==rid for r in reads):continue
  reads.append({'id':rid,'tool':'frozen-source-page-read','arguments':{'path':d['pages_path'],'pdf_page':page,'paragraph_label':label or None},'observed_at':now(),'output':{'route':route,'document_id':docid,'source_url':cache[docid][page-1]['url'],'source_role':d['role'],'source_pdf_sha256':d['sha256'],'source_pages_sha256':d['pages_sha256'],'page_text_sha256':sha(text.encode()),'source_http_observed_at':d['observed_at'],'source_date_status':'capture is not publication or legal applicability','excerpt':excerpt,'excerpt_sha256':sha(excerpt.encode()),'limitation':'Selected machine-extracted paragraph or page; surrounding text and visual layout may matter.'}})
 cases.append({'case_id':c['registry_id'],'original_id':c['original_id'],'prompt':c['prompt']['text'],'prompt_sha256':c['prompt_sha256'],'source_unit':c['source_unit'],'source_read_ids':ids,'selection_method':'case-designed locator hints; paired positive evidence' if guided else 'case-designed source locator hints','response':None,'status':'sources-read; response-not-yet-recorded'})
result={'schema':'okf-dwp-observed-source-read-trace.v1','method':'Executed frozen-source file reads and literal paragraph extraction; not search retrieval or built-bundle interrogation. Source addresses were selected from authored expectations.','started_at':started,'finished_at':now(),'registry_sha256':sha(registryraw),'inventory_sha256':sha(invraw),'reader_path':'/Users/crpage/tmp/okf-dwp-authored-evaluation/read_trial_sources.py','reader_sha256':sha(Path(__file__).read_bytes()),'cases':cases,'reads':reads}
target=OUT/f'personas-reads-{args.batch}-{args.part}.json';assert not target.exists(),target;target.write_bytes(canon(result))
print('TRACE',target.name,sha(target.read_bytes()))
for c in cases:print(c['original_id'],c['prompt'])
for r in reads:print('\n'+r['id']+'\n'+r['output']['excerpt'])
