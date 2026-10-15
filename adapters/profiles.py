"""Prepare the supplied svmono manuscripts for the shared Gerby renderer."""
from hashlib import sha256
from pathlib import Path
import re
import shutil
import subprocess

from common import active_text, uncomment

ROOT = Path(__file__).resolve().parents[1]


def prepare(source, slug, assets, theorems):
    active = active_text(source)
    before, body = active.split(r"\begin{document}", 1)
    if r"\documentclass[envcountsect]{svmono}" not in before:
        raise ValueError(f"{slug}: unexpected source class or theorem counter")
    macros = before[before.index(r"\newcommand{\nef}"):before.index(r"\setlist")]
    if slug == "non-kahler-pluripotential-theory":
        macros += before[before.index(r"\newcommand{\HH}"):before.index(r"\hypersetup{pdftitle")]
    body = r"\begin{document}" + body
    body = body.split(r"\backmatter")[0] + r"\end{document}"
    body = body.replace(r"\preface", r"\chapter*{Preface}")
    body = re.sub(r"\\[Ee]xtrachap\{([^}]+)\}", r"\\chapter*{\1}", body)
    body = re.sub(r"\\font\\russianmottofont=[^\n]+", "", body).replace(r"\russianmottofont", "")
    body = re.sub(r"\\(?:printindex|bibliographystyle\{[^}]+\}|bibliography\{[^}]+\})", "", body)
    # Layout commands do not contribute mathematical content.
    body = body.replace(r"\raggedcolumns", "")
    assets.mkdir(parents=True, exist_ok=True)
    cache = ROOT / "_render_cache" / slug
    cache.mkdir(parents=True, exist_ok=True)

    def graphic(match):
        filename = match[1]
        original = (source / filename).resolve()
        if not original.is_relative_to(source.resolve()) or not original.is_file():
            raise ValueError(f"Missing source illustration: {filename}")
        name = sha256(original.read_bytes()).hexdigest()[:20] + original.suffix.lower()
        shutil.copyfile(original, assets / name)
        return rf"\gerbyimage{{{slug}/{name}}}{{Source illustration}}"

    body = re.sub(r"\\includegraphics(?:\[[^]]*\])?\{([^}]+)\}", graphic, body)

    def diagram(match):
        text = match[0]
        preamble = r"\documentclass[border=4pt]{standalone}" + "\n" + r"\usepackage{amsmath,amssymb,dsfont,tikz-cd}" + "\n" + r"\usetikzlibrary{decorations.pathreplacing,arrows.meta,calc,patterns}" + "\n" + macros
        document = preamble + "\n" + r"\begin{document}" + text + r"\end{document}"
        identifier = sha256(document.encode()).hexdigest()[:20]
        folder = cache / identifier
        folder.mkdir(exist_ok=True)
        vector = folder / "figure.svg"
        if not vector.exists():
            (folder / "figure.tex").write_text(document)
            with (folder / "build.log").open("w") as log:
                result = subprocess.run(["xelatex", "-no-shell-escape", "-interaction=nonstopmode", "-halt-on-error", "figure.tex"], cwd=folder, stdout=log, stderr=subprocess.STDOUT)
            if result.returncode:
                raise ValueError(f"Diagram rendering failed; inspect {folder / 'build.log'}")
            subprocess.run(["pdftocairo", "-svg", str(folder / "figure.pdf"), str(vector)], check=True)
        shutil.copyfile(vector, assets / (identifier + ".svg"))
        return rf"\gerbyimage{{{slug}/{identifier}.svg}}{{Mathematical diagram from the source}}"

    body = re.sub(r"\\begin\{(tikzpicture|tikzcd)\}.*?\\end\{\1\}", diagram, body, flags=re.S)
    environments = r"\newtheorem{theorem}{Theorem}[section]" + "\n"
    environments += "\n".join(rf"\newtheorem{{{name}}}[theorem]{{{name.title()}}}" for name in theorems)
    environments += "\n" + r"\newtheorem*{claim}{Claim}" + "\n"
    return "\\documentclass{book}\n\\usepackage{amsmath,amssymb,hyperref}\n" + environments + macros + body
