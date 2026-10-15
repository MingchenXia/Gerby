from hashlib import sha256
import json
from pathlib import Path
import sys
import tempfile
import unittest

from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from collection import prepare_fragment, statement_fingerprint
from proof_expansions import apply_expansions, check_dependencies


class ProofExpansionTests(unittest.TestCase):
    def setUp(self):
        self.record = {"tag": "1234ABCD", "label": "thm:target", "statement_tex": "A statement.", "html": '<article id="1234ABCD"><p>A statement.</p></article>', "proof_html": ""}
        self.expansion = {"source": "source", "label": "thm:target", "statement_sha256": statement_fingerprint(self.record), "original_proof_sha256": sha256(b"").hexdigest(), "file": "proof.html"}

    def apply(self, records, expansion=None):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "registry.json").write_text(json.dumps({"version": 1, "entries": [expansion or self.expansion]}))
            (root / "proof.html").write_text('<p>Proof. Use <a data-proof-entry="ABCDEF12">the earlier lemma</a>.</p>')
            return apply_expansions({"source": records}, root / "registry.json", statement_fingerprint)

    def test_proof_appears_in_both_entry_and_enclosing_section_without_changing_inputs(self):
        section = {"tag": "00000001", "label": "sec:parent", "statement_tex": "Section", "html": '<h2 id="sec:parent">Section</h2>' + self.record["html"]}
        exports, dependencies = self.apply([section, self.record])
        for record in exports["source"]:
            soup = BeautifulSoup(record["html"], "html.parser")
            self.assertEqual(len(soup.select(".proof-expansion")), 1)
            self.assertEqual(soup.find(id="1234ABCD").find_next_sibling()["class"], ["env-proof", "proof-expansion"])
        self.assertNotIn("proof-expansion", self.record["html"])
        self.assertEqual(dependencies[("source", "thm:target")], {"ABCDEF12"})
        rendered = prepare_fragment({**exports["source"][1], "source": "source"}, {}, {}, "../../")
        self.assertIn('href="../../tag/ABCDEF12/"', rendered)

    def test_changed_statement_or_original_proof_requires_review(self):
        with self.assertRaisesRegex(ValueError, "statement change"):
            self.apply([{**self.record, "statement_tex": "A stronger statement."}])
        with self.assertRaisesRegex(ValueError, "source proof change"):
            self.apply([{**self.record, "proof_html": "A newly supplied proof."}])

    def test_partial_source_proof_is_replaced_instead_of_duplicated(self):
        original = '<article class="env-proof"><p>Deferred old argument.</p></article>'
        record = {**self.record, "proof_html": original, "html": self.record["html"] + original}
        expansion = {**self.expansion, "original_proof_sha256": sha256(original.encode()).hexdigest()}
        exports, _ = self.apply([record], expansion)
        soup = BeautifulSoup(exports["source"][0]["html"], "html.parser")
        self.assertEqual(len(soup.select(".env-proof")), 1)
        self.assertNotIn("Deferred old argument", soup.get_text())

    def test_missing_dependencies_and_circular_expansions_stop_build(self):
        first = {"variants": [{"source": "source", "label": "thm:first"}]}
        second = {"variants": [{"source": "source", "label": "thm:second"}]}
        entries = {"ABCDEF12": first, "1234ABCD": second}
        with self.assertRaisesRegex(ValueError, "Missing internal"):
            check_dependencies(entries, {("source", "thm:first"): {"DEADBEEF"}})
        with self.assertRaisesRegex(ValueError, "Circular"):
            check_dependencies(entries, {("source", "thm:first"): {"1234ABCD"}, ("source", "thm:second"): {"ABCDEF12"}})


if __name__ == "__main__":
    unittest.main()
