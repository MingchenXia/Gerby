"""Export only the selected Helms article from the private literature repository."""
from pathlib import Path
import re
import sys

from common import configure, export, uncomment

SLUG = "classical-potential-theory"
TOPIC = "Kelvin transforms and half-space potentials"
ENTRYPOINT = "integrations/R0001/book.tex"
FRAGMENTS = {
    "kelvin": "results/R0001/proof.tex",
    "halfspace": "results/R0002/proof.tex",
    "bounded-data": "results/R0003/proof.tex",
}


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
    body = body.replace(r"\maketitle", "")
    body = re.sub(r"\\(?:bibliographystyle|bibliography)\{[^}]+\}", "", body)
    # Keep the article's section/theorem numbers and prerequisite prose. Only
    # layout is replaced; bibliography is exported separately by the renderer.
    return (r"\documentclass{article}" "\n"
            r"\usepackage{amsmath,amssymb,hyperref}" "\n"
            r"\newtheorem{theorem}{Theorem}[section]" "\n"
            r"\begin{document}" "\n"
            r"\section*{Prerequisites and conventions}\label{sec:helms-prerequisites}" "\n"
            + body)


def setup():
    configure(SLUG, "Classical potential theory: Kelvin transforms and half-spaces",
              "https://github.com/MingchenXia/Gerby-Literature",
              author="AI-assisted exposition after L. L. Helms",
              bibliography="integrations/R0001/references.bib", topic=TOPIC)


if __name__ == "__main__":
    setup()
    export(Path(sys.argv[1]), Path(sys.argv[2]), prepare=prepare_article)
