#!/usr/bin/env python3
"""Review an in-memory structural build without installing any projection."""
import argparse
from collections import Counter
import gzip
import json
from pathlib import Path

from build_bundle import ROOT, canonical
from build_passage_boundary_units import compile_units
from build_logical_units import sha, require


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();output=ROOT/args.output
    require(not output.exists(),'Use a fresh census directory')
    output.mkdir(parents=True)
    protocol_path=ROOT/'domain-profile/passage-boundary-review/parked-census-protocol.json'
    protocol=json.loads(protocol_path.read_bytes());ref=protocol['source_manifest']
    baseline_raw=(ROOT/ref['path']).read_bytes()
    require(sha(baseline_raw)==ref['sha256'] and len(baseline_raw)==ref['bytes'],'Frozen baseline differs')
    baseline=json.loads(baseline_raw)
    runner=Path(__file__).read_bytes()
    bindings={p:sha((ROOT/p).read_bytes()) for p in ['scripts/evaluate_passage_boundary_candidate.py','scripts/passage_boundary_parser.py','scripts/manual_navigation_regions.py','scripts/build_passage_boundary_units.py']}
    try:
        products=compile_units();candidate=json.loads(products['manifest.json'])
        require(candidate['counts']['source_text_bytes']==baseline['counts']['source_text_bytes'],'Source bytes changed')
        require(candidate['counts']['documents']==baseline['counts']['documents']==513,'Document census changed')
        require(candidate['counts']['authored_units']==baseline['counts']['authored_units']==75,'Authored count changed')
        before_refs={(d['family'],d['document_id']):d for d in baseline['documents']}
        after_refs={(d['family'],d['document_id']):d for d in candidate['documents']}
        require(set(before_refs)==set(after_refs),'Document identities changed')
        reviews=json.loads((ROOT/protocol['reviewed_expectations']['path']).read_bytes())
        require(sha((ROOT/protocol['reviewed_expectations']['path']).read_bytes())==protocol['reviewed_expectations']['sha256'],'Review expectations changed')
        groups={}
        for item in reviews['items']:groups.setdefault(item['document_id'],[]).append(item)
        changed=[];authored_checked=0;items=[]
        for key,bref in before_refs.items():
            aref=after_refs[key]
            old=json.loads(gzip.decompress((ROOT/'structured-units'/bref['path']).read_bytes()))
            new=json.loads(gzip.decompress(products[aref['path']]))
            require(old['source']==new['source'],'Frozen document source identity changed')
            old_auth={u['id']:u for u in old['units'] if u.get('authored')}
            new_auth={u['id']:u for u in new['units'] if u.get('authored')}
            require(old_auth==new_auth,'Authored units changed');authored_checked+=len(old_auth)
            old_records={u['id']:u['record_sha256'] for u in old['units']}
            new_records={u['id']:u['record_sha256'] for u in new['units']}
            if old_records!=new_records:
                changed.append({'family':key[0],'document_id':key[1],'source_role':new['source']['role'],
                    'before_units':len(old_records),'after_units':len(new_records),
                    'unchanged_record_ids':len([i for i in old_records if new_records.get(i)==old_records[i]]),
                    'removed_ids':len(set(old_records)-set(new_records)),
                    'added_ids':len(set(new_records)-set(old_records)),
                    'before_roles':dict(Counter(u['role'] for u in old['units'])),
                    'after_roles':dict(Counter(u['role'] for u in new['units']))})
            for review in groups.get(key[1],[]):
                old_unit=next(u for u in old['units'] if u['id']==review['unit_id'])
                def overlaps(unit):
                    return any(a['page']==b['page'] and max(a['start_utf8'],b['start_utf8'])<min(a['end_utf8'],b['end_utf8'])
                        for a in old_unit['spans'] for b in unit['spans'])
                overlap=[u for u in new['units'] if overlaps(u)]
                probes=[]
                for evidence in review['evidence']:
                    containing=[u for u in new['units'] if any(s['page']==evidence['page'] and s['start_utf8']<=evidence['start_utf8']<s['end_utf8'] for s in u['spans'])]
                    require(len(containing)==1,'Review probe is not covered once')
                    unit=containing[0];probes.append({'source':evidence,'unit_id':unit['id'],'role':unit['role'],'paragraph_labels':unit['paragraph_labels'],'completeness':unit['completeness']})
                items.append({'number':review['number'],'document_id':key[1],'classification':review['classification'],
                    'old_unit_id':old_unit['id'],'old_paragraph_labels':old_unit['paragraph_labels'],'old_text_bytes':old_unit['text_bytes'],
                    'intersecting_units':[{'id':u['id'],'role':u['role'],'paragraph_labels':u['paragraph_labels'],'text_bytes':u['text_bytes'],
                        'spans':u['spans'],'boundary_status':u['boundary_status'],'completeness':u['completeness']} for u in overlap],
                    'source_probes':probes,'review_status':'candidate-boundaries-require-independent-review'})
        require(authored_checked==75,'Authored preservation denominator differs')
        for p,h in bindings.items():require(sha((ROOT/p).read_bytes())==h,'Implementation changed during census')
        require(Path(__file__).read_bytes()==runner,'Runner changed')
        require((ROOT/ref['path']).read_bytes()==baseline_raw,'Frozen source projection changed during census')
        report={'schema':'okf-dwp-amendment-structure-census.v1','protocol':protocol,'implementation_bindings':bindings,
            'candidate_manifest_sha256':sha(products['manifest.json']),'baseline_counts':baseline['counts'],'candidate_counts':candidate['counts'],
            'documents':513,'original_source_bytes':candidate['counts']['source_text_bytes'],'authored_units_exact':authored_checked,
            'changed_documents':changed,'changed_document_count':len(changed),'source_cases':sorted(items,key=lambda i:i['number']),
            'projected_outputs_installed':False,'context_assemblies':0,'network_calls':0,'model_calls':0,
            'limitations':['Full source reconstruction is enforced by segment_source for every document.','This in-memory build does not install source/context projections or establish legal boundaries.','Role and unit-ID changes require independent review and any affected authored-selection rebinding before integration.']}
        (output/'report.json').write_bytes(canonical(report));(output/'candidate-manifest.json').write_bytes(products['manifest.json'])
        print(json.dumps({'documents':513,'source_bytes':report['original_source_bytes'],'authored_exact':75,'changed_documents':len(changed),'units':candidate['counts']['units']}))
    except Exception as error:
        (output/'failure.json').write_bytes(canonical({'error':str(error),'implementation_bindings':bindings}))
        raise


if __name__=='__main__':main()
