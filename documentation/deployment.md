# Deployment and updates

The public project is [MingchenXia/Gerby](https://github.com/MingchenXia/Gerby), served at [mingchenxia.github.io/Gerby/](https://mingchenxia.github.io/Gerby/). The homepage remains at its existing address.

## Publication without GitHub Actions CI

The project builds locally and publishes prebuilt files to `docs/` on `main`, configured as the GitHub Pages source. Authored project documentation is kept separately in `documentation/`. The former `gh-pages` branch is merged into `main`; its history and generated content are retained there. `.nojekyll` prevents a Jekyll transformation. The former Actions build workflow has been removed and disabled; no source build or CI workflow is scheduled on GitHub.

Run `python scripts/build.py --fetch`, then `python scripts/publish.py` in the prepared virtual environment. The publisher validates that a complete collection and source receipt exist, requires a clean `main` checkout, fast-forwards from the remote, checks that source files still match the built revision, replaces only `docs/`, and pushes a normal commit. It never force-pushes. The publisher explicitly requests GitHub's native Pages deployment and waits until the public revision receipt matches the uploaded edition. This also retries an uploaded edition whose earlier deployment did not finish. Publishing requires the authenticated GitHub CLI (`gh`).

GitHub performs [native Pages delivery](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site) of the prebuilt folder; no custom Actions workflow builds the books or runs tests.

The author requests updates manually; no regular checks or automation remain. On request, run `scripts/update.py`. It fast-forwards a clean `main`, compares every tracked source and formalization revision against the published receipt, and rebuilds only when the project or an upstream revision changes. Dependencies are reinstalled only when their pinned manifests change. Publication occurs only after a successful export and complete local-link check. Failed builds leave the deployed edition intact. Network/authentication failures are reported to the author; unchanged state stays quiet. These checks run locally when requested.

The published `upstream.json` contains the build time, the project commit used to build the edition, and the exact source commits. The later commit that stores the generated site may have a different hash. Freshness checks compare project files against the recorded build commit while excluding generated `docs/`; a publication commit alone therefore does not cause an endless rebuild cycle. `/sources/` retains attribution and revision information for readers. A GitHub Actions run is not required to supply formal proof evidence: a committed verification report is also accepted.

## Shared collection

Sources are registered in `books.json`; their status becomes `published` when an adapter is ready. The current sources track the main branches of Foundations, SGPT and the private Hermitian book. Public sources use HTTPS; the private source uses the local authenticated Git credential helper. No credentials or private research files are exported.

Each adapter receives `SOURCE_DIRECTORY OUTPUT_DIRECTORY` and exports:

- `entries.json`: source tag, label/aliases, semantic title, kind, original subject, parent label, section flag, statement TeX fingerprint input, and separate statement/proof HTML fragments;
- `tags.json`: complete tag-to-page inventory;
- `edition.json`: exact source commit and edition metadata;
- `references.json`: cited key, bibliographic identity and formatted HTML;
- `assets/`: illustrations referenced by the active manuscript, including locally rendered vector diagrams;
- temporary reading/tag pages used to validate complete source tag and badge coverage.

`scripts/collection.py` combines exports into `/chapters/`, `/sections/`, `/entries/`, `/tag/TAG/`, `/references/`, `/comments/`, `/search/`, and `/sources/`. Every included source subject must be explicitly assigned to one shared chapter. The current 21-chapter order follows mathematical dependencies across the books, with 72 independently addressable sections. Chapter pages contain section links, not statement lists. `/topics/` permalinks redirect to the corresponding sections. Source-specific pages become redirects, preserving old permalinks. Source records are internal provenance, not separate reading collections. Search includes every retained contribution's text and aliases; visible headings use the manuscript's numbered titles instead of names derived from internal labels.

`scripts/reader.py` defines one reading sequence, including each chapter, its sections, and every canonical entry exactly once. Each page has reciprocal Previous/Next links at both ends, contextual breadcrumbs, a permalink, a BibTeX citation, and a comment panel. `navigation.json` records this order. Tags remain stable and are hidden in reader lists until requested. Serialized TeX label commands are stripped from presentation formulas after cross-references have been resolved.

Section pages are continuous reading pages. They retain source prose between statements and display proofs in full. The renderer tracks source root identifiers so a statement or equation already contained in a larger fragment is not printed a second time. For a reviewed duplicate, the preferred source version appears once; the other occurrence links to the shared entry, where every source version remains available. The build checks complete section coverage. Mathematics on these longer pages is typeset as it approaches the viewport, using the bundled MathJax lazy extension.

Book-origin captions and generic section descriptions are omitted from the reading pages. Bibliographic citations and the underlying source and badge metadata remain. Guarded proof additions in `proofs/` expand external references in both individual entries and continuous sections; see [proof expansion review](proof-expansions.md). Completed changes are proposed in PRs and regularly merged and deployed after local checks, without CI.

Chapter 1 contains only conventions. `collection.json` lists omitted front matter in `excluded_topics`; these subjects and their entries are excluded from the reading order, search, and collection listings. References to omitted material retain their text without a link, and its old section and entry URLs redirect to the table of contents. Source tag inventories retain omitted tags with `canonical_tag: null`.

Comments use [GitHub Discussions through giscus](comments.md), independently of CI and site builds. Enabling Discussions and installing the app for this public repository are required for the embedded form. Static GitHub links allow readers to reach the page's discussion when embedding fails. A published site receipt verifies the reading edition, not the health of the external comments service; verify the actual comment form separately.

Uncurated global tags are twelve uppercase SHA-256 characters derived from `(source slug, source label)`, preventing collisions between identical labels in different texts. `collection.json` reserves canonical tags and can explicitly merge labels from several sources into one entry. Each variant retains its own attribution and formalization marker. The six initially published tags retain their original eight-character identifiers. Topic slugs are based on subject titles rather than source titles. Chapter order, subject membership, and canonical entry titles are curated independently of the books' chapter numbering. Repeated definitions may retain distinct scope explanations in their source versions; theorem hypotheses are never erased to force a merge.

Reviewed duplicate members carry a SHA-256 fingerprint of their mathematical statement (ignoring only labels, index metadata, and whitespace). Changes or missing members fail the build and require a fresh review. Unreviewed exact duplicate definitions/results also fail publication. Repeated equations are unified only inside an already unified parent statement. Numbered list clauses are indexed through their parent when its HTML contains the original clause anchor. Their permalinks, search aliases, and badges remain available. `deduplication.json` publishes the group audit. Alternative source versions are collapsed initially and open automatically when a clause permalink targets them.

## Manuscript adapters

The adapters follow only the input graph activated by `book.tex`. They use the pinned official Gerby renderer, with a web preamble preserving mathematical macros and the shared section theorem counter. They support clever references, optional label types, underscores in labels, labelled equation rows, source-label aliases, equation citations, footnotes, tables, and figures. The two added books use the same shared section theorem counter. The private Hermitian source is read from its `book/` subtree and exports only its active reading content; its working research draft is attributed as such. Math source is HTML-escaped before parsing, preserving inequalities and preventing malformed markup.

Unknown commands, missing fragments, missing badge markers, tag collisions and broken local links fail the build. Foundations requires explicit labels on numbered headings and theorems. The added sources retain their existing labels; unlabelled headings/results receive a source-content identifier without editing the manuscript. Bibliography exports contain only entries cited by the active manuscript, deduplicated by DOI or normalized title/year/author identity. TikZ diagrams are compiled locally with shell escape disabled and exported as SVG; no full book PDF rebuild is involved. References inside formulas are resolved against the source label inventory before being mapped to canonical entry links. Unresolved references and internal parser object names fail publication. Shared assets carry content revisions so returning readers load updated rendering code. Source image paths must stay inside the manuscript directory. Internal image links are checked along with page links and fragments. Mathematics renders with self-hosted MathJax.

For a local preview, `FOUNDATIONS_SOURCE_DIR`, `SGPT_SOURCE_DIR`, and `NON_KAHLER_SOURCE_DIR` can select existing checkouts. Its repository identity and exact commit are checked. The on-request updater explicitly removes preview overrides before fetching sources, so a stale preview checkout cannot silently become a deployment.

## Formalization status

Badge records are keyed by source and source tag, even when several contributions share one canonical entry. Each source variant has a `data-gerby-book` wrapper and each statement a `data-gerby-tag` marker. This keeps evidence attached to the correct informal statement.

Proof repositories are checked on the same requested update. If the tracked proof commit differs from the verified commit, the public record is downgraded to **Pending verification**. A prover-specific check and correspondence review are still required before assigning **0 sorry**. Registry validation checks evidence consistency; it does not execute a theorem prover. See [formalizations.md](formalizations.md).

## Integration audit (15 October 2026)

The reading edition includes 6,330 source tags: 1,190 from Foundations (`da2be417c7b38b386d0b688251cf4978df94d682`), 1,972 from SGPT (`8d91069847dd7aa76034e6a97dddc7dba191437a`), and 3,168 from the private Hermitian draft (`9d4f324ca55f5db30f60825aba5733ecd24a42b5`). The source repositories were not edited for this integration.

The collection contains 5,896 canonical entries in 21 shared chapters. Twelve reviewed groups unify fourteen repeated definitions/results; three identical nested equations are also unified within those groups. The definition groups cover plurisubharmonic functions, analytic singularities, quasi-equisingular approximation, rooftops, multiplier ideals, pluripolarity, plurifine topology, and ordinary singularity order. Four SGPT main-text/appendix repetitions cover almost semigroups and Okounkov bodies. Where definitions use different scopes, the entry explains the distinction and retains every source version. In addition, 417 numbered clauses remain in their parent statements with direct anchors and independent badge markers.

The integration preserves 28 SVG diagrams, three source PNGs, footnotes, tables, and 364 cited bibliographic identities. Local validation covers the parser regressions (optional labels, underscores, dotless math symbols), stale duplicate reviews, distinct hypotheses, clause anchors, chapter coverage, image paths, every internal link/fragment, and badge behavior. A temporary MathJax 3.2.2 checker parsed over 64,000 distinct mathematical excerpts without syntax errors after the web compatibility fixes. This checks rendering syntax, not mathematical validity. No formalization mappings have been supplied.

The hourly Gerby automation was deleted. Updates and source revision checks now run only when requested by the author. No GitHub Actions CI was run.

## Single-branch consolidation

The `gh-pages` history is merged into `main`, with its complete validated reading edition relocated byte for byte into `docs/`. The edition receipt continues to identify the commit that actually rendered that content. This consolidation does not refresh the source books. The next requested update may rebuild once to record the changed publishing infrastructure; later generated-only publication commits are ignored when checking project freshness.
