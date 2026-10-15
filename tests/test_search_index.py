import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from search_index import write_search_index


class SearchIndexTests(unittest.TestCase):
    def test_chunking_preserves_every_record_and_its_order(self):
        records = [{'tag': str(i), 'text': 'An intact mathematical statement.'} for i in range(12)]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_search_index(records, root, max_bytes=150)
            manifest = json.loads((root / 'search.json').read_text())
            result = [row for name in manifest['chunks'] for row in json.loads((root / name).read_text())]
            self.assertEqual(result, records)
            self.assertGreater(len(manifest['chunks']), 1)
