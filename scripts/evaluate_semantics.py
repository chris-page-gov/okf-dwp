#!/usr/bin/env python3
"""Check evidence and migration acceptance; does not grade legal correctness."""
from copy import deepcopy
import json
from pathlib import Path
from build_bundle import ROOT, load_yaml, canonical, digest
from semantic_authoring import check_relation


def main():
    bundle = json.loads((ROOT / 'bundle/okf-bundle.json').read_text())
    nodes = bundle['nodes']
    authored = [row for path in sorted((ROOT/'knowledge').rglob('*.yamlld')) for row in load_yaml(path).get('@graph', [])]
    proposals = [(row, spec) for row in authored for spec in row.get('semantic_relations', [])]
    for row, spec in proposals:
        check_relation(spec, row, nodes)
    assert proposals, 'Expected semantic proposals'
    row, valid = proposals[0]
    controls = []
    def rejected(name, change):
        spec = deepcopy(valid)
        change(spec)
        try:
            check_relation(spec, row, nodes)
        except (ValueError, TypeError, KeyError):
            controls.append(name)
        else:
            raise AssertionError('Invalid proposal accepted: ' + name)
    rejected('identity-equivalence predicate', lambda x:x.update(predicate='http://www.w3.org/2002/07/owl#sameAs'))
    rejected('unresolved concept', lambda x:x.update(target='term/nonexistent'))
    rejected('missing evidence', lambda x:x.update(evidence=[]))
    rejected('missing rationale', lambda x:x.update(rationale=''))
    rejected('fabricated quotation', lambda x:x['evidence'][0].update(quote='This fabricated rule awards every claimant an extra amount.'))
    rejected('wrong source page', lambda x:x['evidence'][0].update(page='page/79/0001'))
    rejected('fabricated paragraph locator', lambda x:x['evidence'][0].update(locator='DMG 99999'))
    rejected('invented subparagraph', lambda x:x['evidence'][0].update(locator='DMG 78001(999)'))
    # This paragraph is mentioned by the valid passage only as a cross-reference.
    rejected('cross-reference mistaken for paragraph anchor', lambda x:x['evidence'][0].update(locator='DMG 78030'))
    rejected('wrong navigation locator', lambda x:x['evidence'][0].update(locator='DMG chapter 79 section navigation, PDF page 1'))
    rejected('CPAG reference used as source text', lambda x:x['evidence'][0].update(page='resource/cpag-welfare-benefits-handbook'))
    rejected('self relationship', lambda x:x.update(target=row['route']))
    model_edges = [r for r in bundle['relationships'] if r['assertion_status']=='model-derived']
    assert len(model_edges) == len(proposals)
    assert all(r['authority']['class']=='model-assisted' and r['review_status']=='unreviewed-specialist-review-required' for r in model_edges)
    original = ['additional-amounts','assessed-income-period','capital','capital-disregards','carers','children','deemed-weekly-income','deprivation-of-capital','earnings','guarantee-credit','household','housing-costs','income-other-than-earnings','mixed-age-couples','notional-capital','notional-income','part-week-payments','pension-credit','qualifying-age','savings-credit','self-employment','severe-disability']
    for slug in original:
        node=nodes['term/'+slug]
        assert node['@id']=='https://chris-page-gov.github.io/okf-dwp/id/term/'+slug
        assert (ROOT/'knowledge/concepts'/f'{slug}.yamlld').is_file()
    receipt={'schema':'okf-dwp-semantic-pilot-validation.v1','snapshot_id':bundle['snapshot_id'],'status':'passed','source_supported_proposals':len(proposals),'preserved_original_concept_identities':len(original),'negative_controls':controls,'model_relationships_remain_unreviewed':True,'bundle_sha256':digest((ROOT/'bundle/okf-bundle.json').read_bytes()),'not_claimed':['Specialist approval','Behavioural or model benchmark execution','Full-corpus conceptual coverage','Current-law applicability','Executable benefits rules']}
    (ROOT/'validation/semantics.json').write_bytes(canonical(receipt))
    print(json.dumps(receipt,indent=2))

if __name__=='__main__':
    main()
