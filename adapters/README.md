# Book conversion adapters

Add a source-specific `<book-slug>.py` only after the actual book repository is available. It receives the checked-out source directory and an empty output directory as arguments. It must produce a static Gerby edition with an `index.html`, stable tag routes, relative assets, and the formalization badge hooks described in `docs/formalizations.md`.

`foundations-of-pluripotential-theory.py` exports the active manuscript of the first registered book with the official Gerby renderer. It preserves the shared section theorem numbering through a web-only preamble and leaves the source repository untouched.

Each adapter also writes `tags.json` to its output directory. It must list the complete source tag inventory, for example `[{"tag": "0001", "page": "tag/0001/index.html"}]`. The build checks that every listed tag has its badge marker on the corresponding page and that all book HTML pages load the shared badge assets. The adapter's source-specific tests must establish that the inventory covers every upstream tag.
