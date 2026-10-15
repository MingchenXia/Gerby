"""Assign reading-edition locators after chapter placement and deduplication."""
import re
from hashlib import sha256


def numbered_title(variant, number):
    # The explicit caption avoids guessing which digits belong to a title, or
    # turning internal source labels into invented mathematical names.
    caption = variant["caption"]
    if variant.get("section"):
        return f"{number} {caption}".strip()
    kind = "Figure" if variant["kind"] == "caption" else variant["kind"].title()
    return f"{kind} {number}" + (f" ({caption})" if caption and variant["kind"] not in {"equation", "caption"} else "")


def assign_numbers(chapters, entries):
    """One block counter per shared section; all source variants share it."""
    references = {}
    for chapter in chapters.values():
        for section, topic in enumerate(chapter["topics"], 1):
            relevant = [entry for entry in entries.values() if entry["topic"] == topic]
            ordinal = 0
            for entry in relevant:
                prefix = f'{chapter["number"]}.{section}'
                if entry.get("section_intro"):
                    number = prefix
                else:
                    ordinal += 1
                    number = f'{prefix}.{ordinal}'
                entry["number"] = number
                entry["reader_title"] = numbered_title(entry["variants"][0], number)
                for variant in entry["variants"]:
                    record = {"number": number, "title": numbered_title(variant, number), "section": variant.get("section", False), "intro": entry.get("section_intro", False), "tag": variant["tag"], "canonical_tag": entry["tag"], "math_row": variant.get("math_row", False)}
                    for identifier in (variant["tag"], variant["label"], *variant.get("aliases", [])):
                        references[variant["source"], identifier] = record
                # Clause numbers describe the logical list within a statement.
                # Their parent supplies the collection locator; do not renumber
                # (i), (ii), etc. or alter the mathematical list structure.
                for clause in entry.get("components", []):
                    tag = sha256((clause["source"] + "\0" + clause["label"]).encode()).hexdigest()[:12].upper()
                    references[clause["source"], clause["tag"]] = {"number": clause["number"], "section": False, "tag": clause["tag"], "canonical_tag": tag, "clause": True}
    return references


def renumber_markup(soup, source, references):
    """Replace structured locators only, leaving prose and mathematics intact."""
    for heading in soup.find_all(re.compile(r"^h[1-6]$")):
        marker = heading.find(attrs={"data-tag": True})
        key = marker["data-tag"] if marker else heading.get("id")
        record = references.get((source, key))
        if not record or not record["section"]:
            continue
        heading.name = "h2"  # Imported headings are below the shared section.
        if marker is None:
            marker = soup.new_tag("span")
            marker["data-tag"] = record["tag"]
            heading.insert(0, " ")
            heading.insert(0, marker)
        marker.string = record["number"]
    for marker in soup.select("[data-tag]"):
        record = references.get((source, marker["data-tag"]))
        if record:
            marker.string = record["number"]
            # A manuscript chapter/section now addresses a Gerby subsection.
            if marker.name == "a" and record["section"]:
                preceding = marker.previous_sibling
                if isinstance(preceding, str):
                    name = "section" if record.get("intro") else "subsection"
                    preceding.replace_with(re.sub(r"\b(?:chapter|section|subsection|subsubsection)(\s*)$", lambda m: (name.title() if m[0][0].isupper() else name) + m[1], preceding, flags=re.I))
