"""Combine Gerby exports into shared chapters with reviewed canonical entries."""
from __future__ import annotations

from hashlib import sha256
from functools import cache
from html import escape
import json
import os
from pathlib import Path
import re
import shutil
from urllib.parse import unquote, urlsplit

from bs4 import BeautifulSoup
from unidecode import unidecode


def slugify(title):
    return re.sub(r"[^a-z0-9]+", "-", unidecode(title).lower()).strip("-") or "general"


def global_tag(source, label):
    return sha256((source + "\0" + label).encode()).hexdigest()[:12].upper()


def statement_fingerprint(record):
    # Ignore identifiers and index metadata, never mathematical operators,
    # hypotheses, or notation. Balanced groups matter for nested index terms.
    text = record.get("statement_tex", "")
    text = re.sub(r"\\(?:begin|end)\{thmenv\}", "", text)
    pattern = re.compile(r"\\(?:label(?:\[[^]]*\])?|index)\s*\{")
    while match := pattern.search(text):
        depth, end = 1, match.end()
        while end < len(text) and depth:
            if text[end] in "{}" and (end == 0 or text[end - 1] != "\\"):
                depth += 1 if text[end] == "{" else -1
            end += 1
        if depth:
            raise ValueError("Unbalanced statement metadata")
        text = text[:match.start()] + text[end:]
    return sha256(re.sub(r"\s+", "", text).encode()).hexdigest()


def organize(exports, configuration):
    if configuration.get("version") != 1:
        raise ValueError("Unsupported collection configuration")
    topics = {item["slug"]: dict(item) for item in configuration["topics"]}
    if len(topics) != len(configuration["topics"]):
        raise ValueError("Duplicate shared topic")
    bindings, reserved, reviewed = {}, set(), {}
    for entry in configuration["entries"]:
        if entry["tag"] in reserved or not re.fullmatch(r"[A-Z0-9]{8,12}", entry["tag"]):
            raise ValueError("Duplicate or invalid canonical tag")
        if entry["topic"] not in topics:
            raise ValueError("Canonical entry references an unknown topic")
        reserved.add(entry["tag"])
        for member in entry["members"]:
            key = member["source"], member["label"]
            if key in bindings:
                raise ValueError("A source label belongs to more than one canonical entry")
            bindings[key] = entry
            if "statement_sha256" in member:
                reviewed[key] = member["statement_sha256"]
    entries, source_tags, labels, seen_reviews = {}, {}, {}, set()
    for source, records in exports.items():
        for record in records:
            aliases = [record["label"], *record.get("aliases", [])]
            for label in aliases:
                key = source, label
                if key in labels:
                    raise ValueError(f"Duplicate source label: {source}/{label}")
                labels[key] = record["tag"]
                if key in reviewed:
                    if statement_fingerprint(record) != reviewed[key]:
                        raise ValueError(f"A deduplicated statement changed and needs review: {source}/{label}")
                    seen_reviews.add(key)
            matches = {bindings[(source, label)]["tag"] for label in aliases if (source, label) in bindings}
            if len(matches) > 1:
                raise ValueError("Aliases resolve to conflicting canonical entries")
            configured = next((bindings[(source, label)] for label in aliases if (source, label) in bindings), None)
            canonical = configured["tag"] if configured else global_tag(source, record["label"])
            if not configured and canonical in reserved:
                raise ValueError("A generated tag collides with a reserved canonical tag")
            topic_title = record.get("topic") or "General"
            topic = configured["topic"] if configured else slugify(topic_title)
            topic_title = configuration.get("topic_titles", {}).get(topic, topic_title)
            topics.setdefault(topic, {"slug": topic, "title": topic_title, "description": "Definitions, results, and proofs on this subject."})
            entry = entries.setdefault(canonical, {"tag": canonical, "title": configured["title"] if configured else record.get("semantic_title", record["title"]), "topic": topic, "kind": record["kind"], "variants": [], "components": [], "merge_note": configured.get("merge_note", "") if configured else ""})
            entry["variants"].append({"source": source, **record})
            key = source, record["tag"]
            if key in source_tags:
                raise ValueError("Duplicate source tag")
            source_tags[key] = canonical
    if reviewed.keys() - seen_reviews:
        raise ValueError(f"Reviewed duplicate members disappeared: {sorted(reviewed.keys() - seen_reviews)}")
    for configured in configuration["entries"]:
        if configured["tag"] in entries:
            preferred = configured.get("preferred")
            if preferred:
                entries[configured["tag"]]["variants"].sort(key=lambda v: (v["source"], v["label"]) != (preferred["source"], preferred["label"]))

    # Numbered clauses remain in their full statement, with their own badge and
    # anchor; they need no second search/index entry repeating the same clause.
    for tag, entry in list(entries.items()):
        if len(entry["variants"]) != 1 or entry["kind"] != "item":
            continue
        variant = entry["variants"][0]
        source, parent = variant["source"], variant.get("parent_label")
        local_parent = labels.get((source, parent))
        parent_tag = source_tags.get((source, local_parent))
        if parent_tag is None or parent_tag == tag:
            continue
        parent_entry = entries[parent_tag]
        matching = [v for v in parent_entry["variants"] if v["source"] == source and v["tag"] == local_parent]
        if matching and BeautifulSoup(matching[0]["html"], "html.parser").find(id=variant["tag"]):
            parent_entry["components"].append(variant)
            source_tags[(source, variant["tag"])] = parent_tag
            del entries[tag]

    # An identical equation repeated inside an already unified statement has
    # the same context. Identical formulas elsewhere are deliberately distinct.
    equation_groups = {}
    for tag, entry in list(entries.items()):
        if entry["kind"] != "equation" or len(entry["variants"]) != 1:
            continue
        v = entry["variants"][0]
        local_parent = labels.get((v["source"], v.get("parent_label")))
        parent_tag = source_tags.get((v["source"], local_parent))
        if not parent_tag or len(entries[parent_tag]["variants"]) < 2:
            continue
        key = parent_tag, statement_fingerprint(v)
        if key in equation_groups:
            canonical = equation_groups[key]
            entries[canonical]["variants"].append(v)
            source_tags[(v["source"], v["tag"])] = canonical
            del entries[tag]
        else:
            equation_groups[key] = tag
    used = {entry["topic"] for entry in entries.values()}
    exact = {}
    for entry in entries.values():
        variant = entry["variants"][0]
        if entry["kind"] not in {"definition", "theorem", "lemma", "proposition", "corollary"} or not variant.get("statement_tex"):
            continue
        family = "definition" if entry["kind"] == "definition" else "result"
        key = family, statement_fingerprint(variant)
        if key in exact:
            raise ValueError(f"Review an exact duplicate before publication: {exact[key]} / {variant['source']}/{variant['label']}")
        exact[key] = variant["source"] + "/" + variant["label"]
    topics = {key: value for key, value in topics.items() if key in used}
    return entries, topics, source_tags


def chapter_structure(topics, configuration):
    chapters, assigned = {}, {}
    for number, chapter in enumerate(configuration["chapters"], 1):
        key = chapter["slug"]
        if key in chapters:
            raise ValueError("Duplicate shared chapter")
        chapters[key] = {**chapter, "number": number, "topics": []}
        for topic in chapter["topics"]:
            if topic in assigned:
                raise ValueError(f"A topic belongs to two chapters: {topic}")
            assigned[topic] = key
            if topic in topics:
                chapters[key]["topics"].append(topic)
    missing = topics.keys() - assigned.keys()
    if missing:
        raise ValueError(f"Assign new source subjects to shared chapters: {sorted(missing)}")
    return {key: c for key, c in chapters.items() if c["topics"]}, assigned


def prepare_fragment(variant, source_tags, references, root, component_anchors=None):
    source = variant["source"]
    fragment = variant["html"].replace(r"\begin{bgroup}", "{").replace(r"\end{bgroup}", "}")
    image = r"\\gerbyimage\{([^}]+)\}\{([^}]+)\}"
    def illustration(match):
        return '<img class="source-figure" src="/asset/' + escape(match[1], quote=True) + '" alt="' + escape(match[2], quote=True) + '" loading="lazy">'
    # Gerby serializes math bodies as TeX. A diagram inside display math must
    # become an image outside the math delimiters, retaining its equation tag.
    fragment = re.sub(r"\\\[\s*" + image + r"\s*\\\]", illustration, fragment)
    fragment = re.sub(r"\\begin\{equation\*?\}\s*(?:\\label\{[^}]+\}\s*)?" + image + r"\s*\\end\{equation\*?\}", illustration, fragment)
    if r"\gerbyimage" in fragment:
        raise ValueError(f"A source diagram remains inside a formula: {source}/{variant['label']}")
    def math_reference(match):
        key = source, match[1]
        if key not in source_tags:
            raise ValueError(f"Unresolved mathematical reference: {source}/{match[1]}")
        url = root + "tag/" + source_tags[key] + "/" + (component_anchors or {}).get(key, "")
        return r"\href{" + url + "}{" + match[2] + "}"
    fragment = re.sub(r"\\gerbyref\{([A-F0-9]{8})\}\{([^{}]+)\}", math_reference, fragment)
    if r"\gerbyref" in fragment or "TeXFragment object at" in fragment:
        raise ValueError(f"An invalid mathematical reference remains: {source}/{variant['label']}")
    soup = BeautifulSoup(fragment, "html.parser")
    for paragraph in list(soup.find_all("p")):
        if paragraph.find(["article", "div", "aside", "figure", "h1", "h2", "h3", "ul", "ol", "table"], recursive=False):
            paragraph.unwrap()
    for image in soup.select('[src^="/asset/"]'):
        image["src"] = root + "assets/sources/" + image["src"].removeprefix("/asset/")
    for anchor in soup.select('a[href^="/tag/"]'):
        local = anchor["href"].split("/")[-1]
        if (source, local) not in source_tags:
            raise ValueError(f"Unresolved source tag: {source}/{local}")
        fragment = (component_anchors or {}).get((source, local), "")
        anchor["href"] = root + "tag/" + source_tags[(source, local)] + "/" + fragment
    for anchor in soup.select('a[href^="/bibliography/"]'):
        key = anchor["href"].split("/")[-1]
        anchor["href"] = root + "references/#" + references[(source, key)]
    for marker in soup.select("[data-tag]"):
        local = marker.get("data-tag")
        if not local:
            continue
        heading = marker.find_parent(re.compile(r"^h[1-6]$"))
        if heading:
            heading["data-gerby-tag"] = local
        else:
            anchor = marker.find_parent("a")
            if anchor and ("environment-identifier" in anchor.get("class", []) or marker.find_parent(class_="equation-label")):
                badge = soup.new_tag("span")
                badge["data-gerby-tag"] = local
                anchor.insert_after(badge)
    for element in soup.select("[id]"):
        identifier = element["id"]
        if re.fullmatch(r"[A-F0-9]{8}", identifier) and not soup.find(attrs={"data-gerby-tag": identifier}):
            badge = soup.new_tag("span")
            badge["data-gerby-tag"] = identifier
            element.insert(0, badge)
    first = soup.find(re.compile(r"^h[1-6]$"))
    if variant.get("section") and first:
        first.decompose()
    prefix = source + "-"
    identifiers = {item["id"] for item in soup.select("[id]")}
    for item in soup.select("[id]"):
        item["id"] = prefix + item["id"]
    for anchor in soup.select('a[href^="#"]'):
        identifier = unquote(anchor["href"][1:])
        if identifier in identifiers:
            anchor["href"] = "#" + prefix + identifier
    return str(soup)


@cache
def asset_revision():
    folder = Path(__file__).resolve().parents[1] / "site" / "assets"
    names = ("book.css", "collection.css", "formalization.css", "math-config.js", "formalization.mjs", "collection.mjs")
    return sha256(b"".join((folder / name).read_bytes() for name in names)).hexdigest()[:12]


def shell(content, title, chapters, root=""):
    navigation = "".join(f'<li><a href="{root}chapters/{escape(key)}/"><span>{chapter["number"]}.</span> {escape(chapter["title"])}</a></li>' for key, chapter in chapters.items())
    assets = root + "assets/"
    version = asset_revision()
    return f'''<!doctype html>
<html lang="en" data-search-index="{root}search.json" data-collection-root="{root}">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{escape(title)} · Gerby</title>
<link rel="icon" href="{assets}favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="{assets}book.css?v={version}"><link rel="stylesheet" href="{assets}collection.css?v={version}"><link rel="stylesheet" href="{assets}formalization.css?v={version}">
<script src="{assets}math-config.js?v={version}"></script><script defer src="{assets}mathjax/tex-chtml.js?v={version}"></script><script type="module" src="{assets}formalization.mjs?v={version}"></script><script type="module" src="{assets}collection.mjs?v={version}"></script></head>
<body><a class="skip" href="#content">Skip to content</a><header class="book-header"><a class="brand" href="{root}">g <span>Gerby</span></a><a href="{root}chapters/">Chapters</a><a href="{root}entries/">All entries</a><a href="{root}sources/">Sources</a></header>
<div class="reading-layout"><aside class="sidebar"><p class="book-name">A shared mathematical reference</p><p class="author">Definitions, results, and proofs</p>
<label for="collection-search">Search all content</label><input id="collection-search" type="search" placeholder="A subject, phrase, or tag" autocomplete="off"><div id="search-results" aria-live="polite"></div><nav aria-label="Shared chapters"><ol>{navigation}</ol></nav><p class="draft-note">Shared chapters bring the source texts together. Each statement retains its attribution and proof status.</p></aside>
<main id="content">{content}<footer class="book-footer">Gerby · Mingchen Xia · <a href="{root}sources/">Sources and revisions</a><br>Formalization status is recorded for each source statement at its verified proof revision.</footer></main></div></body></html>'''


def entry_list(entries, topics, root):
    items = []
    for entry in entries:
        items.append(f'<li class="reference-entry"><span class="entry-kind">{escape(entry["kind"])}</span><a href="{root}tag/{entry["tag"]}/">{escape(entry["title"])}</a><code>{entry["tag"]}</code><span class="entry-topic">{escape(topics[entry["topic"]]["title"])}</span></li>')
    return '<ul class="entry-list">' + "".join(items) + '</ul>'


def redirect(path, target, destination, fragments=None, anchor=""):
    path.parent.mkdir(parents=True, exist_ok=True)
    relative = Path(os.path.relpath(target, path.parent)).as_posix()
    if target.name == "index.html":
        relative = relative.removesuffix("index.html") or "./"
    relative += anchor
    assets = Path(os.path.relpath(destination / "assets", path.parent)).as_posix() + "/"
    path.write_text(f'''<!doctype html><html lang="en" data-redirect="{escape(relative, quote=True)}" data-fragments='{escape(json.dumps(fragments or {}), quote=True)}'><head><meta charset="utf-8"><title>Continue to Gerby</title><link rel="canonical" href="{escape(relative, quote=True)}"><script defer src="{assets}redirect.js"></script></head><body><p>This content is part of the shared Gerby reference. <a href="{escape(relative, quote=True)}">Continue to the shared entry</a>.</p></body></html>''')


def build_collection(books, destination, configuration):
    sources = {book["slug"]: book for book in books if book["status"] == "published"}
    exports, editions, reference_exports, inventories = {}, {}, {}, {}
    for source in sources:
        folder = destination / "books" / source
        exports[source] = json.loads((folder / "entries.json").read_text())
        editions[source] = json.loads((folder / "edition.json").read_text())
        reference_exports[source] = json.loads((folder / "references.json").read_text())
        inventories[source] = json.loads((folder / "tags.json").read_text())
        if (folder / "assets").is_dir():
            shutil.copytree(folder / "assets", destination / "assets" / "sources" / source, dirs_exist_ok=True)
    entries, topics, source_tags = organize(exports, configuration)
    chapters, topic_chapters = chapter_structure(topics, configuration)
    anchors = {(v["source"], v["tag"]): "#" + v["source"] + "-" + v["tag"] for entry in entries.values() for v in entry["components"]}
    references, reference_map = {}, {}
    for source, records in reference_exports.items():
        for record in records:
            identifier = "R" + sha256(record["identity"].encode()).hexdigest()[:12].upper()
            references.setdefault(identifier, {**record, "sources": []})["sources"].append({"source": source, "key": record["key"]})
            reference_map[(source, record["key"])] = identifier

    def write(route, content, title, root):
        page = destination / route / "index.html" if route else destination / "index.html"
        page.parent.mkdir(parents=True, exist_ok=True)
        page.write_text(shell(content, title, chapters, root))

    def chapter_cards(root):
        cards = []
        for key, chapter in chapters.items():
            relevant = [e for e in entries.values() if e["topic"] in chapter["topics"]]
            origins = {v["source"] for e in relevant for v in e["variants"]}
            cards.append(f'<a class="topic-card" href="{root}chapters/{key}/"><span class="eyebrow">Chapter {chapter["number"]}</span><h2>{escape(chapter["title"])}</h2><p class="chapter-description">{escape(chapter["description"])}</p><p>{len(relevant)} entries · {len(origins)} source{"s" if len(origins) != 1 else ""}</p></a>')
        return '<div class="topic-grid">' + "".join(cards) + '</div>'

    introduction = f'<section class="collection-intro"><p class="eyebrow">A shared mathematical reference</p><h1>One collection.<br><em>Connected mathematics.</em></h1><p>Definitions, results, and proofs from contributing texts, organized into shared chapters by mathematical subject.</p><p class="collection-count">{len(entries):,} entries · {len(chapters)} chapters · {len(sources)} sources</p></section>'
    write("", introduction + '<h2>Explore the chapters</h2>' + chapter_cards(""), "Gerby", "")
    write("chapters", '<h1>Chapters</h1><p>The chapter order follows the mathematics across the contributing texts. Original numbering remains in the source attributions.</p>' + chapter_cards("../"), "Chapters", "../")
    for key, chapter in chapters.items():
        content = f'<p class="eyebrow">Chapter {chapter["number"]}</p><h1>{escape(chapter["title"])}</h1><p>{escape(chapter["description"])}</p>'
        for topic in chapter["topics"]:
            relevant = [entry for entry in entries.values() if entry["topic"] == topic]
            origins = sorted({sources[v["source"]]["title"] for e in relevant for v in e["variants"]})
            content += f'<section class="chapter-section" id="{topic}"><h2>{escape(topics[topic]["title"])}</h2><p class="chapter-sources">Contributions from {escape("; ".join(origins))}.</p>' + entry_list(relevant, topics, "../../") + '</section>'
        write("chapters/" + key, content, chapter["title"], "../../")
    write("topics", '<h1>Subjects</h1><p>Subjects are arranged within the shared chapters.</p>' + chapter_cards("../"), "Subjects", "../")
    for key, topic in topics.items():
        redirect(destination / "topics" / key / "index.html", destination / "chapters" / topic_chapters[key] / "index.html", destination, anchor="#" + key)
    write("entries", '<h1>All entries</h1><p>Search across every source, or follow the shared chapter order below.</p>' + "".join(f'<h2><a href="../chapters/{key}/">{chapter["number"]}. {escape(chapter["title"])}</a></h2>' + entry_list([e for e in entries.values() if e["topic"] in chapter["topics"]], topics, "../") for key, chapter in chapters.items()), "All entries", "../")
    search, public_entries, merges = [], [], []
    for entry in entries.values():
        tag, root = entry["tag"], "../../"
        chapter_key = topic_chapters[entry["topic"]]
        chapter = chapters[chapter_key]
        content = f'<p class="eyebrow"><a href="{root}chapters/{chapter_key}/">Chapter {chapter["number"]} · {escape(chapter["title"])}</a> · Tag <code>{tag}</code></p><h1>{escape(entry["title"])}</h1>'
        if len(entry["variants"]) > 1:
            note = entry["merge_note"] or "Repeated statement: one entry retains the original source versions and proofs."
            content += f'<p class="merge-note">{escape(note)}</p>'
        variants, texts = [], []
        for number, variant in enumerate(entry["variants"]):
            source, local = variant["source"], variant["tag"]
            meta = sources[source]
            provenance = f'<div class="source-attribution">From <a href="{root}sources/{source}/">{escape(meta["title"])}</a> · {escape(variant["title"])} <span data-gerby-tag="{local}"></span></div>'
            body = prepare_fragment(variant, source_tags, reference_map, root, anchors)
            if number:
                body = '<details class="source-alternative"><summary>Read this source version and its proof notes</summary>' + body + '</details>'
            content += f'<section class="source-variant" data-gerby-book="{source}">{provenance}{body}</section>'
            texts.append(BeautifulSoup(variant["html"], "html.parser").get_text(" ", strip=True))
            variants.append({"book": source, "tag": local, "label": variant["label"], "revision": editions[source]["commit"]})
        write("tag/" + tag, content, entry["title"], root)
        component_aliases = [value for v in entry["components"] for value in (v["tag"], v["label"])]
        search.append({"tag": tag, "title": entry["title"], "kind": entry["kind"], "topic": chapter["title"], "text": " ".join(texts), "aliases": [v["tag"] for v in variants] + [v["label"] for v in variants] + component_aliases})
        public_entries.append({"tag": tag, "title": entry["title"], "kind": entry["kind"], "chapter": chapter_key, "topic": entry["topic"], "sources": variants, "components": [{"book": v["source"], "tag": v["tag"], "label": v["label"]} for v in entry["components"]]})
        if len(variants) > 1:
            merges.append({"tag": tag, "title": entry["title"], "note": entry["merge_note"], "sources": variants})
        for variant in entry["variants"] + entry["components"]:
            old = global_tag(variant["source"], variant["label"])
            if old != tag:
                redirect(destination / "tag" / old / "index.html", destination / "tag" / tag / "index.html", destination, anchor=anchors.get((variant["source"], variant["tag"]), ""))
    source_list = '<h1>Sources</h1><p>Contributions share one chapter structure. Attribution and exact revisions remain available for every entry. These are working mathematical texts; inclusion does not certify a proof or a formalization.</p><ul class="entry-list">'
    for source, book in sources.items():
        source_list += f'<li><a href="{source}/">{escape(book["title"])}</a> · {escape(book.get("author", ""))}</li>'
        relevant = [entry for entry in entries.values() if any(v["source"] == source for v in entry["variants"])]
        source_content = f'<p class="eyebrow">Source attribution</p><h1>{escape(book["title"])}</h1><p>{escape(book.get("author", ""))}</p><p>These contributions appear throughout the shared chapters.</p>'
        if book.get("visibility") == "private":
            source_content += '<p class="source-notice">This reading edition is published by permission. The source repository remains private; its revision links require access. Research files and source archives are not included.</p>'
        source_content += f'<p><a href="{escape(book["repository"])}/commit/{editions[source]["commit"]}">Source revision {editions[source]["commit"][:12]} ↗</a></p>'
        write("sources/" + source, source_content + entry_list(relevant, topics, "../../"), book["title"], "../../")
        source_folder = destination / "sources" / source
        (source_folder / "tags.json").write_text(json.dumps([{**record, "canonical_tag": source_tags[(source, record["tag"])], "anchor": anchors.get((source, record["tag"]), "")} for record in inventories[source]], indent=2) + "\n")
        (source_folder / "edition.json").write_text(json.dumps(editions[source], indent=2) + "\n")
        old_folder = destination / "books" / source
        shutil.rmtree(old_folder)
        redirect(old_folder / "index.html", source_folder / "index.html", destination)
        for record in inventories[source]:
            canonical = source_tags[(source, record["tag"])]
            redirect(old_folder / record["page"], destination / "tag" / canonical / "index.html", destination, anchor=anchors.get((source, record["tag"]), ""))
        for configured in configuration["entries"]:
            if configured["tag"] in entries and any(m["source"] == source for m in configured["members"]):
                redirect(old_folder / "tag" / configured["tag"] / "index.html", destination / "tag" / configured["tag"] / "index.html", destination)
        redirect(old_folder / "bibliography" / "index.html", destination / "references" / "index.html", destination, {key: identifier for (origin, key), identifier in reference_map.items() if origin == source})
    write("sources", source_list + '</ul><p><a href="../deduplication.json">Reviewed duplicate groups and retained source tags</a></p>', "Sources", "../")
    reference_content = '<h1>References</h1><p>Bibliographic references cited across the shared collection.</p>'
    for identifier, record in sorted(references.items()):
        reference_content += f'<div class="bibliography-entry" id="{identifier}">{record["html"]}</div>'
    write("references", reference_content, "References", "../")
    (destination / "search.json").write_text(json.dumps(search, ensure_ascii=False) + "\n")
    (destination / "collection.json").write_text(json.dumps({"version": 1, "chapters": list(chapters.values()), "topics": list(topics.values()), "entries": public_entries}, ensure_ascii=False, indent=2) + "\n")
    audit = {"groups": merges, "duplicate_entries_unified": sum(len(e["variants"]) - 1 for e in entries.values()), "numbered_clauses_in_parent_statements": len(anchors), "source_tags": sum(len(records) for records in inventories.values()), "canonical_entries": len(entries)}
    (destination / "deduplication.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    return {"entries": len(entries), "topics": len(topics), "chapters": len(chapters), "sources": len(sources)}


def check_links(destination):
    pages = {path.resolve(): BeautifulSoup(path.read_text(), "html.parser") for path in destination.rglob("*.html")}
    identifiers = {path: {item["id"] for item in soup.select("[id]")} for path, soup in pages.items()}
    for page, soup in pages.items():
        for element in soup.select("[href], script[src], img[src]"):
            value = element.get("href", element.get("src", ""))
            parsed = urlsplit(value)
            if parsed.scheme or parsed.netloc:
                continue
            target = (page.parent / unquote(parsed.path)).resolve() if parsed.path else page
            if target.is_dir():
                target = target / "index.html"
            if not target.is_relative_to(destination.resolve()) or not target.is_file():
                raise ValueError(f"Broken internal link on {page}: {value}")
            if parsed.fragment and target in identifiers and unquote(parsed.fragment) not in identifiers[target]:
                raise ValueError(f"Broken fragment on {page}: {value}")
