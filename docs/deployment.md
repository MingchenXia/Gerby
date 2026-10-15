# Deployment and updates

The public repository is `MingchenXia/Gerby`; its GitHub Pages project URL is `https://mingchenxia.github.io/Gerby/`. The existing homepage remains at its current address.

## Publishing

The workflow `.github/workflows/pages.yml` builds a static artifact and deploys it with the official GitHub Pages actions. It runs on:

- pushes to `main`;
- an hourly schedule, at minute 17;
- manual workflow runs;
- `repository_dispatch` events with type `source-updated`.

GitHub schedules can be delayed. For an immediate update, run the workflow manually or dispatch an event from an authorized source repository. A failed build does not replace the last successful deployment. GitHub may disable scheduled workflows after a long period of repository inactivity; a push or manual re-enabling restores them.

## Book integration

The first registered book is **Foundations of pluripotential theory**, tracking the `main` branch of its private upstream repository. CI uses the read-only deploy key named **Gerby automatic publishing (read-only)**, stored only in the encrypted `FOUNDATIONS_SOURCE_SSH_KEY` Actions secret. It checks out the manuscript directories and root files, excluding the private research/reference library from the working tree and public artifact. `FOUNDATIONS_SOURCE_DIR` passes that fresh checkout to the build; the repository identity and exact commit are checked before conversion.

Its adapter uses the official pinned Gerby renderer. A web-only preamble emulates the source's shared section theorem counter while preserving its mathematics macros. The upstream source is never rewritten. Only the input graph activated by `book.tex` is published; inactive chapter skeletons are excluded. Unknown LaTeX commands, missing labels on numbered headings/theorems, missing fragments, and tag-inventory gaps fail the build instead of silently dropping content.

Permanent eight-character tags are derived from each source label with SHA-256. The build rejects collisions. Tags do not depend on theorem numbering or chapter order; renaming a source label needs an explicit permalink migration. Named frontmatter headings receive separate synthetic labels. The exported `tags.json` records every mapping.

The static edition includes a complete reading page, individual tag pages, bibliography entries actually cited in the active text, full-text tag search, and self-hosted MathJax assets. Formalization badges default to **Not recorded** until mappings are supplied.

Each book needs its own entry in `books.json`. An illustrative entry is:

```json
{
  "slug": "example-book",
  "title": "Example Book",
  "repository": "https://github.com/OWNER/BOOK",
  "ref": "main",
  "entrypoint": "book.tex",
  "tags": "tags",
  "status": "pending"
}
```

`ref` is optional; omission follows the upstream default branch. Use a branch to receive future updates, or a commit to freeze an edition. Tag mappings must persist across builds and must never be regenerated with different identities.

Once the actual LaTeX structure is known, add `adapters/<slug>.py` and set `status` to `published`. The build invokes the adapter with:

```text
python3 adapters/<slug>.py SOURCE_DIRECTORY OUTPUT_DIRECTORY
```

An adapter must run the Gerby conversion/export, write `OUTPUT_DIRECTORY/index.html`, preserve tag permalinks and assets, and use relative links compatible with `/Gerby/`. Dependencies are pinned in `requirements.txt` and `vendor/package-lock.json`. Each book has its own output directory and independent tag namespace.

For a published book, the build checks that every HTML page has the formalization badge integration before it can be deployed. See [formalizations.md](formalizations.md). The adapter must mark each theorem/tag with `data-gerby-tag` and include the shared badge module and stylesheet; source-specific integration tests must confirm marker coverage against the book's tag inventory.

The workflow fetches upstream repositories into `_sources/`, runs configured adapters, and records exact revisions in the published `upstream.json`. It never commits generated sources or build outputs to the repository. Newly registered pending books appear in the catalogue with a source link, but have no reading link until conversion is configured.

## Formalization updates

Formalization repositories are fetched on the same hourly schedule. The build compares the current revision with the verified commit. A mismatch downgrades the public badge to **Pending verification**. Once a real proof repository is supplied, its prover toolchain and verification adapter must be added to CI to recheck new revisions and produce evidence before a green badge can be issued.

Registry validation checks metadata consistency. It does not run a theorem prover. The current infrastructure deliberately makes no verification claims while the registries are empty.

## Static Gerby editions

Gerby's upstream pipeline is LaTeX and tags → Gerby plasTeX renderer → database import → Flask. Its [minimal example](https://github.com/gerby-project/hello-world) documents those steps. The exact renderer configuration and static export depend on the source book and will be tested during integration. GitHub Pages cannot run Flask; a full Gerby server would need a separate host, optionally behind the same public route through a proxy-capable host.
