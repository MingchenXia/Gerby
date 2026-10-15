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

An adapter must run the Gerby conversion/export, write `OUTPUT_DIRECTORY/index.html`, preserve tag permalinks and assets, and use relative links compatible with `/Gerby/`. Dependencies belong in the workflow when the first adapter is added; the empty catalogue needs none. Each book has its own output directory and independent tag namespace.

For a published book, the build checks that every HTML page has the formalization badge integration before it can be deployed. See [formalizations.md](formalizations.md). The adapter must mark each theorem/tag with `data-gerby-tag` and include the shared badge module and stylesheet; source-specific integration tests must confirm marker coverage against the book's tag inventory.

The workflow fetches upstream repositories into `_sources/`, runs configured adapters, and records exact revisions in the published `upstream.json`. It never commits generated sources or build outputs to the repository. Newly registered pending books appear in the catalogue with a source link, but have no reading link until conversion is configured.

## Formalization updates

Formalization repositories are fetched on the same hourly schedule. The build compares the current revision with the verified commit. A mismatch downgrades the public badge to **Pending verification**. Once a real proof repository is supplied, its prover toolchain and verification adapter must be added to CI to recheck new revisions and produce evidence before a green badge can be issued.

Registry validation checks metadata consistency. It does not run a theorem prover. The current infrastructure deliberately makes no verification claims while the registries are empty.

## Static Gerby editions

Gerby's upstream pipeline is LaTeX and tags → Gerby plasTeX renderer → database import → Flask. Its [minimal example](https://github.com/gerby-project/hello-world) documents those steps. The exact renderer configuration and static export depend on the source book and will be tested during integration. GitHub Pages cannot run Flask; a full Gerby server would need a separate host, optionally behind the same public route through a proxy-capable host.
