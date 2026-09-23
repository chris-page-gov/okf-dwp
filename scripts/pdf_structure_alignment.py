"""Match source-declared PDF tags to frozen text; never repair source bytes.

Whitespace, soft hyphens and Unicode compatibility glyphs are ignored only in
matching. Ambiguous/out-of-order matches are retained as unknown observations.
"""
from __future__ import annotations

import bisect
import hashlib
import json
from pathlib import Path
import re
import unicodedata


ROOT = Path(__file__).resolve().parents[1]


def normalised(value):
    return ''.join(c.casefold() for c in unicodedata.normalize('NFKC', value)
                   if not c.isspace() and c not in '\u00ad\u200b\ufeff')


def indexed_text(pages):
    chars, starts, ends, page_ends = [], [], [], []
    offset = 0
    for row in pages:
        for character in row['text']:
            end = offset + len(character.encode())
            for atom in normalised(character):
                chars.append(atom); starts.append(offset); ends.append(end)
            offset = end
        page_ends.append(offset)
    return ''.join(chars), starts, ends, page_ends


def align_blocks(pages, blocks):
    haystack, starts, ends, page_ends = indexed_text(pages)
    aligned, missed = [], []
    # Align leaf paragraph/headings first in document order. Container spans
    # can then be recovered from their own literal text without advancing the
    # cursor past their children. No approximate/fuzzy text substitution.
    candidates = []
    containers = {'Table', 'TR', 'TH', 'TD', 'L', 'LI'}
    for block in blocks:
        needle = normalised(block['text'])
        positions = []
        if needle:
            pos = haystack.find(needle)
            while pos >= 0 and len(positions) < 33:
                positions.append((pos, pos + len(needle)))
                pos = haystack.find(needle, pos + 1)
        candidates.append(positions)
    for index, block in enumerate(blocks):
        if not normalised(block['text']):
            continue
        positions = candidates[index]
        method = 'unique-normalised-exact'
        if len(positions) > 1:
            # A heading can repeat in a contents list and in the body. Only
            # independently unique neighbouring leaf blocks may disambiguate
            # it; a greedy first match is not proof of the governing location.
            lower, upper = 0, len(haystack)
            start_line = block.get('tree_line_start', index * 2)
            end_line = block.get('tree_line_end', index * 2 + 1)
            for previous in range(index - 1, -1, -1):
                other = blocks[previous]
                if (other['role'] not in containers and len(candidates[previous]) == 1
                        and other.get('tree_line_end', previous * 2 + 1) < start_line):
                    lower = candidates[previous][0][1]
                    break
            for following in range(index + 1, len(blocks)):
                other = blocks[following]
                if (other['role'] not in containers and len(candidates[following]) == 1
                        and other.get('tree_line_start', following * 2) > end_line):
                    upper = candidates[following][0][0]
                    break
            positions = [(start, end) for start, end in positions if lower <= start and end <= upper] if len(positions) <= 32 else []
            method = 'unique-between-source-text-anchors'
        if len(positions) != 1:
            missed.append({'index': index, 'role': block['role'], 'reason': 'no-unambiguous-exact-text-match'})
            continue
        where, finish = positions[0]
        aligned.append({**block, 'index': index, 'start': starts[where], 'end': ends[finish - 1],
                        'page': bisect.bisect_right(page_ends, starts[where]) + 1,
                        'alignment': method})
    return {'blocks': aligned, 'unmatched': missed,
            'tag_count': len(blocks), 'matched_count': len(aligned),
            'matching_does_not_rewrite_source': True}


def load_alignment(family, doc, pages, root=ROOT):
    identifier = doc.get('id', '')
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]*', identifier):
        return {'status': 'not-available', 'blocks': [], 'unmatched': []}
    from build_pdf_structure import DEFAULT_OUTPUT
    from build_logical_units import Inputs
    active = DEFAULT_OUTPUT if (root / DEFAULT_OUTPUT / 'manifest.json').is_file() else 'pdf-structure'
    path = root / active / family / (identifier + '.structure.json')
    if not path.is_file():
        return {'status': 'not-available', 'blocks': [], 'unmatched': []}
    if family not in {'dmg', 'adm'} or any(parent.is_symlink() for parent in (path, *path.parents)):
        raise ValueError('Unsafe PDF structure path')
    if path.stat().st_size > 64 * 1024 * 1024:
        raise ValueError('PDF structure sidecar exceeds bound')
    data = json.loads(path.read_bytes())
    # The source/sidecar binding is also checked by the full producer. Match
    # only the known document PDF and retain the extractor's status unchanged.
    expected = doc.get('sha256') or doc.get('source_sha256')
    if data.get('pdf_sha256') != expected:
        raise ValueError('PDF structure belongs to a different frozen source')
    manifest_path = root / active / 'manifest.json'
    if manifest_path.is_file():
        manifest = json.loads(Inputs(root).read(str(manifest_path.relative_to(root)), limit=32 * 1024 * 1024))
        entry = next((e for e in manifest['documents'] if e['document_key'] == family + ':' + identifier), None)
        if (entry is None or entry['structure']['path'] != str(path.relative_to(root))
                or entry['structure']['sha256'] != hashlib.sha256(path.read_bytes()).hexdigest()):
            raise ValueError('PDF sidecar is not bound to the active observation manifest')
    relative_tree = data.get('tree', {}).get('path', str(path.with_name(identifier + '.tree.txt').relative_to(root)))
    tree_path = root / relative_tree
    if tree_path.is_symlink() or tree_path.stat().st_size > 16 * 1024 * 1024:
        raise ValueError('PDF structure raw tree exceeds bound or is symlinked')
    tree = Inputs(root).read(relative_tree, limit=16 * 1024 * 1024)
    tree_binding = data.get('tree', {})
    actual = hashlib.sha256(tree).hexdigest()
    if tree_binding.get('sha256') != actual:
        raise ValueError('PDF structural text hash differs')
    if data.get('status') not in {'tagged', 'tagged-with-unparsed-lines', 'untagged', 'no-structure'}:
        if data.get('blocks'):
            raise ValueError('Incomplete PDF structure observation contains admitted blocks')
        return {'status': data.get('status', 'unknown'), 'blocks': [], 'unmatched': [],
                'source': {'path': str(path.relative_to(root)), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'pdf_sha256': expected, 'tree_sha256': actual},
                'reason': 'Incomplete or failed structure observation; source-text fallback only'}
    from build_pdf_structure import parse_tree
    if parse_tree(tree)['blocks'] != data['blocks']:
        raise ValueError('PDF structural blocks differ from retained raw tree')
    return {**align_blocks(pages, data['blocks']), 'status': data['status'],
            'source': {'path': str(path.relative_to(root)), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                       'tree_sha256': actual, 'pdf_sha256': expected}}
