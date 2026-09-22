"""Replace generated projections while retiring only previously bound shards.

Unknown or changed surplus files fail before any output is written. Historical
source/release directories are never passed here. Git retains prior generated
versions; a write-mode receipt names each hash-checked retired shard.
"""
import hashlib
import json
from pathlib import Path

from build_logical_units import admitted_output, require, strict_json


def previous_bindings(directory, mode):
    directory = Path(directory)
    name = 'manifest.json' if mode == 'units' else 'build-review.json'
    path = admitted_output(directory, name)
    if not path.exists():
        return {}
    require(path.is_file() and path.stat().st_size <= 64 * 1024 * 1024, 'Invalid previous projection declaration')
    old = strict_json(path.read_bytes())
    if mode == 'units':
        require(old.get('schema') == 'okf-dwp-structured-units.v1', 'Unknown previous unit declaration')
        refs = [*old['documents'], *old['records']['shards']]
    else:
        require(mode == 'context' and old.get('schema') == 'okf-dwp-structured-context-build.v1', 'Unknown previous context declaration')
        prefix = directory.name + '/'
        require(all(ref['path'].startswith(prefix) for ref in old['outputs']), 'Previous outputs leave projection root')
        refs = [{**ref, 'path': ref['path'][len(prefix):]} for ref in old['outputs']]
    owned = {}
    for ref in refs:
        admitted_output(directory, ref['path'])
        require(ref['path'] not in owned, 'Duplicate prior generated path')
        owned[ref['path']] = ref
    return owned


def install_projection(directory, outputs, *, check, mode):
    directory = Path(directory)
    require(mode in {'units', 'context'}, 'Unknown projection mode')
    require(not directory.is_symlink(), 'Output root symlink not admitted')
    require(not directory.exists() or directory.is_dir(), 'Output root is not a directory')
    destinations = {name: admitted_output(directory, name) for name in outputs}
    entries = list(directory.rglob('*')) if directory.exists() else []
    require(not any(p.is_symlink() for p in entries), 'Projection tree contains a symlink')
    require(all(p.is_file() or p.is_dir() for p in entries), 'Projection contains a non-regular entry')
    for path in destinations.values():
        require(not path.exists() or path.is_file(), 'Output destination is not a regular file')
        for parent in path.parents:
            if parent == directory:
                break
            require(not parent.exists() or parent.is_dir(), 'Output parent is not a directory')
    actual = {p.relative_to(directory).as_posix() for p in entries if p.is_file()}
    surplus = sorted(actual - set(outputs))
    if check:
        require(not surplus, 'Unbound or obsolete projection output: ' + ', '.join(surplus))
        for name, raw in outputs.items():
            path = destinations[name]
            require(path.is_file() and path.read_bytes() == raw, 'Stale structured projection: ' + name)
        return []
    previous = previous_bindings(directory, mode)
    retired = []
    for name in surplus:
        require(name in previous, 'Unknown surplus output; no files written: ' + name)
        ref = previous[name]
        raw = admitted_output(directory, name).read_bytes()
        require(len(raw) == ref['bytes'] and hashlib.sha256(raw).hexdigest() == ref['sha256'],
                'Changed surplus output; no files written: ' + name)
        retired.append({'path': name, 'bytes': len(raw), 'sha256': ref['sha256']})
    # Admit every destination and surplus before altering any projection bytes.
    # Declarations are written last; publication still uses a separately built,
    # checked release rather than serving an actively changing checkout.
    for name in sorted(outputs, key=lambda n: (n in {'manifest.json', 'build-review.json', 'okf-explorer.json'}, n)):
        path = destinations[name]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(outputs[name])
    for ref in retired:
        path = admitted_output(directory, ref['path'])
        require(hashlib.sha256(path.read_bytes()).hexdigest() == ref['sha256'], 'Surplus changed during build')
        path.unlink()
    if retired:
        print(json.dumps({'status': 'retired-previously-bound-generated-shards', 'projection': directory.name, 'files': retired}))
    return retired
