"""Build the Pages catalogue and invoke registered Gerby conversion adapters."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
from html import escape
from html.parser import HTMLParser
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = re.compile(r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z")
SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
STANDARD_AXIOMS = {"propext", "Classical.choice", "Quot.sound"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def text_field(record, key):
    require(isinstance(record.get(key), str) and bool(record[key].strip()), f"Missing or empty {key}")


def relative_path(value):
    require(isinstance(value, str) and bool(value) and "\\" not in value, "Invalid relative path")
    path = PurePosixPath(value)
    require(not path.is_absolute() and ".." not in path.parts, "Paths must stay inside the source/output directory")
    return path


def source_fields(record):
    require(isinstance(record.get("repository"), str) and REPOSITORY.fullmatch(record["repository"]), "Expected a public GitHub repository URL")
    if "ref" in record:
        require(isinstance(record["ref"], str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_./-]*", record["ref"]), "Invalid source ref")


def validate(books, formalizations):
    require(books.get("version") == 1 and isinstance(books.get("books"), list), "Invalid books registry")
    require(formalizations.get("version") == 1 and isinstance(formalizations.get("entries"), list), "Invalid formalization registry")
    slugs = set()
    for book in books["books"]:
        require(isinstance(book, dict), "Book entries must be objects")
        require(isinstance(book.get("slug"), str) and SLUG.fullmatch(book["slug"]), "Invalid book slug")
        require(book["slug"] not in slugs, "Duplicate book slug")
        slugs.add(book["slug"])
        text_field(book, "title")
        source_fields(book)
        require(book.get("status") in {"pending", "published"}, "Invalid book status")
        for field in ("entrypoint", "tags"):
            if field in book:
                relative_path(book[field])
    keys = set()
    for item in formalizations["entries"]:
        require(isinstance(item, dict), "Formalization entries must be objects")
        require(item.get("book") in slugs, "Formalization references an unknown book")
        require(isinstance(item.get("tag"), str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9:._-]*", item["tag"]), "Invalid tag")
        key = (item["book"], item["tag"])
        require(key not in keys, "Duplicate book/tag formalization")
        keys.add(key)
        source_fields(item)
        require(item.get("state") in {"pending", "verified"}, "Invalid verification state")
        if item["state"] == "verified":
            require(isinstance(item.get("commit"), str) and re.fullmatch(r"[a-f0-9]{40}", item["commit"]), "Verified records require an exact commit")
            relative_path(item.get("file"))
            text_field(item, "declaration")
            evidence = item.get("verification")
            require(isinstance(evidence, dict), "Verified records require evidence")
            text_field(evidence, "command")
            require(isinstance(evidence.get("evidence_url"), str) and re.fullmatch(r"https://github\.com/[^/]+/[^/]+/(?:actions/runs/\d+|blob/[^\s]+)", evidence["evidence_url"]), "Expected a GitHub run or committed evidence report")
            text_field(evidence, "checked_at")
            checked = datetime.fromisoformat(evidence["checked_at"].replace("Z", "+00:00"))
            require(checked.utcoffset() is not None and checked.utcoffset().total_seconds() == 0, "Verification time must be UTC")
            axioms = evidence.get("axioms")
            require(isinstance(axioms, list) and all(isinstance(a, str) for a in axioms), "Expected audited axiom dependencies")
            require(set(axioms) <= STANDARD_AXIOMS, "Unapproved axiom dependency (including sorryAx)")


def source_key(record):
    return record["repository"], record.get("ref", "HEAD")


def fetch_source(record, cache):
    key = source_key(record)
    if key not in cache:
        destination = ROOT / "_sources" / sha256("\0".join(key).encode()).hexdigest()[:16]
        if destination.exists():
            shutil.rmtree(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "clone", "--filter=blob:none", "--depth=1", "--no-checkout", key[0], str(destination)], check=True)
        if key[1] == "HEAD":
            subprocess.run(["git", "-C", str(destination), "checkout", "--detach", "HEAD"], check=True)
        else:
            subprocess.run(["git", "-C", str(destination), "fetch", "--depth=1", "origin", key[1]], check=True)
            subprocess.run(["git", "-C", str(destination), "checkout", "--detach", "FETCH_HEAD"], check=True)
        commit = subprocess.check_output(["git", "-C", str(destination), "rev-parse", "HEAD"], text=True).strip()
        cache[key] = {"path": destination, "commit": commit}
    return cache[key]


def public_formalizations(registry, cache):
    result = json.loads(json.dumps(registry))
    for item in result["entries"]:
        current = cache.get(source_key(item), {}).get("commit")
        if item["state"] == "verified" and current != item["commit"]:
            item["state"] = "pending"
            item["reason"] = "The current upstream revision has not been verified."
        if current:
            item["current_commit"] = current
    return result


class PageTags(HTMLParser):
    def __init__(self):
        super().__init__()
        self.books, self.tags, self.scripts, self.styles = set(), set(), [], []

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if "data-gerby-book" in attrs:
            self.books.add(attrs["data-gerby-book"])
        if "data-gerby-tag" in attrs:
            self.tags.add(attrs["data-gerby-tag"])
        if tag == "script":
            self.scripts.append(attrs.get("src", ""))
        if tag == "link":
            self.styles.append(attrs.get("href", ""))


def check_book(output, slug):
    require((output / "index.html").is_file(), f"{slug}: missing book index")
    inventory_path = output / "tags.json"
    require(inventory_path.is_file(), f"{slug}: adapter must export a complete tags.json inventory")
    inventory = json.loads(inventory_path.read_text())
    require(isinstance(inventory, list) and bool(inventory), f"{slug}: empty tag inventory")
    seen = set()
    for item in inventory:
        text_field(item, "tag")
        require(item["tag"] not in seen, f"{slug}: duplicate inventory tag")
        seen.add(item["tag"])
        page = output / relative_path(item.get("page"))
        require(page.suffix == ".html" and page.is_file(), f"{slug}: missing page for {item['tag']}")
        parsed = PageTags()
        parsed.feed(page.read_text())
        require(slug in parsed.books and item["tag"] in parsed.tags, f"{slug}: missing book/tag badge marker for {item['tag']}")
    for page in output.rglob("*.html"):
        parsed = PageTags()
        parsed.feed(page.read_text())
        require(slug in parsed.books, f"{page}: missing book namespace")
        for name, references in (("formalization.mjs", parsed.scripts), ("formalization.css", parsed.styles)):
            expected = ROOT / "_site" / "assets" / name
            require(any((page.parent / ref).resolve() == expected.resolve() for ref in references), f"{page}: missing shared {name}")


def book_markup(books):
    if not books:
        return '<div class="empty-state"><span class="book-icon" aria-hidden="true"></span><div><h3>The first chapter is ahead.</h3><p>No books have been published yet. Online editions will appear here as their source repositories are added.</p></div></div>'
    cards = []
    for book in books:
        title, slug = escape(book["title"]), escape(book["slug"])
        source = escape(book["repository"], quote=True)
        reading = f'<a href="./books/{slug}/">Read book →</a> · ' if book["status"] == "published" else ""
        status = "Published" if book["status"] == "published" else "Preparing this edition"
        cards.append(f'<article class="book-card"><p class="status">{status}</p><h3>{title}</h3><p>{reading}<a href="{source}">Source repository ↗</a></p></article>')
    return '<div class="books">' + "".join(cards) + '</div>'


def build(fetch=False):
    books = json.loads((ROOT / "books.json").read_text())
    formalizations = json.loads((ROOT / "formalizations.json").read_text())
    validate(books, formalizations)
    cache = {}
    if fetch:
        for record in books["books"] + formalizations["entries"]:
            fetch_source(record, cache)
    destination = ROOT / "_site"
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(ROOT / "site", destination)
    for book in books["books"]:
        if book["status"] != "published":
            continue
        require(fetch, "Published books require --fetch so editions cannot silently use stale sources")
        adapter = ROOT / "adapters" / f"{book['slug']}.py"
        require(adapter.is_file(), f"Missing Gerby adapter: {adapter.name}")
        output = destination / "books" / book["slug"]
        output.mkdir(parents=True)
        subprocess.run([sys.executable, str(adapter), str(cache[source_key(book)]["path"]), str(output)], check=True, cwd=ROOT)
        check_book(output, book["slug"])
    page = (destination / "index.html").read_text()
    count = len(books["books"])
    page = page.replace("@@COUNT@@", f"{count} book{'s' if count != 1 else ''}").replace("@@BOOKS@@", book_markup(books["books"]))
    if count:
        page = page.replace("No proofs are claimed to be verified yet.", "Status badges refer to the exact linked proof revisions.")
    (destination / "index.html").write_text(page)
    (destination / "formalizations.json").write_text(json.dumps(public_formalizations(formalizations, cache), indent=2) + "\n")
    revisions = [{"repository": repo, "ref": ref, "commit": info["commit"]} for (repo, ref), info in sorted(cache.items())]
    (destination / "upstream.json").write_text(json.dumps({"built_at": datetime.now(timezone.utc).isoformat(), "sources": revisions}, indent=2) + "\n")
    (destination / ".nojekyll").touch()
    print(f"Built {count} book(s), {len(revisions)} upstream revision(s): {destination}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fetch", action="store_true", help="Fetch upstream repositories and run book adapters")
    args = parser.parse_args()
    try:
        build(fetch=args.fetch)
    except (ValueError, subprocess.CalledProcessError) as error:
        print(f"Build failed: {error}", file=sys.stderr)
        sys.exit(1)
