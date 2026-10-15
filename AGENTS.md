# Integration and reading-edition rules

- Read [the integration layout contract](documentation/integration-layout.md) before integrating or reorganizing content.
- Arrange content by mathematical subject in the current Gerby chapters and sections. Do not import an entire source chapter as one oversized reading section. Review long or mixed sections and record deliberate heading promotions in `collection.json`.
- Source chapter/section numbers, theorem numbers, and equation numbers are provenance only. Generate reader locators after section placement and canonical deduplication. Theorems, lemmas, definitions, equations, and subordinate headings use the **current Gerby section number** as their prefix. Never hard-code reader numbers in adapters, prose, HTML, or CSS.
- Absorb a source heading that repeats its containing section title. Preserve its introductory prose, attribution, tags, and old permalinks; do not add a duplicate heading or reading step.
- Chapter pages must list their sections and subsections. Keep equation labels beside their formulas when space permits. Show tags must reveal chapter, section, subsection, statement, equation, and clause tags.
- Do not display metadata descriptions or summary subtitles beneath section titles. Start the reading content directly after the title.
- Cite this page must open the citation panel, including repeated clicks and direct `#cite` links. Verify the copyable BibTeX citation in the browser.
- Render footnotes as numbered references at their original text or formula positions. Put note bodies after the containing environment, with links in both directions. Keep numbering consistent between entry and section pages.
- Formalization badges describe complete statements. Logical list conditions retain their tags and anchors, but do not receive separate badges.
- Outside historical sections, prefer internal Gerby references and keep external citations only when the argument needs an unavailable external input. Put bibliographical attribution and reading recommendations under Sources. Rewrite or remove source-book introductions, author commentary, and instructions to read other books; preserve mathematical assumptions and conventions.
- Update structured HTML and TeX cross-references with the same numbering map. Preserve mathematical constants, logical clause labels, external bibliographic locators, stable source labels, and permanent tags.
- Run the Python and JavaScript tests, the complete build with its numbering/link checks, and desktop/mobile browser checks before publishing. Check all sources affected by a shared rendering change, including the exact examples reported by the author.
- Keep project documentation and interface text in English. Keep private research files and retained scans out of public exports. Updates remain on request; do not add schedules or GitHub Actions CI.
