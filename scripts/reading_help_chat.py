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
    """Resolve the authorised tmp relocation, then confine the actual parent."""
    path = path.expanduser().absolute()
    roots = (Path("/Users/crpage/tmp").resolve(strict=True),
             (ROOT / "evaluation/reading-help-rollout/chat-imports").resolve())
    require(path.parent.is_dir(), "Output parent must exist")
    parent = path.parent.resolve(strict=True)
    require(any(parent == root or parent.is_relative_to(root) for root in roots),
            "Output must stay in tmp or evaluation quarantine")
    require(not path.is_symlink() and not path.exists(), "Output must be a new regular file")
    return parent / path.name


def write_new(path, data):
    with path.open("xb") as stream:
        stream.write(data)


def bounded_file(path, limit):
    require(path.is_file() and not path.is_symlink(), "Input must be a regular file")
    with path.open("rb") as stream:
        data = stream.read(limit + 1)
    require(len(data) <= limit, "Input exceeds byte bound")
    return data


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
            "rules_sha256": index["rules_sha256"], "complete_selected_passages": True,
            "total_candidate_count": sum(c["status"] in ("unresolved", "ambiguous")
                for passage in source.values() for c in passage["cards"]),
            "selected_count": 0, "selection_truncated": False, "skipped_count": 0,
            "passages": {}, "requests": [], "skipped": [],
            "instruction": "Suggest reading help only. Quote exact source occurrences; retain ambiguity and legal uncertainty.",
            "reply_json_schema": {"type": "object", "additionalProperties": False,
                "required": ["schema", "request_id", "occurrence_id", "literal_sha256", "status", "proposal"],
                "properties": {"schema": {"const": SCHEMA}, "request_id": {"type": "string"},
                    "occurrence_id": {"type": "string"}, "literal_sha256": {"type": "string"},
                    "status": {"enum": ["proposed", "unresolved", "rejected"]},
                    "proposal": {"type": "string", "maxLength": 2000}}}}
    for passage_id, passage in source.items():
        for card in passage["cards"]:
            if card["status"] not in ("unresolved", "ambiguous"):
                continue
            if len(pack["requests"]) >= limit:
                pack["selection_truncated"] = True
                continue
            occurrence = next(o for o in passage["occurrences"] if o["id"] == card["occurrence_id"])
            ident = sha(canonical([document_id, card["id"], index["rules_sha256"]]))[:24]
            if len(canonical(passage)) > 96*1024:
                pack["skipped_count"] += 1
                if len(pack["skipped"]) < 24:
                    pack["skipped"].append({"request_id": ident, "passage_id": passage_id,
                                            "reason": "complete-passage-exceeds-bound"})
                pack["selection_truncated"] = True
                continue
            pack["passages"][passage_id] = passage
            pack["requests"].append({"request_id": ident, "passage_id": passage_id,
                                     "unit_sha256": passage["unit_sha256"],
                                     "occurrence": occurrence, "card": card})
            if len(canonical(pack)) > MAX_PACK - 8192:
                pack["requests"].pop()
                if not any(r["passage_id"] == passage_id for r in pack["requests"]):
                    del pack["passages"][passage_id]
                pack["skipped_count"] += 1
                if len(pack["skipped"]) < 24:
                    pack["skipped"].append({"request_id": ident, "passage_id": passage_id,
                                            "reason": "pack-exceeds-bound"})
                pack["selection_truncated"] = True
    pack["selected_count"] = len(pack["requests"])
    pack["selection_truncated"] |= pack["selected_count"] < pack["total_candidate_count"]
    require(pack["total_candidate_count"], "No unresolved candidates")
    data = canonical(pack)
    require(len(data) <= MAX_PACK, "Pack byte bound")
    write_new(output, data)
    print(json.dumps({"requests": len(pack["requests"]), "skipped": pack["skipped_count"],
                      "sha256": sha(data), "path": str(output)}))


def import_replies(requests, request_hash, replies, output):
    output = safe_output(output)
    raw = bounded_file(requests, MAX_PACK)
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
    reply_raw = bounded_file(replies, 128*1024)
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
    write_new(output, data)
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
