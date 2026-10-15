"""Publish locally built static files from main/docs, without CI."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import time
from urllib.error import URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = "https://github.com/MingchenXia/Pome.git"
PUBLIC_RECEIPT = "https://mingchenxia.github.io/Pome/upstream.json"


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
        print("The public Pome site is current.")
        return
    # Native Pages delivery only; manuscript builds and tests remain local.
    subprocess.run(["gh", "api", "-X", "POST", "repos/MingchenXia/Pome/pages/builds"], check=True, cwd=ROOT)
    for _ in range(24):
        if deployment_current(receipt):
            print("Verified the new edition at https://mingchenxia.github.io/Pome/")
            return
        time.sleep(15)
    raise RuntimeError("Files are uploaded, but the public Pages revision is not current yet; retry publication")


def git(*arguments, cwd=ROOT, capture=False):
    result = subprocess.run(["git", *arguments], cwd=cwd, check=True, text=True,
                            stdout=subprocess.PIPE if capture else None)
    return result.stdout.strip() if capture else None


def project_unchanged(revision, cwd=ROOT):
    """Generated publication commits must not look like new source changes."""
    if not isinstance(revision, str) or not re.fullmatch(r"[a-f0-9]{40}", revision):
        return False
    return subprocess.run(["git", "diff", "--quiet", revision, "HEAD", "--", ".", ":(exclude)docs"],
                          cwd=cwd, stderr=subprocess.DEVNULL).returncode == 0


def stage_publication(site, destination):
    if not all((site / filename).is_file() for filename in (".nojekyll", "collection.json", "upstream.json")):
        raise ValueError("Build the complete shared collection before publishing")
    receipt = json.loads((site / "upstream.json").read_text())
    if not receipt.get("sources"):
        raise ValueError("Refusing to publish an edition without source revisions")
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(site, destination)
    return receipt


def publish():
    site = ROOT / "_site"
    if not (site / "upstream.json").is_file():
        raise ValueError("Build the complete shared collection before publishing")
    receipt = json.loads((site / "upstream.json").read_text())
    if git("branch", "--show-current", capture=True) != "main":
        raise ValueError("Publication requires the main branch")
    if git("status", "--porcelain", capture=True):
        raise ValueError("Commit or save local Pome changes before publication")
    remote = git("remote", "get-url", "origin", capture=True).removesuffix(".git").replace("git@github.com:", "https://github.com/")
    if remote != REPOSITORY.removesuffix(".git"):
        raise ValueError("The publication remote does not match the Pome repository")
    git("pull", "--ff-only", "origin", "main")
    if not project_unchanged(receipt.get("publishing_commit")):
        raise ValueError("The project changed after this build; rebuild before publication")
    stage_publication(site, ROOT / "docs")
    git("add", "--all", "--", "docs")
    unchanged = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=ROOT).returncode == 0
    if not unchanged:
        git("commit", "-m", "Publish shared Pome reference from main/docs [skip ci]")
    git("-c", "http.version=HTTP/1.1", "-c", "http.postBuffer=104857600", "push", "origin", "main")
    print("Prebuilt files are published in main/docs.")
    request_deployment(receipt)


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__).parse_args()
    publish()
