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

    def test_optional_labels_underscores_and_dotless_math_symbols(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, working = root / "source", root / "render"
            (source / "style").mkdir(parents=True)
            working.mkdir()
            (source / "style/book-preamble.tex").write_text("\\newcommand{\\nef}{\\mathrm{nef}}\n\\setlist")
            (source / "book.tex").write_text(r"""\documentclass[envcountsect]{svmono}
\begin{document}
\chapter{Appendix}\label[appendix]{chap:with_underscore}
\section{A section}\label{sec:test}
\begin{definition}\label{def:with_underscore}For $\iota,\jmath$, the rest of this definition survives.\end{definition}
\begin{equation}\label{eq:with_underscore}x<y\end{equation}
See \cref{def:with_underscore,eq:with_underscore}.
\[x<y\quad\textup{by \cref{def:with_underscore} and \eqref{eq:with_underscore}}\]
\end{document}""")
            records = adapter.render_fragments(source, working)
            self.assertEqual({r["label"] for r in records}, {"chap:with_underscore", "sec:test", "def:with_underscore", "eq:with_underscore"})
            definition = next(r for r in records if r["kind"] == "definition")
            self.assertIn("the rest of this definition survives", definition["html"])
            self.assertEqual(definition["parent_label"], "sec:test")
            self.assertNotIn("TeXFragment object", str(records))
            section = next(r for r in records if r["label"] == "sec:test")
            self.assertIn(r"\gerbyref{765FE373}{1.1.1}", section["html"])
            self.assertIn(r"\gerbyref{2C442D09}{1.1}", section["html"])

    def test_footnote_marks_keep_source_fingerprints_and_render_linkable_identities(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, working = root / 'source', root / 'render'
            (source / 'style').mkdir(parents=True)
            working.mkdir()
            (source / 'style/book-preamble.tex').write_text(r'\newcommand{\nef}{\mathrm{nef}}' + '\n' + r'\setlist')
            (source / 'book.tex').write_text(r'''\documentclass[envcountsect]{svmono}
\begin{document}\chapter{Notes}\label{chap:notes}\section{A section}\label{sec:notes}
\begin{definition}\label{def:notes}A term\footnote{Its meaning.}.
\[x=2\footnotemark\]\footnotetext{The formula note.}\end{definition}\end{document}''')
            records = adapter.render_fragments(source, working)
            definition = next(r for r in records if r['label'] == 'def:notes')
            self.assertIn(r'\footnotemark', definition['statement_tex'])
            self.assertNotIn(r'\gerbyfootnotemark', definition['statement_tex'])
            self.assertIn(r'\gerbyfootnotemark{', definition['html'])
            self.assertIn('data-footnote-mark=', definition['html'])


if __name__ == "__main__":
    unittest.main()
