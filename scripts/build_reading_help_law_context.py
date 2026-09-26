#!/usr/bin/env python3
"""Admit a validated, separately selected context; preserve earlier corpus releases."""
from __future__ import annotations
import argparse
from copy import deepcopy
import json
from pathlib import Path
from build_reading_help_law import build as bridge_build, read_safe, sha, pretty, BASE, AUTHORING, PROJECTED, LIMITATIONS, OGL, REPO, DCT
from build_reading_help_references import build as reference_build
ROOT=Path(__file__).resolve().parents[1]
BASELINE='combined/context/assembly-index.json'
REFERENCE='reading-help-ch60-references.json'

def load(root,path): return json.loads(read_safe(root,path))
def walk(tree):
    yield tree
    for child in tree.get('children',[]): yield from walk(child)

def build(root=ROOT):
    for outputs in (bridge_build(root),{REFERENCE: reference_build(root)}):
        for path,raw in outputs.items():
            if read_safe(root,path)!=raw: raise ValueError('Unvalidated source projection: '+path)
    overlay=load(root,AUTHORING+'/context-overlay.json');index=load(root,BASELINE)
    helper=load(root,REFERENCE);admission=load(root,AUTHORING+'/citation-admission.json')
    before=deepcopy(index);records={r['id']:r for r in index['records']};edges={r['id']:r for r in index['assertions']}
    for external in overlay['external_record_ids']:
        if external not in records:raise ValueError('Missing existing statutory record')
    for r in overlay['records']:
        if r['id'] in records:raise ValueError('Duplicate admitted record')
        records[r['id']]=deepcopy(r)
    for e in overlay['assertions']:
        if e['id'] in edges or e['source'] not in records or e['target'] not in records:raise ValueError('Invalid admitted edge')
        edges[e['id']]=deepcopy(e)
    sources={s['id']:s for s in helper['sources']};occurrences={o['id']:o for o in helper['occurrences']};cards={c['id']:c for c in helper['cards']}
    for p in helper['passages']:
        source=sources[p['source_id']];identifier=BASE+'reading-help-law/passage/'+p['id']
        records[identifier]={'id':identifier,'route':'reading-help-law/passage/'+p['id'],'label':p['label'],'kind':'evidence',
          'text':'\n'.join(s['literal'] for s in p['spans']),'assertion_status':'normalized','review_status':'unreviewed',
          'authority':{'class':'derived','label':'Frozen machine extraction of DWP guidance; applicability unreviewed','source':source['pdf_url']},
          'scope':'Selected complete reading-help passage including retained notes and citations; dependency closure not established.','rights':OGL,'access':'public',
          'provenance':[{'url':source['pdf_url']+'#page='+str(s['page']),'source_sha256':source['pdf_sha256'],'literal_sha256':s['literal_sha256'],
           'locator':f"PDF page {s['page']}; extracted UTF-8 bytes {s['page_start_utf8']}:{s['page_end_utf8']}"} for s in p['spans']]}
    # Reuse existing concept-to-page routes, then normalise each exact overlapping
    # source location to the complete retained reading-help passage.
    for p in helper['passages']:
        destination=BASE+'reading-help-law/passage/'+p['id'];source=sources[p['source_id']]
        for span in p['spans']:
            page_id=BASE+'page/'+p['source_id']+'/'+str(span['page']).zfill(4)
            if page_id not in records: continue
            page=records[page_id];literal=page['text'].encode()[span['page_start_utf8']:span['page_end_utf8']]
            if literal.decode()!=span['literal'] or sha(literal)!=span['literal_sha256']:
                raise ValueError('Existing page and exact reading passage differ')
            identifier=BASE+'reading-help-law-location/'+sha((page_id+'\0'+destination).encode())
            edges[identifier]={'id':identifier,'source':page_id,'target':destination,'predicate':DCT,
              'label':'Exact source location is retained within this complete reading-help passage',
              'assertion_status':'normalized','scope':'Source-span navigation only; the passage may continue on another source page.',
              'authority':{'class':'derived','label':'Exact source span normalisation','source':source['pdf_url']},
              'provenance':[{'url':source['pdf_url']+'#page='+str(span['page']),'source_sha256':source['pdf_sha256'],
                'literal_sha256':span['literal_sha256'],'locator':f"Extracted UTF-8 bytes {span['page_start_utf8']}:{span['page_end_utf8']}"}]}
    outcomes=[];seen=set()
    for m in admission['mappings']:
        if m['card_id'] in seen:raise ValueError('Duplicate citation admission')
        seen.add(m['card_id']);card=cards[m['card_id']];original_card_sha256=sha(pretty(card))
        if card['kind']!='citation_navigation':raise ValueError('Only explicit citation identities may be admitted')
        bound=[occurrences[o] for o in card['occurrence_ids']];passage_ids={o['passage_id'] for o in bound}
        if len(passage_ids)!=1:raise ValueError('Citation crosses passage scope')
        projection=load(root,PROJECTED+'/provisions/'+m['target'].replace('/','--')+'.json')
        variants=[]
        for u in projection['units']:
            matched=[t for t in walk(u['body_tree']) if t.get('attributes',{}).get('id')==m['structural_id']]
            if not matched:continue
            if len(matched)!=1:raise ValueError('Ambiguous structural locator')
            dest=BASE+'reading-help-law/body/'+m['target']+'/'+u['variant'];source=BASE+'reading-help-law/passage/'+next(iter(passage_ids))
            edge_id=BASE+'reading-help-law-citation/'+sha((m['card_id']+'\0'+source+'\0'+dest).encode())
            edges[edge_id]={'id':edge_id,'source':source,'target':dest,'predicate':DCT,'label':'Printed citation points to retained provision; applicability unreviewed',
              'assertion_status':'normalized','scope':'Exact citation identity only; sibling qualifications and geographical applicability remain separate review tasks.',
              'authority':{'class':'derived','label':'Printed citation normalisation','source':REPO+AUTHORING+'/citation-admission.json'},
              'provenance':[{'url':sources[s['source_id']]['pdf_url']+'#page='+str(s['page']),'source_sha256':sources[s['source_id']]['pdf_sha256'],
                  'literal_sha256':s['literal_sha256'],'locator':f"Citation card {card['id']}; PDF page {s['page']}; extracted UTF-8 bytes {s['page_start_utf8']}:{s['page_end_utf8']}"} for s in card['source_support']]}
            variants.append({'record_id':dest,'variant':u['variant'],'structural_id':m['structural_id'],'source_native_url':u['version_url']+'#'+m['structural_id']})
        if not variants:raise ValueError('No retained source target for '+m['card_id'])
        # Source-native metadata confirms the dated generic provision route; both variants remain visible in the context.
        url=projection['metadata']['document_identifier'].replace('http:','https:')+'#'+m['structural_id']
        card['target']={'status':'resolved','url':url,'label':'Open dated official provision: '+m['target'].split('/',3)[-1]}
        card['body']+=' The separately captured provision contains this structural locator. This resolves navigation only; legal applicability and dependency completeness remain unreviewed.'
        outcomes.append({**m,'variants':variants,'source_card_sha256':original_card_sha256})
    if any(cards[c]['target']['status']!='unresolved' for c in admission['unresolved_cards']):raise ValueError('Unsupported reference silently resolved')
    inputs=[BASELINE,REFERENCE,AUTHORING+'/citation-admission.json',AUTHORING+'/context-overlay.json','scripts/build_reading_help_law_context.py']
    bindings=[{'path':p,'sha256':sha(read_safe(root,p))} for p in inputs];snapshot='reading-help-law-'+sha(pretty(bindings))[:20]
    index['records']=sorted(records.values(),key=lambda r:r['id']);index['assertions']=sorted(edges.values(),key=lambda r:r['id'])
    index['bundle']={**index['bundle'],'id':BASE+'bundle/reading-help-law','snapshot':snapshot}
    index['scope']='Selected staff evidence plus a bounded Chapter 60 citation bridge; this index is not full-corpus search.'
    index['limitations']=list(dict.fromkeys(index['limitations']+LIMITATIONS))
    if index['requirements']!=before['requirements']:raise ValueError('Requirements changed')
    helper['limitations'].append('New dated statutory links resolve source navigation only. Select territorial variants and review dependencies separately.')
    helper['proposal_inputs']['citation_admission']={'path':AUTHORING+'/citation-admission.json','sha256':sha(read_safe(root,AUTHORING+'/citation-admission.json'))}
    outputs={AUTHORING+'/assembly-index.json':pretty(index),'reading-help-ch60-law.json':pretty(helper)}
    if len(outputs['reading-help-ch60-law.json'])>256*1024 or len(outputs[AUTHORING+'/assembly-index.json'])>8*1024*1024:raise ValueError('Consumer byte limit exceeded')
    receipt={'schema':'okf-reading-help-law-admission.v1','snapshot':snapshot,'bindings':bindings,'citation_mappings':outcomes,
      'added_records':len(records)-len(before['records']),'added_relationships':len(edges)-len(before['assertions']),
      'preserved_requirements':len(index['requirements']),'deployed_service':'unchanged; this optional context is explicitly selected',
      'unresolved_cards':admission['unresolved_cards'],'limitations':LIMITATIONS,
      'outputs':[{'path':p,'bytes':len(b),'sha256':sha(b)} for p,b in outputs.items()]}
    outputs[AUTHORING+'/admission.json']=pretty(receipt);return outputs

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');args=parser.parse_args()
    for path,raw in build().items():
        if args.check:
            if read_safe(ROOT,path)!=raw:raise ValueError('Stale admitted output '+path)
        else:(ROOT/path).write_bytes(raw)
    print('PASS: explicit citation admission; original requirements and sources preserved')
if __name__=='__main__':main()
