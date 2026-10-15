"""Export the reviewed whole-book Helms supplement, preserving published tags."""
from pathlib import Path
import re
import sys

from common import configure, export, uncomment

SLUG = "classical-potential-theory"
TOPIC = "Kelvin transforms and half-space potentials"
ENTRYPOINT = "contributions/classical-potential-theory.tex"
RESULTS = ("R0005", "R0006", "R0007", "R0001", "R0002", "R0003",
           "R0008", "R0009", "R0010", "R0011", "R0013", "R0012",
           "R0014", "R0015", "R0016", "R0018", "R0019", "R0017",
           "R0020", "R0021", "R0022", "R0023", "R0024", "R0026",
           "R0027", "R0028", "R0025", "R0029", "R0030")
FRAGMENTS = {f"results/{result}/proof": f"results/{result}/proof.tex" for result in RESULTS}


def result_topic(result):
    number = int(result[1:])
    if number <= 3:
        return TOPIC
    if number <= 11:
        return "Classical harmonic analysis"
    if number in {12, 13, 14, 15, 16, 20}:
        return "Green functions and potentials"
    if number in {17, 18, 19, 24}:
        return "Polar sets, capacity and sweeping"
    if number in {29, 30}:
        return "Green energy and Martin boundaries"
    return "Perron theory and fine boundary limits"


def selected_text(source, name):
    path = (source / name).resolve()
    if not path.is_relative_to(source.resolve()) or not path.is_file():
        raise ValueError(f"Missing or unsafe selected literature file: {name}")
    return uncomment(path.read_text())


def prepare_article(source):
    article = selected_text(source, ENTRYPOINT)
    preamble, body = article.split(r"\begin{document}", 1)
    if (r"\documentclass[11pt,a4paper]{article}" not in preamble
            or r"\newtheorem{theorem}{Theorem}[section]" not in preamble):
        raise ValueError("Review the literature article class and theorem numbering")
    used = []

    def include(match):
        name = match[1]
        if name not in FRAGMENTS or name in used:
            raise ValueError(f"Unreviewed literature input: {name}")
        used.append(name)
        return selected_text(source, FRAGMENTS[name])

    body = re.sub(r"\\(?:input|include)\s*\{([^}]+)\}", include, body)
    if used != list(FRAGMENTS) or re.search(r"\\(?:input|include)\b", body):
        raise ValueError("Review the selected literature input graph")
    scope = r"\section*{Scope, attribution and conventions}"
    if body.count(scope) != 1:
        raise ValueError("Review the literature scope and conventions heading")
    # This introduction supersedes the first article's prerequisites. Retain
    # its published source label so every existing tag URL still resolves.
    body = body.replace(scope, scope + r"\label{sec:helms-prerequisites}")
    body = body.replace(r"\maketitle", "").replace(r"\tableofcontents", "")
    body = re.sub(r"\\(?:bibliographystyle|bibliography)\{[^}]+\}", "", body)
    # Keep the article's section/theorem numbers and prerequisite prose. Only
    # layout is replaced; bibliography is exported separately by the renderer.
    theorem_names = "lemma proposition corollary definition example remark".split()
    environments = "\n".join(rf"\newtheorem{{{name}}}[theorem]{{{name.title()}}}" for name in theorem_names)
    return (r"\documentclass{article}" "\n"
            r"\usepackage{amsmath,amssymb,hyperref}" "\n"
            r"\newtheorem{theorem}{Theorem}[section]" "\n"
            + environments + "\n" + r"\begin{document}" + "\n" + body)


def assign_topics(source, records):
    labels = {"sec:helms-prerequisites": "Conventions"}
    for result in RESULTS:
        text = selected_text(source, f"results/{result}/proof.tex")
        for label in re.findall(r"\\label\{([^}]+)\}", text):
            if label in labels:
                raise ValueError(f"Duplicate literature label: {label}")
            labels[label] = result_topic(result)
    if {record["label"] for record in records} != labels.keys():
        raise ValueError("Review complete literature label and subject coverage")
    for record in records:
        record["topic"] = labels[record["label"]]
    return records


def setup():
    configure(SLUG, "Classical potential theory: supplements after Helms",
              "https://github.com/MingchenXia/Gerby-Literature",
              author="Gerby Literature preparation after L. L. Helms",
              bibliography="contributions/classical-potential-theory.bib")


if __name__ == "__main__":
    setup()
    export(Path(sys.argv[1]), Path(sys.argv[2]), prepare=prepare_article, transform=assign_topics)
