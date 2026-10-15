"""Publish already-built static files to the GitHub Pages branch, without CI."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = "https://github.com/MingchenXia/Gerby.git"


def git(*arguments, cwd=ROOT, capture=False):
    result = subprocess.run(["git", *arguments], cwd=cwd, check=True, text=True,
                            stdout=subprocess.PIPE if capture else None)
    return result.stdout.strip() if capture else None


def publish():
    site = ROOT / "_site"
    if not (site / ".nojekyll").is_file() or not (site / "collection.json").is_file():
        raise ValueError("Build the complete shared collection before publishing")
    receipt = json.loads((site / "upstream.json").read_text())
    if not receipt["sources"]:
        raise ValueError("Refusing to publish an edition without source revisions")
    temporary = ROOT / "_publish"
    temporary.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=temporary) as directory:
        checkout = Path(directory)
        exists = git("ls-remote", "--heads", REPOSITORY, "refs/heads/gh-pages", capture=True)
        if exists:
            git("clone", "--depth=1", "--single-branch", "--branch", "gh-pages", REPOSITORY, directory)
        else:
            git("init", "-b", "gh-pages", cwd=checkout)
            git("remote", "add", "origin", REPOSITORY, cwd=checkout)
        for item in checkout.iterdir():
            if item.name != ".git":
                shutil.rmtree(item) if item.is_dir() else item.unlink()
        shutil.copytree(site, checkout, dirs_exist_ok=True)
        git("add", "--all", cwd=checkout)
        unchanged = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=checkout).returncode == 0
        if unchanged:
            print("Published files are already current.")
            return
        git("commit", "-m", "Publish shared Gerby reference [skip ci]", cwd=checkout)
        git("-c", "http.version=HTTP/1.1", "-c", "http.postBuffer=104857600", "push", "origin", "HEAD:gh-pages", cwd=checkout)
        print("Published prebuilt files to gh-pages. GitHub Pages will serve the update.")


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__).parse_args()
    publish()
