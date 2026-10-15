# Gerby

A shared mathematical reference combining definitions, theorems, and proofs from contributing texts. Browse by **shared chapter or permanent tag**, search across all content, and see each statement's formalization status.

**[Read Gerby](https://mingchenxia.github.io/Gerby/)** · [Source contributions](https://mingchenxia.github.io/Gerby/sources/)

## Content and organization

The collection integrates four sources, tracking their `main` branches:

- [Foundations of pluripotential theory](https://github.com/MingchenXia/foundations-of-pluripotential-theory).
- [Singularities in global pluripotential theory (SGPT)](https://github.com/MingchenXia/SGPT).
- **Singularities in Hermitian pluripotential theory**, from the author's private `non-kahler-pluripotential-theory` repository. Only the authorized reading edition is published; the source repository remains private.

- **Classical potential theory: supplements after Helms**, from `Gerby-Literature/main`, including the merged `codex/helms-whole-book` work. The supplement follows the recorded complete-book review and includes harmonic boundary limits, Green functions, polar sets, sweeping, Perron theory, the Wiener criterion, energy and Martin boundaries, with reconstructed proofs and attribution. The retained scan and research records stay private.

Only each manuscript's active input graph is included. Excluded drafts and private research material are not exported.

The collection has **21 shared chapters**, ordered by mathematical subject across the books, with 78 more specific subjects inside them. Chapter 1 contains only conventions; manuscript prefaces, acknowledgments, introductions, and part overviews are omitted. Original statement numbering is retained; source metadata and exact revisions are collected under Sources rather than repeated beside every statement. The chapter structure is curated independently of the original tables of contents. Existing book and topic URLs continue to resolve.

Reviewed duplicates have one canonical entry and one search result. Alternative source wording, proofs, and formalization badges remain accessible within that entry. Numbered clauses stay inside their parent statements, retaining their own tags and badges. `collection.json` records each reviewed statement fingerprint: a changed statement requires a new review before it can be merged again. Results with different hypotheses remain separate.

All interface text and project documentation are in English. The source texts and formal proofs remain in their original repositories and retain their licenses.

The reading interface follows the Stacks Project: compact navigation, a breadcrumb trail, and a reading column with page tools at the side. It adapts to computers, tablets, and phones; long equations and tables scroll inside the reading column.

- Chapter pages list **sections only**. Section pages show the full text, definitions, theorems, equations, and proofs directly, with individual entry permalinks. Nested statements and equations are displayed once rather than repeated as separate list items.
- **Previous** and **Next** links appear above and below each page, following one complete order through chapters, sections, and statements. Breadcrumbs return directly to the containing section or chapter.
- Statement headings use manuscript names and numbers, such as **Definition 1.2.3**. Internal LaTeX labels are searchable identifiers and are never shown as reader headings. Permanent tags are hidden initially and can be revealed with **Show tags**.
- Search accepts mathematical subjects, phrases, statement numbers, or tags. An exact unambiguous tag opens its entry directly. Each page also has a permalink and a copyable BibTeX citation.

The color palette follows the [Stacks Project](https://stacks.math.columbia.edu/): white pages, black text, blue links (`#1d5cb4`), and warm gray navigation (`#d9d8d1` and `#edece6`). Theme colors are defined in `site/assets/book.css` and shared across the collection.

## Comments

Every reading page has its own public comment thread, backed by [GitHub Discussions](https://github.com/MingchenXia/Gerby/discussions). The inline [giscus](https://giscus.app/) panel lets readers sign in with GitHub, comment, reply, and react. Readers can also open or start the same page's discussion directly on GitHub. The maintainer moderates the threads there. No credentials are included in the site.

GitHub Discussions is enabled. Inline comments require the [giscus GitHub App](https://github.com/apps/giscus) to be installed for **only `MingchenXia/Gerby`**. `comments.json` holds the public repository and discussion-category IDs; `giscus.json` limits the allowed site origins. Threads use stable page identifiers, so changing a heading or manuscript revision does not create a new thread. A GitHub link remains available when the embedded service cannot load. See [comment setup and moderation](documentation/comments.md).

## Formalization badges

Every tagged statement displays a badge:

| Badge | Meaning |
| --- | --- |
| Not recorded | No formalization mapping has been supplied. |
| Pending verification | A proof repository is linked, but the current revision has not been verified. |
| ✓ 0 sorry | The mapped declaration at the linked exact revision passed the recorded proof and axiom checks. |

No formalization repositories have been supplied yet, so the collection currently shows **Not recorded**. A repository link alone cannot produce a verified badge. New proof commits revert to pending until verified. See [the evidence requirements](documentation/formalizations.md).

## Adding content

Supply a source repository link and, when available, its formalization repository. Integration records the active LaTeX entry point, stable source labels, shared chapters, and the correspondence with formal declarations.

- `books.json` registers contributing source repositories and tracked revisions.
- `collection.json` defines the shared chapters, subject assignments, and reviewed canonical entries.
- `formalizations.json` records declaration mappings and verification evidence.
- `proofs/registry.json` and its HTML fragments add proofs and necessary qualifications to the shared reading edition. Statement and original-proof fingerprints require review when upstream mathematics changes; see [proof expansion review](documentation/proof-expansions.md).
- `adapters/` exports each source through the pinned official Gerby renderer.
- [Deployment and updates](documentation/deployment.md) documents the export and publishing contracts.

## Updates without CI

GitHub Actions CI is disabled at the author's request. Builds run locally, and `scripts/publish.py` commits the checked static output to `docs/` on `main`. GitHub Pages serves that folder at `/Gerby/`. The repository uses a single branch; the former `gh-pages` history is merged into `main`. Authored project documentation lives in `documentation/`.

Updates are **on request only**. There is no scheduled monitoring or publication. When the author asks to update Gerby, `scripts/update.py` checks all registered source and formalization revisions, rebuilds changed content, checks internal links, and verifies the published revision. Publication commits that change only generated `docs/` files do not trigger another rebuild on the next requested check. The former hourly automation has been removed.

## Local build and publication

Requires Python 3.11+, Git, Node.js, npm, XeLaTeX with the `standalone` and TikZ packages, and Poppler (`pdftocairo`); publication also uses the authenticated GitHub CLI (`gh`). The private Hermitian source requires authenticated read access; credentials stay outside the project.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
npm ci --prefix vendor --ignore-scripts --no-audit --no-fund
.venv/bin/python -m unittest discover -s tests
node --test tests/*.test.mjs
.venv/bin/python scripts/build.py --fetch
python3 -m http.server 8000 --directory _site
```

Open `http://localhost:8000`. With authorized push access to `MingchenXia/Gerby`, publish a completed build or check for upstream updates:

```sh
.venv/bin/python scripts/publish.py
.venv/bin/python scripts/update.py
```

The on-request updater requires a clean `main` checkout and uses a fast-forward pull. It never overwrites uncommitted edits. To preview an existing source checkout, set `FOUNDATIONS_SOURCE_DIR`, `SGPT_SOURCE_DIR`, `NON_KAHLER_SOURCE_DIR`, or `LITERATURE_SOURCE_DIR` to its absolute path before building; requested update checks ignore preview overrides and fetch the tracked sources afresh.

## Gerby on GitHub Pages

[Gerby](https://gerby-project.github.io/) provides the LaTeX-to-tag renderer used here. This static export includes chapters and sections, individual entries, full-text search, citations, formalization badges, and self-hosted MathJax. GitHub Pages serves the reading edition; comments persist in GitHub Discussions through giscus. The Flask/database backend is not required.
