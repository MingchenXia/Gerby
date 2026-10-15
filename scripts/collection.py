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
from reader import Reader, display_title, tag_code
from numbering import renumber_markup
from structure import arrange_sections
from proof_expansions import apply_expansions, check_dependencies


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
            topics.setdefault(topic, {"slug": topic, "title": topic_title, "description": ""})
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
    excluded = set(configuration.get("excluded_topics", []))
    entries = {tag: entry for tag, entry in entries.items() if entry["topic"] not in excluded}
    # Keep excluded source tags distinguishable from unresolved references.
    source_tags = {key: tag if tag in entries else None for key, tag in source_tags.items()}
    used = {entry["topic"] for entry in entries.values()}
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
            if topic in configuration.get("excluded_topics", []):
                raise ValueError(f"An excluded topic belongs to a chapter: {topic}")
            if topic in assigned:
                raise ValueError(f"A topic belongs to two chapters: {topic}")
            assigned[topic] = key
            if topic in topics:
                chapters[key]["topics"].append(topic)
    missing = topics.keys() - assigned.keys()
    if missing:
        raise ValueError(f"Assign new source subjects to shared chapters: {sorted(missing)}")
    return {key: c for key, c in chapters.items() if c["topics"]}, assigned


def prepare_fragment(variant, source_tags, references, root, component_anchors=None, numbering=None):
    source = variant["source"]
    fragment = variant["html"].replace(r"\begin{bgroup}", "{").replace(r"\end{bgroup}", "}")
    def math_label(match):
        target = (numbering or {}).get((source, match[1]), {})
        # Align rows need a tag inside their parent's TeX; standalone pages
        # already have an HTML equation label.
        if target.get("math_row") and not (variant.get("math_row") and target.get("tag") == variant["tag"]):
            return r"\tag{" + target["number"] + "}"
        return ""
    fragment = re.sub(r"\\label(?:\[[^]]*\])?\s*\{([^{}]*)\}", math_label, fragment)
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
        if source_tags[key] is None:
            return match[2]
        url = root + "tag/" + source_tags[key] + "/" + (component_anchors or {}).get(key, "")
        number = (numbering or {}).get(key, {}).get("number", match[2])
        return r"\href{" + url + "}{" + number + "}"
    fragment = re.sub(r"\\gerbyref\{([A-F0-9]{8})\}\{([^{}]+)\}", math_reference, fragment)
    if r"\gerbyref" in fragment or "TeXFragment object at" in fragment:
        raise ValueError(f"An invalid mathematical reference remains: {source}/{variant['label']}")
    soup = BeautifulSoup(fragment, "html.parser")
    if numbering is not None:
        renumber_markup(soup, source, numbering)
    for anchor in soup.select("a[data-proof-entry]"):
        anchor["href"] = root + "tag/" + anchor["data-proof-entry"] + "/"
    for paragraph in list(soup.find_all("p")):
        if paragraph.find(["article", "div", "aside", "figure", "h1", "h2", "h3", "ul", "ol", "table"], recursive=False):
            paragraph.unwrap()
    for image in soup.select('[src^="/asset/"]'):
        image["src"] = root + "assets/sources/" + image["src"].removeprefix("/asset/")
    for anchor in soup.select('a[href^="/tag/"]'):
        local = anchor["href"].split("/")[-1]
        if (source, local) not in source_tags:
            raise ValueError(f"Unresolved source tag: {source}/{local}")
        if source_tags[(source, local)] is None:
            anchor.unwrap()
            continue
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
    for equation in soup.select(".equation"):
        if equation.find(class_="equation-label", recursive=False):
            equation["class"] = [*equation.get("class", []), "numbered-equation"]
    if variant.get("section") and first:
        first.decompose()
    for marker in soup.select("[data-gerby-tag]"):
        canonical = (numbering or {}).get((source, marker["data-gerby-tag"]), {}).get("canonical_tag")
        if canonical:
            code = soup.new_tag("code", attrs={"class": "tag-id"})
            code.string = canonical
            marker.append(code)
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
    names = ("book.css", "collection.css", "formalization.css", "math-config.js", "formalization.mjs", "collection.mjs", "favicon.svg", "comments.mjs", "search.mjs")
    return sha256(b"".join((folder / name).read_bytes() for name in names)).hexdigest()[:12]


def entry_list(entries, topics, root):
    items = []
    for entry in entries:
        if entry.get("section_intro"):
            continue
        items.append(f'<li class="reference-entry"><span class="entry-kind">{escape(entry["kind"])}</span><a href="{root}tag/{entry["tag"]}/">{escape(display_title(entry))}</a><code class="tag-id">{entry["tag"]}</code><span class="entry-topic">{escape(topics[entry["topic"]]["title"])}</span></li>')
    return '<ul class="entry-list">' + "".join(items) + '</ul>'


def source_roots(entries):
    """Locate exported entries inside the larger source sections containing them."""
    roots = {}
    for entry in entries.values():
        for variant in entry["variants"]:
            soup = BeautifulSoup(variant["html"], "html.parser")
            node = next((found for identifier in (variant["tag"], variant["label"], *variant.get("aliases", [])) if (found := soup.find(id=identifier))), None)
            if node:
                key = variant["source"], node["id"]
                if key in roots and roots[key]["tag"] != entry["tag"]:
                    raise ValueError(f"Two entries share a source root: {key}: {roots[key]['tag']} / {entry['tag']}")
                roots[key] = {"tag": entry["tag"], "preferred": variant is entry["variants"][0]}
    return roots


def continuous_section(relevant, entries, roots, sources, source_tags, references, root, anchors, numbering=None):
    """Read full source fragments once, retaining prose between statements."""
    covered, chunks = set(), []
    topic = relevant[0]["topic"]
    rooted = {origin["tag"] for origin in roots.values() if origin["preferred"]}
    rootless = [(entry["tag"], entry["variants"][0]["source"], str(BeautifulSoup(entry["variants"][0]["html"], "html.parser"))) for entry in relevant if entry["tag"] not in rooted]
    for entry in relevant:
        if entry["tag"] in covered:
            continue
        variant = entry["variants"][0]
        source = variant["source"]
        soup = BeautifulSoup(variant["html"], "html.parser")
        for node in list(soup.find_all(id=True)):
            if not node.parent:
                continue
            origin = roots.get((source, node["id"]))
            if not origin:
                continue
            canonical = origin["tag"]
            target = entries[canonical]
            if canonical not in covered and target["topic"] == topic and origin["preferred"]:
                continue
            # A parent section may contain an entry whose preferred version is
            # elsewhere. Keep a reference here instead of repeating its proof.
            replacement = soup.new_tag("p")
            replacement["class"] = "shared-entry-reference"
            link = soup.new_tag("a", href=root + "tag/" + canonical + "/")
            link.string = display_title(target)
            replacement.append("See ")
            replacement.append(link)
            replacement.append(".")
            if re.fullmatch(r"h[1-6]", node.name):
                level = int(node.name[1])
                for sibling in list(node.next_siblings):
                    if getattr(sibling, "name", None) and re.fullmatch(r"h[1-6]", sibling.name) and int(sibling.name[1]) <= level:
                        break
                    sibling.extract()
            elif node.name == "article":
                following = node.find_next_sibling()
                if following and "env-proof" in following.get("class", []):
                    following.decompose()
            node.replace_with(replacement)
        represented = {roots[(source, node["id"])]["tag"] for node in soup.find_all(id=True) if (source, node["id"]) in roots}
        retained = str(soup)
        represented.update(tag for tag, origin, fragment in rootless if origin == source and fragment in retained)
        represented.add(entry["tag"])
        if represented & covered:
            raise ValueError(f"A section repeats entries: {sorted(represented & covered)}")
        covered.update(represented)
        body = prepare_fragment({**variant, "html": retained}, source_tags, references, root, anchors, numbering)
        heading = f'<h2><a href="{root}tag/{entry["tag"]}/">{escape(display_title(entry))}</a>{tag_code(entry["tag"])}</h2>' if variant.get("section") and not entry.get("section_intro") else ""
        badge = f'<span data-gerby-tag="{variant["tag"]}"></span>'
        chunks.append(f'<section class="reading-chunk" id="entry-{entry["tag"]}" data-section-entries="{" ".join(sorted(represented))}"><div class="source-variant" data-gerby-book="{source}">{heading}{badge}{body}</div></section>')
    expected = {entry["tag"] for entry in relevant}
    if covered != expected:
        raise ValueError(f"Section reading coverage differs: missing {sorted(expected - covered)}, extra {sorted(covered - expected)}")
    return '<div class="section-reading">' + "".join(chunks) + '</div>'


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
    dependencies = {}
    if configuration.get("proof_expansions"):
        registry = Path(__file__).resolve().parents[1] / configuration["proof_expansions"]
        exports, dependencies = apply_expansions(exports, registry, statement_fingerprint)
    entries, topics, source_tags = organize(exports, configuration)
    check_dependencies(entries, dependencies)
    configuration = arrange_sections(entries, topics, configuration)
    chapters, topic_chapters = chapter_structure(topics, configuration)
    comments = json.loads((Path(__file__).resolve().parents[1] / "comments.json").read_text())
    reader = Reader(chapters, topics, entries, sources, comments)
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
        page.write_text(reader.shell(content, route, root, asset_revision()))

    introduction = f'<section class="collection-intro"><h1>Gerby</h1><p>A mathematical reference combining definitions, results, and proofs from contributing texts.</p><p class="collection-count">{len(entries):,} entries · {len(chapters)} chapters · {len(topics)} sections · {len(sources)} sources</p></section>'
    write("", introduction + '<nav class="home-links" aria-label="Explore Gerby"><a href="chapters/">Table of contents</a><a href="search/">Search</a><a href="references/">Bibliography</a><a href="comments/">Comments</a><a href="sources/">Sources</a><a href="https://github.com/MingchenXia/Gerby">GitHub</a></nav><h2>Table of contents</h2>' + reader.contents(""), "Gerby", "")
    write("chapters", '<h1>Table of contents</h1>' + reader.contents("../"), "Table of contents", "../")
    for key, chapter in chapters.items():
        content = f'<p class="eyebrow">Chapter {chapter["number"]}</p><h1>{escape(chapter["title"])}{tag_code(chapter["tag"])}</h1><p>{escape(chapter.get("description", ""))}</p>'
        content += '<h2>Sections and subsections</h2>' + reader.section_list(key, "../../", anchors=True, subsections=True)
        write("chapters/" + key, content, chapter["title"], "../../")
        if chapter["tag"] in entries:
            raise ValueError("A chapter tag collides with an entry")
        redirect(destination / "tag" / chapter["tag"] / "index.html", destination / "chapters" / key / "index.html", destination)
    roots = source_roots(entries)
    for topic, section in reader.sections.items():
        content = f'<h1>{section["number"]} {escape(section["title"])}{tag_code(section["tag"])}</h1>'
        description = topics[topic].get("description", "")
        if description and description != "Definitions, results, and proofs on this subject.":
            content += f'<p>{escape(description)}</p>'
        content += continuous_section(section["entries"], entries, roots, sources, source_tags, reference_map, "../../", anchors, reader.numbering)
        write("sections/" + topic, content, section["title"], "../../")
        if section["tag"] not in entries:
            redirect(destination / "tag" / section["tag"] / "index.html", destination / "sections" / topic / "index.html", destination)
    redirect(destination / "topics" / "index.html", destination / "chapters" / "index.html", destination)
    for key, topic in topics.items():
        redirect(destination / "topics" / key / "index.html", destination / "sections" / key / "index.html", destination)
    # Removed front matter leaves the reading edition, while old permalinks
    # continue to reach the collection rather than a missing page.
    contents = destination / "chapters" / "index.html"
    for topic in configuration.get("excluded_topics", []):
        for route in ("topics", "sections"):
            redirect(destination / route / topic / "index.html", contents, destination)
    for source, records in exports.items():
        for record in records:
            if source_tags[(source, record["tag"])] is None:
                redirect(destination / "tag" / global_tag(source, record["label"]) / "index.html", contents, destination)
    for configured in configuration["entries"]:
        if configured["topic"] in configuration.get("excluded_topics", []):
            redirect(destination / "tag" / configured["tag"] / "index.html", contents, destination)
    write("entries", '<h1>All entries</h1><p>Search across every source, or follow the shared chapter order below.</p>' + "".join(f'<h2><a href="../chapters/{key}/">{chapter["number"]}. {escape(chapter["title"])}</a></h2>' + entry_list([e for e in entries.values() if e["topic"] in chapter["topics"]], topics, "../") for key, chapter in chapters.items()), "All entries", "../")
    search = [{"tag": chapter["tag"], "title": f'{chapter["number"]} {chapter["title"]}', "search_title": chapter["title"], "kind": "chapter", "topic": chapter["title"], "text": "", "aliases": []} for chapter in chapters.values()]
    search += [{"tag": section["tag"], "title": f'{section["number"]} {section["title"]}', "search_title": section["title"], "kind": "section", "topic": chapters[section["chapter"]]["title"], "text": "", "aliases": []} for section in reader.sections.values() if not any(e.get("section_intro") for e in section["entries"])]
    public_entries, merges, section_search = [], [], {}
    for entry in entries.values():
        tag, root = entry["tag"], "../../"
        chapter_key = topic_chapters[entry["topic"]]
        chapter = chapters[chapter_key]
        content = f'<h1>{escape(display_title(entry))}<code class="tag-id">{tag}</code></h1>'
        if len(entry["variants"]) > 1:
            note = entry["merge_note"] or "Repeated statement: one entry retains the original source versions and proofs."
            content += f'<p class="merge-note">{escape(note)}</p>'
        variants, texts = [], []
        for number, variant in enumerate(entry["variants"]):
            source, local = variant["source"], variant["tag"]
            badge = f'<span data-gerby-tag="{local}"></span>'
            body = prepare_fragment(variant, source_tags, reference_map, root, anchors, reader.numbering)
            if number:
                body = '<details class="source-alternative"><summary>Read the alternative statement and proof</summary>' + body + '</details>'
            content += f'<section class="source-variant" data-gerby-book="{source}">{badge}{body}</section>'
            texts.append(BeautifulSoup(body, "html.parser").get_text(" ", strip=True))
            variants.append({"book": source, "tag": local, "label": variant["label"], "revision": editions[source]["commit"]})
        if entry.get("section_intro"):
            redirect(destination / "tag" / tag / "index.html", destination / "sections" / entry["topic"] / "index.html", destination, anchor="#entry-" + tag)
        else:
            write("tag/" + tag, content, display_title(entry), root)
        component_aliases = [value for v in entry["components"] for value in (v["tag"], v["label"])]
        search_record = {"tag": tag, "title": display_title(entry), "search_title": entry["title"], "kind": entry["kind"], "topic": chapter["title"], "section": reader.sections[entry["topic"]]["number"] + " " + topics[entry["topic"]]["title"], "text": " ".join(texts), "aliases": [v["tag"] for v in variants] + [v["label"] for v in variants] + component_aliases}
        if entry["section_intro"] and entry["topic"] in section_search:
            previous = section_search[entry["topic"]]
            previous["aliases"] += [tag, *search_record["aliases"]]
            previous["text"] += " " + search_record["text"]
        else:
            search.append(search_record)
            if entry["section_intro"]:
                search_record["kind"] = "section"
                section_search[entry["topic"]] = search_record
        public_entries.append({"tag": tag, "number": entry["number"], "section_intro": entry["section_intro"], "title": display_title(entry), "kind": entry["kind"], "chapter": chapter_key, "topic": entry["topic"], "sources": variants, "components": [{"book": v["source"], "tag": v["tag"], "label": v["label"]} for v in entry["components"]]})
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
            target = destination / "tag" / canonical / "index.html" if canonical else contents
            redirect(old_folder / record["page"], target, destination, anchor=anchors.get((source, record["tag"]), ""))
        for configured in configuration["entries"]:
            if any(m["source"] == source for m in configured["members"]):
                if configured["tag"] in entries:
                    redirect(old_folder / "tag" / configured["tag"] / "index.html", destination / "tag" / configured["tag"] / "index.html", destination)
                elif configured["topic"] in configuration.get("excluded_topics", []):
                    redirect(old_folder / "tag" / configured["tag"] / "index.html", contents, destination)
        redirect(old_folder / "bibliography" / "index.html", destination / "references" / "index.html", destination, {key: identifier for (origin, key), identifier in reference_map.items() if origin == source})
    write("sources", source_list + '</ul><p><a href="../deduplication.json">Reviewed duplicate groups and retained source tags</a></p>', "Sources", "../")
    reference_content = '<h1>Bibliography</h1><p>Bibliographic references cited across the shared collection.</p>'
    for identifier, record in sorted(references.items()):
        reference_content += f'<div class="bibliography-entry" id="{identifier}">{record["html"]}</div>'
    write("references", reference_content, "References", "../")
    write("search", '<h1>Search</h1><form class="page-search" role="search"><label for="page-search">Keywords, a statement number, or a permanent tag</label><input id="page-search" type="search" name="q" autocomplete="off" aria-controls="page-search-results"><button type="submit">Search</button></form><div id="page-search-results" aria-live="polite"></div>', "Search", "../")
    write("comments", '<h1>Comments and corrections</h1><p>Each chapter, section, and entry has its own comment thread. Use the Comments link on a reading page for a question or correction about that page.</p><p><a href="https://github.com/MingchenXia/Gerby/discussions">Browse all discussions on GitHub</a></p><p>The comment thread below is for general feedback about the reference. Markdown and mathematical notation are supported by GitHub Discussions. Please identify the statement and give enough detail for others to check a proposed correction.</p>', "Comments", "../")
    (destination / "search.json").write_text(json.dumps(search, ensure_ascii=False) + "\n")
    public_topics = [{**topic, "number": reader.sections[key]["number"], "tag": reader.sections[key]["tag"]} for key, topic in topics.items()]
    (destination / "collection.json").write_text(json.dumps({"version": 1, "chapters": list(chapters.values()), "topics": public_topics, "entries": public_entries}, ensure_ascii=False, indent=2) + "\n")
    (destination / "navigation.json").write_text(json.dumps([reader.pages[route] for route in reader.order], ensure_ascii=False, indent=2) + "\n")
    audit = {"groups": merges, "duplicate_entries_unified": sum(len(e["variants"]) - 1 for e in entries.values()), "numbered_clauses_in_parent_statements": len(anchors), "source_tags": sum(len(records) for records in inventories.values()), "canonical_entries": len(entries)}
    (destination / "deduplication.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    return {"entries": len(entries), "topics": len(topics), "chapters": len(chapters), "sources": len(sources)}


def check_links(destination):
    pages = {path.resolve(): BeautifulSoup(path.read_text(), "html.parser") for path in destination.rglob("*.html")}
    identifiers = {path: {item["id"] for item in soup.select("[id]")} for path, soup in pages.items()}
    numbers = {}
    if (destination / "collection.json").exists():
        entries = {entry["tag"]: entry for entry in json.loads((destination / "collection.json").read_text())["entries"]}
        for inventory in (destination / "sources").glob("*/tags.json"):
            for record in json.loads(inventory.read_text()):
                canonical = record["canonical_tag"]
                if canonical:
                    numbers[inventory.parent.name, record["tag"]] = record["title"].strip() if record.get("anchor") else entries[canonical]["number"]
    for page, soup in pages.items():
        for wrapper in soup.select("[data-gerby-book]"):
            for marker in wrapper.select("[data-tag]"):
                expected = numbers.get((wrapper["data-gerby-book"], marker["data-tag"]))
                if expected is not None and marker.get_text(strip=True) != expected:
                    raise ValueError(f"Stale source numbering on {page}: {marker['data-tag']}: expected {expected}")
        if len(identifiers[page]) != len(soup.select('[id]')):
            raise ValueError(f"Duplicate identifiers on {page}")
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
