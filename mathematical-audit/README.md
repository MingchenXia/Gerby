# Ongoing mathematical audit

## Mandate and publication boundary

On 16 October 2026 the author requested continuing hourly review of Pome for mathematical errors, missing arguments or hypotheses, duplicates, and dependence on external literature, with the findings and proposed corrections committed to this repository. The first priority is a genuinely justified Demailly approximation theorem with controlled loss of positivity. Proofs should be as self-contained as possible; Hironaka resolution and principalization are the explicitly permitted external inputs. Historical attribution is to be retained, not confused with an unproved dependency.

This directory is maintained on `review/mathematical-audit`, with draft PR #9. It contains audit records and proposed repairs, not automatically accepted changes to the reading edition. No source manuscript, permanent tag, canonicalization registry, generated `docs/` file, or existing `main` content is changed by these audit increments. No GitHub Actions workflow or website-publication schedule is introduced. The separately requested hourly audit does not reinstate automatic website publication.

## Current checkpoint

- Baseline reviewed: `main` at `66f8176be2a006b9404ae6db49ee15621dea5523`.
- Latest report: [2026-10-16: nonclosed gluing, sharp transfer, and a misplaced equation](reports/2026-10-16-continuation-nonclosed-gluing.md).
- Historical first report: [2026-10-16: positivity control and dependency baseline](reports/2026-10-16-initial-positivity-audit.md).
- Principal observation remains: Theorem 6.17.6 already **states** an error `c' 2^{-j}`. Its proof must be audited transitively, and retaining an arbitrary prescribed lower bound is stronger than starting from a positive current. Do not report simply that the current text contains no quantitative estimate.
- New verified component: a complete cutoff-gluing lemma for an arbitrary continuous, possibly nonclosed, common curvature lower bound, including the singular limiting step and the explicit loss `2 J A exp(C_B)/m`. This requires local candidates and a uniform overlap comparison as hypotheses. It does **not** construct those candidates or close the stronger Demailly theorem.
- New confirmed editorial defect: the equation tagged `EF5655B5F536`, inside the canonical Definition 6.17.5, still appears and navigates as Equation 5.18.9. The mathematical formula is not false. The production placement/numbering repair remains proposed.
- New mathematical adjudication: Lemma 6.17.4's threshold `lambda lambda'/(lambda'-lambda)` was checked and shown sharp by explicit disc counterexamples below the threshold. The two canonical variants of Definition 6.17.5 were checked to be equivalent, not an unresolved duplication.
- Earlier verified components remain: smooth cutoff-sum algebra, dyadic monotonicity arithmetic, and the smooth **closed** prescribed-lower-bound deduction conditional on the base theorem.
- New confirmed false existing theorem statements across these two increments: none. Unchecked prerequisites are not demonstrated proof gaps.

## Coverage and issue ledger

| ID | Current status | Next action |
| --- | --- | --- |
| POME-REG-001 | Requested strengthening; open | Construct and justify local approximants preserving a prescribed continuous lower bound, with scale and comparison errors tracked. |
| POME-REG-002 | Partly checked dependency chain; open | Finish L2, extension, generation, and convergence prerequisites transitively. |
| POME-DEP-001 | External-dependency audit open | Distinguish attribution, proved internal replacements, and actual unproved inputs. |
| POME-XREF-001 | Confirmed placement/numbering defect | Trace and repair canonical-parent descendant placement in a reviewable production patch; do not hand-edit generated numbers. |
| POME-REG-003 | Verified proposed gluing lemma | Apply only after its local lower-bound and overlap hypotheses have been proved. |
| POME-REG-004 | Verified transfer implication and sharpness | Retain exact parameter dependence; consider adding the sharpness example. |
| POME-DUP-001 | Canonical variants verified equivalent | Retain canonicalization; repair the separate descendant equation defect. |

New complete reads include the fixed atlas construction in Section 6.16; Lemma 6.16.2; all of Lemma 6.17.1; Lemmas 6.15.1 and 6.15.3; the bounded-division proof in Lemma 6.8.10; Lemmas 6.5.2 and 6.5.3; Lemma 6.17.4; and both versions of Definition 6.17.5. Lemma 6.17.3 and Theorem 6.17.6 were reread in full. See the latest report for precisely which analytic prerequisites remain conditional.

Theorem 6.8.9, Theorem 6.5.4, and Theorem 6.4.7 were read **only in part** in the second increment. Their concluding passages and all transitively invoked operator-domain, exhaustion, extension, and coherence arguments are not yet certified. This remains a limited audit, not a whole-book review.

The standard-library script `checks/check_transfer_threshold.py` ran successfully: 96 exact below-threshold counterexamples, 96 exact coefficient checks at or above threshold, and 9 exact twisted-L2 constant checks. `py_compile` passed. These checks supplement the written proof, not a formalization or a full project build. Direct container downloads still failed at DNS resolution; GitHub connector reads and writes worked. No complete Python/JavaScript project suite, site build, or browser verification has been run by this audit.

## Next review units

1. Finish the smooth/singular L2 and extension chain: `F85650C9CE6A`, `88735CB0C076`, `D315377B239D`, `33DEA3F4EDB8`, and `5AEABFD276A6`; inspect all operator-domain, exhaustion, and limiting prerequisites actually used. Finish the partially read coherence/generation theorem `FE623FA661C4`.
2. For the prescribed lower-bound version, prove the local Bergman and overlap inputs required by POME-REG-003. Track chart radii, the modulus of continuity of the lower form, cutoff derivatives, comparison constants, and the Bergman parameter. Supply a valid diagonal choice; do not import a scale-independent `O(1/m)` rate or monotonicity without proof.
3. Trace POME-XREF-001 through canonicalization and placement before numbering, using its exact permanent tags. Proposed tests must compare a subordinate equation with its canonical parent's actual section, not merely with an already stale numbering map. Preserve all tags and mathematical contents.
4. Extend the coverage ledger across the collection. Review genuine mathematical duplicates before proposing canonicalization; differing hypotheses are not duplicates. Review `proofs/open-dependencies.json` item by item, distinguishing actual external proof inputs from attribution and already available internal proofs.

## Rules for each increment

Read current `main` and the existing audit branch before reviewing or writing. Record the reviewed commit and stable labels/tags, not merely reader theorem numbers. Every reported defect must identify its exact text, assumptions, supporting argument or counterexample, proposed correction, and affected dependents. Use separate statuses for confirmed error, demonstrated proof gap, requested strengthening, verified conditional deduction, candidate awaiting verification, duplication, and resolved item. Maintain actual coverage and the unresolved list. Never infer full mathematical verification from compilation, matching titles, a previous review, or a formalization badge that does not cover the modified statement.

Push only new substantive review records or proposed patches; do not create unchanged commits. Preserve all existing work, read current blob SHAs before updates, and never force-push or auto-merge. Keep project documentation in English. Do not copy private source scans, unpublished private research, credentials, or unrelated personal data into this public repository. Report checks actually performed and blockers actually encountered.
