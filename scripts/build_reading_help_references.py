#!/usr/bin/env python3
"""Add exact footer occurrences to a separate, v1-compatible Chapter 60 aid."""
import argparse
import json
from copy import deepcopy
from pathlib import Path
from acquire_legal_bodies import sha, pretty
from build_reading_help import build as verify_baseline
from build_legal_body_evidence import read_safe

ROOT=Path(__file__).resolve().parents[1]
AUTHOR='domain-profile/reading-help-law/reference-links.json'
OUTPUT='reading-help-ch60-references.json'

def build(root=ROOT):
    author=json.loads(read_safe(root,AUTHOR));raw=read_safe(root,author['baseline_path'])
    if sha(raw)!=author['baseline_sha256']:raise ValueError('Baseline manifest hash differs')
    # The earlier source checker must still pass; never replace its critical
    # source/body occurrence bindings just to admit a footer.
    expected=pretty(verify_baseline())
    if expected!=raw:raise ValueError('Earlier reading-help baseline differs')
    manifest=deepcopy(json.loads(raw));cards={c['id']:c for c in manifest['cards']};occ={o['id']:o for o in manifest['occurrences']}
    passages={p['id']:p for p in manifest['passages']};sources={s['id']:s for s in manifest['sources']}
    seen=set()
    for link in author['links']:
        card=cards[link['card_id']];body=occ[link['body_occurrence_id']];footer=link['footer_support']
        if body['role']!='source_marker' or body['id'] not in card['occurrence_ids']:raise ValueError('Unbound body occurrence')
        if footer['source_id']!=body['source_id']:raise ValueError('Footer escaped its document')
        if footer not in card['source_support']:raise ValueError('Footer is not existing exact support')
        if link['footer_occurrence_id'] in occ or card['id'] in seen:raise ValueError('Duplicate footer mapping')
        seen.add(card['id']);p=passages[body['passage_id']]
        if not any(s['page']==footer['page'] and s['page_start_utf8']<=footer['page_start_utf8']<footer['page_end_utf8']<=s['page_end_utf8'] for s in p['spans']):raise ValueError('Footer escaped its passage')
        source=sources[footer['source_id']];pages_raw=read_safe(root,source['pages_url'])
        if sha(pages_raw)!=source['pages_sha256']:raise ValueError('Source hash mismatch')
        text=next(x['text'] for x in json.loads(pages_raw)['pages'] if x['page']==footer['page']).encode()
        literal=text[footer['page_start_utf8']:footer['page_end_utf8']]
        if literal.decode()!=footer['quote'] or sha(literal)!=footer['literal_sha256']:raise ValueError('Footer span mismatch')
        for old in occ.values():
            if old['source_id']==footer['source_id'] and old['page']==footer['page'] and old['page_start_utf8']<footer['page_end_utf8'] and footer['page_start_utf8']<old['page_end_utf8']:raise ValueError('Footer overlaps an existing occurrence')
        item={'id':link['footer_occurrence_id'],'passage_id':body['passage_id'],'source_id':footer['source_id'],'page':footer['page'],
              'page_start_utf8':footer['page_start_utf8'],'page_end_utf8':footer['page_end_utf8'],'literal':footer['quote'],
              'literal_sha256':footer['literal_sha256'],'role':'source_marker'}
        manifest['occurrences'].append(item);occ[item['id']]=item;card['occurrence_ids'].append(item['id'])
    if len(seen)!=20:raise ValueError('Expected all 20 explicit body/reference pairs')
    manifest['limitations'].append('Reference-row links use explicit existing card and occurrence identities. Selecting a footer does not resolve malformed legal citations or establish applicability. The frozen v1 demonstration remains separately available.')
    return pretty(manifest)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');a=p.parse_args();raw=build()
    if a.check:
        if read_safe(ROOT,OUTPUT)!=raw:raise ValueError('Stale reference aid')
    else:(ROOT/OUTPUT).write_bytes(raw)
    print('PASS 20 exact body/reference-row pairs; original Chapter 60 manifest unchanged')
if __name__=='__main__':main()
