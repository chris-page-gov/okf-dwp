import argparse, datetime, hashlib, json, tarfile, urllib.request
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--artifact',required=True);p.add_argument('--commit',required=True);p.add_argument('--run',required=True);p.add_argument('--output',required=True);a=p.parse_args()
out=Path(a.output);assert not out.exists()
root='https://chris-page-gov.github.io/okf-dwp/'
result={'schema':'okf-reading-help-learning-site-observation.v1','status':'failed','source_commit':a.commit,'workflow_run':int(a.run),'workflow_url':f'https://github.com/chris-page-gov/okf-dwp/actions/runs/{a.run}','started_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'requests':[],'errors':[],'scope':'Selected public documentation bytes compared with the exact successful Pages artefact. This is not corpus delivery, service, legal or specialist acceptance.'}
class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,*args,**kwargs):return None
opener=urllib.request.build_opener(NoRedirect)
try:
 artifact=Path(a.artifact);assert artifact.stat().st_size<=128*1024*1024
 with artifact.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
 result['artifact']={'name':artifact.name,'bytes':artifact.stat().st_size,'sha256':digest}
 with tarfile.open(artifact) as archive:
  members=archive.getmembers();assert len(members)<=10000
  byname={m.name.removeprefix('./'):m for m in members}
  def read(name,maximum=2*1024*1024):
   m=byname[name];assert m.isfile() and 0<m.size<=maximum
   with archive.extractfile(m) as f:b=f.read(maximum+1)
   assert len(b)==m.size;return b
  expected=read('site-manifest.json');manifest=json.loads(expected);assert manifest['source_commit']==a.commit
  files={r['path']:r for r in manifest['files']};names=['site-manifest.json','index.html','docs/learning-path.html','docs/reading-help-demo-2026-09-30.html','docs/reading-help-corpus-contract.html','docs/reading-help-legislation-bridge.html','docs/backlog-work-packages.html']
  for name in names:
   b=expected if name=='site-manifest.json' else read(name)
   sha=hashlib.sha256(b).hexdigest()
   if name!='site-manifest.json':assert len(b)==files[name]['bytes'] and sha==files[name]['sha256']
   url=root+name;req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 OKF-release-verifier'})
   with opener.open(req,timeout=20) as response:
    actual=response.read(len(b)+1);row={'path':name,'url':url,'response_url':response.url,'status':response.status,'bytes':len(actual),'sha256':hashlib.sha256(actual).hexdigest(),'expected_sha256':sha}
   row['matched']=row['response_url']==url and row['status']==200 and len(actual)==len(b) and row['sha256']==sha
   result['requests'].append(row);assert row['matched'],f'Public bytes differ: {name}'
 result['status']='passed'
except Exception as e:result['errors'].append(f'{type(e).__name__}: {e}')
result['finished_at']=datetime.datetime.now(datetime.timezone.utc).isoformat();result['verifier_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
with out.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps({'status':result['status'],'matched':sum(r['matched'] for r in result['requests']),'errors':result['errors'],'output':str(out)}))
raise SystemExit(0 if result['status']=='passed' else 1)
