import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("foundations", Path(__file__).resolve().parents[1] / "adapters/foundations-of-pluripotential-theory.py")
adapter = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = adapter
spec.loader.exec_module(adapter)


class FoundationsTests(unittest.TestCase):
    def test_tag_uses_the_label_rather_than_position_or_number(self):
        self.assertEqual(adapter.stable_tag("def:distribution"), "55085BC2")
        self.assertNotEqual(adapter.stable_tag("def:distribution"), adapter.stable_tag("def:measure"))

    def test_badges_are_outside_permalink_anchors(self):
        markup = '<article><p><a class="environment-identifier" href="/tag/55085BC2">Definition <span data-tag="55085BC2">1.1.1</span>.</a> Text.</p></article>'
        soup = adapter.BeautifulSoup(adapter.decorate(markup, "../../"), "html.parser")
        self.assertEqual(soup.a["href"], "../../tag/55085BC2/")
        self.assertIsNone(soup.a.find(attrs={"data-gerby-tag": True}))
        self.assertEqual(soup.a.find_next_sibling()["data-gerby-tag"], "55085BC2")

    def test_only_active_inputs_are_read_and_recursive_inputs_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "book.tex").write_text("% \\input{inactive}\n\\input{active}")
            (root / "active.tex").write_text("Active text.")
            self.assertIn("Active text.", adapter.active_text(root))
            (root / "active.tex").write_text("\\input{book}")
            with self.assertRaises(ValueError):
                adapter.active_text(root)

    def test_official_gerby_renderer_keeps_shared_section_numbering(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, working = root / "source", root / "render"
            (source / "style").mkdir(parents=True)
            working.mkdir()
            (source / "style/book-preamble.tex").write_text("\\newcommand{\\nef}{\\mathrm{nef}}\n\\setlist")
            (source / "book.tex").write_text(r"""\documentclass[envcountsect]{svmono}
\begin{document}
\chapter{A chapter}\label{chap:test}
\section{A section}\label{sec:test}
\begin{definition}\label{def:test}A definition with $x<y$ and $x^2$.\end{definition}
\begin{lemma}\label{lem:test}A lemma.\end{lemma}
\begin{proof}A proof.\end{proof}
\begin{align}
a&<b\label{eq:first}\\
b&<c\label{eq:second}
\end{align}
See \cref{def:test,eq:first}.
\end{document}""")
            records = adapter.render_fragments(source, working)
            self.assertEqual(len(records), 6)
            self.assertEqual(records[2]["title"], "Definition 1.1.1")
            self.assertEqual(records[3]["title"], "Lemma 1.1.2")
            self.assertIn("A proof.", records[3]["html"])
            self.assertIn("x&lt;y", records[2]["html"])
            self.assertTrue(all(record["kind"] == "equation" for record in records[4:]))
            self.assertTrue(all("&lt;" in record["html"] for record in records[4:]))
            self.assertTrue(all(record["html"].strip() for record in records))


if __name__ == "__main__":
    unittest.main()
