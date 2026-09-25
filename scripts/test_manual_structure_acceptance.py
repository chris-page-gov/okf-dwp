"""Source-led structure acceptance and negative controls, independent of a parser.

The eight frozen cases are not an answerability or specialist-review gold set.
The parser adapter must emit observed spans/headings/roles, not pass booleans.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "evaluation/manual-structure/protocol.json"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalise(value: str) -> str:
    return " ".join(value.split())


def normalise_heading(value: str) -> str:
    return normalise(re.sub(r"\s*[-–—]\s*", " - ", value))


def load_cases(root: Path = ROOT) -> tuple[dict, list[dict]]:
    protocol = json.loads((root / PROTOCOL.relative_to(ROOT)).read_text())
    cases = []
    for binding in protocol["fixtures"]:
        data = (root / binding["path"]).read_bytes()
        if len(data) != binding["bytes"] or digest(data) != binding["sha256"]:
            raise ValueError(f"Frozen fixture changed: {binding['path']}")
        cases.append(json.loads(data))
    return protocol, cases


def read_pages(case: dict, root: Path = ROOT) -> list[dict]:
    """Verify immutable source bindings before interpreting any observation."""
    source = case["source"]
    for field in ("inventory", "pdf", "pages"):
        binding = source[field]
        data = (root / binding["path"]).read_bytes()
        if len(data) != binding["bytes"] or digest(data) != binding["sha256"]:
            raise ValueError(f"Source identity mismatch: {binding['path']}")
    document = json.loads((root / source["pages"]["path"]).read_text())
    if document["document_id"] != source["document_id"]:
        raise ValueError("Source document identity mismatch")
    if document["source_sha256"] != source["pdf"]["sha256"]:
        raise ValueError("Extraction does not bind the frozen PDF")
    return document["pages"]


def source_bytes(spans: list[dict], pages: list[dict], *, provenance: bool = True) -> bytes:
    """Reject malformed, reordered, duplicate or untraceable source spans."""
    chunks = []
    previous = None
    for span in spans:
        page = span["page"]
        start, end = span["start_byte"], span["end_byte"]
        if any(type(value) is not int for value in (page, start, end)):
            raise ValueError("Source offsets must be integers")
        if not 1 <= page <= len(pages):
            raise ValueError("Source page outside document")
        row = pages[page - 1]
        data = row["text"].encode("utf-8")
        if not 0 <= start < end <= len(data):
            raise ValueError("Source offsets outside page or empty")
        if previous is not None and (page, start) < previous:
            raise ValueError("Source spans are reordered or overlap")
        previous = (page, end)
        part = data[start:end]
        part.decode("utf-8")
        if provenance:
            if span.get("page_text_sha256") != digest(data):
                raise ValueError("Missing or incorrect source-page hash")
            if span.get("span_sha256") != digest(part):
                raise ValueError("Missing or incorrect source-span hash")
            if span.get("url") != row["url"]:
                raise ValueError("Missing or incorrect source-page URL")
        chunks.append(part)
    return b"".join(chunks)


def covers(actual: list[dict], expected: list[dict]) -> bool:
    """Coverage tolerates finer spans, but not a one-byte gap or page omission."""
    for need in expected:
        cursor = need["start_byte"]
        for span in actual:
            if span["page"] != need["page"]:
                continue
            if span["start_byte"] <= cursor < span["end_byte"]:
                cursor = min(need["end_byte"], span["end_byte"])
            if cursor == need["end_byte"]:
                break
        if cursor != need["end_byte"]:
            return False
    return True


def validate_case(case: dict, observation: dict, pages: list[dict]) -> list[str]:
    """Compare real structure observations with source-bound expectations.

    A document observation contains source identity, a complete flat partition,
    coherent units and separately classified structures. Hierarchical unit spans
    may overlap; the accounting partition may not. Report all discovered errors.
    """
    errors: list[str] = []
    expected = case["expectations"]
    for key in ("document_id", "family", "role", "url"):
        if observation.get("source", {}).get(key) != case["source"][key]:
            errors.append(f"source_identity:{key}")
    for key in ("inventory", "pdf", "pages"):
        if observation.get("source", {}).get(key) != case["source"][key]:
            errors.append(f"source_identity:{key}")
    # Independently recompute the byte accounting; reported totals are not proof.
    try:
        partition = observation["partition"]
        source_bytes(partition, pages)
        for row in pages:
            spans = [s for s in partition if s["page"] == row["page"]]
            cursor = 0
            for span in spans:
                if span["start_byte"] != cursor:
                    raise ValueError("Partition gap or overlap")
                cursor = span["end_byte"]
            if cursor != len(row["text"].encode("utf-8")):
                raise ValueError("Partition does not conserve every source byte")
    except (KeyError, TypeError, ValueError, UnicodeDecodeError) as exc:
        errors.append(f"byte_conservation:{exc}")
    units = observation.get("units", [])
    valid_units = []
    for unit in units:
        try:
            data = source_bytes(unit["source_spans"], pages)
            if unit.get("text_sha256") != digest(data):
                raise ValueError("Unit source content hash mismatch")
            if unit.get("specialist_review") != "not-reviewed":
                raise ValueError("Machine structure promoted to specialist review")
            if unit.get("legal_effect_status") is None:
                raise ValueError("Missing explicit unresolved legal boundary")
            if unit.get("legal_effect_status") != "unresolved":
                raise ValueError("Machine structure promoted to legal resolution")
            valid_units.append((unit, data))
        except (KeyError, TypeError, ValueError, UnicodeDecodeError) as exc:
            errors.append(f"provenance:{unit.get('id', '?')}:{exc}")
    primary = case["regions"]["primary"]
    matches = [(unit, data) for unit, data in valid_units
               if covers(unit["source_spans"], primary["spans"])
               and unit.get("role") == expected["primary_role"]]
    if not matches:
        errors.append("complete_passage:no complete unit with expected role")
    else:
        # Deterministic, smallest complete unit. An entire-document fallback
        # cannot conceal an absent coherent passage by supplying the whole book.
        unit, data = min(matches, key=lambda pair: (len(pair[1]), pair[0].get("id", "")))
        text = normalise(data.decode("utf-8"))
        headings = [normalise_heading(h) for h in unit.get("heading_path", [])]
        for field in ("governing_heading", "ancestor_heading"):
            if expected.get(field) and normalise_heading(expected[field]) not in headings:
                errors.append(f"governing_heading:missing {field}")
        for heading in expected.get("forbidden_governing_headings", []):
            if normalise_heading(heading) in headings:
                errors.append("governing_heading:mini-contents promoted")
        for phrase in expected.get("must_contain", []):
            if normalise(phrase) not in text:
                errors.append(f"complete_passage:missing {phrase}")
        for phrase in expected.get("forbidden_primary_text", []):
            if normalise(phrase) in text:
                errors.append(f"complete_passage:absorbs next structure {phrase}")
        for label in expected.get("forbidden_body_labels", []):
            if label in unit.get("paragraph_labels", []):
                errors.append(f"roles:invented body label {label}")
        # References must belong to this passage or an explicit case structure,
        # never be satisfied from any unrelated item in the document.
        scoped_refs = list(unit.get("references", []))
        if "annotations" in case["regions"]:
            for structure in observation.get("structures", []):
                if structure.get("role") == expected.get("annotations_role") and covers(
                        structure.get("source_spans", []), case["regions"]["annotations"]["spans"]):
                    scoped_refs.extend(structure.get("references", []))
        for reference in expected.get("references", []):
            if not any(all(ref.get(key) == value for key, value in reference.items()) for ref in scoped_refs):
                errors.append(f"reference_scope:missing or promoted {reference['target']}")
    for region_name in ("navigation", "disclaimer", "annotations", "contacts"):
        if region_name not in case["regions"]:
            continue
        role = expected.get(region_name + "_role")
        if not role:
            continue
        structures = [s for s in observation.get("structures", [])
                      if s.get("role") == role and covers(s.get("source_spans", []), case["regions"][region_name]["spans"])]
        if not structures:
            errors.append(f"roles:missing {region_name}")
        for structure in structures:
            try:
                source_bytes(structure["source_spans"], pages)
            except (KeyError, TypeError, ValueError, UnicodeDecodeError) as exc:
                errors.append(f"provenance:{region_name}:{exc}")
    if observation.get("source_instructions_inert") is not True:
        errors.append("reference_scope:source instructions not explicitly inert")
    return errors


def validate_stage(protocol: dict, cases: list[dict], stage: str, observations: dict, root: Path = ROOT) -> dict:
    """Return four/eight case results; never convert component count to cases."""
    declaration = next(row for row in protocol["stages"] if row["id"] == stage)
    by_id = {case["id"]: case for case in cases}
    results = []
    for case_id in declaration["case_ids"]:
        case = by_id[case_id]
        try:
            pages = read_pages(case, root)
            document = observations[case["source"]["document_id"]]
            errors = validate_case(case, document, pages)
        except (KeyError, TypeError, ValueError) as exc:
            errors = [f"source_or_observation_missing:{exc}"]
        results.append({"case_id": case_id, "passed": not errors, "failures": errors})
    return {"stage": stage, "case_denominator": declaration["denominator"],
            "passed_cases": sum(row["passed"] for row in results), "cases": results,
            "specialist_review": "not-reviewed", "legal_answerability": "not-established"}


def expected_observation(case: dict, pages: list[dict]) -> dict:
    """Synthetic validator control, never a parser or experiment result."""
    spans = []
    for row in pages:
        data = row["text"].encode("utf-8")
        if data:
            spans.append({"page": row["page"], "start_byte": 0, "end_byte": len(data),
                          "page_text_sha256": digest(data), "span_sha256": digest(data), "url": row["url"]})
    expected = case["expectations"]
    primary = case["regions"]["primary"]
    unit = {"id": "synthetic-validator-control", "source_spans": copy.deepcopy(primary["spans"]),
            "text_sha256": primary["sha256"], "role": expected["primary_role"],
            "heading_path": [expected[key] for key in ("ancestor_heading", "governing_heading") if key in expected],
            "paragraph_labels": [], "references": copy.deepcopy(expected.get("references", [])),
            "specialist_review": "not-reviewed", "legal_effect_status": "unresolved"}
    structures = []
    for name in ("navigation", "disclaimer", "annotations", "contacts"):
        if name in case["regions"] and name + "_role" in expected:
            structures.append({"role": expected[name + "_role"],
                               "source_spans": copy.deepcopy(case["regions"][name]["spans"]),
                               "references": copy.deepcopy(expected.get("references", [])) if name == "annotations" else []})
    return {"source": copy.deepcopy(case["source"]), "partition": spans, "units": [unit],
            "structures": structures, "source_instructions_inert": True}

def adapt_parser_output(case: dict, pages: list[dict], units: list[dict], structure: dict) -> dict:
    """Translate parser fields without supplying missing semantic observations.

    Names/offset encodings differ between the parser and acceptance contract.
    Hashes/URLs are reconstructed from the parser's spans and frozen pages; the
    parser's original literal hashes and joiner hash are checked first.
    """
    from build_logical_units import source_spans as parser_source_spans

    role_names = {"paragraph": "guidance-passage", "reserved": "reserved-range",
                  "contents": "contents-navigation", "contents-entry": "contents-navigation",
                  "annotation": "update-annotation", "contact": "administrative-contact"}

    def spans_of(spans):
        result = []
        for span in spans:
            row = pages[span["page"] - 1]
            data = row["text"].encode()
            start, end = span["start_utf8"], span["end_utf8"]
            if digest(data[start:end]) != span["literal_sha256"]:
                raise ValueError("Parser span hash does not match frozen source")
            result.append({"page": span["page"], "start_byte": start, "end_byte": end,
                           "page_text_sha256": digest(data), "span_sha256": span["literal_sha256"],
                           "url": row["url"]})
        return result

    def references_of(refs):
        output = []
        for ref in refs:
            kind = ref.get("kind")
            if kind is None:
                kind = {"paragraph": "guidance-reference", "chapter": "guidance-reference",
                        "memo": "update-annotation", "legislation": "legislation-citation"}.get(ref.get("target_kind"))
            target = ref.get("target", ref.get("target_label", ""))
            aliases = [target]
            manual = str(ref.get("manual", "")).upper()
            if ref.get("target_kind") == "chapter":
                aliases.append(f"{manual} Chapter {target}")
            elif ref.get("target_kind") in ("paragraph", "memo") and manual:
                aliases.append(f"{manual} {target}")
            # These are equivalent identifier spellings from the actual parsed
            # reference. We never add references by inspecting the fixture.
            status = ref.get("legal_effect_status")
            if status is None and ref.get("legal_dependency") == "not-established":
                status = "unresolved"
            for alias in dict.fromkeys(aliases):
                output.append({"target": alias, "kind": kind, "legal_effect_status": status})
        return output

    converted = []
    for unit in units:
        spans = spans_of(unit["spans"])
        raw = source_bytes(spans, pages)
        joined = b"\n".join(pages[s["page"] - 1]["text"].encode()[s["start_byte"]:s["end_byte"]] for s in spans)
        if unit.get("text_sha256") != digest(joined):
            raise ValueError("Parser unit/joiner content hash does not match source spans")
        headings = list(unit.get("heading_path", []))
        for heading in unit.get("heading_context", []):
            if all(key in heading for key in ("title", "low", "high")):
                suffix = heading["low"] if heading["low"] == heading["high"] else f"{heading['low']} - {heading['high']}"
                headings.append(heading["title"] + " " + suffix)
        status = unit.get("legal_effect_status", structure.get("legal_effect_status"))
        if status is None and unit.get("completeness") == "unresolved":
            status = "unresolved"
        converted.append({"id": unit.get("id", unit.get("key")), "source_spans": spans,
                          "text_sha256": digest(raw), "role": role_names.get(unit.get("role", unit.get("kind")), unit.get("role", unit.get("kind"))),
                          "paragraph_labels": unit.get("paragraph_labels", []), "heading_path": headings,
                          "references": references_of(unit.get("references", [])),
                          "specialist_review": unit.get("specialist_review"), "legal_effect_status": status})
    structures = []
    for region in structure.get("regions", []):
        spans = region.get("spans")
        if spans is None and "start" in region and "end" in region:
            spans = parser_source_spans(pages, region["start"], region["end"])
        if spans is not None:
            structures.append({"role": role_names.get(region["role"], region["role"]),
                               "source_spans": spans_of(spans), "references": references_of(region.get("references", []))})
    # A classified standalone unit may also be an auxiliary structure. This
    # does not turn arbitrary range-heading candidates into navigation regions.
    for unit in converted:
        if unit["role"] in {"contents-navigation", "document-notice", "update-annotation", "administrative-contact"}:
            structures.append({"role": unit["role"], "source_spans": unit["source_spans"], "references": unit["references"]})
    partition = [span for unit in converted for span in unit["source_spans"]]
    partition.sort(key=lambda span: (span["page"], span["start_byte"]))
    return {"source": copy.deepcopy(case["source"]), "partition": partition,
            "units": converted, "structures": structures,
            "structure_provenance": copy.deepcopy(structure.get("pdf_structure", {})),
            "source_instructions_inert": structure.get("source_instructions_inert", False)}


def verify_retained_bindings(bindings, root=ROOT):
    """A passing gate is reusable only with the same consumed source inputs."""
    for binding in bindings:
        raw = (root / binding["path"]).read_bytes()
        if digest(raw) != binding["sha256"] or ("bytes" in binding and len(raw) != binding["bytes"]):
            raise ValueError("Retained run binding changed: " + binding["path"])


def evaluate_source_cases(stage: str, engine: str, output: Path, initial_report: Path | None = None) -> dict:
    """Explicit experiment entry point: retain every result in a fresh directory."""
    import gzip
    import time

    protocol, cases = load_cases()
    if stage == "expanded":
        if initial_report is None:
            raise ValueError("Expanded experiment requires retained passing initial candidate report")
        gate = json.loads(initial_report.read_text())
        if (gate.get("engine") != "candidate" or gate.get("stage") != "initial"
                or gate.get("passed_cases") != 4 or gate.get("case_denominator") != 4):
            raise ValueError("Expanded gate is not a passing four-case candidate run")
        if gate.get("protocol_sha256") != digest(PROTOCOL.read_bytes()):
            raise ValueError("Expanded gate belongs to a different frozen protocol")
        if engine == "candidate":
            verify_retained_bindings(gate.get("implementation_bindings", []))
            verify_retained_bindings(gate.get("consumed_pdf_structure_bindings", []))
            current = {row["path"]: row["sha256"] for row in gate.get("implementation_bindings", [])}
            required = {"scripts/test_manual_structure_acceptance.py", "scripts/passage_boundary_parser.py",
                        "scripts/pdf_structure_alignment.py", "scripts/build_logical_units.py",
                        "scripts/manual_references.py", "scripts/manual_auxiliary_structure.py", "scripts/manual_navigation_regions.py", "scripts/build_pdf_structure.py", "profiles/pdf-structure/v1/document.schema.json"}
            if not required <= current.keys():
                raise ValueError("Expanded gate lacks complete current implementation bindings")
    selected = next(row["case_ids"] for row in protocol["stages"] if row["id"] == stage)
    observations, errors, inputs = {}, {}, []
    consumed_structure = {}
    implementation_paths = ["scripts/test_manual_structure_acceptance.py", "scripts/passage_boundary_parser.py",
                            "scripts/pdf_structure_alignment.py", "scripts/build_logical_units.py",
                            "scripts/manual_references.py", "scripts/manual_auxiliary_structure.py", "scripts/manual_navigation_regions.py", "scripts/build_pdf_structure.py", "profiles/pdf-structure/v1/document.schema.json"]
    before_implementation = [{"path": path, "sha256": digest((ROOT / path).read_bytes())} for path in implementation_paths]
    started = time.perf_counter()
    for case in cases:
        if case["id"] not in selected:
            continue
        pages = read_pages(case)
        source = case["source"]
        inventory = json.loads((ROOT / source["inventory"]["path"]).read_text())
        document = next(row for row in inventory["documents"] if row["id"] == source["document_id"])
        try:
            if engine == "candidate":
                from passage_boundary_parser import segment_source
                units, structure = segment_source(source["family"], document, pages)
                observed_source = structure.get("pdf_structure", {}).get("source")
                if observed_source:
                    path = observed_source["path"]
                    raw_sidecar = (ROOT / path).read_bytes()
                    if digest(raw_sidecar) != observed_source["sha256"]:
                        raise ValueError("Consumed PDF structure changed during evaluation")
                    sidecar = json.loads(raw_sidecar)
                    related = [path, sidecar["tree"]["path"], sidecar["stderr"]["path"]]
                    # Bind the exact retained observation manifest when present.
                    observation_root = Path(path).parent.parent
                    manifest_path = str(observation_root / "manifest.json")
                    if (ROOT / manifest_path).is_file():
                        related.append(manifest_path)
                    for dependency in related:
                        data = (ROOT / dependency).read_bytes()
                        consumed_structure[dependency] = {"path": dependency, "sha256": digest(data), "bytes": len(data)}
            elif engine == "baseline":
                path = ROOT / f"logical-units/documents/{source['family']}/{source['document_id']}.json.gz"
                data = path.read_bytes()
                manifest_path = ROOT / "logical-units/manifest.json"
                binding = next(row for row in protocol["baseline_bindings"] if row["path"] == "logical-units/manifest.json")
                if digest(manifest_path.read_bytes()) != binding["sha256"]:
                    raise ValueError("Baseline manifest changed")
                manifest = json.loads(manifest_path.read_text())
                record = next(row for row in manifest["documents"] if row["document_id"] == source["document_id"])
                if record["sha256"] != digest(data):
                    raise ValueError("Baseline document is not bound by frozen manifest")
                old = json.loads(gzip.decompress(data))
                units = old["units"]
                limitations = old.get("limitations", [])
                structure = {"source_instructions_inert": any("Source instructions remain inert data." in item for item in limitations)}
                if (any("Author-declared completeness means complete within the declared excerpt boundary only." in item for item in limitations)
                        and any("it does not establish complete rules, legal applicability or semantic dependency closure." in item for item in limitations)):
                    structure["legal_effect_status"] = "unresolved"
                structure["retained_catalogue_limitations"] = limitations
                inputs.append({"path": str(path.relative_to(ROOT)), "sha256": digest(data), "bytes": len(data)})
            else:
                raise ValueError("Unknown engine")
            observations[source["document_id"]] = adapt_parser_output(case, pages, units, structure)
        except (KeyError, TypeError, ValueError) as exc:
            errors[case["id"]] = f"{type(exc).__name__}: {exc}"
    report = validate_stage(protocol, cases, stage, observations)
    report.update({"schema": "okf-dwp-manual-structure-run.v1", "engine": engine,
                   "protocol_sha256": digest(PROTOCOL.read_bytes()),
                   "source_baseline_commit": protocol["source_baseline_commit"],
                   "runtime_seconds": round(time.perf_counter() - started, 6),
                   "adapter_errors": errors, "baseline_document_bindings": inputs,
                   "implementation_bindings": before_implementation,
                   "consumed_pdf_structure_bindings": [consumed_structure[path] for path in sorted(consumed_structure)],
                   "implementation_changed_during_run": [row["path"] for row in before_implementation if digest((ROOT / row["path"]).read_bytes()) != row["sha256"]],
                   "pdf_structure_changed_during_run": [path for path, row in consumed_structure.items() if digest((ROOT / path).read_bytes()) != row["sha256"]],
                   "registration_note": "Fixtures predate source-case execution/results; parser drafting occurred concurrently. These are not blinded held-out cases.",
                   "review_boundary": "Structural acceptance only; legal applicability, specialist review and answer quality remain unestablished."})
    if report["implementation_changed_during_run"] or report["pdf_structure_changed_during_run"]:
        report["passed_cases"] = 0
        for row in report["cases"]:
            row["passed"] = False
            row["failures"].append("reproducibility:implementation or consumed PDF structure changed during run")
    output.mkdir(parents=True, exist_ok=False)
    encoded = json.dumps(observations, ensure_ascii=False, separators=(",", ":")).encode()
    (output / "observations.json.gz").write_bytes(gzip.compress(encoded, mtime=0))
    report["observations"] = {"path": "observations.json.gz", "decoded_sha256": digest(encoded), "decoded_bytes": len(encoded),
                              "sha256": digest((output / "observations.json.gz").read_bytes())}
    (output / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    return report


class FrozenStructureProtocolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.protocol, cls.cases = load_cases()
        cls.by_id = {case["id"]: case for case in cls.cases}

    def test_changed_consumed_binding_invalidates_reuse(self):
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "sidecar.json").write_bytes(b"original")
            binding = {"path": "sidecar.json", "sha256": digest(b"original"), "bytes": 8}
            verify_retained_bindings([binding], root)
            (root / "sidecar.json").write_bytes(b"modified")
            with self.assertRaisesRegex(ValueError, "Retained run binding changed"):
                verify_retained_bindings([binding], root)

    def test_case_membership_is_four_then_eight(self):
        initial, expanded = self.protocol["stages"]
        self.assertEqual((initial["denominator"], expanded["denominator"]), (4, 8))
        self.assertEqual(len(set(initial["case_ids"])), 4)
        self.assertEqual(len(set(expanded["case_ids"])), 8)
        self.assertTrue(set(initial["case_ids"]) < set(expanded["case_ids"]))
        self.assertEqual(set(self.by_id), set(expanded["case_ids"]))

    def test_source_regions_have_exact_frozen_bytes(self):
        for case in self.cases:
            with self.subTest(case=case["id"]):
                pages = read_pages(case)
                for name, region in case["regions"].items():
                    data = source_bytes(region["spans"], pages)
                    self.assertEqual((len(data), digest(data)), (region["bytes"], region["sha256"]), name)
                self.assertEqual(case["review"]["specialist_review"], "not-reviewed")

    def control(self, case_id):
        case = self.by_id[case_id]
        pages = read_pages(case)
        return case, pages, expected_observation(case, pages)

    def test_synthetic_expected_observations_pass_validator_only(self):
        for case in self.cases:
            pages = read_pages(case)
            self.assertEqual(validate_case(case, expected_observation(case, pages), pages), [])

    def test_known_misleading_heading_fails(self):
        for case_id in ("dmg-77031-heading", "adm-p4087-heading"):
            case, pages, observation = self.control(case_id)
            observation["units"][0]["heading_path"] = case["expectations"]["forbidden_governing_headings"]
            self.assertTrue(any(error.startswith("governing_heading:") for error in validate_case(case, observation, pages)))

    def test_cross_page_example_omission_fails(self):
        case, pages, observation = self.control("dmg-077001-cross-page-examples")
        observation["units"][0]["source_spans"].pop()
        observation["units"][0]["text_sha256"] = digest(source_bytes(observation["units"][0]["source_spans"], pages))
        self.assertIn("complete_passage:no complete unit with expected role", validate_case(case, observation, pages))

    def test_partition_gap_fails_even_when_reported_total_is_correct(self):
        case, pages, observation = self.control("dmg-77031-heading")
        observation["partition"].pop()
        observation["source_text_bytes"] = sum(len(row["text"].encode()) for row in pages)
        self.assertTrue(any(error.startswith("byte_conservation:") for error in validate_case(case, observation, pages)))

    def test_invented_reserved_paragraph_fails(self):
        case, pages, observation = self.control("adm-reserved-range")
        observation["units"][0]["paragraph_labels"] = ["F1093"]
        self.assertIn("roles:invented body label F1093", validate_case(case, observation, pages))

    def test_promoted_dictionary_fails(self):
        case, pages, observation = self.control("dmg-reference-abbreviations")
        observation["units"][0]["role"] = "guidance-passage"
        self.assertIn("complete_passage:no complete unit with expected role", validate_case(case, observation, pages))

    def test_missing_table_continuation_fails(self):
        case, pages, observation = self.control("dmg-capital-table-continuation")
        observation["units"][0]["source_spans"].pop()
        observation["units"][0]["text_sha256"] = digest(source_bytes(observation["units"][0]["source_spans"], pages))
        self.assertIn("complete_passage:no complete unit with expected role", validate_case(case, observation, pages))

    def test_changed_source_hash_fails(self):
        case, pages, observation = self.control("adm-p4087-heading")
        observation["source"]["pdf"]["sha256"] = "0" * 64
        self.assertIn("source_identity:pdf", validate_case(case, observation, pages))

    def test_missing_or_promoted_update_reference_fails(self):
        case, pages, observation = self.control("adm-c1988-cross-page-examples")
        observation["units"][0]["references"][0]["legal_effect_status"] = "resolved"
        self.assertTrue(any(error.startswith("reference_scope:") for error in validate_case(case, observation, pages)))

    def test_specialist_or_source_instruction_promotion_fails(self):
        case, pages, observation = self.control("adm-memo-contents-examples-annotations")
        observation["units"][0]["specialist_review"] = "accepted"
        observation["source_instructions_inert"] = False
        errors = validate_case(case, observation, pages)
        self.assertTrue(any(error.startswith("provenance:") for error in errors))
        self.assertIn("reference_scope:source instructions not explicitly inert", errors)

    def test_declared_boundary_completeness_does_not_promote_legal_review(self):
        case, pages, observation = self.control("dmg-077001-cross-page-examples")
        unit = observation["units"][0]
        self.assertEqual(unit["legal_effect_status"], "unresolved")
        unit["completeness"] = "complete-within-declared-boundary"
        self.assertEqual(validate_case(case, observation, pages), [])
        del unit["legal_effect_status"]
        self.assertTrue(any("Missing explicit unresolved legal boundary" in error for error in validate_case(case, observation, pages)))

    def test_memo_navigation_and_contacts_cannot_disappear(self):
        case, pages, observation = self.control("adm-memo-contents-examples-annotations")
        observation["structures"] = []
        errors = validate_case(case, observation, pages)
        self.assertIn("roles:missing navigation", errors)
        self.assertIn("roles:missing contacts", errors)
        self.assertIn("roles:missing annotations", errors)


if __name__ == "__main__":
    import sys
    if "--evaluate" in sys.argv:
        import argparse
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument("--evaluate", action="store_true")
        parser.add_argument("--stage", choices=("initial", "expanded"), required=True)
        parser.add_argument("--engine", choices=("baseline", "candidate"), required=True)
        parser.add_argument("--output", type=Path, required=True)
        parser.add_argument("--initial-report", type=Path)
        args = parser.parse_args()
        report = evaluate_source_cases(args.stage, args.engine, args.output, args.initial_report)
        print(json.dumps({key: report[key] for key in ("engine", "stage", "passed_cases", "case_denominator", "adapter_errors")}, indent=2))
        sys.exit(0 if report["passed_cases"] == report["case_denominator"] else 1)
    else:
        unittest.main()
