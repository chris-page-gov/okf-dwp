#!/usr/bin/env python3
"""Add a corpus-enabled Explorer descriptor without rewriting the DMG release."""
import argparse
from copy import deepcopy
import json

from build_bundle import ROOT, canonical, digest, pretty
from build_context_corpus import compile_corpus
from build_context_discovery import require


def compile_explorer(root=ROOT):
    corpus = compile_corpus(root)
    for name, raw in corpus.items():
        require((root / "context/corpus" / name).read_bytes() == raw, "Stale source context corpus")
    original_path = "full-dmg/okf-explorer.json"
    original = (root / original_path).read_bytes()
    descriptor = deepcopy(json.loads(original))
    corpus_manifest = json.loads(corpus["manifest.json"])
    binding = {"path": "context/corpus/manifest.json", "bytes": len(corpus["manifest.json"]),
               "sha256": digest(corpus["manifest.json"])}
    descriptor["entrypoints"]["context_corpus"] = binding
    descriptor["entrypoint_integrity"]["context_corpus"] = binding
    descriptor["title"] = "DWP guidance: DMG Reader and full-source Ask OKF"
    descriptor["description"] = (
        "Independent experimental research. Reader and Search retain the frozen full-DMG release; "
        "Ask OKF also searches the separately captured ADM corpus. Source retrieval is not legal completeness or benefits advice.")
    publication = descriptor["exploratory_publication"]
    publication["limitations"] = [
        "Reader, Search and graph use the frozen DMG release. The separate Ask OKF context corpus includes DMG and ADM source pages.",
        "The original custody completeness profile remains separately available; the corpus discovery profile has no completeness requirements.",
        *["Reader scope: " + value for value in publication["limitations"]],
        *corpus_manifest["limitations"],
    ]
    outputs = {"full-dmg/okf-corpus-context.json": canonical(descriptor)}
    outputs.update({"full-dmg/context/corpus/" + name: raw for name, raw in corpus.items()})
    receipt = {"schema": "okf-dwp-corpus-explorer-projection.v1",
               "source_descriptor": {"path": original_path, "sha256": digest(original)},
               "corpus_snapshot": corpus_manifest["bundle"]["snapshot"],
               "producer": {"path": "scripts/build_context_corpus_explorer.py",
                            "sha256": digest((root / "scripts/build_context_corpus_explorer.py").read_bytes())},
               "files": [{"path": name, "bytes": len(raw), "sha256": digest(raw)} for name, raw in sorted(outputs.items())]}
    outputs["context/corpus-explorer-projection.json"] = pretty(receipt)
    return outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    outputs = compile_explorer()
    for name, raw in outputs.items():
        path = ROOT / name
        if args.check:
            require(path.is_file() and path.read_bytes() == raw, "Stale corpus Explorer projection: " + name)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
    print(json.dumps({"status": "verified" if args.check else "built", "files": len(outputs),
                      "descriptor": "full-dmg/okf-corpus-context.json"}))


if __name__ == "__main__":
    main()
