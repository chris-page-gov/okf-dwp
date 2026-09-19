"""Reject private correspondence in the Git index without reading its contents."""

import argparse
from pathlib import Path, PurePosixPath
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PRIVATE_BASENAME = '.email.md'


def check(root: Path) -> list[str]:
    tracked = subprocess.run(
        ['git', '-C', str(root), 'ls-files', '-z'],
        check=True, capture_output=True, text=True,
    ).stdout.split('\0')
    tracked = [path for path in tracked if path]
    errors = [
        f'Private correspondence is in the Git index: {path}'
        for path in tracked if PurePosixPath(path).name == PRIVATE_BASENAME
    ]

    ignore_path = root / '.gitignore'
    if not ignore_path.is_file() or PRIVATE_BASENAME not in ignore_path.read_text().splitlines():
        errors.append('Root .gitignore must contain the unanchored .email.md rule.')
        return errors

    # Probe root, a new nested directory and every existing tracked directory.
    # Only path names and public ignore rules are inspected, never email bodies.
    directories = {PurePosixPath('.'), PurePosixPath('__okf_private_input_probe__')}
    for path in tracked:
        directories.update(PurePosixPath(path).parents)
    probes = sorted(str(directory / PRIVATE_BASENAME) for directory in directories)
    result = subprocess.run(
        ['git', '-C', str(root), '-c', 'core.excludesFile=/dev/null',
         'check-ignore', '--no-index', '--verbose', '-z', '--stdin'],
        input='\0'.join(probes) + '\0', capture_output=True, text=True,
    )
    if result.returncode not in (0, 1):
        raise RuntimeError('Git could not verify the private-input ignore rules.')
    fields = result.stdout.split('\0')
    ignored = {
        fields[index + 3]
        for index in range(0, len(fields) - 1, 4)
        if not fields[index + 2].startswith('!')
    }
    errors.extend(f'Private correspondence is not ignored at: {path}' for path in probes if path not in ignored)
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    args = parser.parse_args()
    try:
        errors = check(args.root.resolve())
    except (OSError, subprocess.CalledProcessError, RuntimeError) as error:
        print(f'Private-input check failed: {error}', file=sys.stderr)
        return 1
    if errors:
        print('\n'.join(errors), file=sys.stderr)
        return 1
    print('Private-input check passed: no .email.md in the index; root and nested ignore rules verified.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
