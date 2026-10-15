"""Check upstream revisions and publish changed sources locally, without CI."""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys

from publish import deployment_current, request_deployment

ROOT = Path(__file__).resolve().parents[1]


def run(*arguments, capture=False):
    result = subprocess.run(arguments, cwd=ROOT, check=True, text=True,
                            stdout=subprocess.PIPE if capture else None)
    return result.stdout.strip() if capture else None


def current_revision(repository, ref):
    reference = ref or "HEAD"
    matches = run("git", "ls-remote", repository, reference, capture=True).splitlines()
    if len(matches) == 1:
        return matches[0].split()[0]
    if len(reference) == 40 and all(c in "0123456789abcdef" for c in reference):
        return reference
    raise ValueError(f"Cannot resolve an unambiguous upstream revision: {repository} {reference}")


def update(force=False):
    # Never overwrite an editor's uncommitted work or change their branch.
    if run("git", "status", "--porcelain", capture=True):
        raise ValueError("Commit or save local Gerby changes before automatic publication")
    if run("git", "branch", "--show-current", capture=True) != "main":
        raise ValueError("The local updater requires the main branch")
    run("git", "pull", "--ff-only", "origin", "main")
    publishing_commit = run("git", "rev-parse", "HEAD", capture=True)
    books = json.loads((ROOT / "books.json").read_text())["books"]
    proofs = json.loads((ROOT / "formalizations.json").read_text())["entries"]
    keys = {(item["repository"], item.get("ref", "HEAD")) for item in books + proofs}
    revisions = [{"repository": repo, "ref": ref, "commit": current_revision(repo, ref)}
                 for repo, ref in sorted(keys)]
    run("git", "fetch", "origin", "gh-pages")
    receipt = json.loads(run("git", "show", "FETCH_HEAD:upstream.json", capture=True))
    if not force and receipt.get("publishing_commit") == publishing_commit and receipt["sources"] == revisions:
        if deployment_current(receipt):
            print("No changes: the public Gerby collection is current.")
        else:
            request_deployment(receipt)
        return
    requirements = ROOT / "requirements.txt"
    cache = ROOT / "_update"
    cache.mkdir(exist_ok=True)
    dependency_hash = sha256(requirements.read_bytes()).hexdigest()
    stamp = cache / "requirements.sha256"
    if not stamp.exists() or stamp.read_text() != dependency_hash:
        run(sys.executable, "-m", "pip", "install", "-r", str(requirements))
        stamp.write_text(dependency_hash)
    package_hash = sha256((ROOT / "vendor/package-lock.json").read_bytes()).hexdigest()
    npm_stamp = cache / "package-lock.sha256"
    if not npm_stamp.exists() or npm_stamp.read_text() != package_hash or not (ROOT / "vendor/node_modules/mathjax").exists():
        run("npm", "ci", "--prefix", "vendor", "--ignore-scripts", "--no-audit", "--no-fund")
        npm_stamp.write_text(package_hash)
    # Automatic runs always fetch fresh public sources, ignoring preview overrides.
    environment = os.environ.copy()
    environment["GIT_TERMINAL_PROMPT"] = "0"
    for item in books:
        if item.get("checkout_env"):
            environment.pop(item["checkout_env"], None)
    subprocess.run([sys.executable, "scripts/build.py", "--fetch"], cwd=ROOT, env=environment, check=True)
    run(sys.executable, "scripts/publish.py")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="Rebuild even when revisions are unchanged")
    update(parser.parse_args().force)
