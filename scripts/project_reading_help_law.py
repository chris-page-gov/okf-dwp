#!/usr/bin/env python3
"""Offline variant-preserving re-projection of already captured legal responses."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
from acquire_legal_bodies import safe_tree, pretty, sha, local, public_ref, OPAQUE, text_of
from acquire_legal_reconciliation import legislative_metadata

ROOT=Path(__file__).resolve().parents[1]
SOURCE='source/reading-help-law-2026-09-26'
OUTPUT='source/reading-help-law-2026-09-26-v2'
DATE='2026-09-20'

def complete_text(tree):
    """Retain all visible text slots, including punctuation-only trailing blocks."""
    blocks=[]
    def add(value):
        value=re.sub(r'\s+',' ',value or '').strip()
        if value:blocks.append(value)
    def visit(node):
        if local(node['tag']) in {'Text','Pnumber','Number','Title','AppendText','Addition'}:
            add(text_of(node));return
        add(node.get('text'))
        for child in node['children']:
            visit(child);add(child.get('tail'))
    visit(tree)
    return '\n'.join(blocks)

def project(data, target, date=DATE):
    if b'<!DOCTYPE' in data.upper() or b'<!ENTITY' in data.upper():raise ValueError('DTD/entity rejected')
    root=ET.fromstring(data);parents={child:parent for parent in root.iter() for child in parent}
    canonical='http://www.legislation.gov.uk/id/'+target
    elements=[e for e in root.iter() if e.get('IdURI')==canonical]
    if not elements:raise ValueError('Canonical unit absent')
    metadata=legislative_metadata(data,target)
    prefix='http://www.legislation.gov.uk/'+target
    if metadata['document_identifier'] != prefix+'/'+date:raise ValueError('Requested metadata version differs')
    pattern=re.compile(re.escape(prefix)+r'(?:/(england\+wales|scotland|england|wales|northernireland))?/'+re.escape(date)+r'$')
    seen=set();units=[];omissions=[];refs=set()
    for ordinal,element in enumerate(elements,1):
        uri=element.get('DocumentURI','');match=pattern.fullmatch(uri)
        if not match or uri in seen:raise ValueError('Ambiguous, duplicate or undated variant identity')
        seen.add(uri);restrictions=[];headings=[];cursor=element
        while cursor is not None:
            attrs={k:v for k,v in cursor.attrib.items() if k in {'IdURI','DocumentURI','RestrictExtent','RestrictStartDate','RestrictEndDate','Status'}}
            if attrs:restrictions.append({'element':local(cursor.tag),'attributes':attrs})
            for child in cursor:
                if local(child.tag)=='Title':
                    title=re.sub(r'\s+',' ',''.join(child.itertext())).strip()
                    if title and title not in headings:headings.append(title)
            cursor=parents.get(cursor)
        tree=safe_tree(element,omissions,'variant-'+str(ordinal));text=complete_text(tree)
        if not text or len(text.encode())>131072:raise ValueError('Complete selected variant exceeds byte budget')
        commentary={e.get('Ref') for e in element.iter() if local(e.tag)=='CommentaryRef' and e.get('Ref')};refs.update(commentary)
        units.append({'canonical_identifier':canonical,'source_native_document_uri':uri,'version_url':uri.replace('http:','https:',1),
            'target':target,'variant':match.group(1) or 'unqualified-source-route','source_xml_ordinal':ordinal,
            'body_tree':tree,'body_text':text,'body_text_sha256':sha(text.encode()),
            'ancestor_headings_nearest_first':headings,'target_and_ancestor_restrictions':restrictions,
            'commentary_ids':sorted(public_ref(x) for x in commentary),
            'applicability':'unresolved; a source route is not an applicability decision'})
    lookup={e.get('id'):e for e in root.iter() if local(e.tag)=='Commentary'}
    notes=[];missing=[]
    for ref in sorted(refs):
        if ref not in lookup:missing.append(public_ref(ref));continue
        tree=safe_tree(lookup[ref],omissions,'commentary/'+public_ref(ref))
        notes.append({'id':public_ref(ref),'tree':tree,'text':complete_text(tree)})
    result={'schema':'okf-reading-help-law-projection.v2','target':target,'requested_version_date':date,
        'metadata':metadata,'units':units,'commentaries':notes,'missing_commentary_ids':missing,'omitted_attributes':omissions,
        'status':'all-observed-target-variants-retained','response_sha256':sha(data),
        'projection_policy':'Complete selected XML subtrees and every visible text slot; whitespace normalised; opaque attributes omitted with hashes. All observed canonical-target variants retained independently. Metadata and editorial commentary remain distinct. Public projection is lossy; exact raw response is retained only in the audit cache.',
        'dependency_status':'not-a-complete-dependency-set','legal_review':'not-specialist-reviewed'}
    if OPAQUE.search(pretty(result).decode()):raise ValueError('Opaque identifier remains')
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--raw-cache',type=Path,required=True);args=parser.parse_args()
    dest=ROOT/OUTPUT
    if dest.exists():raise ValueError('Projection snapshot exists; preserve it')
    prior=(ROOT/SOURCE/'manifest.json').read_bytes();manifest=json.loads(prior)
    for row in manifest['files']:
        raw=(ROOT/SOURCE/row['path']).read_bytes()
        if sha(raw)!=row['sha256'] or len(raw)!=row['bytes']:raise ValueError('Acquisition file mismatch')
    files=[];dest.mkdir(parents=True)
    for path in sorted((ROOT/SOURCE/'provisions').glob('*.json')):
        original=json.loads(path.read_bytes());receipt=original['receipt']
        if receipt['status']!='observed':continue
        raw=(args.raw_cache/receipt['response_sha256']).read_bytes()
        if sha(raw)!=receipt['response_sha256'] or len(raw)!=receipt['response_bytes']:raise ValueError('Raw audit-cache binding mismatch')
        projection=project(raw,original['target']);projection['receipt']=receipt
        projection['previous_attempt_status']=original['status']
        data=pretty(projection);name='provisions/'+path.name;(dest/'provisions').mkdir(exist_ok=True);(dest/name).write_bytes(data)
        files.append({'path':name,'bytes':len(data),'sha256':sha(data)})
    result={'schema':'okf-reading-help-law-reprojection.v1','prior_snapshot':SOURCE,'prior_manifest_sha256':sha(prior),
        'network_requests':0,'files':files,'projector_sha256':sha(Path(__file__).read_bytes()),
        'comparison_date':DATE,'scope':'All observed variants of three previously acquired provisions; applicability unresolved.'}
    (dest/'manifest.json').write_bytes(pretty(result));print('Retained offline variant projections:',len(files))

if __name__=='__main__':main()
