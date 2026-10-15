# Gerby

A shared mathematical reference combining definitions, theorems, and proofs from contributing texts. Browse by **topic or permanent tag**, search across all content, and see each statement's formalization status.

**[Read Gerby](https://mingchenxia.github.io/Gerby/)** · [Source contributions](https://mingchenxia.github.io/Gerby/sources/)

## Content and organization

The first source is [Foundations of pluripotential theory](https://github.com/MingchenXia/foundations-of-pluripotential-theory), tracking its public `main` branch. The complete active manuscript is exported, including both parts and the appendices. The earlier Section 1.1-only edition came from the initial seed revision; the source branches have since been consolidated into `main`.

Contributions form one collection of shared topics and global tags. Source titles and original numbering appear as attribution within entries. As more texts are added, `collection.json` can map statements from different sources to the same canonical entry while retaining each version and its proof status. Existing book URLs redirect to the shared entries.

All interface text and project documentation are in English. The source texts and formal proofs remain in their original repositories and retain their licenses.

## Formalization badges

Every tagged statement displays a badge:

| Badge | Meaning |
| --- | --- |
| Not recorded | No formalization mapping has been supplied. |
| Pending verification | A proof repository is linked, but the current revision has not been verified. |
| ✓ 0 sorry | The mapped declaration at the linked exact revision passed the recorded proof and axiom checks. |

No formalization repositories have been supplied yet, so the collection currently shows **Not recorded**. A repository link alone cannot produce a green badge. New proof commits revert to pending until verified. See [the evidence requirements](docs/formalizations.md).

## Adding content

Supply a source repository link and, when available, its formalization repository. Integration records the active LaTeX entry point, stable source labels, shared topics, and the correspondence with formal declarations.

- `books.json` registers contributing source repositories and tracked revisions.
- `collection.json` defines shared topics and explicit cross-source canonical entries.
- `formalizations.json` records declaration mappings and verification evidence.
- `adapters/` exports each source through the pinned official Gerby renderer.
- [Deployment and updates](docs/deployment.md) documents the export and publishing contracts.

## Updates without CI

GitHub Actions CI is disabled at the author's request. Builds run locally, and `scripts/publish.py` commits the checked static output to `gh-pages`. GitHub Pages serves that prebuilt branch at `/Gerby/`.

An hourly local Codex automation checks both this project and the registered upstream repositories. When a revision changes, `scripts/update.py` fetches fresh sources, rebuilds, checks internal links, and publishes. It stays quiet when nothing has changed. This local automation requires the computer and Codex to be available and GitHub authentication to remain valid. It consumes no GitHub Actions CI minutes.

## Local build and publication

Requires Python 3.11+, Git, Node.js, and npm; publication also uses the authenticated GitHub CLI (`gh`). No private-source key is needed for the current public source.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
npm ci --prefix vendor --ignore-scripts --no-audit --no-fund
.venv/bin/python -m unittest discover -s tests
node --test tests/formalization.test.mjs
.venv/bin/python scripts/build.py --fetch
python3 -m http.server 8000 --directory _site
```

Open `http://localhost:8000`. With authorized push access to `MingchenXia/Gerby`, publish a completed build or check for upstream updates:

```sh
.venv/bin/python scripts/publish.py
.venv/bin/python scripts/update.py
```

The updater requires a clean `main` checkout and uses a fast-forward pull. It never overwrites uncommitted edits. To preview an existing source checkout, set `FOUNDATIONS_SOURCE_DIR` to its absolute path before building; automatic updates ignore that preview override and fetch public sources afresh.

## Gerby on GitHub Pages

[Gerby](https://gerby-project.github.io/) provides the LaTeX-to-tag renderer used here. This static export includes topic browsing, individual entries, full-text search, cited references, formalization badges, and self-hosted MathJax. GitHub Pages does not run the Flask/database backend, so accounts and server-side comments are not included.
