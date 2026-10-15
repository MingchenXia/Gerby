"""Add reviewed proofs to source fragments without changing the source books."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import re

from bs4 import BeautifulSoup


def inject_proof(html, identifier, proof_html, proof_id):
    if f'id="{identifier}"' not in html and f"id='{identifier}'" not in html:
        return None
    soup = BeautifulSoup(html, "html.parser")
    if soup.find(attrs={"data-proof-expansion": proof_id}):
        raise ValueError(f"Duplicate proof expansion: {proof_id}")
    statement = soup.find(id=identifier)
    if statement is None:
        return None
    proof = BeautifulSoup(proof_html, "html.parser")
    article = soup.new_tag("article")
    article["class"] = ["env-proof", "proof-expansion"]
    article["data-proof-expansion"] = proof_id
    for node in list(proof.contents):
        article.append(node.extract())
    following = statement.find_next_sibling()
    if following and "env-proof" in following.get("class", []):
        following.replace_with(article)
    else:
        statement.insert_after(article)
    return str(soup)


def apply_expansions(exports, registry_path, fingerprint):
    registry_path = Path(registry_path)
    registry = json.loads(registry_path.read_text())
    if registry.get("version") != 1:
        raise ValueError("Unsupported proof expansion registry")
    result = deepcopy(exports)
    seen, dependencies = set(), {}
    for expansion in registry["entries"]:
        source, label = expansion["source"], expansion["label"]
        key = source, label
        if key in seen:
            raise ValueError(f"Duplicate proof target: {source}/{label}")
        seen.add(key)
        matches = [record for record in result.get(source, []) if label in [record["label"], *record.get("aliases", [])]]
        if len(matches) != 1:
            raise ValueError(f"Missing or ambiguous proof target: {source}/{label}")
        target = matches[0]
        if fingerprint(target) != expansion["statement_sha256"]:
            raise ValueError(f"A proof expansion needs review after a statement change: {source}/{label}")
        if sha256(target.get("proof_html", "").encode()).hexdigest() != expansion["original_proof_sha256"]:
            raise ValueError(f"A proof expansion needs review after a source proof change: {source}/{label}")
        path = (registry_path.parent / expansion["file"]).resolve()
        if not path.is_relative_to(registry_path.parent.resolve()) or path.suffix != ".html":
            raise ValueError("Proof files must remain inside the proof directory")
        html = path.read_text()
        proof = BeautifulSoup(html, "html.parser")
        if proof.select("script, iframe, form, object, embed"):
            raise ValueError(f"Unsupported proof markup: {path.name}")
        links = {a["data-proof-entry"] for a in proof.select("a[data-proof-entry]")}
        if any(not re.fullmatch(r"[A-Z0-9]{8,12}", tag) for tag in links):
            raise ValueError(f"Invalid internal proof dependency: {path.name}")
        proof_id = source + ":" + label
        dependencies[key] = links
        inserted = False
        for record in result[source]:
            changed = inject_proof(record["html"], target["tag"], html, proof_id)
            if changed is not None:
                record["html"] = changed
                if record is target:
                    inserted = True
        if not inserted:
            raise ValueError(f"The proof target has no statement root: {source}/{label}")
    return result, dependencies


def check_dependencies(entries, dependencies):
    targets = {}
    for tag, entry in entries.items():
        for variant in entry["variants"]:
            for label in [variant["label"], *variant.get("aliases", [])]:
                targets[(variant["source"], label)] = tag
    graph = {}
    for key, links in dependencies.items():
        target = targets.get(key)
        if target is None:
            raise ValueError(f"An expanded statement is absent from the collection: {key}")
        if links - entries.keys():
            raise ValueError(f"Missing internal proof dependencies: {sorted(links - entries.keys())}")
        graph.setdefault(target, set()).update(links)
    visited, active = set(), set()

    def visit(tag):
        if tag in active:
            raise ValueError(f"Circular proof expansions: {tag}")
        if tag in visited:
            return
        active.add(tag)
        for dependency in graph.get(tag, ()):
            visit(dependency)
        active.remove(tag)
        visited.add(tag)

    for tag in graph:
        visit(tag)
