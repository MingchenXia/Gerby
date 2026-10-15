# Integration and reading-edition rules

- Read [the integration layout contract](documentation/integration-layout.md) before integrating or reorganizing content.
- Arrange content by mathematical subject in the current Gerby chapters and sections. Do not import an entire source chapter as one oversized reading section. Review long or mixed sections and record deliberate heading promotions in `collection.json`.
- Source chapter/section numbers, theorem numbers, and equation numbers are provenance only. Generate reader locators after section placement and canonical deduplication. Theorems, lemmas, definitions, equations, and subordinate headings use the **current Gerby section number** as their prefix. Never hard-code reader numbers in adapters, prose, HTML, or CSS.
- Absorb a source heading that repeats its containing section title. Preserve its introductory prose, attribution, tags, and old permalinks; do not add a duplicate heading or reading step.
- Chapter pages must list their sections and subsections. Keep equation labels beside their formulas when space permits. Show tags must reveal chapter, section, subsection, statement, equation, and clause tags.
- Update structured HTML and TeX cross-references with the same numbering map. Preserve mathematical constants, logical clause labels, external bibliographic locators, stable source labels, and permanent tags.
- Run the Python and JavaScript tests, the complete build with its numbering/link checks, and desktop/mobile browser checks before publishing. Check all sources affected by a shared rendering change, including the exact examples reported by the author.
- Keep project documentation and interface text in English. Keep private research files and retained scans out of public exports. Updates remain on request; do not add schedules or GitHub Actions CI.
