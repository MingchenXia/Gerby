"""Numbered, bidirectional notes placed after their containing environment."""
from collections import defaultdict
import re

from bs4 import BeautifulSoup

MATH_MARK = re.compile(r"\\gerbyfootnotemark\{([^{}]+)\}")


def collect_notes(candidates, soup, entry, variant, position):
    for index, note in enumerate(soup.select("aside.source-footnote[id]")):
        key = variant["source"], note["id"]
        record = {"id": note["id"], "mark": note.get("data-footnote-mark") or note["id"], "source": variant["source"], "topic": entry["topic"], "position": (position, index), "size": len(variant["html"]), "html": str(note)}
        # An enclosing chapter contains copies of its statements' notes. The
        # smallest actual fragment supplies their current section and order.
        if key not in candidates or record["size"] < candidates[key]["size"]:
            candidates[key] = record


def number_notes(candidates):
    counters, references = defaultdict(int), {}
    for record in sorted(candidates.values(), key=lambda r: r["position"]):
        counters[record["topic"]] += 1
        record = {**record, "number": str(counters[record["topic"]])}
        for identifier in {record["id"], record["mark"]}:
            references[record["source"], identifier] = record
    return references


def relocate_notes(markup, source, references=None):
    if not any(token in markup for token in ("source-footnote", "gerbyfootnotemark")):
        return markup
    soup = BeautifulSoup(markup, "html.parser")
    references = references or {}
    notes = {note["id"]: note for note in soup.select("aside.source-footnote[id]")}
    # A standalone equation can contain its mark while its footnotetext is in
    # the surrounding statement. Include the same note on both reading views.
    for match in MATH_MARK.finditer(markup):
        record = references.get((source, match[1]))
        if not record:
            raise ValueError(f"Unresolved mathematical footnote: {source}/{match[1]}")
        if record["id"] not in notes:
            notes[record["id"]] = BeautifulSoup(record["html"], "html.parser").select_one("aside.source-footnote")
    tails = {}
    for index, (identifier, note) in enumerate(notes.items(), 1):
        record = references.get((source, identifier), {})
        number = record.get("number", str(index))
        mark_id = note.get("data-footnote-mark") or identifier
        reference_id = "fnref-" + identifier
        marker = soup.find(id=mark_id) if mark_id != identifier else None
        math_text = next((text for text in soup.find_all(string=MATH_MARK) if any(m[1] == mark_id for m in MATH_MARK.finditer(text))), None)
        if math_text is not None:
            marker = soup.new_tag("span", id=reference_id, attrs={"class": "math-footnote-reference", "tabindex": "-1"})
            container = math_text.parent
            container.insert(0, marker)
            math_text.replace_with(MATH_MARK.sub(lambda m: (r"{}^{\href{#" + identifier + "}{" + number + "}}") if m[1] == mark_id else m[0], math_text))
        else:
            replacement = soup.new_tag("sup", id=reference_id, attrs={"class": "footnote-reference"})
            link = soup.new_tag("a", href="#" + identifier, attrs={"role": "doc-noteref", "aria-label": "Footnote " + number})
            link.string = number
            replacement.append(link)
            if marker is not None:
                marker.replace_with(replacement)
            elif note.parent is not None:
                note.insert_before(replacement)
            else:
                raise ValueError(f"A footnote has no reference position: {source}/{identifier}")
            marker = replacement
        environments = marker.find_parents("article")
        boundary = environments[-1] if environments else (marker.find_parent("blockquote") or marker.find_parent("figure") or marker.find_parent("p") or marker.find_parent("li") or marker.find_parent(class_="equation") or marker)
        note.extract()
        for label in note.select(".footnote-label"):
            label.decompose()
        note.attrs.pop("data-footnote-mark", None)
        note["role"] = "doc-footnote"
        backlink = soup.new_tag("a", href="#" + reference_id, attrs={"class": "footnote-backlink", "role": "doc-backlink", "aria-label": "Back to reference " + number})
        backlink.string = number + ". ↩"
        note.insert(0, backlink)
        note.insert(1, " ")
        tail = tails.get(id(boundary), boundary)
        tail.insert_after(note)
        tails[id(boundary)] = note
    if MATH_MARK.search(str(soup)) or soup.select(".source-footnotemark"):
        raise ValueError(f"An unpaired footnote marker remains: {source}")
    return str(soup)
