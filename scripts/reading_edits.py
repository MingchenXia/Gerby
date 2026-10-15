"""Reviewed prose edits and internal references for the Pome reading edition.

Mathematical source strings and proof guards are left intact. Original attribution
is retained on Sources pages; historical sections retain the original exposition.
"""
from hashlib import sha256
import json
import re

from bs4 import BeautifulSoup
from reader import display_title


def normalized_text(node):
    return re.sub(r"\s+", " ", node.get_text(" ", strip=True)).strip()


def context_key(source, node):
    return source, sha256(normalized_text(node).encode()).hexdigest()


def validate_reading_edits(exports, registry_path):
    registry = json.loads(registry_path.read_text())
    expected = {(r['source'], r['text_sha256']) for r in registry['paragraphs'] if 'replacement_html' in r}
    found = set()
    for source, records in exports.items():
        if not any(key[0] == source for key in expected):
            continue
        for variant in records:
            soup = BeautifulSoup(variant['html'], 'html.parser')
            for node in soup.select('p, aside, .motto'):
                key = context_key(source, node)
                if key in expected:
                    found.add(key)
    if missing := expected - found:
        raise ValueError(f'Review changed source prose before publishing: {sorted(missing)}')


def attribution_markup(node):
    copy = BeautifulSoup(str(node), "html.parser")
    for element in copy.select('.environment-identifier, [data-gerby-tag], .source-footnotemark'):
        element.decompose()
    for element in copy.select('[id]'):
        del element['id']
    for note in copy.select('aside.source-footnote'):
        note.name = 'span'
        note.attrs = {'class': 'attribution-note'}
    for text in copy.find_all(string=re.compile(r'\\gerbyfootnotemark')):
        text.replace_with(re.sub(r'\\gerbyfootnotemark\{[^{}]+\}', '', text))
    return str(copy)


def replacement_fragment(original, markup):
    replacement = BeautifulSoup(markup, 'html.parser')
    # Parser-generated footnote IDs are not stable source identities. Reuse
    # this export's pairing metadata when a reviewed paragraph retains notes.
    for selector in ('aside.source-footnote', '.source-footnotemark'):
        old, new = original.select(selector), replacement.select(selector)
        if new and len(old) != len(new):
            raise ValueError('Review a prose edit that changes only some of its footnotes')
        for current, retained in zip(old, new):
            for key in ('id', 'data-footnote-mark'):
                if current.has_attr(key):
                    retained[key] = current[key]
    return replacement


def source_locator_targets(cite, locators, current_tag):
    """Resolve explicit SGPT coordinates only; never guess from similar names."""
    keys = [a.get('href', '').removeprefix('/bibliography/') for a in cite.select('a')]
    if keys != ['SGPT']:
        return []
    postnote = cite.select_one('.postnote')
    if not postnote:
        return []
    text = normalized_text(postnote)
    numbers = re.findall(r'\b(?:[A-Z]|\d+)\.(?:\d+\.)*\d+\b', text)
    if not numbers:
        numbers = re.findall(r'\b(?:chapter|section|subsection)\s+([A-Z]|\d+)\b', text, re.I)
    if not numbers:
        # Named headings are exact source captions, not guessed concepts.
        titles = re.findall(r'[“"]([^”"]+)[”"]', text)
        if not titles:
            titles = [re.sub(r'^(?:subsection|section)\s+', '', text, flags=re.I)]
        targets = [locators.get(('caption', title.casefold())) for title in titles]
    else:
        if len(numbers) == 2 and re.search(r'[–—]', text):
            start, end = numbers
            if start.rsplit('.', 1)[0] == end.rsplit('.', 1)[0]:
                prefix = start.rsplit('.', 1)[0]
                numbers = [f'{prefix}.{n}' for n in range(int(start.split('.')[-1]), int(end.split('.')[-1]) + 1)]
        family = 'heading' if re.search(r'\b(?:chapter|section|subsection)\b', text, re.I) else 'statement'
        targets = [locators.get((family, n)) for n in numbers]
    if not targets or any(t is None or t['tag'] == current_tag for t in targets):
        return []
    return list({t['tag']: t for t in targets}.values())


def apply_reading_edits(entries, topic_chapters, registry_path):
    registry = json.loads(registry_path.read_text())
    if registry['version'] != 1:
        raise ValueError('Unsupported reading-edition registry')
    edits = {}
    for item in registry['paragraphs']:
        digest = sha256(item['context'].encode()).hexdigest()
        if digest != item['text_sha256']:
            raise ValueError('Reading context fingerprint does not match its text')
        edits[item['source'], digest] = item
    locators = {}
    for entry in entries.values():
        for v in entry['variants']:
            if v['source'] != 'sgpt':
                continue
            family = 'heading' if v.get('section') else 'statement'
            if v['kind'] not in {'equation', 'item'} and v.get('number'):
                locators[family, v['number']] = entry
            if v.get('section'):
                locators['caption', v['caption'].casefold()] = entry
    notes, counts = {}, {'reviewed_edits': 0, 'internal_references': 0, 'source_notes': 0}

    def retain(source, node, entry, variant):
        key = context_key(source, node)
        note = {'source': source, 'tag': entry['tag'], 'html': attribution_markup(node), 'size': len(variant['html']), 'label': variant['label']}
        if key not in notes or note['size'] < notes[key]['size']:
            notes[key] = note

    for entry in entries.values():
        if topic_chapters[entry['topic']] == 'historical-notes':
            continue
        for variant in entry['variants']:
            source = variant['source']
            soup = BeautifulSoup(variant['html'], 'html.parser')
            caption_attributions = set()
            # A motto is the original author's front matter, not an assumption.
            for node in list(soup.select('.motto')):
                retain(source, node, entry, variant)
                node.decompose()
            for node in list(soup.find_all(['p', 'aside'])):
                if node.parent is None or not any(parent is soup for parent in node.parents) or node.find('p'):
                    continue
                edit = edits.get(context_key(source, node))
                if edit is None or 'replacement_html' not in edit:
                    continue
                if node.select('.cite, aside.source-footnote'):
                    retain(source, node, entry, variant)
                node.replace_with(replacement_fragment(node, edit['replacement_html']))
                counts['reviewed_edits'] += 1
            # Pure bibliographical footnotes must not interrupt an existing proof.
            for node in list(soup.select('aside.source-footnote')):
                text = normalized_text(node)
                inline = node.get('data-footnote-mark', node.get('id')) == node.get('id')
                if inline and node.select_one('.cite') and re.match(r'Note\. (?:The original argument in|In (?:the (?:original article|proof of)|\[)|The proof of|We remind the readers that the (?:statement|third displayed))', text):
                    retain(source, node, entry, variant)
                    node.decompose()
            # A source locator in a proved statement's caption is attribution.
            # Unproved external inputs retain their visible citation.
            for named in list(soup.select('.named')):
                article = named.find_parent('article')
                following = article.find_next_sibling('article') if article else None
                proved = following is not None and 'env-proof' in following.get('class', [])
                definition = article is not None and 'env-definition' in article.get('class', [])
                if not (proved or definition):
                    continue
                for cite in list(named.select('.cite')):
                    retain(source, cite, entry, variant)
                    if article.has_attr('id'):
                        caption_attributions.add(article['id'])
                    cite.decompose()
                if not named.get_text(strip=True).strip('() ,;'):
                    named.decompose()
            for cite in list(soup.select('.cite')):
                targets = source_locator_targets(cite, locators, entry['tag'])
                if not targets:
                    continue
                retain(source, cite, entry, variant)
                replacement = soup.new_tag('span', attrs={'class': 'internal-references'})
                postnote = cite.select_one('.postnote')
                if postnote and normalized_text(postnote).lower().startswith('proof of'):
                    replacement.append('the proof of ')
                for i, target in enumerate(targets):
                    if i:
                        replacement.append(', ')
                    anchor = soup.new_tag('a', attrs={'data-proof-entry': target['tag']})
                    anchor.string = display_title(target)
                    replacement.append(anchor)
                cite.replace_with(replacement)
                counts['internal_references'] += 1
            for anchor in soup.select('a[data-reading-entry]'):
                tag = anchor['data-reading-entry']
                if tag not in entries:
                    raise ValueError('Missing reading-edition reference: ' + tag)
                anchor['data-proof-entry'] = tag
                anchor.string = display_title(entries[tag])
                del anchor['data-reading-entry']
            # Neutral scope language; mathematical assumptions and names survive.
            for text in list(soup.find_all(string=True)):
                if text.parent.name in {'script', 'style'}:
                    continue
                value = str(text)
                value = re.sub(r'\b(?:in the whole book|in this book)\b', 'here', value, flags=re.I)
                value = re.sub(r'\bthroughout (?:the whole book|the book)\b', 'throughout these constructions', value, flags=re.I)
                if value != str(text):
                    text.replace_with(value)
            variant['html'] = str(soup)
            root_article = soup.find('article', id=variant['tag'])
            if root_article is not None:
                identifier = root_article.select_one('.environment-identifier')
                if identifier is not None and not identifier.select_one('.named .cite'):
                    caption = variant.get('caption', '')
                    if variant['tag'] in caption_attributions:
                        variant['caption'] = re.sub(r'\[[^\[\]]*\]', '', caption).strip(' ,;')
                    elif caption.startswith('[') and identifier.select_one('.named') is None:
                        variant['caption'] = ''
    counts['source_notes'] = len(notes)
    return list(notes.values()), counts
