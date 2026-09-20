#!/usr/bin/env python3
"""Bounded optional re-observation of public legislation effect-identifier digests.

Never called by offline checks. Writes a new receipt, not a source refresh or
credential-scanner bypass. No opaque identifier values or XML bodies are retained.
"""
from concurrent.futures import ThreadPoolExecutor
import argparse
import json
from pathlib import Path
import xml.etree.ElementTree as ET

from acquire_legal_reconciliation import fetch, pretty, sha

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "source/legal-discovery-2026-09-20"
MAX_REQUESTS = 21


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-official",action="store_true")
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    if not args.verify_official:
        parser.error("Explicit --verify-official is required for network observation")
    if args.output.exists():
        parser.error("Preserve existing receipts; choose a new output path")
    rows=[];expected=set()
    for path in sorted((SOURCE/"legislation").glob("*.json")):
        value=json.loads(path.read_text())
        identities={e["effect_identifier_sha256"] for e in value.get("metadata",{}).get("effect_metadata",[])}
        if identities:
            rows.append((path,value,identities));expected|=identities
    remaining=set(expected);selected=[]
    while remaining:
        row=max(rows,key=lambda r:len(r[2]&remaining))
        selected.append(row);remaining-=row[2]
    if len(selected)>MAX_REQUESTS:
        raise ValueError("Verification request census exceeds budget")

    def check(row):
        path,value,identities=row
        body,receipt=fetch(value["receipt"]["requested_url"])
        result={"observation_path":str(path.relative_to(ROOT)),"receipt":receipt,
                "expected_identifier_sha256":sorted(identities)}
        if body is None:
            return {**result,"status":"failed"}
        if b"<!DOCTYPE" in body.upper() or b"<!ENTITY" in body.upper():
            raise ValueError("XML entities are not accepted")
        matches=[];ordinal=0
        for element in ET.fromstring(body).iter():
            if element.tag.rsplit("}",1)[-1] not in {"Effect","UnappliedEffect"}:
                continue
            ordinal+=1
            identifier=element.get("EffectId")
            if identifier and sha(identifier.encode()) in expected:
                matches.append({"effect_identity_sha256":sha(identifier.encode()),"element":element.tag,
                    "effect_element_ordinal":ordinal,"source_row":element.get("Row"),
                    "uri_matches_official_effect_identifier":element.get("URI")=="http://www.legislation.gov.uk/id/effect/"+identifier})
        observed={m["effect_identity_sha256"] for m in matches}
        return {**result,"status":"all-expected-identifiers-observed" if identities<=observed else "some-identifiers-not-observed",
                "observations":matches}

    with ThreadPoolExecutor(max_workers=4) as pool:
        observations=list(pool.map(check,selected))
    verified={e["effect_identity_sha256"] for row in observations for e in row.get("observations",[])}
    output={"schema":"okf-public-effect-identifier-verification.v1",
        "scope":"Read-only official XML Effect/UnappliedEffect identity-digest observations; no credentials or body retention.",
        "maximum_requests":MAX_REQUESTS,"actual_requests":len(observations),"response_bodies_retained":False,
        "expected_distinct_identifiers":len(expected),"verified_distinct_identifiers":len(expected&verified),
        "all_expected_identifiers_observed":expected<=verified,"observations":observations}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_bytes(pretty(output))
    print(json.dumps({k:output[k] for k in ["actual_requests","expected_distinct_identifiers","verified_distinct_identifiers","all_expected_identifiers_observed"]}))


if __name__=="__main__":
    main()
