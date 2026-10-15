from pathlib import Path
import sys
import unittest

from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from footnotes import collect_notes, number_notes, relocate_notes


class FootnoteTests(unittest.TestCase):
    def test_inline_note_moves_after_the_complete_environment_with_return_link(self):
        html = '<article class="env-definition"><p>A <em>positive</em><aside id="n1" class="source-footnote"><span class="footnote-label">Note.</span>Weak positivity.</aside> current.</p><p>The remaining definition.</p></article>'
        soup = BeautifulSoup(relocate_notes(html, "test"), "html.parser")
        self.assertEqual(soup.article.p.get_text(), "A positive1 current.")
        self.assertIsNone(soup.article.find('aside'))
        self.assertEqual(soup.article.find_next_sibling()['id'], 'n1')
        self.assertEqual(soup.select_one('.footnote-reference a')['href'], '#n1')
        self.assertEqual(soup.select_one('.footnote-backlink')['href'], '#fnref-n1')

    def test_multiple_notes_follow_the_environment_in_source_order(self):
        html = '<article><p>First<aside class="source-footnote" id="a">One.</aside> second<aside class="source-footnote" id="b">Two.</aside>.</p></article>'
        soup = BeautifulSoup(relocate_notes(html, "test"), "html.parser")
        self.assertEqual([n['id'] for n in soup.select('aside')], ['a', 'b'])
        self.assertEqual([n.get_text() for n in soup.select('sup a')], ['1', '2'])

    def test_prose_and_quotation_notes_follow_their_blocks(self):
        html = '<blockquote>A quotation<aside class="source-footnote" id="a">An explanation.</aside>.</blockquote>'
        soup = BeautifulSoup(relocate_notes(html, "test"), "html.parser")
        self.assertIsNone(soup.blockquote.aside)
        self.assertEqual(soup.blockquote.find_next_sibling()['id'], 'a')

    def test_separate_html_mark_uses_the_original_reference_position(self):
        html = '<article><p>Text<span class="source-footnotemark" id="mark"></span> continues.</p><aside class="source-footnote" id="note" data-footnote-mark="mark">Explanation.</aside></article>'
        soup = BeautifulSoup(relocate_notes(html, "test"), "html.parser")
        self.assertEqual(soup.article.p.get_text(), 'Text1 continues.')
        self.assertIsNone(soup.select_one('.source-footnotemark'))

    def test_math_marks_and_standalone_equations_share_a_note_and_number(self):
        note = '<aside class="source-footnote" id="note" data-footnote-mark="mark">An explanation.</aside>'
        references = {('test', key): {'id': 'note', 'number': '3', 'html': note} for key in ('mark', 'note')}
        html = r'<div class="equation">\[x=2\gerbyfootnotemark{mark}\]</div>'
        soup = BeautifulSoup(relocate_notes(html, 'test', references), 'html.parser')
        self.assertIn(r'{}^{\href{#test-note}{3}}', soup.get_text())
        self.assertTrue(soup.find(id='fnref-note'))
        self.assertEqual(soup.select_one('.footnote-backlink')['href'], '#fnref-note')
        self.assertIsNone(soup.div.aside)

    def test_note_numbering_uses_the_smallest_owner_and_resets_by_section(self):
        candidates = {}
        html = '<aside class="source-footnote" id="a">A note.</aside>'
        parent = {'source': 'test', 'html': html * 3}
        collect_notes(candidates, BeautifulSoup(html, 'html.parser'), {'topic': 'overview'}, parent, 0)
        collect_notes(candidates, BeautifulSoup(html, 'html.parser'), {'topic': 'first'}, {**parent, 'html': html}, 1)
        second = html.replace('id="a"', 'id="b"')
        collect_notes(candidates, BeautifulSoup(second, 'html.parser'), {'topic': 'second'}, {**parent, 'html': second}, 2)
        references = number_notes(candidates)
        self.assertEqual(references['test', 'a']['topic'], 'first')
        self.assertEqual(references['test', 'a']['number'], '1')
        self.assertEqual(references['test', 'b']['number'], '1')

    def test_unpaired_math_marks_fail_instead_of_becoming_asterisks(self):
        with self.assertRaisesRegex(ValueError, 'Unresolved mathematical footnote'):
            relocate_notes(r'\[x\gerbyfootnotemark{unknown}\]', 'test')


if __name__ == '__main__':
    unittest.main()
