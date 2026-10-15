"""Reading order, navigation, citations, and the shared reference interface."""
from hashlib import sha1
from html import escape
from urllib.parse import urlencode

PUBLIC_ROOT = "https://mingchenxia.github.io/Gerby/"
DISCUSSIONS = "https://github.com/MingchenXia/Gerby/discussions"


def display_title(entry):
    """Environment names come from the manuscript, never from a TeX label."""
    return entry["variants"][0]["title"]


def bibtex(title, route):
    def field(value):
        replacements = {"\\": r"\textbackslash{}", "{": r"\{", "}": r"\}", "\n": " "}
        return "".join(replacements.get(char, char) for char in value)
    key = "gerby-" + (route.replace("/", "-") or "home")
    return f'@misc{{{key},\n  author = {{{{Gerby contributors}}}},\n  title = {{{field(title)}}},\n  howpublished = {{Gerby}},\n  url = {{{PUBLIC_ROOT}{route + "/" if route else ""}}}\n}}'


class Reader:
    def __init__(self, chapters, topics, entries, sources, comments):
        self.chapters, self.topics, self.entries = chapters, topics, entries
        self.sources, self.comments = sources, comments
        self.sections, self.pages, self.order = {}, {}, []
        self.add("", "Gerby")
        self.add("chapters", "Table of contents")
        for key, chapter in chapters.items():
            self.add("chapters/" + key, f'{chapter["number"]} {chapter["title"]}', chapter=key)
            for number, topic in enumerate(chapter["topics"], 1):
                relevant = [e for e in entries.values() if e["topic"] == topic]
                self.sections[topic] = {**topics[topic], "chapter": key, "number": f'{chapter["number"]}.{number}', "entries": relevant}
                self.add("sections/" + topic, f'{chapter["number"]}.{number} {topics[topic]["title"]}', chapter=key, section=topic)
                for entry in relevant:
                    self.add("tag/" + entry["tag"], display_title(entry), chapter=key, section=topic, tag=entry["tag"])
        self.add("entries", "All entries")
        self.add("references", "Bibliography")
        self.add("sources", "Sources")
        for source, book in sources.items():
            self.add("sources/" + source, book["title"])
        self.add("search", "Search")
        self.add("comments", "Comments")
        expected = {"tag/" + tag for tag in entries}
        if {route for route in self.order if route.startswith("tag/")} != expected:
            raise ValueError("Reading order must contain every canonical entry exactly once")
        self.positions = {route: number for number, route in enumerate(self.order)}

    def add(self, route, title, **context):
        if route in self.pages:
            raise ValueError("Duplicate reading route: " + route)
        self.pages[route] = {"route": route, "title": title, **context}
        self.order.append(route)

    @staticmethod
    def href(route, root):
        return root + (route + "/" if route else "")

    def neighbors(self, route):
        position = self.positions[route]
        return (self.order[position - 1] if position else None,
                self.order[position + 1] if position + 1 < len(self.order) else None)

    def pager(self, route, root, bottom=False):
        previous, following = self.neighbors(route)
        links = []
        for direction, target, caption in (("prev", previous, "← Previous"), ("next", following, "Next →")):
            if target is None:
                links.append(f'<span class="pager-{direction} pager-boundary">{"Start of collection" if direction == "prev" else "End of collection"}</span>')
            else:
                page = self.pages[target]
                links.append(f'<a class="pager-{direction}" rel="{direction}" href="{self.href(target, root)}"><span>{caption}</span><small>{escape(page["title"])}</small></a>')
        return f'<nav class="page-navigation" aria-label="Page navigation{" bottom" if bottom else ""}">{"".join(links)}</nav>'

    def section_list(self, chapter, root, current=None, anchors=False):
        rows = []
        for topic in self.chapters[chapter]["topics"]:
            section = self.sections[topic]
            active = ' aria-current="page"' if current == topic else ""
            anchor = "section-" + topic if topic in {"comments", "cite", "content", "collection-search", "citation-text", "search-results"} else topic
            identifier = f' id="{anchor}"' if anchors else ""
            rows.append(f'<li{identifier}><a href="{self.href("sections/" + topic, root)}"{active}><span>{section["number"]}</span> {escape(section["title"])}</a></li>')
        return '<ol class="section-list">' + "".join(rows) + '</ol>'

    def contents(self, root):
        parts = []
        for key, chapter in self.chapters.items():
            parts.append(f'<details class="toc-chapter" open><summary><a href="{self.href("chapters/" + key, root)}">Chapter {chapter["number"]}. {escape(chapter["title"])}</a></summary>{self.section_list(key, root)}</details>')
        return '<div class="toc-controls"><button type="button" data-toc="expand">Expand all</button><button type="button" data-toc="collapse">Collapse all</button></div><div class="table-of-contents">' + "".join(parts) + '</div>'

    def breadcrumbs(self, route, root):
        page = self.pages[route]
        crumbs = [("Table of contents", "chapters")]
        if chapter := page.get("chapter"):
            crumbs.append((f'Chapter {self.chapters[chapter]["number"]}: {self.chapters[chapter]["title"]}', "chapters/" + chapter))
        if section := page.get("section"):
            crumbs.append((f'Section {self.sections[section]["number"]}: {self.sections[section]["title"]}', "sections/" + section))
        if not crumbs or crumbs[-1][1] != route:
            crumbs.append((page["title"], route))
        return '<nav class="breadcrumbs" aria-label="Breadcrumb"><ol>' + "".join(f'<li><a href="{self.href(path, root)}"' + (' aria-current="page"' if path == route else '') + f'>{escape(title)}</a></li>' for title, path in crumbs) + '</ol></nav>'

    def comment_panel(self, route):
        page = self.pages[route]
        term = "Gerby /" + (route + "/" if route else "")
        url = PUBLIC_ROOT + (route + "/" if route else "")
        body = f'Page: [{page["title"]}]({url})\n\nWrite your comment below.\n\n<!-- sha1: {sha1(term.encode()).hexdigest()} -->'
        new = DISCUSSIONS + "/new?" + urlencode({"category": self.comments["category_slug"], "title": term, "body": body})
        find = DISCUSSIONS + "?" + urlencode({"discussions_q": '"' + term + '"'})
        attrs = " ".join(f'data-{key.replace("_", "-")}="{escape(str(value), quote=True)}"' for key, value in self.comments.items() if key in {"repo", "repo_id", "category", "category_id"})
        return f'''<section class="comments-panel" id="comments" aria-labelledby="comments-heading" data-comment-term="{escape(term, quote=True)}" {attrs}>
<h2 id="comments-heading">Comments<span data-comment-count></span></h2><p>Corrections, questions, and mathematical discussion are welcome. Sign in with GitHub to comment. Comments are public.</p>
<div class="comment-actions"><a href="{escape(find, quote=True)}">Read this page’s discussion on GitHub</a><a href="{escape(new, quote=True)}">Post a comment on GitHub</a></div>
<button type="button" data-load-comments>Load comments</button><p class="comment-status" role="status"></p><div class="giscus"></div><noscript><p>Use the GitHub links above to read or leave comments.</p></noscript></section>'''

    def shell(self, content, route, root, version):
        page = self.pages[route]
        assets, title = root + "assets/", page["title"]
        permalink = PUBLIC_ROOT + (route + "/" if route else "")
        chapter_menu = "".join(f'<li><a href="{self.href("chapters/" + key, root)}">{chapter["number"]}. {escape(chapter["title"])}</a></li>' for key, chapter in self.chapters.items())
        local = '<h2>In this chapter</h2>' + self.section_list(page["chapter"], root, page.get("section")) if page.get("chapter") else ""
        citation = escape(bibtex(title, route))
        tools = f'''<div class="page-tools"><a href="#comments">Comments</a><a href="#cite">Cite this page</a><a href="{permalink}">Permalink</a><button type="button" data-copy-link="{permalink}">Copy link</button><label class="tag-switch"><input type="checkbox" data-show-tags> Show tags</label><span class="copy-status" role="status"></span></div>'''
        return f'''<!doctype html><html lang="en" data-reading-mode="{"continuous" if route.startswith("sections/") else "page"}" data-asset-revision="{version}" data-search-index="{root}search.json" data-collection-root="{root}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="theme-color" content="#d9d8d1"><meta name="giscus:backlink" content="{permalink}"><title>{escape(title)} · Gerby</title><link rel="canonical" href="{permalink}">
<link rel="icon" href="{assets}favicon.svg?v={version}" type="image/svg+xml"><link rel="stylesheet" href="{assets}book.css?v={version}"><link rel="stylesheet" href="{assets}collection.css?v={version}"><link rel="stylesheet" href="{assets}formalization.css?v={version}"><script src="{assets}math-config.js?v={version}"></script><script defer src="{assets}mathjax/tex-chtml.js?v={version}"></script><script type="module" src="{assets}formalization.mjs?v={version}"></script><script type="module" src="{assets}collection.mjs?v={version}"></script><script type="module" src="{assets}comments.mjs?v={version}"></script></head>
<body><a class="skip" href="#content">Skip to content</a><header class="book-header"><a class="brand" href="{root}" aria-label="Gerby home">Gerby</a><nav aria-label="Primary"><a href="{root}chapters/">Contents</a><a href="{root}references/">Bibliography</a><a href="{root}comments/">Comments</a></nav><form class="quick-search" action="{root}search/" role="search"><label class="visually-hidden" for="collection-search">Search Gerby</label><input id="collection-search" name="q" type="search" placeholder="Keywords or a tag" autocomplete="off" aria-controls="search-results"><div id="search-results" aria-live="polite"></div></form></header>
{self.breadcrumbs(route, root)}<div class="reading-layout"><aside class="sidebar"><details class="chapter-navigation" open><summary>Browse and page tools</summary><div class="reader-tools">{local}{tools}<details class="all-chapters"><summary>All chapters</summary><nav aria-label="All chapters"><ol>{chapter_menu}</ol></nav></details><p><a href="{root}sources/">Sources and revisions</a><br><a href="{root}entries/">All entries</a><br><a href="https://github.com/MingchenXia/Gerby">GitHub repository</a></p></div></details></aside>
<main id="content" tabindex="-1">{self.pager(route, root)}{content}{self.pager(route, root, True)}
<details class="citation" id="cite"><summary>Cite this page</summary><label for="citation-text">BibTeX citation</label><textarea id="citation-text" readonly rows="7">{citation}</textarea><button type="button" data-copy-citation>Copy citation</button><span class="copy-status" role="status"></span></details>
{self.comment_panel(route)}<footer class="book-footer">Gerby · <a href="{root}sources/">Sources and revisions</a> · <a href="{root}comments/">Comments</a></footer></main></div></body></html>'''
