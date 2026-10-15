import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "adapters"))
spec = importlib.util.spec_from_file_location("literature", ROOT / "adapters/classical-potential-theory.py")
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)


class LiteratureTests(unittest.TestCase):
    def source(self, root):
        entry = root / adapter.ENTRYPOINT
        entry.parent.mkdir(parents=True)
        entry.write_text(r"""\documentclass[11pt,a4paper]{article}
\newtheorem{theorem}{Theorem}[section]
\begin{document}
\maketitle
\section*{Scope, attribution and conventions}
Prerequisite text and attribution \cite[p.~36]{Helms1969}.
""" + "\n".join(r"\input{" + name + "}" for name in adapter.FRAGMENTS) + r"""
\bibliographystyle{alpha}\bibliography{contributions/classical-potential-theory}
\end{document}""")
        for number, (name, filename) in enumerate(adapter.FRAGMENTS.items(), 1):
            path = root / filename
            path.parent.mkdir(parents=True)
            result = path.parent.name.lower()
            path.write_text(rf"""\section{{{result}}}\label{{sec:{result}}}
\begin{{theorem}}\label{{thm:{result}}}For $x<y$, a selected statement.\end{{theorem}}
\begin{{proof}}Complete proof {number}.\end{{proof}}
""")
        (entry.parent / "classical-potential-theory.bib").write_text("@book{Helms1969, author={Helms, L. L.}, title={Introduction to Potential Theory}, year={1969}, publisher={Wiley-Interscience}}")
        private = root / "library/originals"
        private.mkdir(parents=True)
        (private / "unselected.tex").write_text("PRIVATE LIBRARY SENTINEL")
        return entry

    def test_export_preserves_article_numbering_proofs_citations_and_all_selected_tags(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source, output = root / "source", root / "export"
            self.source(source)
            subprocess.run(["git", "init", "-q", str(source)], check=True)
            subprocess.run(["git", "-C", str(source), "add", "."], check=True)
            subprocess.run(["git", "-C", str(source), "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-qm", "fixture"], check=True)
            subprocess.run([sys.executable, str(ROOT / "adapters/classical-potential-theory.py"), str(source), str(output)], check=True, capture_output=True)
            entries = json.loads((output / "entries.json").read_text())
            inventory = json.loads((output / "tags.json").read_text())
            self.assertEqual(len(inventory), 1 + 2 * len(adapter.RESULTS))
            self.assertEqual({e["label"] for e in entries}, {"sec:helms-prerequisites", *[f"{kind}:{result.lower()}" for kind in ("sec", "thm") for result in adapter.RESULTS]})
            self.assertEqual({e["topic"] for e in entries}, {"Conventions", *[adapter.result_topic(result) for result in adapter.RESULTS]})
            theorems = [e for e in entries if e["kind"] == "theorem"]
            self.assertEqual([e["title"] for e in theorems], [f"Theorem {number}.1" for number in range(1, len(adapter.RESULTS) + 1)])
            self.assertTrue(all("Complete proof" in e["proof_html"] and "x&lt;y" in e["statement_html"] for e in theorems))
            self.assertIn("Prerequisite text", entries[0]["html"])
            self.assertEqual(entries[0]["tag"], "59016F1B")
            self.assertEqual(next(e for e in theorems if e["label"] == "thm:r0001")["topic"], adapter.TOPIC)
            self.assertEqual(json.loads((output / "references.json").read_text())[0]["key"], "Helms1969")
            for item in inventory:
                page = (output / item["page"]).read_text()
                self.assertIn(f'data-gerby-tag="{item["tag"]}"', page)
                self.assertIn('data-gerby-book="classical-potential-theory"', page)
            self.assertFalse(any("PRIVATE LIBRARY SENTINEL" in p.read_text() for p in output.rglob("*") if p.is_file()))

    def test_changed_input_graph_or_nested_input_requires_review(self):
        first = next(iter(adapter.FRAGMENTS))
        initial = r"\input{" + first + "}"
        for replacement in (r"\input{../../library/originals/unselected}", initial + initial):
            with self.subTest(replacement=replacement), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                entry = self.source(root)
                entry.write_text(entry.read_text().replace(initial, replacement))
                with self.assertRaisesRegex(ValueError, "Unreviewed literature input"):
                    adapter.prepare_article(root)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.source(root)
            (root / adapter.FRAGMENTS[first]).write_text(r"\input{private}")
            with self.assertRaisesRegex(ValueError, "input graph"):
                adapter.prepare_article(root)

    def test_selected_symlink_cannot_escape_source_repository(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            self.source(source)
            outside = root / "outside.tex"
            outside.write_text("Outside manuscript")
            fragment = source / next(iter(adapter.FRAGMENTS.values()))
            fragment.unlink()
            fragment.symlink_to(outside)
            with self.assertRaisesRegex(ValueError, "unsafe selected"):
                adapter.prepare_article(source)


if __name__ == "__main__":
    unittest.main()
