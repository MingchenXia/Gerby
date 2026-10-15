# Integration layout and numbering

Reader numbering belongs to Gerby's current organization, independently of the original manuscripts. This rule applies to every contributing source and future integration.

## Sections and subordinate material

`collection.json` assigns subjects to shared chapters. Its reviewed `section_promotions` identify stable canonical heading tags at which a long or mixed subject splits into smaller sections. Boundaries are checked in source order; a missing, repeated, or reordered boundary fails the build. The existing broad subject URL remains an overview with its introductory prose and links. It is not a second full copy of its child sections.

A retained source heading below a Gerby section is a subsection. A heading that repeats its containing section's title is absorbed into that section. Its old tag URL redirects to the introduction inside the section, and its source metadata and content remain available. Chapter pages list sections and their retained subsections.

Section titles are followed directly by reading content. Do not display topic metadata descriptions as small explanatory subtitles beneath them.

The 15 October 2026 layout review subdivides 36 section groups at 413 reviewed headings. It separates complex Hessian equations, Gauduchon variational volume, equations with prescribed singularities, and historical notes into their own chapters. The collection has 25 chapters and 491 sections. Future edits should review subject coherence and reading length, rather than copy these counts or impose a word limit without mathematical judgment.

## Generated locators

Chapters and sections have locators `C` and `C.S`. Addressable subordinate blocks share one counter within their containing section: a subsection may be `3.2.1`, a theorem `3.2.2`, and its labelled equation `(3.2.3)`. Theorems, lemmas, definitions, propositions, examples, remarks, equations, figures, and retained headings all use this sequence. This makes each locator unique within a section; counters continue across sources and reset at the next Gerby section. Absorbed introductory headings use `C.S` and do not consume a block number. Deduplicated source variants share the canonical entry's number.

`adapters/common.py` exports the original `number` and an explicit `caption` separately from source titles and semantic search terms. `scripts/structure.py` applies reviewed section boundaries. `scripts/numbering.py` assigns reader numbers after placement and deduplication. `scripts/collection.py` uses that map for headings, environment identifiers, equation labels, HTML references, references inside mathematics, navigation, search, and public inventories. Never extract a mathematical name from an internal LaTeX label.

Renumber only structured locators. Do not replace digits globally: mathematical dimensions, exponents, constants, logical list items such as (i)/(ii), and external references such as “Helms's Theorem 2.24, p. 36” retain their meaning. Source inventories under Sources retain original manuscript coordinates for provenance. A split or move may change display numbers; permanent tags and URLs must continue to resolve.

Equation labels sit beside their formulas in a two-column row. Long mathematics scrolls within its own column on narrow screens. Labelled align rows receive generated TeX tags inside their parent formula without duplicating their standalone HTML labels.

## Tags and verification

Show tags reveals tags for all addressable reading structures, including chapters and sections. A section reuses its absorbed introductory heading's tag when available; otherwise its tag derives from its stable route. Chapter tags also derive from stable routes. Renumbering does not change these identifiers. Subsections, mathematical statements, equations, and logical clauses keep their existing tags. A structure tag identifies content; it does not assert formalization.

Cite this page opens the citation panel immediately, including when clicked again with an existing `#cite` fragment. Direct citation links also expand the panel. Copy citation copies the displayed BibTeX entry; the permalink and title must identify the current reading page.

Footnotes use numbered links at their original positions in text or formulas. Note bodies follow the containing definition, theorem, proof, or prose block, with a return link to the reference. Number notes within each current Gerby section and reuse those numbers on standalone entries. Logical list conditions keep their existing tags and anchors; only the complete statement has a formalization badge.

The mathematical body should read as Gerby, independently of its source books. Rewrite source-specific introductions and preserve assumptions and conventions. Outside historical sections, use internal statements instead of external references whenever the required result is available. Keep necessary external inputs explicit; moving a citation must not disguise an unproved dependency. Bibliographical attribution, source commentary, and further-reading recommendations belong under Sources.

Before publication, run:

```sh
.venv/bin/python -m unittest discover -s tests
node --test tests/*.test.mjs
.venv/bin/python scripts/build.py --fetch
```

The build checks every structured visible source locator against the current collection numbers, along with all internal links and fragments. Regression tests cover subsection listings, section splits, numbering resets, merged variants, HTML/TeX references, equation rows, and stale-number rejection. Browser checks must cover the reported Kelvin-transform and Bedford–Taylor examples, section/chapter tag visibility, equation alignment on desktop and mobile, and representative pages from all sources.
