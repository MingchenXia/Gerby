import json
from pathlib import Path
import sys
import tempfile
import unittest

from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from collection import prepare_fragment, check_links
from numbering import assign_numbers
from reader import Reader, display_title
from structure import arrange_sections, title_key


class NumberingTests(unittest.TestCase):
    def setUp(self):
        self.entries = {}
        for index, (kind, caption, old) in enumerate((("chapter", "Analysis", "47"), ("section", "Inversion", "4"), ("theorem", "Kelvin transform", "4.1"), ("equation", "", "2"), ("lemma", "", "4.2"), ("section", "Boundary limits", "5"), ("theorem", "", "5.1")), 1):
            tag = f"{index:08X}"
            variant = {"source": "first", "tag": tag, "label": "label:" + tag, "kind": kind, "caption": caption, "number": old, "title": old + " " + caption, "section": kind in {"chapter", "section"}, "html": ""}
            self.entries[tag] = {"tag": tag, "topic": "analysis", "kind": kind, "variants": [variant], "components": []}
        self.topics = {"analysis": {"title": "Analysis"}}
        self.config = {"chapters": [{"slug": "analysis", "number": 3, "title": "Analysis", "topics": ["analysis"]}], "section_promotions": {"analysis": [{"start": "00000002", "slug": "inversion", "title": "Inversion"}, {"start": "00000006", "slug": "limits", "title": "Boundary limits"}]}}

    def arrange(self):
        config = arrange_sections(self.entries, self.topics, self.config)
        return config, assign_numbers({c["slug"]: c for c in config["chapters"]}, self.entries)

    def test_numbers_follow_current_section_and_reset_after_a_split(self):
        _, numbers = self.arrange()
        self.assertEqual(display_title(self.entries["00000003"]), "Theorem 3.2.1 (Kelvin transform)")
        self.assertEqual(display_title(self.entries["00000004"]), "Equation 3.2.2")
        self.assertEqual(display_title(self.entries["00000005"]), "Lemma 3.2.3")
        self.assertEqual(display_title(self.entries["00000007"]), "Theorem 3.3.1")
        self.assertEqual(numbers["first", "00000002"]["number"], "3.2")
        # Source coordinates remain provenance, never the reading locator.
        self.assertEqual(self.entries["00000003"]["variants"][0]["number"], "4.1")

    def test_merged_source_variants_share_one_number(self):
        variant = {**self.entries["00000003"]["variants"][0], "source": "second", "number": "99.7"}
        self.entries["00000003"]["variants"].append(variant)
        _, numbers = self.arrange()
        self.assertEqual(numbers["second", variant["tag"]]["number"], "3.2.1")

    def test_html_and_math_references_change_without_touching_mathematics(self):
        _, numbers = self.arrange()
        variant = {**self.entries["00000003"]["variants"][0], "html": '<a class="environment-identifier" href="/tag/00000003">Theorem <span data-tag="00000003">4.1</span>.</a><p>By (<a href="/tag/00000004" data-tag="00000004">2</a>), $d=2$.</p>' + r'\[x=2\quad\text{by \gerbyref{00000003}{4.1}}\]'}
        links = {("first", tag): tag for tag in self.entries}
        html = prepare_fragment(variant, links, {}, "../../", numbering=numbers)
        self.assertIn('data-tag="00000003">3.2.1</span>', html)
        self.assertIn('data-tag="00000004" href="../../tag/00000004/">3.2.2</a>', html)
        self.assertIn(r"\href{../../tag/00000003/}{3.2.1}", html)
        self.assertIn("$d=2$", html)
        self.assertIn("x=2", html)

    def test_imported_headings_appear_in_chapter_subsection_lists(self):
        config = arrange_sections(self.entries, self.topics, {**self.config, "section_promotions": {}})
        reader = Reader({c["slug"]: c for c in config["chapters"]}, self.topics, self.entries, {}, {})
        soup = BeautifulSoup(reader.section_list("analysis", "../../", subsections=True), "html.parser")
        self.assertEqual([a.get_text() for a in soup.select('.subsection-list a')], ['3.1.1 Inversion', '3.1.5 Boundary limits'])
        self.assertNotIn("tag/00000001", str(soup))
        self.assertNotIn("tag/00000001", reader.pages)

    def test_a_second_source_introduction_returns_to_the_overview(self):
        second = {**self.entries["00000001"], "tag": "00000008"}
        self.entries[second["tag"]] = second
        self.arrange()
        self.assertEqual(second["topic"], "analysis")
        self.assertTrue(second["section_intro"])

    def test_missing_split_boundaries_fail_instead_of_silently_moving_content(self):
        self.config["section_promotions"]["analysis"][0]["start"] = "DEADBEEF"
        with self.assertRaisesRegex(ValueError, "Missing or reordered"):
            self.arrange()

    def test_a_promoted_heading_is_absorbed_even_with_an_editorial_title(self):
        self.config["section_promotions"]["analysis"][0]["title"] = "Inversion and Kelvin transforms"
        self.arrange()
        self.assertTrue(self.entries["00000002"]["section_intro"])
        self.assertEqual(self.entries["00000003"]["number"], "3.2.1")

    def test_tex_styling_does_not_hide_a_duplicate_section_title(self):
        self.assertEqual(title_key(r"Multiplier-ideal envelopes and $\mathcal I$-goodness"), title_key("Multiplier-ideal envelopes and I-goodness"))

    def test_build_check_rejects_stale_display_numbers(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "sources/first").mkdir(parents=True)
            (root / "collection.json").write_text(json.dumps({"entries": [{"tag": "AAAAAAAA", "number": "3.2.1"}]}))
            (root / "sources/first/tags.json").write_text(json.dumps([{"tag": "00000003", "canonical_tag": "AAAAAAAA"}]))
            page = root / "index.html"
            page.write_text('<div data-gerby-book="first"><span data-tag="00000003">4.1</span></div>')
            with self.assertRaisesRegex(ValueError, "Stale source numbering"):
                check_links(root)
            page.write_text(page.read_text().replace('>4.1<', '>3.2.1<'))
            check_links(root)

    def test_equation_labels_have_a_shared_row_and_align_rows_get_current_tags(self):
        _, numbers = self.arrange()
        variant = {**self.entries["00000004"]["variants"][0], "html": '<div class="equation"><span class="equation-label"><a href="/tag/00000004" data-tag="00000004">2</a></span><div>\\[x=2\\]</div></div>'}
        html = prepare_fragment(variant, {("first", "00000004"): "00000004"}, {}, "../../", numbering=numbers)
        self.assertIn('class="equation numbered-equation"', html)
        numbers["first", "row"] = {"math_row": True, "tag": "00000004", "number": "3.2.2"}
        variant["html"] = r'\begin{align}x=2\label{row}\end{align}'
        self.assertIn(r"\tag{3.2.2}", prepare_fragment(variant, {}, {}, "../../", numbering=numbers))


if __name__ == "__main__":
    unittest.main()
