import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from collection import build_collection, check_links, continuous_section, source_roots
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

    def test_chapters_list_sections_and_sections_show_full_statements(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.build(root)
            chapter = BeautifulSoup((root / "chapters/first/index.html").read_text(), "html.parser")
            self.assertEqual(len(chapter.select('main .section-list a')), 2)
            self.assertFalse(chapter.select('main .reference-entry'))
            section = BeautifulSoup((root / "sections/alpha/index.html").read_text(), "html.parser")
            self.assertFalse(section.select('main .reference-entry'))
            self.assertEqual(len(section.select('main .env-definition')), 2)
            self.assertEqual(section.select_one('html')['data-reading-mode'], 'continuous')
            self.assertIn('A statement.', section.select_one('main').get_text())
            self.assertFalse(section.select('.source-attribution'))
            self.assertNotIn('From Test source', section.select_one('main').get_text())
            entry = BeautifulSoup(next((root / 'tag').glob('*/index.html')).read_text(), 'html.parser')
            self.assertFalse(entry.select('.source-attribution'))
            self.assertTrue(entry.select('[data-gerby-book="source"] [data-gerby-tag]'))
            check_links(root)

    def test_nested_statements_and_proofs_are_readable_once(self):
        for record in self.records[:2]:
            record['html'] = record['html'].replace('<article ', f'<article id="{record["tag"]}" ')
        parent = {'tag': '00000010', 'label': 'sec:alpha', 'title': '1 Alpha', 'kind': 'section', 'topic': 'Alpha', 'section': True, 'html': '<h2 id="sec:alpha">1 Alpha</h2><p>Opening explanation.</p>' + self.records[0]['html'] + '<article class="env-proof"><p>Proof. The required argument.</p></article><p>Connecting explanation.</p>' + self.records[1]['html']}
        self.records.insert(0, parent)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.build(root)
            soup = BeautifulSoup((root / 'sections/alpha/index.html').read_text(), 'html.parser')
            self.assertEqual(len(soup.select('.reading-chunk')), 1)
            self.assertEqual(len(soup.select('.env-definition')), 2)
            self.assertEqual(len(soup.select('.env-proof')), 1)
            self.assertFalse(soup.select('.env-proof')[0].find_parent('details'))
            text = soup.select_one('.section-reading').get_text()
            self.assertEqual(text.count('Opening explanation.'), 1)
            self.assertEqual(text.count('Connecting explanation.'), 1)
            ids = [node['id'] for node in soup.select('[id]')]
            self.assertEqual(len(ids), len(set(ids)))
            check_links(root)

    def test_excluded_front_matter_leaves_reading_order_and_preserves_old_urls(self):
        self.config['excluded_topics'] = ['beta']
        self.config['chapters'][0]['topics'] = ['alpha']
        self.config['entries'] = [{'tag': 'ABCDEF12', 'title': 'Removed overview', 'topic': 'beta', 'members': [{'source': 'source', 'label': self.records[2]['label']}]}]
        self.records[0]['html'] += '<p>See <a href="/tag/00000003">the overview</a>.</p>' + r'\[x=\gerbyref{00000003}{1}\]'
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            pages = self.build(root)
            self.assertFalse(any(p.get('section') == 'beta' for p in pages))
            chapter = BeautifulSoup((root / 'chapters/first/index.html').read_text(), 'html.parser')
            self.assertEqual([a.get_text(' ', strip=True) for a in chapter.select('main .section-list a')], ['1.1 Alpha'])
            section = BeautifulSoup((root / 'sections/alpha/index.html').read_text(), 'html.parser')
            self.assertIn('See the overview.', section.get_text())
            self.assertFalse(section.select('a[href*="ABCDEF12"]'))
            self.assertIn(r'\[x=1\]', section.get_text())
            collection = json.loads((root / 'collection.json').read_text())
            self.assertEqual({t['slug'] for t in collection['topics']}, {'alpha', 'gamma'})
            self.assertEqual(len(collection['entries']), 3)
            self.assertNotIn('ABCDEF12', {r['tag'] for r in json.loads((root / 'search.json').read_text())})
            for route in ('sections/beta', 'topics/beta', 'tag/ABCDEF12', 'books/source/tag/00000003', 'books/source/tag/ABCDEF12'):
                path = root / route / 'index.html'
                soup = BeautifulSoup(path.read_text(), 'html.parser')
                self.assertEqual((path.parent / soup.html['data-redirect'] / 'index.html').resolve(), (root / 'chapters/index.html').resolve())
                self.assertNotIn('Definition 1.1.3', soup.get_text())
            check_links(root)

    def test_section_keeps_only_the_preferred_version_of_a_shared_result(self):
        old = '<article id="22222222"><p>Definition 1. The repeated statement.</p></article><article class="env-proof"><p>Old source proof.</p></article>'
        preferred = '<article id="33333333"><p>Definition 2. The preferred statement.</p></article><article class="env-proof"><p>Preferred proof.</p></article>'
        entries = {
            'AAAAAAAA': {'tag': 'AAAAAAAA', 'topic': 'alpha', 'variants': [{'source': 'a', 'tag': '11111111', 'label': 'sec:alpha', 'title': '1 Alpha', 'section': True, 'html': '<h2 id="sec:alpha">1 Alpha</h2>' + old}]},
            'BBBBBBBB': {'tag': 'BBBBBBBB', 'topic': 'alpha', 'variants': [{'source': 'b', 'tag': '33333333', 'label': 'def:new', 'title': 'Definition 2', 'html': preferred}, {'source': 'a', 'tag': '22222222', 'label': 'def:old', 'title': 'Definition 1', 'html': old}]}
        }
        html = continuous_section(list(entries.values()), entries, source_roots(entries), {'a': {'title': 'Source A'}, 'b': {'title': 'Source B'}}, {}, {}, '../../', {})
        soup = BeautifulSoup(html, 'html.parser')
        self.assertNotIn('Old source proof.', soup.get_text())
        self.assertEqual(soup.get_text().count('Preferred proof.'), 1)
        self.assertEqual(len(soup.select('.shared-entry-reference')), 1)

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

    def test_a_section_named_comments_does_not_replace_the_comment_panel_anchor(self):
        self.records[-1]['topic'] = 'Comments'
        self.config['topics'][-1] = {'slug': 'comments', 'title': 'Comments'}
        self.config['chapters'][-1]['topics'] = ['comments']
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.build(root)
            soup = BeautifulSoup((root / 'chapters/second/index.html').read_text(), 'html.parser')
            self.assertEqual(len(soup.select('#comments')), 1)
            self.assertEqual(soup.select_one('#comments')['class'], ['comments-panel'])
            self.assertTrue(soup.select_one('#section-comments a'))
            check_links(root)

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
