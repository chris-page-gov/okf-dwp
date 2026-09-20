#!/usr/bin/env python3
"""Publish whitelisted historical reader results without private Playwright traces."""
import argparse
import hashlib
import json
from pathlib import Path
import re


def digest(value):
    return hashlib.sha256(value).hexdigest()


def cases(suite):
    yield from suite.get("specs", [])
    for child in suite.get("suites", []):
        yield from cases(child)


def project_results(raw, harness):
    lines = harness.splitlines()
    titles = re.findall(r"test\('([^']+)'", harness)
    assert len(titles) == 4 and len(set(titles)) == 4
    rows = []
    for suite in raw["suites"]:
        for spec in cases(suite):
            assert spec["title"] in titles
            for test in spec["tests"]:
                assert test["projectName"] in {"chrome", "firefox", "webkit"}
                assert len(test["results"]) == 1, "Retries must remain separate observations"
                result = test["results"][0]
                assert result["retry"] == 0
                error = result.get("error", {})
                line = error.get("location", {}).get("line")
                # A failure at the final console assertion proves preceding journey
                # assertions ran. Any other failure stays a functional failure.
                final_console = bool(line and 0 < line <= len(lines)
                                     and lines[line - 1].strip() == "expect(errors).toEqual([]);"
                                     and Path(error["location"]["file"]).name == "evidence-review.spec.ts"
                                     and len(result.get("errors", [])) == 1)
                passed = result["status"] == "passed"
                rows.append({
                    "browser": test["projectName"], "title": spec["title"],
                    "strict_status": "passed" if passed else "failed",
                    "functional_status": "passed" if passed or final_console else "failed",
                    "reached_final_console_assertion": passed or final_console,
                    "console_assertion_line": line if final_console else None,
                    "failure_class": ("host-cookie-domain-rejection" if final_console and "__cf_bm" in error.get("message", "")
                                      and "invalid domain" in error["message"] else "console-error" if final_console
                                      else None if passed else "other-test-failure"),
                    "error_message_sha256": digest(error["message"].encode()) if error.get("message") else None,
                    "duration_ms": result["duration"], "retry": result["retry"],
                    "request_mode": ("delayed-real-response-ui-control" if titles.index(spec["title"]) == 2
                                     else "synthetic-response-ui-control" if titles.index(spec["title"]) == 3
                                     else "public-service-without-response-routing")
                })
    assert len(rows) == 12
    assert len({(row["browser"], row["title"]) for row in rows}) == 12
    return rows


def safe_console(message):
    return {"classification": "host-cookie-domain-rejection" if "__cf_bm" in message and "invalid domain" in message else "other-console-error",
            "message_sha256": digest(message.encode())}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ["raw-directory", "explorer-root", "deployment", "output"]:
        parser.add_argument("--" + name, required=True, type=Path)
    args = parser.parse_args()
    out = args.output
    out.mkdir(parents=True, exist_ok=True)
    assert not (out / "run-summary.json").exists(), "Never overwrite an observation"
    app = args.explorer_root / "apps/okf-explorer"
    harness = app / "tests/service-review/evidence-review.spec.ts"
    config = app / "playwright.service-review.config.ts"
    raw_bytes = (args.raw_directory / "results.json").read_bytes()
    raw = json.loads(raw_bytes)
    harness_bytes = harness.read_bytes()
    rows = project_results(raw, harness_bytes.decode())
    deployment_bytes = args.deployment.read_bytes()
    deployment = json.loads(deployment_bytes)
    assert deployment["deployment"]["status"] == "succeeded"
    copies = []
    for source in [harness, config]:
        data = source.read_bytes()
        name = source.stem + "-" + digest(data) + source.suffix
        target = out / name
        if target.exists():
            assert target.read_bytes() == data
        else:
            target.write_bytes(data)
        copies.append({"source_path": str(source.relative_to(args.explorer_root)), "sha256": digest(data), "copy": name})
    receipts = []
    for engine in ["chrome", "firefox", "webkit"]:
        data = (args.raw_directory / (engine + "-receipt.json")).read_bytes()
        original = json.loads(data)
        assert original["base_url"].rstrip("/") == deployment["deployment"]["url"].rstrip("/")
        assert original["browser"] == engine and original["target"] == "external-service"
        public = {key: original[key] for key in ["schema", "observed_at", "browser", "base_url", "target", "functional_assertions", "console_gate",
                  "test_candidate_build_receipt_sha256", "deployment_identity", "version", "context_id", "selected_records", "first_catalogue_count",
                  "record_text_id", "record_text_sha256", "package_sha256", "assertions", "calls", "limitations"]}
        public["console_errors"] = [safe_console(message) for message in original["console_errors"]]
        public["projection"] = {"raw_receipt_sha256": digest(data), "console_messages": "Classification and digest only; raw URLs, private paths and trace attachments omitted."}
        target = out / (engine + "-receipt.json")
        assert not target.exists()
        target.write_text(json.dumps(public, indent=2) + "\n")
        receipts.append({"browser": engine, "path": target.name, "sha256": digest(target.read_bytes())})
        screenshot = args.raw_directory / (engine + "-source-evidence.png")
        if screenshot.exists():
            (out / screenshot.name).write_bytes(screenshot.read_bytes())
    summary = {
        "schema": "okf-historical-service-browser-projection.v1", "service_version": deployment["service_version"],
        "base_url": deployment["deployment"]["url"],
        "deployment": {"runtime_commit": deployment["runtime_commit"], "runtime_worker_sha256": deployment["runtime_worker_sha256"],
                       "site_version_number": deployment["site_version_number"], "receipt_sha256": digest(deployment_bytes)},
        "harness": copies, "projector_sha256": digest(Path(__file__).read_bytes()),
        "raw_results_sha256": digest(raw_bytes), "raw_results_and_traces_published": False,
        "stats": {key: raw["stats"][key] for key in ["startTime", "duration", "expected", "skipped", "unexpected", "flaky"]},
        "functional_tests_passed": sum(row["functional_status"] == "passed" for row in rows),
        "strict_tests_passed": sum(row["strict_status"] == "passed" for row in rows),
        "strict_tests_failed": sum(row["strict_status"] != "passed" for row in rows),
        "strict_status": "passed" if all(row["strict_status"] == "passed" for row in rows) else "failed",
        "tests": rows, "receipts": receipts,
        "limits": ["Existing four historical UI journeys in each of three browser engines; retries disabled and one worker.",
                   "Delayed-response and synthetic-markup cases intentionally use routing to test UI boundaries; these are not untouched source-evidence observations.",
                   "A failure at the final console assertion records preceding functional assertions as passed, while preserving strict failure.",
                   "Hosting cookie errors remain failures. No browser security or privacy setting was weakened.",
                   "Public projection omits raw trace/network data, error snippets, private paths and console URLs. Digests identify retained local originals.",
                   "Historical research sufficiency is not current legal, specialist, model-answer or whole-corpus acceptance."]
    }
    (out / "run-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({key: summary[key] for key in ["functional_tests_passed", "strict_tests_passed", "strict_tests_failed", "strict_status"]}))


if __name__ == "__main__":
    main()
