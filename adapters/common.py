"""Render the active manuscript with the official Gerby renderer and export static pages."""
from __future__ import annotations

import collections
import collections.abc
from hashlib import sha256
from html import escape
import importlib
import json
import logging
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

from bs4 import BeautifulSoup
from unidecode import unidecode

SLUG = "foundations-of-pluripotential-theory"
TITLE = "Foundations of pluripotential theory"
REPOSITORY = f"https://github.com/MingchenXia/{SLUG}"
AUTHOR = "Mingchen Xia"
DIRECTORY = ""
BIBLIOGRAPHY = "ComplexGeometry.bib"
ASSETS = None


def configure(slug, title, repository, author="Mingchen Xia", directory="", bibliography="ComplexGeometry.bib"):
    global SLUG, TITLE, REPOSITORY, AUTHOR, DIRECTORY, BIBLIOGRAPHY
    SLUG, TITLE, REPOSITORY, AUTHOR, DIRECTORY, BIBLIOGRAPHY = slug, title, repository, author, directory, bibliography
SECTIONS = {"part", "chapter", "section", "subsection", "subsubsection", "paragraph", "subparagraph"}
THEOREMS = "case conjecture corollary definition example exercise lemma note problem property proposition question solution remark".split()


def stable_tag(label):
    # A tag depends on the source label, never its number or position in the book.
    return sha256(label.encode("utf-8")).hexdigest()[:8].upper()


def uncomment(text):
    return re.sub(r"(?<!\\)%[^\n]*", "", text)


def active_text(source, name="book.tex", stack=()):
    path = (source / name).resolve()
    if not path.is_relative_to(source.resolve()) or path in stack:
        raise ValueError(f"Invalid or recursive manuscript input: {name}")
    text = uncomment(path.read_text())
    def expand(match):
        nested = match[1] if Path(match[1]).suffix else match[1] + ".tex"
        return active_text(source, nested, (*stack, path))
    return re.sub(r"\\(?:input|include)\s*\{([^}]+)\}", expand, text)


def prepare_tex(source):
    if SLUG != "foundations-of-pluripotential-theory":
        from profiles import prepare
        return prepare(source, SLUG, ASSETS, THEOREMS)
    book = uncomment((source / "book.tex").read_text())
    if r"\documentclass[envcountsect]{svmono}" not in book:
        raise ValueError("The source document class changed; review the Gerby numbering adapter")
    body = book[book.index(r"\begin{document}"):]
    def expand(match):
        name = match[1] if Path(match[1]).suffix else match[1] + ".tex"
        return active_text(source, name)
    body = re.sub(r"\\(?:input|include)\s*\{([^}]+)\}", expand, body)
    body = body.replace(r"\preface", r"\chapter*{Preface}")
    body = re.sub(r"\\extrachap\{([^}]+)\}", r"\\chapter*{\1}", body)
    # Bibliography entries are exported separately from the cited upstream database.
    body = re.sub(r"\\(?:printindex|bibliographystyle\{[^}]+\}|bibliography\{[^}]+\})", "", body)
    preamble = uncomment((source / "style/book-preamble.tex").read_text())
    macros = preamble[preamble.index(r"\newcommand{\nef}"):preamble.index(r"\setlist")]
    theorems = r"\newtheorem{theorem}{Theorem}[section]" + "\n"
    theorems += "\n".join(rf"\newtheorem{{{name}}}[theorem]{{{name.title()}}}" for name in THEOREMS)
    theorems += "\n" + r"\newtheorem*{claim}{Claim}" + "\n"
    return "\\documentclass{book}\n\\usepackage{amsmath,amssymb}\n" + theorems + macros + body


def compatibility():
    # Gerby's pinned renderer predates the collections.abc namespace.
    collections.Callable = collections.abc.Callable
    context = importlib.import_module("plasTeX.Context")
    from plasTeX.Tokenizer import Tokenizer, EndInput
    class MacroTokenizer(Tokenizer):
        def __iter__(self):
            # Context materializes macro strings as lists. Its Tokenizer now
            # raises EndInput; the TeX input-stack tokenizer must retain that behavior.
            try:
                yield from super().__iter__()
            except EndInput:
                return
    context.Tokenizer = MacroTokenizer


def register_commands(document):
    from plasTeX import Command
    class label(Command):
        args = "[ type:str ] label:id"
    document.context.addGlobal("label", label)
    class CrossReference(Command):
        args = "* labels:str"

        def invoke(self, tex):
            self.parse(tex)
            names = {"chap": "Chapter", "sec": "Section", "thm": "Theorem", "lem": "Lemma", "prop": "Proposition", "cor": "Corollary", "def": "Definition", "eq": "Equation", "ex": "Example", "rem": "Remark"}
            references = []
            for label in self.attributes["labels"].split(","):
                label = label.strip()
                prefix = names.get(label.split(":")[0], "")
                if self.nodeName == "cref":
                    prefix = prefix.lower()
                references.append((prefix + " " if prefix else "") + r"\ref{" + label + "}")
            tex.input(", ".join(references))
            return []
    document.context.addGlobal("cref", type("cref", (CrossReference,), {}))
    document.context.addGlobal("Cref", type("Cref", (CrossReference,), {}))
    class Needspace(Command):
        args = "amount:nox"

        def invoke(self, tex):
            self.parse(tex)
            return []
    document.context.addGlobal("Needspace", Needspace)
    class addtocontents(Needspace):
        args = "target:str content:nox"
    document.context.addGlobal("addtocontents", addtocontents)
    document.context.newcommand("eqref", 1, r"(\ref{#1})")
    document.context.newcommand("texorpdfstring", 2, "#1")
    document.context.newcommand("aa", 0, "å")
    for name in ("itemref", "Itemref"):
        class ItemReference(Command):
            args = "label:str"

            def invoke(self, tex):
                self.parse(tex)
                label = self.attributes["label"]
                parent = ":".join(label.split(":")[1:-1])
                tex.input((r"\cref{" + parent + "} " if parent else "") + r"\ref{" + label + "}")
                return []
        document.context.addGlobal(name, type(name, (ItemReference,), {}))
    class gerbyimage(Command):
        args = "path:str alt:str"
    document.context.addGlobal("gerbyimage", gerbyimage)
    from plasTeX import Environment
    class partbacktext(Environment):
        pass
    document.context.addGlobal("partbacktext", partbacktext)
    class motto(Command):
        args = "[ width:str ] self"
    document.context.addGlobal("motto", motto)
    document.context.newcommand("subtitle", 1, "")
    class resizebox(Command):
        args = "* width:str height:str self"
    document.context.addGlobal("resizebox", resizebox)
    # The pinned fork accidentally redeclares these zero-argument symbols as
    # one-argument accents, which can swallow a closing math delimiter.
    from plasTeX.Base.LaTeX.Math import MathSymbol
    for symbol in ("imath", "jmath"):
        document.context.addGlobal(symbol, type(symbol, (MathSymbol,), {}))


class ParseProblems(logging.Handler):
    def __init__(self):
        super().__init__()
        self.problems = []

    def emit(self, record):
        message = record.getMessage()
        if record.levelno >= logging.ERROR or "unrecognized command/environment" in message:
            self.problems.append(message)


def nodes_in_order(node):
    yield node
    for child in node.childNodes:
        yield from nodes_in_order(child)


def render_fragments(source, working):
    compatibility()
    from plasTeX import TeXDocument
    from plasTeX.TeX import TeX
    from plasTeX.Config import config
    from plasTeX.Renderers.Gerby.Config import config as gerby_config
    from plasTeX.Renderers.Gerby import Renderer
    from plasTeX.Logging import getLogger
    problems = ParseProblems()
    getLogger().addHandler(problems)
    tex_source = prepare_tex(source)
    (working / "book.tex").write_text(tex_source)
    config += gerby_config
    config["general"]["renderer"] = "Gerby"
    config["files"]["directory"] = ""
    config["images"]["imager"] = "none"
    config["images"]["vector-imager"] = "none"
    document = TeXDocument(config=config)
    register_commands(document)
    os.environ.setdefault("TEXINPUTS", str(working) + os.pathsep)
    tex = TeX(document)
    # Source labels are identifiers. An underscore must not become a math
    # subscript node while plasTeX casts a label or a reference argument.
    tex.argtypes["id"] = (tex.castLabel, {"_": 12})
    tex.argtypes["idref"] = (tex.castRef, {"_": 12})
    tex.argtypes["str"] = (tex.castString, {"_": 12})
    tex.input(tex_source)
    document.userdata["working-dir"] = str(working)
    document.userdata["jobname"] = "book"
    tex.parse()
    if problems.problems:
        raise ValueError("Unsupported manuscript commands: " + "; ".join(problems.problems))
    starred = dict(re.findall(r"\\chapter\*\{([^{}]+)\}\s*\\label\{([^}]+)\}", tex_source))
    for node in document.getElementsByTagName("chapter"):
        if node.ref is None and node.title.textContent.strip() in starred:
            document.context.label(starred[node.title.textContent.strip()], node)
            node.ref = document.createDocumentFragment()
    labelled = {}
    for label, node in document.context.labels.items():
        labelled.setdefault(id(node), []).append(label)
    records, tags = [], {}
    for node in nodes_in_order(document):
        if node.nodeName not in SECTIONS and node.nodeName != "thmenv" and id(node) not in labelled:
            continue
        if id(node) not in labelled:
            if node.nodeName in SECTIONS and node.ref is None:
                title = node.title.textContent.strip()
                # Frontmatter/part headings in svmono need synthetic, named labels.
                label = "heading:" + re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
                document.context.label(label, node)
                node.ref = document.createDocumentFragment()
            elif node.nodeName == "part":
                label = "part:" + re.sub(r"[^a-z0-9]+", "-", node.title.textContent.lower()).strip("-")
                document.context.label(label, node)
            elif SLUG != "foundations-of-pluripotential-theory":
                label = "unlabelled:" + node.nodeName + ":" + sha256(node.source.encode()).hexdigest()[:16]
                document.context.label(label, node)
            else:
                raise ValueError(f"Every numbered heading and theorem needs a source label: {node.nodeName}")
        aliases = labelled.get(id(node), [node.id])
        label = aliases[0]
        document.context.label(label, node)
        tag = stable_tag(label)
        if tag in tags and tags[tag] != label:
            raise ValueError("Gerby tag collision: reserve an explicit alias before publication")
        tags[tag] = label
        number = node.ref.textContent.strip() if getattr(node, "ref", None) is not None else ""
        kind = node.thmName if node.nodeName == "thmenv" else node.nodeName
        if kind in {"ArrayRow", "align", "gather", "eqnarray"}:
            kind = "equation"
        title = node.title.textContent.strip() if getattr(node, "title", None) else ""
        semantic_title = title or label.split(":")[-1].replace("-", " ").replace("_", " ").capitalize()
        if node.nodeName == "thmenv":
            title = kind.title() + (" " + number if number else "") + (f" ({title})" if title else "")
        elif number:
            title = number + " " + title
        if not title:
            title = kind.title() + (" " + number if number else "")
        if SLUG == "sgpt" and node.nodeName == "thmenv" and not getattr(node, "title", None):
            # Legacy SGPT identifiers such as L1122 are source coordinates,
            # rather than reader-facing names. Definitions acquire their
            # emphasized term after rendering; other unnamed results keep
            # their original, unambiguous theorem locator.
            semantic_title = title
        if semantic_title.startswith("-good singularities"):
            semantic_title = "I" + semantic_title
        semantic_title = semantic_title.replace("and -goodness", "and I-goodness")
        parent = node
        while parent.parentNode is not None and parent.nodeName != "chapter":
            parent = parent.parentNode
        topic = parent.title.textContent.strip() if parent.nodeName == "chapter" else "Project notes"
        ancestor = node.parentNode
        while ancestor is not None and ancestor.nodeName not in SECTIONS | {"thmenv"}:
            ancestor = ancestor.parentNode
        parent_label = ancestor.id if ancestor is not None else None
        records.append({"tag": tag, "label": label, "aliases": aliases[1:], "title": title, "semantic_title": semantic_title, "kind": kind, "math_row": node.nodeName == "ArrayRow", "topic": topic, "section": node.nodeName in SECTIONS, "statement_tex": node.source, "parent_label": parent_label})
    (working / "tags").write_text("".join(f"{tag},{label}\n" for tag, label in tags.items()))
    previous = Path.cwd()
    rows = {record["tag"]: record for record in records if record["math_row"]}
    row_nodes = {stable_tag(node.id): node for node in nodes_in_order(document) if node.nodeName == "ArrayRow" and node.id}
    class StaticRenderer(Renderer):
        textDefault = staticmethod(lambda value: escape(str(value), quote=False))

        def cleanup(self, document, files, postProcess=None):
            # Math environments render their TeX source as a whole, so their
            # labelled rows are not separately traversed by the Gerby renderer.
            for tag, record in rows.items():
                filename = next((name for name in files if f"-{tag}-" in name), None)
                if filename and not Path(filename).exists():
                    row = row_nodes[tag]
                    latex = row.source.strip().removesuffix(r"\\")
                    Path(filename).write_text(f'<div class="equation" id="{tag}"><span class="equation-label"><a href="/tag/{tag}" data-tag="{tag}">{escape(record["title"])}</a></span><div>\\[\\begin{{aligned}}{escape(latex)}\\end{{aligned}}\\]</div></div>')
            return super().cleanup(document, files, postProcess)
    try:
        os.chdir(working)
        StaticRenderer().render(document)
    finally:
        os.chdir(previous)
    if problems.problems:
        raise ValueError("Gerby rendering errors: " + "; ".join(problems.problems))
    for record in records:
        fragments = list(working.glob(f"*-{record['tag']}-*.tag"))
        if len(fragments) != 1:
            raise ValueError(f"Expected exactly one Gerby fragment for {record['kind']} {record['tag']} {record['label']}: {record['statement_tex'][:500]}")
        record["html"] = fragments[0].read_text()
        record["statement_html"] = record["html"]
        if record["kind"] == "definition":
            term = BeautifulSoup(record["html"], "html.parser").find("em")
            if term and 3 <= len(term.get_text()) <= 120:
                name = term.get_text(" ", strip=True)
                record["semantic_title"] = name[:1].upper() + name[1:]
        record["proof_html"] = "".join(path.read_text() for path in sorted(working.glob(record["tag"] + "-*.proof")))
        record["html"] += record["proof_html"]
    floats = {}
    for record in records:
        if record["section"] and '<figure class="source-float"' in record["html"]:
            for figure in BeautifulSoup(record["html"], "html.parser").select("figure.source-float"):
                for caption in figure.select("figcaption[id]"):
                    floats[caption["id"]] = str(figure)
    for record in records:
        if record["kind"] == "caption" and record["tag"] in floats:
            record["html"] = record["statement_html"] = floats[record["tag"]]
    return records


def decorate(fragment, root):
    soup = BeautifulSoup(fragment, "html.parser")
    for illustration in soup.select('[src^="/asset/"]'):
        illustration["src"] = root + "../../assets/sources/" + illustration["src"].removeprefix("/asset/")
    for paragraph in list(soup.find_all("p")):
        if paragraph.find(["article", "div", "h1", "h2", "h3", "ul", "ol"], recursive=False):
            paragraph.unwrap()
    for anchor in soup.select('a[href^="/tag/"]'):
        anchor["href"] = root + "tag/" + anchor["href"].split("/")[-1] + "/"
    for anchor in soup.select('a[href^="/bibliography/"]'):
        anchor["href"] = root + "bibliography/#" + anchor["href"].split("/")[-1]
    for marker in soup.select("[data-tag]"):
        tag = marker.get("data-tag")
        if not tag:
            continue
        heading = marker.find_parent(re.compile(r"^h[1-6]$"))
        if heading:
            heading["data-gerby-tag"] = tag
        elif marker.find_parent("a", class_="environment-identifier") or marker.find_parent(class_="equation-label"):
            anchor = marker.find_parent("a")
            if anchor and not anchor.find_next_sibling(attrs={"data-gerby-tag": tag}):
                badge = soup.new_tag("span")
                badge["data-gerby-tag"] = tag
                anchor.insert_after(badge)
    for element in soup.select("[id]"):
        identifier = element["id"]
        if re.fullmatch(r"[A-F0-9]{8}", identifier) and not soup.find(attrs={"data-gerby-tag": identifier}):
            badge = soup.new_tag("span")
            badge["data-gerby-tag"] = identifier
            element.insert(0, badge)
    return str(soup)


def shell(content, title, records, revision, root=""):
    assets = root + "../../assets/"
    toc = "".join(f'<li class="toc-{escape(r["kind"])}"><a href="{root}tag/{r["tag"]}/">{escape(r["title"])}</a></li>' for r in records if r["section"])
    return f'''<!doctype html>
<html lang="en" data-gerby-book="{SLUG}" data-search-index="{root}search.json" data-book-root="{root}">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(title)} · Gerby</title>
<link rel="stylesheet" href="{assets}book.css"><link rel="stylesheet" href="{assets}formalization.css">
<link rel="icon" href="{assets}favicon.svg" type="image/svg+xml">
<script src="{assets}math-config.js"></script><script defer src="{assets}mathjax/tex-chtml.js"></script>
<script type="module" src="{assets}formalization.mjs"></script><script type="module" src="{assets}book.mjs"></script>
</head><body><a class="skip" href="#content">Skip to book text</a>
<header class="book-header"><a href="{root}../../" class="brand">g <span>Gerby</span></a><a href="{root}">Book contents</a><a href="{REPOSITORY}">Source ↗</a></header>
<div class="reading-layout"><aside class="sidebar"><p class="book-name">{TITLE}</p><p class="author">{escape(AUTHOR)}</p>
<label for="book-search">Search this book</label><input id="book-search" type="search" placeholder="A title, phrase, or tag" autocomplete="off"><div id="search-results" aria-live="polite"></div>
<nav aria-label="Book contents"><ul><li><a href="{root}">Read the active draft</a></li>{toc}<li><a href="{root}bibliography/">Bibliography</a></li></ul></nav>
<p class="draft-note">Work in progress. This edition follows the active manuscript.</p></aside>
<main id="content">{content}<footer class="book-footer">{escape(AUTHOR)} · Draft edition · Source revision <a href="{REPOSITORY}/commit/{revision}">{revision[:12]}</a><br>Tags identify source labels. Formalization status is recorded independently of the mathematical text.</footer></main></div></body></html>'''


def export(source, output):
    global ASSETS
    source, output = source.resolve(), output.resolve()
    ASSETS = output / "assets"
    ASSETS.mkdir(parents=True, exist_ok=True)
    revision = subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip()
    subprocess.run(["git", "-C", str(source), "diff", "--exit-code", "HEAD"], check=True, stdout=subprocess.DEVNULL)
    if not re.fullmatch(r"[a-f0-9]{40}", revision):
        raise ValueError("Missing exact source revision")
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="gerby-foundations-") as temporary:
        records = render_fragments(source / DIRECTORY, Path(temporary))
    index = f'<div class="book-title"><p class="eyebrow">An online draft</p><h1>{TITLE}</h1><p>{escape(AUTHOR)}</p></div>'
    index += "".join(decorate(record["html"], "") for record in records if record["section"])
    (output / "index.html").write_text(shell(index, TITLE, records, revision))
    inventory, search = [], []
    for position, record in enumerate(records):
        page = output / "tag" / record["tag"] / "index.html"
        page.parent.mkdir(parents=True, exist_ok=True)
        fragment = decorate(record["html"], "../../")
        if not record["section"]:
            fragment = f'<h1>{escape(record["title"])}</h1>' + fragment
        tag_header = f'<p class="tag-caption">Tag <code>{record["tag"]}</code> · <code>{escape(record["label"])}</code></p>'
        neighbours = '<nav class="neighbours" aria-label="Adjacent tags">'
        for offset, text in ((-1, "← Previous"), (1, "Next →")):
            adjacent = position + offset
            if 0 <= adjacent < len(records):
                neighbours += f'<a href="../../tag/{records[adjacent]["tag"]}/">{text}</a>'
        neighbours += '</nav>'
        page.write_text(shell(tag_header + fragment + neighbours, record["title"], records, revision, "../../"))
        inventory.append({k: record[k] for k in ("tag", "label", "title", "kind") } | {"page": str(page.relative_to(output))})
        search.append({"tag": record["tag"], "title": record["title"], "label": record["label"], "text": BeautifulSoup(record["html"], "html.parser").get_text(" ", strip=True)})
    citations = sorted({anchor["href"].split("/")[-1] for record in records for anchor in BeautifulSoup(record["html"], "html.parser").select('a[href^="/bibliography/"]')})
    from pybtex.database.input.bibtex import Parser
    from pybtex.plugin import find_plugin
    class CitedBibliography(Parser):
        def process_entry(self, entry_type, key, fields):
            # Only cited entries belong in this edition. Unrelated legacy
            # duplicates in the shared database must not change its contents.
            if key in citations:
                super().process_entry(entry_type, key, fields)
    database = CitedBibliography().parse_file(str(source / DIRECTORY / BIBLIOGRAPHY))
    style = find_plugin("pybtex.style.formatting", "plain")()
    backend = find_plugin("pybtex.backends", "html")()
    bibliography = '<h1>Bibliography</h1>'
    reference_records = []
    for key in citations:
        if key not in database.entries:
            raise ValueError(f"Missing bibliography entry: {key}")
        formatted = next(iter(style.format_entries([database.entries[key]])))
        formatted_html = formatted.text.render(backend)
        bibliography += f'<div class="bibliography-entry" id="{escape(key)}"><strong>[{escape(key)}]</strong> {formatted_html}</div>'
        fields = database.entries[key].fields
        if fields.get("doi"):
            identity = "doi:" + fields["doi"].strip().lower().removeprefix("https://doi.org/").removeprefix("http://dx.doi.org/")
        else:
            authors = database.entries[key].persons.get("author", [])
            author = " ".join(authors[0].last_names) if authors else ""
            identity = "title:" + re.sub(r"[^a-z0-9]", "", unidecode(fields.get("title", "")).lower()) + ":" + fields.get("year", "") + ":" + unidecode(author).casefold()
        reference_records.append({"key": key, "identity": identity, "html": formatted_html})
    (output / "bibliography").mkdir(exist_ok=True)
    (output / "bibliography" / "index.html").write_text(shell(bibliography, "Bibliography", records, revision, "../"))
    (output / "tags.json").write_text(json.dumps(inventory, indent=2) + "\n")
    (output / "entries.json").write_text(json.dumps(records, ensure_ascii=False) + "\n")
    (output / "references.json").write_text(json.dumps(reference_records, ensure_ascii=False) + "\n")
    (output / "search.json").write_text(json.dumps(search, ensure_ascii=False) + "\n")
    (output / "edition.json").write_text(json.dumps({"source": REPOSITORY, "commit": revision, "renderer": "Gerby", "tags": len(records)}, indent=2) + "\n")
    print(f"Exported {len(records)} permanent tags from the active manuscript")


if __name__ == "__main__":
    export(Path(sys.argv[1]), Path(sys.argv[2]))
