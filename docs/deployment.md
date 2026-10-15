# Deployment and updates

The public project is [MingchenXia/Gerby](https://github.com/MingchenXia/Gerby), served at [mingchenxia.github.io/Gerby/](https://mingchenxia.github.io/Gerby/). The homepage remains at its existing address.

## Publication without GitHub Actions CI

The project builds locally and publishes prebuilt files to `gh-pages`, configured as the GitHub Pages source at its root. `.nojekyll` prevents a Jekyll transformation. The former Actions build workflow has been removed and disabled; no source build or CI workflow is scheduled on GitHub.

Run `python scripts/build.py --fetch`, then `python scripts/publish.py` in the prepared virtual environment. The publisher validates that a complete collection and source receipt exist, creates a temporary checkout of `gh-pages`, replaces its generated files, and pushes a normal commit. It never force-pushes. GitHub's native Pages service publishes those static files.

The hourly local Codex automation runs `scripts/update.py`. It fast-forwards a clean `main`, compares every tracked source and formalization revision against the published receipt, and rebuilds only when the project or an upstream revision changes. Dependencies are reinstalled only when their pinned manifests change. Publication occurs only after a successful export and complete local-link check. Failed builds leave the deployed edition intact. Network/authentication failures are reported by the automation; unchanged state stays quiet. The computer and Codex must be available for these checks.

The published `upstream.json` contains the build time, publishing-project commit, and exact source commits. `/sources/` retains attribution and revision information for readers. A GitHub Actions run is not required to supply formal proof evidence: a committed verification report is also accepted.

## Shared collection

Sources are registered in `books.json`; their status becomes `published` when an adapter is ready. The current public source tracks `MingchenXia/foundations-of-pluripotential-theory` on `main`. HTTPS fetching requires no deploy key or private-source Actions secret.

Each adapter receives `SOURCE_DIRECTORY OUTPUT_DIRECTORY` and exports:

- `entries.json`: source tag, label/aliases, semantic title, kind, topic, section flag and Gerby HTML fragment;
- `tags.json`: complete tag-to-page inventory;
- `edition.json`: exact source commit and edition metadata;
- `references.json`: cited key, bibliographic identity and formatted HTML;
- temporary reading/tag pages used to validate complete source tag and badge coverage.

`scripts/collection.py` combines exports into `/topics/`, `/entries/`, `/tag/TAG/`, `/references/` and `/sources/`. Source-specific pages become redirects, preserving old permalinks. Source records are internal provenance, not separate reading collections. Search includes every contribution's text and aliases.

Uncurated global tags are twelve uppercase SHA-256 characters derived from `(source slug, source label)`, preventing collisions between identical labels in different texts. `collection.json` reserves canonical tags and can explicitly merge labels from several sources into one entry. Each variant retains its own attribution and formalization marker. The six initially published tags retain their original eight-character identifiers. Topic slugs are based on subject titles rather than source titles. Topic membership and canonical entry titles can be curated independently of the books' chapter numbering.

## Foundations adapter

The adapter follows only the input graph activated by `book.tex`. It uses the pinned official Gerby renderer, with a web preamble preserving mathematical macros and the shared section theorem counter. It supports clever references, labelled equation rows and source-label aliases. Math source is HTML-escaped before parsing, preserving inequalities and preventing malformed markup.

Unknown commands, missing labels on numbered headings/theorems, missing fragments, missing badge markers, tag collisions and broken local links fail the build. Bibliography exports contain only entries cited by the active manuscript. Mathematics renders with self-hosted MathJax.

For a local preview, `FOUNDATIONS_SOURCE_DIR` can select an existing checkout. Its repository identity and exact commit are checked. The scheduled updater explicitly removes preview overrides before fetching sources, so a stale local checkout cannot silently become an automatic deployment.

## Formalization status

Badge records are keyed by source and source tag, even when several contributions share one canonical entry. Each source variant has a `data-gerby-book` wrapper and each statement a `data-gerby-tag` marker. This keeps evidence attached to the correct informal statement.

Proof repositories are checked on the same local schedule. If the tracked proof commit differs from the verified commit, the public record is downgraded to **Pending verification**. A prover-specific check and correspondence review are still required before assigning **0 sorry**. Registry validation checks evidence consistency; it does not execute a theorem prover. See [formalizations.md](formalizations.md).
