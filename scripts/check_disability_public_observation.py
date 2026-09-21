#!/usr/bin/env python3
"""Check one retained disability-source public observation offline; never execute it."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'validation/household-reader-public/df352daa-c4f2de0a'
APPROVED = {'app_manifest_sha256': '9fc8cb1bbf10e4e5182efd69d56f2b5ed39a2e6ecf942dce64357c4a529d1ce8', 'context_sha256': {'care-home': '9a1e1fe1ca5980d88a1bafb9bc249b860f14592d9e6a68345e24f8ad8037b7ba', 'sda': '25907642db042a4c74f0c2591d3a339d0709ca116e135201ecd71b36b72f2e73'}, 'engine_commit': 'c4f2de0a99b7bc2f8b8c8a06a3c715fb56b66d8e', 'harness_sha256': 'ea694325984cb8ba1a746e8be2c3ff97b196a19288f70fb522138494308b1366', 'observation_sha256': '849b2901f5f8afc7708c62b09dd2e44e966b139b48286af6c98c1f40cacd8592', 'source_commit': 'df352daa5d1d6a99a30fddcb2db341f74c6473e5'}
CHECKERS = {'check_pinned_public_household_observation.py': '887f94a6516e3f48ca5107673249c0e96f4a4bd63bd79babbe1cb68342556b44', 'check_household_reader_observations.py': 'a3d04e7a7d46a1a29ca9db7f6b3485b4d40ef9b25fa722b0f6c2c6826fa31b19'}


def admit_checker_sources(directory):
    for part in [*reversed(directory.absolute().parents), directory.absolute()]:
        if not stat.S_ISDIR(part.lstat().st_mode):
            raise ValueError('Checker directory must not be a symlink')
    sources = {}
    for name, expected in CHECKERS.items():
        path = directory / name
        info = path.lstat()
        if not stat.S_ISREG(info.st_mode) or not 0 < info.st_size <= 1024 * 1024:
            raise ValueError('Checker source type or size rejected')
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(descriptor, 'rb') as stream:
            opened = os.fstat(stream.fileno())
            if not stat.S_ISREG(opened.st_mode) or (info.st_dev, info.st_ino, info.st_size) != (opened.st_dev, opened.st_ino, opened.st_size):
                raise ValueError('Checker source changed while opening')
            raw = stream.read(1024 * 1024 + 1)
        if len(raw) != info.st_size or hashlib.sha256(raw).hexdigest() != expected:
            raise ValueError('Checker source differs from reviewed bytes')
        sources[name] = raw
    return sources


def core_checker():
    directory = ROOT / 'scripts'
    sources = admit_checker_sources(directory)
    # Only the two approved, hash-checked local modules above are imported.
    for name in ['check_household_reader_observations', 'check_pinned_public_household_observation']:
        module = ModuleType(name)
        module.__file__ = str(directory / (name + '.py'))
        sys.modules[name] = module
        exec(compile(sources[name + '.py'], module.__file__, 'exec'), module.__dict__)
    return module


def verify(write=False):
    core = core_checker()
    core.checked_directory(BASE)
    approval = {'schema': 'okf-pinned-public-reader-approval.v1', 'release': 'df352daa-c4f2de0a',
        'binding': APPROVED, 'boundary': 'Post-observation integrity admission; no fresh browser or legal acceptance.'}
    if not write:
        core.require(core.parse(core.bounded_read(BASE / 'approval-manifest.json', core.MAX_MANIFEST)) == approval,
            'Approved binding differs')
    result = core.validate(BASE, approval=APPROVED)
    manifest = {'schema': 'okf-pinned-public-reader-artefacts.v1',
        'approval_sha256': core.sha(core.encoded(approval)),
        'checker_sources': {**{str(Path('scripts') / n): value for n, value in CHECKERS.items()},
            'scripts/check_disability_public_observation.py': core.sha(core.bounded_read(Path(__file__), core.MAX_MEMBER))},
        'files': core.inventory(BASE), 'integrity': result}
    for name, value in [('approval-manifest.json', approval), ('artifact-manifest.json', manifest)]:
        raw = core.encoded(value)
        core.require(len(raw) <= core.MAX_MANIFEST, 'Metadata exceeds bound')
        target = BASE / name
        if write and not target.exists():
            with target.open('xb') as stream: stream.write(raw)
        else:
            core.require(core.bounded_read(target, core.MAX_MANIFEST) == raw, 'Retained metadata differs; no overwrite')
    return {'status': 'verified-offline-receipt-integrity', 'source_commit': APPROVED['source_commit'],
        'source_files': result['source_files_verified_against_git'],
        'cases': {k: {n: v[n] for n in ['selected_records', 'relationships', 'compact_bytes',
            'relationships_with_unselected_targets', 'returned_required_path_occurrences',
            'returned_required_paths_fully_retained']} for k, v in result['cases'].items()},
        'network_or_model_calls': 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write-manifest', action='store_true')
    print(json.dumps(verify(parser.parse_args().write_manifest)))


if __name__ == '__main__': main()
