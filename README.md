# Gerby

A public library of online books, with a formalization status beside each theorem or tag.

**Website: [mingchenxia.github.io/Gerby/](https://mingchenxia.github.io/Gerby/)**

This repository hosts the catalogue and the publishing infrastructure. Book sources and formal proofs stay in their original GitHub repositories.

## Current state

The catalogue publishes the active draft of **Foundations of pluripotential theory**. Its private source repository stays private; the public artifact contains only the generated reading edition. No formalization repositories have been supplied yet, so its tags show **Not recorded**.

## Adding books and formalizations

Supply the GitHub link for each book. When available, also supply its formalization repository. The integration records the book's LaTeX entry point, permanent tags, and the correspondence between tags and formal declarations.

- `books.json` lists books and their source repositories.
- `formalizations.json` maps a book and tag to a formalization repository and verification evidence.
- `adapters/` contains source-specific conversion scripts, added when real books are supplied.
- [Deployment](docs/deployment.md) explains the publishing and update process.
- [Formalization badges](docs/formalizations.md) defines the badge states and integration contract.

All public text is in English.

## Automatic updates

The Pages workflow publishes on every push to `main`, checks registered upstream repositories hourly, and supports manual runs and `repository_dispatch` events of type `source-updated`. Each scheduled run fetches current source revisions and rebuilds all configured books. A source repository can optionally dispatch an event for faster updates.

Formalization badges are tied to exact commits. When an upstream formalization moves beyond its verified commit, the published badge becomes **Pending verification** until that revision is checked. A repository link alone never produces a **0 sorry** badge.

## Local preview

Requires Python 3.11+, Git, and Node.js 22+. Install the pinned renderer and self-hosted mathematics assets, then provide a local checkout of the private book:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
npm ci --prefix vendor --ignore-scripts
.venv/bin/python -m unittest discover -s tests
node --test tests/formalization.test.mjs
export FOUNDATIONS_SOURCE_DIR=/absolute/path/to/foundations-of-pluripotential-theory
.venv/bin/python scripts/build.py --fetch
python3 -m http.server 8000 --directory _site
```

Open `http://localhost:8000`. CI checks out the current book revision with a repository-specific read-only deploy key before running the same build. Published books always require a fresh source checkout.

## Gerby and GitHub Pages

[Gerby](https://gerby-project.github.io/) converts labelled LaTeX into an online, tag-based view. Its full website runs Flask with SQLite. GitHub Pages serves static files, so this project will publish static book editions prepared by source-specific Gerby adapters. Server-side comments, accounts, and Gerby's database-backed search require a separate backend; they are not provided by the current static catalogue.

Original books and proofs retain their upstream licenses. This repository does not change their licensing or redistribute any books before they are integrated.
