import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import query


class QueryScopeTests(unittest.TestCase):
    def test_full_scope_and_history_do_not_leak_into_pilot(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'source/full-dmg-2026-09-15').mkdir(parents=True)
            documents = []
            for identifier, role in [('pilot', 'substantive'), ('new-chapter', 'substantive'), ('memo', 'memo')]:
                path = f'source/{identifier}.json'
                (root / path).write_text(json.dumps({'pages': [{'page': 1, 'url': 'https://www.gov.uk/example.pdf#page=1', 'text': 'Evidence sentinel appears in this source.'}]}))
                documents.append({'id': identifier, 'title': identifier, 'role': role, 'kind': 'memo' if role == 'memo' else 'chapter',
                                  'pages_path': path, 'sha256': 'source-hash', 'observed_at': '2026-09-15T00:00:00Z'})
            (root / 'source/inventory.json').write_text(json.dumps({'documents': documents[:1]}))
            (root / 'source/full-dmg-2026-09-15/inventory.json').write_text(json.dumps({'documents': documents}))
            with patch.object(query, 'ROOT', root):
                pilot = query.search('sentinel')
                full = query.search('sentinel', scope='full-dmg')
                history = query.search('sentinel', include_history=True, scope='full-dmg')
                empty = query.search('unfindablezz', scope='full-dmg')
            self.assertEqual([r['document_id'] for r in pilot['results']], ['pilot'])
            self.assertEqual({r['document_id'] for r in full['results']}, {'pilot', 'new-chapter'})
            self.assertEqual({r['document_id'] for r in history['results']}, {'pilot', 'new-chapter', 'memo'})
            self.assertNotEqual(pilot['inventory_sha256'], full['inventory_sha256'])
            self.assertEqual(empty['results'], [])
            self.assertEqual(history['searched_documents'], 3)

    def test_unknown_scope_fails_closed(self):
        with self.assertRaises(ValueError):
            query.search('capital', scope='unknown')


if __name__ == '__main__':
    unittest.main()
