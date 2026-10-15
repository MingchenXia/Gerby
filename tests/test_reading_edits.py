import json
from pathlib import Path
import sys
import tempfile
import unittest
from hashlib import sha256

from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from reading_edits import apply_reading_edits, normalized_text, source_locator_targets, validate_reading_edits, replacement_fragment


class ReadingEditsTests(unittest.TestCase):
    def entry(self, tag, html, **extra):
        return {'tag': tag, 'topic': 'body', 'reader_title': 'Theorem 1.2.3', 'variants': [{'source': 'sgpt', 'label': tag, 'tag': tag, 'html': html, 'title': 'Theorem 3.4.1', 'statement_tex': 'Original mathematical source.', 'caption': '', 'number': '3.4.1', 'kind': 'theorem', **extra}]}

    def apply(self, entries, paragraphs=(), historical=False):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'registry.json'
            path.write_text(json.dumps({'version': 1, 'paragraphs': list(paragraphs)}))
            return apply_reading_edits(entries, {'body': 'historical-notes' if historical else 'analysis'}, path)

    def test_reviewed_intro_moves_attribution_and_preserves_mathematical_source(self):
        html = '<p>Our presentation follows <span class="cite"><a href="/bibliography/Book">Book</a></span>.</p>'
        context = normalized_text(BeautifulSoup(html, 'html.parser'))
        edit = {'source': 'sgpt', 'context': context, 'text_sha256': sha256(context.encode()).hexdigest(), 'replacement_html': '<p>A mathematical introduction.</p>'}
        entries = {'A': self.entry('A', html)}
        notes, counts = self.apply(entries, [edit])
        self.assertIn('A mathematical introduction.', entries['A']['variants'][0]['html'])
        self.assertIn('Book', notes[0]['html'])
        self.assertEqual(entries['A']['variants'][0]['statement_tex'], 'Original mathematical source.')
        self.assertEqual(counts['source_notes'], 1)

    def test_history_and_necessary_external_proof_inputs_remain_explicit(self):
        html = '<article class="env-proof"><p>Use <span class="cite"><a href="/bibliography/External">External</a></span>.</p></article>'
        entries = {'A': self.entry('A', html)}
        self.apply(entries)
        self.assertIn('External', entries['A']['variants'][0]['html'])
        historical = '<blockquote class="motto">An original quotation.</blockquote>'
        entries = {'A': self.entry('A', historical)}
        self.apply(entries, historical=True)
        self.assertEqual(entries['A']['variants'][0]['html'], historical)

    def test_exact_source_locator_becomes_a_current_gerby_link(self):
        cite = '<span class="cite">[<span class="postnote">Theorem 3.4.1</span>, <a href="/bibliography/SGPT">SGPT</a>]</span>'
        entries = {'A': self.entry('A', '<p>By '+cite+'.</p>', number='2.1.1'), 'B': self.entry('B', '<p>A result.</p>')}
        notes, counts = self.apply(entries)
        soup = BeautifulSoup(entries['A']['variants'][0]['html'], 'html.parser')
        self.assertEqual(soup.select_one('a[data-proof-entry]')['data-proof-entry'], 'B')
        self.assertEqual(soup.a.get_text(), 'Theorem 1.2.3')
        self.assertEqual(counts['internal_references'], 1)
        self.assertIn('SGPT', notes[0]['html'])

    def test_self_references_and_inexact_locators_are_not_substituted(self):
        cite = BeautifulSoup('<span class="cite"><span class="postnote">Theorem 3.4.1</span><a href="/bibliography/SGPT">SGPT</a></span>', 'html.parser').span
        self.assertEqual(source_locator_targets(cite, {('statement', '3.4.1'): {'tag': 'A'}}, 'A'), [])
        self.assertEqual(source_locator_targets(cite, {}, 'B'), [])
        wrong_kind = {('statement', '3.4.1'): {'tag': 'B', 'source_kind': 'definition'}}
        self.assertEqual(source_locator_targets(cite, wrong_kind, 'A'), [])

    def test_motto_and_its_notes_move_together_without_duplicate_ids(self):
        entries = {'A': self.entry('A', '<blockquote class="motto">A quote<aside class="source-footnote" id="n">An author biography.</aside>.</blockquote><p>A condition $x=1$.</p>')}
        notes, _ = self.apply(entries)
        self.assertNotIn('motto', entries['A']['variants'][0]['html'])
        self.assertIn('$x=1$', entries['A']['variants'][0]['html'])
        self.assertIn('biography', notes[0]['html'])
        self.assertNotIn('id=', notes[0]['html'])

    def test_proved_statement_caption_moves_attribution_but_preserves_its_name(self):
        html = '<article class="env-theorem" id="A"><p><a class="environment-identifier"><span class="named">(A name <span class="cite">[Book]</span>)</span></a> A statement.</p></article><article class="env-proof"><p>A proof.</p></article>'
        entries = {'A': self.entry('A', html, caption='A name [Book]')}
        notes, _ = self.apply(entries)
        variant = entries['A']['variants'][0]
        self.assertEqual(variant['caption'], 'A name')
        self.assertIn('A name', variant['html'])
        self.assertNotIn('Book', variant['html'])
        self.assertIn('Book', notes[0]['html'])

    def test_changed_reviewed_source_context_fails_before_publication(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'registry.json'
            path.write_text(json.dumps({'version': 1, 'paragraphs': [{'source': 'sgpt', 'text_sha256': sha256(b'Old intro.').hexdigest(), 'replacement_html': '<p>New intro.</p>'}]}))
            with self.assertRaisesRegex(ValueError, 'Review changed source prose'):
                validate_reading_edits({'sgpt': [{'html': '<p>Changed source intro.</p>'}]}, path)

    def test_reviewed_note_keeps_the_current_exports_pairing_metadata(self):
        original = BeautifulSoup('<p><aside class="source-footnote" id="current-note" data-footnote-mark="current-mark">A note.</aside></p>', 'html.parser').p
        replacement = replacement_fragment(original, '<p><aside class="source-footnote" id="old-note" data-footnote-mark="">An adapted note.</aside></p>')
        self.assertEqual(replacement.aside['id'], 'current-note')
        self.assertEqual(replacement.aside['data-footnote-mark'], 'current-mark')


if __name__ == '__main__':
    unittest.main()
