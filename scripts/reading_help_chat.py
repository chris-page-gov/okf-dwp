#!/usr/bin/env python3
"""Export complete unresolved source packs and quarantine checked Chat replies."""
from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path

from build_logical_units import Inputs, canonical, require, sha

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "okf-reading-help-chat.v1"
MAX_PACK = 1024 * 1024


def safe_output(path):
    path = path.absolute()
    require(not path.exists() and path.parent.is_dir(), "Output must be new and its parent must exist")
    require(path.is_relative_to(Path("/Users/crpage/tmp")) or path.is_relative_to(
        ROOT / "evaluation/reading-help-rollout/chat-imports"), "Output must stay in tmp or evaluation quarantine")
    require(not any(p.is_symlink() for p in [path, *path.parents] if p.exists()), "Symlink output path")
    return path


def read_json(path, expected=None, limit=16*1024*1024):
    raw = Inputs(ROOT).read(path, expected, limit=limit)
    return json.loads(raw)


def document(document_id):
    catalogue = read_json("reading-help-corpus/manifest.json")
    found = [d for d in catalogue["documents"] if d["document_id"] == document_id]
    require(len(found) == 1, "Unknown document")
    return read_json(found[0]["path"], found[0]["sha256"])


def bound_passages(index):
    result = {}
    for leaf in index["leaves"]:
        packed = Inputs(ROOT).read(leaf["path"], leaf["sha256"], leaf["bytes"])
        decoded = gzip.decompress(packed)
        require(len(decoded) == leaf["decoded_bytes"] and len(decoded) <= 256*1024
                and sha(decoded) == leaf["decoded_sha256"], "Leaf decoded binding differs")
        for row in json.loads(decoded)["passages"]:
            item = result.setdefault(row["id"], {"parts": {}, "segment_count": row["segment_count"],
                   "text_sha256": row["text_sha256"], "unit_sha256": row["unit_sha256"],
                   "source_spans": row["source_spans"], "reference_list_segments": [],
                   "occurrences": [], "cards": [], "leaf_refs": []})
            ordinal = row["segment"]["ordinal"]
            require(ordinal not in item["parts"], "Duplicate passage segment")
            item["parts"][ordinal] = row["segment"]["text"]
            item["reference_list_segments"].extend(row["reference_list_segments"])
            item["occurrences"].extend(row["occurrences"])
            item["cards"].extend(row["cards"])
            item["leaf_refs"].append({"path": leaf["path"], "sha256": leaf["sha256"],
                                      "occurrence_ids": [o["id"] for o in row["occurrences"]]})
    for item in result.values():
        require(set(item["parts"]) == set(range(item["segment_count"])), "Incomplete passage")
        text = "".join(item["parts"][i] for i in range(item["segment_count"]))
        require(sha(text.encode()) == item["text_sha256"], "Complete source text differs")
        item["text"] = text
        del item["parts"]
    return result


def export(document_id, limit, output):
    output = safe_output(output)
    index = document(document_id)
    source = bound_passages(index)
    pack = {"schema": SCHEMA, "document_id": document_id, "family": index["family"],
            "source_sha256": index["source"]["sha256"],
            "extraction_sha256": index["extraction"]["sha256"],
            "rules_sha256": index["rules_sha256"], "complete": True,
            "passages": {}, "requests": [], "skipped": [],
            "instruction": "Suggest reading help only. Quote exact source occurrences; retain ambiguity and legal uncertainty."}
    for passage_id, passage in source.items():
        for card in passage["cards"]:
            if card["status"] not in ("unresolved", "ambiguous"):
                continue
            if len(pack["requests"]) >= limit:
                break
            occurrence = next(o for o in passage["occurrences"] if o["id"] == card["occurrence_id"])
            ident = sha(canonical([document_id, card["id"], index["rules_sha256"]]))[:24]
            if len(canonical(passage)) > 96*1024:
                pack["skipped"].append({"request_id": ident, "passage_id": passage_id,
                                        "reason": "complete-passage-exceeds-bound"})
                pack["complete"] = False
                continue
            pack["passages"][passage_id] = passage
            pack["requests"].append({"request_id": ident, "passage_id": passage_id,
                                     "unit_sha256": passage["unit_sha256"],
                                     "occurrence": occurrence, "card": card})
            if len(canonical(pack)) > MAX_PACK - 8192:
                pack["requests"].pop()
                if not any(r["passage_id"] == passage_id for r in pack["requests"]):
                    del pack["passages"][passage_id]
                pack["skipped"].append({"request_id": ident, "passage_id": passage_id,
                                        "reason": "pack-exceeds-bound"})
                pack["complete"] = False
    require(pack["requests"] or pack["skipped"], "No unresolved candidates")
    data = canonical(pack)
    require(len(data) <= MAX_PACK, "Pack byte bound")
    output.write_bytes(data)
    print(json.dumps({"requests": len(pack["requests"]), "skipped": len(pack["skipped"]),
                      "sha256": sha(data), "path": str(output)}))


def import_replies(requests, request_hash, replies, output):
    output = safe_output(output)
    raw = requests.read_bytes()
    require(len(raw) <= MAX_PACK and sha(raw) == request_hash, "Request pack size/hash differs")
    pack = json.loads(raw)
    require(pack["schema"] == SCHEMA and len(pack["requests"]) <= 24, "Invalid request pack")
    index = document(pack["document_id"])
    require(pack["source_sha256"] == index["source"]["sha256"] and
            pack["extraction_sha256"] == index["extraction"]["sha256"] and
            pack["rules_sha256"] == index["rules_sha256"], "Current document binding differs")
    current = bound_passages(index)
    issued = {}
    for request in pack["requests"]:
        passage = current[request["passage_id"]]
        require(pack["passages"][request["passage_id"]] == passage and
                request["unit_sha256"] == passage["unit_sha256"] and
                request["occurrence"] in passage["occurrences"] and
                request["card"] in passage["cards"], "Request/card/source passage differs")
        require(request["request_id"] not in issued, "Duplicate request")
        issued[request["request_id"]] = request
    reply_raw = replies.read_bytes()
    require(len(reply_raw) <= 128*1024, "Reply file exceeds bound")
    accepted = []
    for line in reply_raw.splitlines():
        require(len(line) <= 4096 and len(accepted) < 24, "Reply line/count bound")
        reply = json.loads(line)
        require(set(reply) == {"schema", "request_id", "occurrence_id", "literal_sha256",
                               "status", "proposal"}, "Wrong reply shape")
        require(reply["schema"] == SCHEMA and reply["request_id"] in issued,
                "Unknown response identity")
        occurrence = issued[reply["request_id"]]["occurrence"]
        require(reply["occurrence_id"] == occurrence["id"] and
                reply["literal_sha256"] == occurrence["literal_sha256"], "Exact source occurrence differs")
        require(reply["status"] in ("proposed", "unresolved", "rejected") and
                isinstance(reply["proposal"], str) and len(reply["proposal"]) <= 2000,
                "Invalid bounded proposal")
        accepted.append({**reply, "review_status": "unreviewed", "publication_status": "excluded",
                         "request_pack_sha256": request_hash})
    require(len({r["request_id"] for r in accepted}) == len(accepted), "Duplicate response")
    data = b"".join(canonical(row) for row in accepted)
    output.write_bytes(data)
    print(json.dumps({"imported": len(accepted), "sha256": sha(data), "path": str(output)}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    e = commands.add_parser("export")
    e.add_argument("--document-id", required=True)
    e.add_argument("--limit", type=int, default=12)
    e.add_argument("--output", type=Path, required=True)
    i = commands.add_parser("import")
    i.add_argument("--requests", type=Path, required=True)
    i.add_argument("--requests-sha256", required=True)
    i.add_argument("--replies", type=Path, required=True)
    i.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "export":
        require(1 <= args.limit <= 24, "Export limit must be 1 to 24")
        export(args.document_id, args.limit, args.output)
    else:
        import_replies(args.requests, args.requests_sha256, args.replies, args.output)


if __name__ == "__main__":
    main()
