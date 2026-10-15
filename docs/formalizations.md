# Formalization badges

Every integrated theorem/tag receives one of these English badges:

| Badge | Meaning | Link |
| --- | --- | --- |
| Not recorded | No formalization has been recorded for this book/tag. | None |
| Pending verification | A formalization repository is known, but its current revision has not passed verification. | Formalization repository |
| ✓ 0 sorry | The exact linked revision has passed the documented proof check for this declaration. | Formalization repository at the verified commit |
| Status unavailable | The status data could not be loaded. | None |

“Not recorded” does not assert that no formalization exists. A badge refers to the mapped declaration at the displayed commit, not every declaration in the repository. The correspondence between the informal statement and formal declaration also needs review.

## Registry

`formalizations.json` contains entries keyed by `(book, tag)`. Book namespaces prevent collisions when different books use the same Gerby tag.

A pending record has `book`, `tag`, `state: "pending"`, and `repository`. Optional `ref` selects the tracked branch; otherwise the default branch is tracked.

A verified record additionally requires:

- `commit`: the exact 40-character Git commit;
- `file` and `declaration`: the proof location and declaration name;
- `verification.command`: the check that was run;
- `verification.evidence_url`: a public GitHub Actions run or committed verification report;
- `verification.checked_at`: an ISO 8601 UTC timestamp;
- `verification.axioms`: the audited transitive axiom dependencies.

For Lean, a successful build alone is insufficient: Lean can compile incomplete proofs. Check `#print axioms Declaration.name` and reject `sorryAx`, including dependencies. This project's green badge accepts only the standard axioms `propext`, `Classical.choice`, and `Quot.sound` (or no axioms). Additional axioms require an explicit policy review instead of silently receiving a green badge. See the official [Lean proof validation guide](https://lean-lang.org/doc/reference/latest/ValidatingProofs/).

No verified records are seeded. Proof repositories, mappings, and verifier configuration will be added when supplied. Metadata validation is not a substitute for executing and reviewing the proof check.

## Book page contract

Every generated book page sets `data-gerby-book` on its root element. Every theorem/tag heading, including the primary heading on a single-tag page, includes `data-gerby-tag`:

```html
<html lang="en" data-gerby-book="example-book">
  <!-- Other page content and head elements omitted. -->
  <h2 data-gerby-tag="0001">Theorem 1.1</h2>
  <link rel="stylesheet" href="../../../assets/formalization.css">
  <script type="module" src="../../../assets/formalization.mjs"></script>
</html>
```

Adjust the relative asset paths to the actual page depth. The module locates the registry relative to its own URL, so it works under `/Gerby/` and nested tag routes. It adds a badge beside every marked heading, defaults missing mappings to **Not recorded**, and never treats a fetch failure as successful verification. Book conversion adapters are responsible for emitting a marker for every tag and testing this against the source tag inventory.

The linked verified repository revision is also available in `formalizations.json` together with the declaration, file, audit command, and evidence URL. When upstream changes, the public build downgrades stale verification records until the new revision is checked.
