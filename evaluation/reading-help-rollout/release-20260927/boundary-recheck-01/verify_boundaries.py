from pathlib import Path
import hashlib,json,datetime,subprocess,sys
root=Path.cwd();out=root/'evaluation/reading-help-rollout/release-20260927/boundary-recheck-01';out.mkdir(exist_ok=False)
def digest(b):return hashlib.sha256(b).hexdigest()
def binding(p):
 b=p.read_bytes();return {'path':p.relative_to(root).as_posix(),'bytes':len(b),'sha256':digest(b)}
report={'schema':'okf-reading-help-boundary-recheck.v1','status':'failed','source_review':binding(root/'evaluation/passage-boundary-candidate/substantive-scope-review.json'),'documents':[],'commands':[],'errors':[],'boundary':'Byte and fixed-output non-regression of the retained source review. No new visual, legal or specialist acceptance; case 014 remains unresolved.'}
try:
 v=json.loads((root/report['source_review']['path']).read_bytes());assert v['documents_reviewed']==len(v['items'])==9
 for row in v['items']:
  p=root/row['pdf_path'];e=root/row['extraction_path'];pb=p.read_bytes();eb=e.read_bytes();assert digest(pb)==row['pdf_sha256'];assert digest(eb)==row['extraction_sha256']
  pages={p['page']:p['text'].encode() for p in json.loads(eb)['pages']};seen=[]
  for s in row['bare_line_observations']:
   b=pages[s['page']][s['start_utf8']:s['end_utf8']];assert b and digest(b)==s['literal_sha256'];seen.append({k:s[k] for k in ['page','start_utf8','end_utf8','literal_sha256']})
  report['documents'].append({'document_id':row['document_id'],'pdf':binding(p),'extraction':binding(e),'source_observations':seen,'status':'passed'})
 for cmd in [['uv','run','--locked','python','scripts/build_passage_boundary_review.py','--check'],['uv','run','--locked','python','-m','unittest','discover','-s','scripts','-p','test_passage_boundary_review.py']]:
  r=subprocess.run(cmd,capture_output=True,text=True,timeout=120);name=f'command-{len(report["commands"])+1:02d}.txt';(out/name).write_text(r.stdout+r.stderr);report['commands'].append({'argv':cmd,'exit_code':r.returncode,'log':binding(out/name)});assert r.returncode==0
 report['status']='passed'
except Exception as e:report['errors'].append(f'{type(e).__name__}: {e}')
report['recorded_at']=datetime.datetime.now(datetime.timezone.utc).isoformat();report['verifier_sha256']=digest(Path(__file__).read_bytes());(out/'receipt.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':report['status'],'documents':len(report['documents']),'errors':report['errors']}));sys.exit(0 if report['status']=='passed' else 1)
