import copy
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("build", Path(__file__).resolve().parents[1] / "scripts/build.py")
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)


class RegistryTests(unittest.TestCase):
    def setUp(self):
        self.books = {"version": 1, "books": [{"slug": "sample", "title": "A <book>", "repository": "https://github.com/owner/book", "status": "pending"}]}
        self.item = {"book": "sample", "tag": "0001", "state": "verified", "repository": "https://github.com/owner/proofs", "commit": "a" * 40, "file": "Proofs/Main.lean", "declaration": "Book.theorem_one", "verification": {"command": "lake build; lake env lean Audit.lean", "evidence_url": "https://github.com/owner/proofs/actions/runs/123", "checked_at": "2026-10-15T00:00:00Z", "axioms": ["propext", "Classical.choice", "Quot.sound"]}}
        self.registry = {"version": 1, "entries": [self.item]}

    def test_empty_and_verified_metadata(self):
        build.validate({"version": 1, "books": []}, {"version": 1, "entries": []})
        build.validate(self.books, self.registry)

    def test_no_verified_badge_for_sorry_or_custom_axioms(self):
        for axiom in ("sorryAx", "Book.assumed_theorem"):
            with self.subTest(axiom=axiom):
                self.item["verification"]["axioms"] = [axiom]
                with self.assertRaises(ValueError):
                    build.validate(self.books, self.registry)

    def test_unknown_books_and_duplicate_tags_are_rejected(self):
        invalid = copy.deepcopy(self.registry)
        invalid["entries"][0]["book"] = "missing"
        with self.assertRaises(ValueError):
            build.validate(self.books, invalid)
        self.registry["entries"].append(copy.deepcopy(self.item))
        with self.assertRaises(ValueError):
            build.validate(self.books, self.registry)

    def test_verification_requires_evidence_and_exact_commit(self):
        for key in ("commit", "verification", "declaration", "file"):
            with self.subTest(key=key):
                invalid = copy.deepcopy(self.registry)
                del invalid["entries"][0][key]
                with self.assertRaises(ValueError):
                    build.validate(self.books, invalid)

    def test_new_upstream_commit_downgrades_badge(self):
        key = build.source_key(self.item)
        result = build.public_formalizations(self.registry, {key: {"commit": "b" * 40}})
        self.assertEqual(result["entries"][0]["state"], "pending")
        self.assertEqual(self.item["state"], "verified")
        result = build.public_formalizations(self.registry, {key: {"commit": "a" * 40}})
        self.assertEqual(result["entries"][0]["state"], "verified")

    def test_unchecked_local_build_does_not_claim_current_verification(self):
        result = build.public_formalizations(self.registry, {})
        self.assertEqual(result["entries"][0]["state"], "pending")

    def test_source_and_output_paths_are_constrained(self):
        for path in ("../secret", "/tmp/book", "a/../../secret", "a\\file"):
            with self.subTest(path=path):
                with self.assertRaises(ValueError):
                    build.relative_path(path)
        self.books["books"][0]["repository"] = "https://example.com/book"
        with self.assertRaises(ValueError):
            build.validate(self.books, {"version": 1, "entries": []})

    def test_catalogue_escapes_titles_and_has_no_pending_read_link(self):
        markup = build.book_markup(self.books["books"])
        self.assertIn("A &lt;book&gt;", markup)
        self.assertNotIn("Read book", markup)
        self.assertIn("Source repository", markup)


if __name__ == "__main__":
    unittest.main()
