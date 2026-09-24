#!/usr/bin/env python3
"""Check the frozen context projection alongside its independently built successor.

The original projection owns all files in structured-context/ and rejects
unknown surplus. The evidence-connect producer owns a small additive namespace
there. Validate every successor byte, set only those declared files aside for
the original check, then restore and validate them again.
"""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable

from build_bundle import ROOT
from build_evidence_connect import compile_connect
from build_logical_units import admitted_output, require


def check_successor(root: Path, outputs: dict[str, bytes]) -> None:
    base = root / 'structured-context'
    for name, raw in outputs.items():
        path = admitted_output(base, name)
        require(path.is_file() and not path.is_symlink(), 'Missing or linked successor output: ' + name)
        require(path.read_bytes() == raw, 'Successor projection drift: ' + name)


def run_base_check(root: Path) -> None:
    subprocess.run([sys.executable, str(root / 'scripts/build_structured_context.py'), '--check'],
                   cwd=root, check=True)


def check_base_with_successor(root: Path = ROOT, *, outputs: dict[str, bytes] | None = None,
                              base_check: Callable[[Path], None] = run_base_check) -> None:
    outputs = compile_connect(root) if outputs is None else outputs
    check_successor(root, outputs)
    base = root / 'structured-context'
    moved: list[tuple[Path, Path]] = []
    staging = Path(tempfile.mkdtemp(prefix='.successor-check-', dir=root))
    primary: BaseException | None = None
    try:
        for name in sorted(outputs):
            source = admitted_output(base, name)
            target = admitted_output(staging, name)
            target.parent.mkdir(parents=True, exist_ok=True)
            os.replace(source, target)
            moved.append((source, target))
        base_check(root)
    except BaseException as error:
        primary = error
    restoration_errors = []
    for source, target in reversed(moved):
        try:
            require(not source.exists() and not source.is_symlink(),
                    'Successor destination changed during base check: ' + str(source))
            require(target.is_file() and not target.is_symlink(), 'Staged successor changed: ' + str(target))
            os.replace(target, source)
        except BaseException as error:
            restoration_errors.append(error)
    if not restoration_errors:
        try:
            check_successor(root, outputs)
        except BaseException as error:
            restoration_errors.append(error)
    if restoration_errors:
        detail = '; '.join(str(error) for error in restoration_errors)
        if primary is not None:
            primary.add_note('Successor restoration or verification failed; staging retained at '
                             + str(staging) + ': ' + detail)
            raise primary
        raise RuntimeError('Successor restoration or verification failed; staging retained at '
                           + str(staging) + ': ' + detail) from restoration_errors[0]
    shutil.rmtree(staging)
    if primary is not None:
        raise primary
    print('{"status":"verified","successor_files":%d}' % len(outputs))


if __name__ == '__main__':
    check_base_with_successor()
