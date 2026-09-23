import json,gzip,hashlib,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
triage=json.loads((ROOT/'evaluation/manual-structure/final-source-review/large-paragraph-triage.json').read_text())
mraw=(ROOT/'structured-units/manifest.json').read_bytes();assert sha(mraw)==triage['manifest']['sha256'];m=json.loads(mraw)
items=[]
for n,t in enumerate(triage['items'],1):
 ref=next(r for r in m['documents'] if r['document_id']==t['document_id'] and r['family']==t['family'])
 b=(ROOT/'structured-units'/ref['path']).read_bytes();assert sha(b)==ref['sha256']; doc=json.loads(gzip.decompress(b));u=next(x for x in doc['units'] if x['id']==t['id'])
 assert u['record_sha256']==t['record_sha256']; assert len(u['text'].encode())==t['text_bytes']
 pp=Path(next(x['path'] for x in m['inputs'] if x['sha256']==t['source']['pages_sha256'] and '/pages/' in x['path']));pb=(ROOT/pp).read_bytes();assert sha(pb)==t['source']['pages_sha256'];p=json.loads(pb)
 texts={i['page']:i['text'] for i in p['pages']};spans=[];profiles=[]
 for s in u['spans']:
  b=texts[s['page']].encode()[s['start_utf8']:s['end_utf8']];assert sha(b)==s['literal_sha256'];spans.append(b)
  text=b.decode();lines=[l.strip() for l in text.splitlines() if l.strip()]
  numeric=[l for l in lines if re.match(r'^\d{5,6}\s+\S',l)]
  leaders=[l for l in lines if re.search(r'\.{5,}',l)]
  profiles.append({'page':s['page'],'bytes':len(b),'nonblank_lines':len(lines),'dotted_leader_lines':len(leaders),'paragraph_start_candidates':numeric,'opening_lines':lines[:4],'closing_lines':lines[-3:]})
 assert b'\n'.join(spans)==u['text'].encode()
 item={'number':n,**t,'unit_text_sha256':sha(u['text'].encode()),'pages_path':str(pp),'structure_document':ref,
 'full_text_mechanical_scan':True,'source_reconstruction':'every original span hash and complete newline-joined text verified',
 'page_profiles':profiles,'opening':u['text'][:1200],'ending':u['text'][-900:]}
 items.append(item)
summary={'schema':'okf-dwp-large-paragraph-source-review-input.v1','scope':'Source-bound structural triage only; full text scanned mechanically, source boundaries are separately reviewed below; no specialist/legal acceptance.', 'triage':triage['manifest'],'items':items}
assert (OUT/'source-observations.json').read_text()==json.dumps(summary,ensure_ascii=False,indent=2)+'\n'
print(json.dumps({'verified_candidates':len(items),'source_spans':sum(len(i['page_profiles']) for i in items),'writes':0}))
