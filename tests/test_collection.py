import copy
import tempfile
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from collection import organize, prepare_fragment, statement_fingerprint, chapter_structure, check_links, redirect


class CollectionTests(unittest.TestCase):
    def setUp(self):
        self.record = {"tag": "1234ABCD", "label": "thm:shared", "title": "Theorem 1.1", "semantic_title": "A shared theorem", "kind": "theorem", "topic": "Potential theory", "html": "<p>A statement.</p>"}
        self.config = {"version": 1, "topics": [], "entries": []}

    def test_same_source_label_in_two_texts_cannot_collide(self):
        entries, topics, links = organize({"first": [self.record], "second": [self.record]}, self.config)
        self.assertEqual(len(entries), 2)
        self.assertEqual(len(topics), 1)
        self.assertNotEqual(links[("first", "1234ABCD")], links[("second", "1234ABCD")])

    def test_canonical_merge_retains_both_source_statements(self):
        self.config["topics"] = [{"slug": "potential-theory", "title": "Potential theory"}]
        self.config["entries"] = [{"tag": "ABCD1234", "title": "Shared result", "topic": "potential-theory", "members": [{"source": source, "label": "thm:shared"} for source in ("first", "second")]}]
        entries, _, links = organize({"first": [self.record], "second": [self.record]}, self.config)
        self.assertEqual(list(entries), ["ABCD1234"])
        self.assertEqual({v["source"] for v in entries["ABCD1234"]["variants"]}, {"first", "second"})
        self.assertEqual(set(links.values()), {"ABCD1234"})

    def test_aliases_cannot_point_to_conflicting_canonical_entries(self):
        self.config["topics"] = [{"slug": "potential-theory", "title": "Potential theory"}]
        self.config["entries"] = [{"tag": tag, "title": tag, "topic": "potential-theory", "members": [{"source": "first", "label": label}]} for tag, label in (("ABCD1234", "thm:shared"), ("DCBA4321", "thm:alias"))]
        record = {**self.record, "aliases": ["thm:alias"]}
        with self.assertRaises(ValueError):
            organize({"first": [record]}, self.config)

    def test_cross_references_use_global_routes_and_keep_source_status(self):
        variant = {**self.record, "source": "first", "html": '<h2><a href="/tag/1234ABCD"><span data-tag="1234ABCD">1.1</span></a></h2><p>$x&lt;y$ <a href="/bibliography/Author">citation</a></p>'}
        result = prepare_fragment(variant, {("first", "1234ABCD"): "ABCD1234"}, {("first", "Author"): "R0001"}, "../../")
        self.assertIn('href="../../tag/ABCD1234/"', result)
        self.assertIn('data-gerby-tag="1234ABCD"', result)
        self.assertIn('href="../../references/#R0001"', result)
        self.assertIn("$x&lt;y$", result)

    def test_changed_statement_requires_new_duplicate_review(self):
        first = {**self.record, "statement_tex": r"\begin{thmenv}\label{thm:shared}Assume $x>0$. Then $x^2>0$.\end{thmenv}"}
        self.config["topics"] = [{"slug": "potential-theory", "title": "Potential theory"}]
        self.config["entries"] = [{"tag": "ABCD1234", "title": "Shared result", "topic": "potential-theory", "members": [{"source": s, "label": "thm:shared", "statement_sha256": statement_fingerprint(first)} for s in ("first", "second")]}]
        organize({"first": [first], "second": [first]}, self.config)
        changed = {**first, "statement_tex": first["statement_tex"].replace("x>0", "x<0")}
        with self.assertRaisesRegex(ValueError, "changed and needs review"):
            organize({"first": [first], "second": [changed]}, self.config)

    def test_unreviewed_exact_duplicates_stop_publication(self):
        record = {**self.record, "statement_tex": r"\label{thm:shared}A statement with $x<y$."}
        with self.assertRaisesRegex(ValueError, "exact duplicate"):
            organize({"first": [record], "second": [record]}, self.config)
        different = {**record, "statement_tex": r"\label{thm:shared}A statement with $x\leq y$."}
        entries, _, _ = organize({"first": [record], "second": [different]}, self.config)
        self.assertEqual(len(entries), 2)

    def test_numbered_clause_retains_its_parent_anchor_and_badge(self):
        parent = {**self.record, "html": '<article><ol><li id="8765ABCD">A condition.</li></ol></article>'}
        clause = {**self.record, "tag": "8765ABCD", "label": "itm:shared:1", "kind": "item", "parent_label": "thm:shared", "html": '<li id="8765ABCD">A condition.</li>'}
        entries, _, links = organize({"first": [parent, clause]}, self.config)
        self.assertEqual(len(entries), 1)
        entry = next(iter(entries.values()))
        self.assertEqual(entry["components"][0]["tag"], "8765ABCD")
        self.assertEqual(links[("first", "8765ABCD")], entry["tag"])
        fragment = prepare_fragment({**parent, "source": "first", "html": parent["html"] + '<a href="/tag/8765ABCD">the condition</a>'}, links, {}, "../../", {("first", "8765ABCD"): "#first-8765ABCD"})
        self.assertIn('data-gerby-tag="8765ABCD"', fragment)
        self.assertIn('/#first-8765ABCD"', fragment)

    def test_every_subject_needs_an_editorial_chapter(self):
        topics = {"first": {"title": "First"}, "second": {"title": "Second"}}
        config = {"chapters": [{"slug": "shared", "title": "A shared chapter", "topics": ["first"]}]}
        with self.assertRaisesRegex(ValueError, "Assign new source subjects"):
            chapter_structure(topics, config)
        config["chapters"][0]["topics"].append("second")
        chapters, mapping = chapter_structure(topics, config)
        self.assertEqual(chapters["shared"]["number"], 1)
        self.assertEqual(set(mapping.values()), {"shared"})

    def test_missing_source_illustrations_are_broken_links(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "index.html").write_text('<img src="missing.svg" alt="A diagram">')
            with self.assertRaisesRegex(ValueError, "Broken internal link"):
                check_links(root)

    def test_absorbed_heading_redirects_keep_clause_fragment_targets(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "assets").mkdir()
            (root / "assets/redirect.js").touch()
            (root / "section.html").write_text('<h1 id="intro">Analysis</h1><li id="source-clause">A condition.</li>')
            redirect(root / "tag/index.html", root / "section.html", root, {"source-clause": "source-clause"}, anchor="#intro")
            (root / "index.html").write_text('<a href="tag/#source-clause">The condition</a>')
            check_links(root)

    def test_display_math_diagrams_become_real_images(self):
        html = r'\[ \gerbyimage{first/diagram.svg}{A diagram} \]'
        result = prepare_fragment({**self.record, "source": "first", "html": html}, {}, {}, "../../")
        self.assertIn('src="../../assets/sources/first/diagram.svg"', result)
        self.assertNotIn(r"\gerbyimage", result)
        self.assertNotIn(r"\[", result)

    def test_equation_citations_link_to_the_correct_source_statement(self):
        html = r'\[x&lt;y\quad\textup{by \gerbyref{1234ABCD}{1.1}}\]'
        result = prepare_fragment({**self.record, "source": "first", "html": html}, {("first", "1234ABCD"): "ABCD1234"}, {}, "../../")
        self.assertIn(r"\href{../../tag/ABCD1234/}{1.1}", result)
        with self.assertRaisesRegex(ValueError, "Unresolved mathematical reference"):
            prepare_fragment({**self.record, "source": "second", "html": html}, {("first", "1234ABCD"): "ABCD1234"}, {}, "../../")

    def test_tex_labels_are_not_exposed_inside_reader_formulas(self):
        html = r'\begin{equation}\label{eq:internal_name}x=y\end{equation}'
        result = prepare_fragment({**self.record, "source": "first", "html": html}, {}, {}, "../../")
        self.assertNotIn(r"\label", result)
        self.assertNotIn("internal_name", result)
        self.assertIn("x=y", result)


if __name__ == "__main__":
    unittest.main()
