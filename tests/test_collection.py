import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from collection import organize, prepare_fragment


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


if __name__ == "__main__":
    unittest.main()
