"""Publish already-built static files to the GitHub Pages branch, without CI."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
from urllib.error import URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = "https://github.com/MingchenXia/Gerby.git"
PUBLIC_RECEIPT = "https://mingchenxia.github.io/Gerby/upstream.json"


def deployment_current(receipt):
    try:
        request = Request(PUBLIC_RECEIPT + "?check=" + str(time.time_ns()), headers={"Cache-Control": "no-cache"})
        with urlopen(request, timeout=20) as response:
            deployed = json.load(response)
        return all(deployed.get(key) == receipt.get(key) for key in ("publishing_commit", "sources"))
    except (URLError, OSError, ValueError):
        return False


def request_deployment(receipt):
    if deployment_current(receipt):
        print("The public Gerby site is current.")
        return
    # Native Pages deployment only; no manuscript build or CI workflow is run.
    subprocess.run(["gh", "api", "-X", "POST", "repos/MingchenXia/Gerby/pages/builds"], check=True, cwd=ROOT)
    for _ in range(24):
        if deployment_current(receipt):
            print("Verified the new edition at https://mingchenxia.github.io/Gerby/")
            return
        time.sleep(15)
    raise RuntimeError("Files are uploaded, but the public Pages revision is not current yet; retry publication")


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
            request_deployment(receipt)
            return
        git("commit", "-m", "Publish shared Gerby reference [skip ci]", cwd=checkout)
        git("-c", "http.version=HTTP/1.1", "-c", "http.postBuffer=104857600", "push", "origin", "HEAD:gh-pages", cwd=checkout)
        print("Published prebuilt files to gh-pages.")
        request_deployment(receipt)


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__).parse_args()
    publish()
