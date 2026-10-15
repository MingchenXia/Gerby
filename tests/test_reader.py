import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from collection import build_collection, check_links
from reader import Reader, bibtex


class ReaderTests(unittest.TestCase):
    def setUp(self):
        self.records = [{"tag": f"{n:08X}", "label": f"def:internal_label_{n}", "title": f"Definition 1.1.{n}", "semantic_title": f"Internal label {n}", "kind": "definition", "topic": topic, "html": f'<article class="env-definition"><p>Definition 1.1.{n}. A statement.</p></article>'} for n, topic in enumerate(("Alpha", "Alpha", "Beta", "Gamma"), 1)]
        self.config = {"version": 1, "entries": [], "topics": [{"slug": name.lower(), "title": name} for name in ("Alpha", "Beta", "Gamma")], "chapters": [{"slug": "first", "title": "First chapter", "topics": ["alpha", "beta"]}, {"slug": "second", "title": "Second chapter", "topics": ["gamma"]}]}
        self.book = {"slug": "source", "title": "Test source", "author": "Test author", "status": "published", "repository": "https://github.com/example/source"}

    def build(self, root):
        folder = root / "books" / "source"
        folder.mkdir(parents=True)
        for name, value in (("entries", self.records), ("references", []), ("tags", [{"tag": r["tag"], "page": f'tag/{r["tag"]}/index.html'} for r in self.records]), ("edition", {"commit": "a" * 40})):
            (folder / (name + ".json")).write_text(json.dumps(value))
        shutil.copytree(ROOT / "site" / "assets", root / "assets")
        (root / "assets" / "mathjax").mkdir()
        (root / "assets" / "mathjax" / "tex-chtml.js").touch()
        build_collection([self.book], root, self.config)
        return json.loads((root / "navigation.json").read_text())

    def test_chapters_list_sections_and_sections_list_entries(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.build(root)
            chapter = BeautifulSoup((root / "chapters/first/index.html").read_text(), "html.parser")
            self.assertEqual(len(chapter.select('main .section-list a')), 2)
            self.assertFalse(chapter.select('main .reference-entry'))
            section = BeautifulSoup((root / "sections/alpha/index.html").read_text(), "html.parser")
            self.assertEqual(len(section.select('main .reference-entry')), 2)
            check_links(root)

    def test_reading_chain_covers_every_page_once_with_reciprocal_links(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            order = self.build(root)
            routes = [page["route"] for page in order]
            self.assertEqual(len(routes), len(set(routes)))
            self.assertEqual(sum(route.startswith("tag/") for route in routes), 4)
            self.assertLess(routes.index("chapters/first"), routes.index("sections/alpha"))
            self.assertLess(routes.index("sections/beta"), routes.index("chapters/second"))
            for index, route in enumerate(routes):
                page = root / route / "index.html"
                soup = BeautifulSoup(page.read_text(), "html.parser")
                ids = [element['id'] for element in soup.select('[id]')]
                self.assertEqual(len(ids), len(set(ids)), route)
                for direction, offset in (("prev", -1), ("next", 1)):
                    links = soup.select(f'nav.page-navigation a[rel="{direction}"]')
                    if not 0 <= index + offset < len(routes):
                        self.assertFalse(links)
                    else:
                        self.assertEqual(len(links), 2)
                        target = (page.parent / links[0]["href"] / "index.html").resolve()
                        self.assertEqual(target, (root / routes[index + offset] / "index.html").resolve())

    def test_labels_are_searchable_but_not_reader_headings_or_result_titles(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            pages = self.build(root)
            for page in pages:
                soup = BeautifulSoup((root / page["route"] / "index.html").read_text(), "html.parser")
                self.assertNotIn("internal_label_", soup.get_text())
                self.assertNotIn("Internal label", soup.get_text())
            search = json.loads((root / "search.json").read_text())
            self.assertEqual(search[0]["title"], "Definition 1.1.1")
            self.assertIn("def:internal_label_1", search[0]["aliases"])

    def test_comments_follow_stable_routes_and_always_offer_a_github_fallback(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            pages = self.build(root)
            terms = []
            for page in pages:
                soup = BeautifulSoup((root / page["route"] / "index.html").read_text(), "html.parser")
                panel = soup.select_one('[data-comment-term]')
                terms.append(panel['data-comment-term'])
                self.assertEqual(panel['data-repo'], 'MingchenXia/Gerby')
                self.assertIn('discussions/new?', panel.select_one('.comment-actions a:last-child')['href'])
            self.assertEqual(len(terms), len(set(terms)))


if __name__ == "__main__":
    unittest.main()
