"""Combine source exports into a shared reference with global topics and tags."""
from __future__ import annotations

from hashlib import sha256
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


def organize(exports, configuration):
    if configuration.get("version") != 1:
        raise ValueError("Unsupported collection configuration")
    topics = {item["slug"]: dict(item) for item in configuration["topics"]}
    if len(topics) != len(configuration["topics"]):
        raise ValueError("Duplicate shared topic")
    bindings, reserved = {}, set()
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
    entries, source_tags = {}, {}
    for source, records in exports.items():
        for record in records:
            labels = [record["label"], *record.get("aliases", [])]
            matches = {bindings[(source, label)]["tag"] for label in labels if (source, label) in bindings}
            if len(matches) > 1:
                raise ValueError("Aliases resolve to conflicting canonical entries")
            configured = next((bindings[(source, label)] for label in labels if (source, label) in bindings), None)
            canonical = configured["tag"] if configured else global_tag(source, record["label"])
            if not configured and canonical in reserved:
                raise ValueError("A generated tag collides with a reserved canonical tag")
            topic_title = record.get("topic") or "General"
            topic = configured["topic"] if configured else slugify(topic_title)
            topics.setdefault(topic, {"slug": topic, "title": topic_title, "description": "Definitions, results, and proofs on this subject."})
            entry = entries.setdefault(canonical, {"tag": canonical, "title": configured["title"] if configured else record.get("semantic_title", record["title"]), "topic": topic, "kind": record["kind"], "variants": []})
            entry["variants"].append({"source": source, **record})
            key = source, record["tag"]
            if key in source_tags:
                raise ValueError("Duplicate source tag")
            source_tags[key] = canonical
    used = {entry["topic"] for entry in entries.values()}
    topics = {key: value for key, value in topics.items() if key in used}
    return entries, topics, source_tags


def prepare_fragment(variant, source_tags, references, root):
    source = variant["source"]
    soup = BeautifulSoup(variant["html"], "html.parser")
    for paragraph in list(soup.find_all("p")):
        if paragraph.find(["article", "div", "h1", "h2", "h3", "ul", "ol"], recursive=False):
            paragraph.unwrap()
    for anchor in soup.select('a[href^="/tag/"]'):
        local = anchor["href"].split("/")[-1]
        if (source, local) not in source_tags:
            raise ValueError(f"Unresolved source tag: {source}/{local}")
        anchor["href"] = root + "tag/" + source_tags[(source, local)] + "/"
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
    # The canonical title provides the heading; source numbering is retained
    # in attribution and in mathematical cross-references inside the excerpt.
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


def shell(content, title, topics, root=""):
    navigation = "".join(f'<li><a href="{root}topics/{escape(key)}/">{escape(topic["title"])}</a></li>' for key, topic in sorted(topics.items(), key=lambda pair: pair[1]["title"].casefold()))
    assets = root + "assets/"
    return f'''<!doctype html>
<html lang="en" data-search-index="{root}search.json" data-collection-root="{root}">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{escape(title)} · Gerby</title>
<link rel="icon" href="{assets}favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="{assets}book.css"><link rel="stylesheet" href="{assets}collection.css"><link rel="stylesheet" href="{assets}formalization.css">
<script src="{assets}math-config.js"></script><script defer src="{assets}mathjax/tex-chtml.js"></script><script type="module" src="{assets}formalization.mjs"></script><script type="module" src="{assets}collection.mjs"></script></head>
<body><a class="skip" href="#content">Skip to content</a><header class="book-header"><a class="brand" href="{root}">g <span>Gerby</span></a><a href="{root}topics/">Topics</a><a href="{root}entries/">All entries</a><a href="{root}sources/">Sources</a></header>
<div class="reading-layout"><aside class="sidebar"><p class="book-name">A shared mathematical reference</p><p class="author">Definitions, results, and proofs</p>
<label for="collection-search">Search all content</label><input id="collection-search" type="search" placeholder="A topic, phrase, or tag" autocomplete="off"><div id="search-results" aria-live="polite"></div><nav aria-label="Shared topics"><ul>{navigation}</ul></nav><p class="draft-note">Content is combined by topic. Every excerpt retains its source and proof status.</p></aside>
<main id="content">{content}<footer class="book-footer">Gerby · Mingchen Xia · <a href="{root}sources/">Sources and revisions</a><br>Formalization status is recorded for each source statement at its verified proof revision.</footer></main></div></body></html>'''


def entry_list(entries, topics, root):
    items = []
    for entry in sorted(entries, key=lambda item: item["title"].casefold()):
        items.append(f'<li class="reference-entry"><span class="entry-kind">{escape(entry["kind"])}</span><a href="{root}tag/{entry["tag"]}/">{escape(entry["title"])}</a><code>{entry["tag"]}</code><span class="entry-topic">{escape(topics[entry["topic"]]["title"])}</span></li>')
    return '<ul class="entry-list">' + "".join(items) + '</ul>'


def redirect(path, target, destination, fragments=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    relative = Path(os.path.relpath(target, path.parent)).as_posix()
    if target.name == "index.html":
        relative = relative.removesuffix("index.html") or "./"
    assets = Path(os.path.relpath(destination / "assets", path.parent)).as_posix() + "/"
    path.write_text(f'''<!doctype html><html lang="en" data-redirect="{escape(relative, quote=True)}" data-fragments='{escape(json.dumps(fragments or {}), quote=True)}'><head><meta charset="utf-8"><title>Continue to Gerby</title><link rel="canonical" href="{escape(relative, quote=True)}"><script defer src="{assets}redirect.js"></script></head><body><p>This content is part of the shared Gerby reference. <a href="{escape(relative, quote=True)}">Continue to the shared entry</a>.</p></body></html>''')


def build_collection(books, destination, configuration):
    published = [book for book in books if book["status"] == "published"]
    sources = {book["slug"]: book for book in published}
    exports, editions, reference_exports, inventories = {}, {}, {}, {}
    for source in sources:
        folder = destination / "books" / source
        exports[source] = json.loads((folder / "entries.json").read_text())
        editions[source] = json.loads((folder / "edition.json").read_text())
        reference_exports[source] = json.loads((folder / "references.json").read_text())
        inventories[source] = json.loads((folder / "tags.json").read_text())
    entries, topics, source_tags = organize(exports, configuration)
    references, reference_map = {}, {}
    for source, records in reference_exports.items():
        for record in records:
            identifier = "R" + sha256(record["identity"].encode()).hexdigest()[:12].upper()
            references.setdefault(identifier, {**record, "sources": []})["sources"].append({"source": source, "key": record["key"]})
            reference_map[(source, record["key"])] = identifier
    def write(route, content, title, root):
        page = destination / route / "index.html" if route else destination / "index.html"
        page.parent.mkdir(parents=True, exist_ok=True)
        page.write_text(shell(content, title, topics, root))
    topic_cards = '<div class="topic-grid">' + "".join(f'<a class="topic-card" href="./topics/{key}/"><h2>{escape(topic["title"])}</h2><p>{sum(e["topic"] == key for e in entries.values())} entries</p></a>' for key, topic in sorted(topics.items(), key=lambda pair: pair[1]["title"].casefold())) + '</div>'
    introduction = f'<section class="collection-intro"><p class="eyebrow">A shared mathematical reference</p><h1>One collection.<br><em>Connected mathematics.</em></h1><p>Definitions, results, and proofs from contributing texts, brought together by topic.</p><p class="collection-count">{len(entries)} entries · {len(topics)} topics · {len(sources)} source{"s" if len(sources) != 1 else ""}</p></section>'
    write("", introduction + '<h2>Explore by topic</h2>' + topic_cards, "Gerby", "")
    write("topics", '<h1>Topics</h1>' + topic_cards.replace('href="./topics/', 'href="../topics/'), "Topics", "../")
    for key, topic in topics.items():
        relevant = [entry for entry in entries.values() if entry["topic"] == key]
        write("topics/" + key, f'<p class="eyebrow">Shared topic</p><h1>{escape(topic["title"])}</h1><p>{escape(topic["description"])}</p>' + entry_list(relevant, topics, "../../"), topic["title"], "../../")
    write("entries", '<h1>All entries</h1><p>Browse the shared collection, or search across every source using the search field.</p>' + entry_list(entries.values(), topics, "../"), "All entries", "../")
    search, public_entries = [], []
    for entry in entries.values():
        tag = entry["tag"]
        root = "../../"
        content = f'<p class="eyebrow"><a href="{root}topics/{entry["topic"]}/">{escape(topics[entry["topic"]]["title"])}</a> · Tag <code>{tag}</code></p><h1>{escape(entry["title"])}</h1>'
        variants = []
        texts = []
        for variant in entry["variants"]:
            source, local = variant["source"], variant["tag"]
            meta = sources[source]
            provenance = f'<div class="source-attribution">From <a href="{root}sources/{source}/">{escape(meta["title"])}</a> · {escape(variant["title"])} <span data-gerby-tag="{local}"></span></div>'
            content += f'<section class="source-variant" data-gerby-book="{source}">{provenance}{prepare_fragment(variant, source_tags, reference_map, root)}</section>'
            texts.append(BeautifulSoup(variant["html"], "html.parser").get_text(" ", strip=True))
            variants.append({"book": source, "tag": local, "label": variant["label"], "revision": editions[source]["commit"]})
        write("tag/" + tag, content, entry["title"], root)
        search.append({"tag": tag, "title": entry["title"], "kind": entry["kind"], "topic": topics[entry["topic"]]["title"], "text": " ".join(texts), "aliases": [v["tag"] for v in variants] + [v["label"] for v in variants]})
        public_entries.append({"tag": tag, "title": entry["title"], "kind": entry["kind"], "topic": entry["topic"], "sources": variants})
    source_list = '<h1>Sources</h1><p>Source texts contribute to the same topic collection. Attribution and exact revisions remain available for every entry.</p><ul class="entry-list">'
    for source, book in sources.items():
        source_list += f'<li><a href="{source}/">{escape(book["title"])}</a> · {escape(book.get("author", ""))}</li>'
        relevant = [entry for entry in entries.values() if any(v["source"] == source for v in entry["variants"])]
        source_content = f'<p class="eyebrow">Source attribution</p><h1>{escape(book["title"])}</h1><p>{escape(book.get("author", ""))}</p><p>These contributions are integrated into the shared topic collection.</p><p><a href="{escape(book["repository"])}/commit/{editions[source]["commit"]}">Source revision {editions[source]["commit"][:12]} ↗</a></p>'
        write("sources/" + source, source_content + entry_list(relevant, topics, "../../"), book["title"], "../../")
        source_folder = destination / "sources" / source
        (source_folder / "tags.json").write_text(json.dumps([{**record, "canonical_tag": source_tags[(source, record["tag"])]} for record in inventories[source]], indent=2) + "\n")
        (source_folder / "edition.json").write_text(json.dumps(editions[source], indent=2) + "\n")
        old_folder = destination / "books" / source
        shutil.rmtree(old_folder)
        redirect(old_folder / "index.html", source_folder / "index.html", destination)
        for record in inventories[source]:
            canonical = source_tags[(source, record["tag"])]
            redirect(old_folder / record["page"], destination / "tag" / canonical / "index.html", destination)
        # Keep the initially published local tags alive when source aliases change.
        for configured in configuration["entries"]:
            if configured["tag"] in entries and any(m["source"] == source for m in configured["members"]):
                redirect(old_folder / "tag" / configured["tag"] / "index.html", destination / "tag" / configured["tag"] / "index.html", destination)
        redirect(old_folder / "bibliography" / "index.html", destination / "references" / "index.html", destination, {key: identifier for (origin, key), identifier in reference_map.items() if origin == source})
    write("sources", source_list + '</ul>', "Sources", "../")
    reference_content = '<h1>References</h1><p>Bibliographic references cited across the shared collection.</p>'
    for identifier, record in sorted(references.items()):
        reference_content += f'<div class="bibliography-entry" id="{identifier}">{record["html"]}</div>'
    write("references", reference_content, "References", "../")
    (destination / "search.json").write_text(json.dumps(search, ensure_ascii=False) + "\n")
    (destination / "collection.json").write_text(json.dumps({"version": 1, "topics": list(topics.values()), "entries": public_entries}, ensure_ascii=False, indent=2) + "\n")
    return {"entries": len(entries), "topics": len(topics), "sources": len(sources)}


def check_links(destination):
    pages = {path.resolve(): BeautifulSoup(path.read_text(), "html.parser") for path in destination.rglob("*.html")}
    identifiers = {path: {item["id"] for item in soup.select("[id]")} for path, soup in pages.items()}
    for page, soup in pages.items():
        for element in soup.select("[href], script[src]"):
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
