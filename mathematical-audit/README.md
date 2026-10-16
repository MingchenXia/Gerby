# Ongoing mathematical audit

## Mandate and publication boundary

On 16 October 2026 the author requested continuing hourly review of Pome for mathematical errors, missing arguments or hypotheses, duplicates, and dependence on external literature, with the findings and proposed corrections committed to this repository. The first priority is a genuinely justified Demailly approximation theorem with controlled loss of positivity. Proofs should be as self-contained as possible; Hironaka resolution and principalization are the explicitly permitted external inputs. Historical attribution is to be retained, not confused with an unproved dependency.

This directory is maintained on `review/mathematical-audit`. It contains audit records and proposed repairs, not automatically accepted changes to the reading edition. No source manuscript, permanent tag, canonicalization registry, generated `docs/` file, or `main` content is changed by this initial audit commit. No GitHub Actions workflow or website-publication schedule is introduced. The separately requested hourly audit does not reinstate automatic website publication.

## Current checkpoint

- Baseline reviewed: `main` at `66f8176be2a006b9404ae6db49ee15621dea5523`.
- Latest report: [2026-10-16: positivity control and dependency baseline](reports/2026-10-16-initial-positivity-audit.md).
- Actual initial coverage: repository proof-insertion policy and selected integrated entries in Sections 6.15–6.17, together with the singular-weight L2 theorem they use. This is not a whole-book audit.
- Principal observation: Theorem 6.17.6 already **states** an error `c' 2^{-j}`. Its proof must be audited transitively, and the version retaining an arbitrary prescribed lower bound must be distinguished from the version starting with a positive current. Do not report simply that the current text contains no quantitative estimate.
- Verified partial work: direct algebra of the smooth cutoff-sum curvature estimate; the arithmetic converting the stated doubling inequality into monotonicity; and the deduction for a smooth **closed** prescribed lower bound, conditional on the base approximation theorem. These checks do not certify all analytic inputs.
- New confirmed false theorem statements in this initial pass: none. New confirmed duplicates: none. Unchecked dependencies are not to be presented as demonstrated proof gaps.

## Next review units

1. Finish reading and verifying all of Lemma 6.17.1, especially its singular-limit, ideal-generation, and log-resolution steps. Verify the fixed atlas hypotheses used in Lemma 6.16.2, rather than assuming them from the phrase "fixed geometry".
2. Audit the complete L2 and extension dependency chain: tags `F85650C9CE6A`, `D315377B239D`, `33DEA3F4EDB8`, `09CBB2B6BA0F`, and `5AEABFD276A6`, along with any further prerequisites they actually invoke. Review the multiplier-ideal transfer at `7EFB7FFA3AB8` and the exact quasi-equisingular definition at `165F88FAE668`.
3. Search the other integrated statements for regularization preserving a prescribed smooth or continuous lower bound, especially a nonclosed Hermitian lower bound. Record its exact hypotheses and prove the required quantitative patching estimates. If such a proof is absent, draft it in dependency order; do not silently replace it by the closed-background theorem.
4. Extend the coverage ledger across the collection. Review genuine mathematical duplicates before proposing canonicalization; differing hypotheses are not duplicates. Review `proofs/open-dependencies.json` item by item, distinguishing actual external proof inputs from attribution and already available internal proofs.

## Rules for each increment

Read current `main` and the existing audit branch before reviewing or writing. Record the reviewed commit and stable labels/tags, not merely reader theorem numbers. Every reported defect must identify its exact text, assumptions, supporting argument or counterexample, proposed correction, and affected dependents. Use separate statuses for confirmed error, demonstrated proof gap, requested strengthening, verified conditional deduction, candidate awaiting verification, duplication, and resolved item. Maintain actual coverage and the unresolved list. Never infer full mathematical verification from compilation, matching titles, a previous review, or a formalization badge that does not cover the modified statement.

Push only new substantive review records or proposed patches; do not create unchanged commits. Preserve all existing work, read current blob SHAs before updates, and never force-push or auto-merge. Keep project documentation in English. Do not copy private source scans, unpublished private research, credentials, or unrelated personal data into this public repository. Report checks actually performed and blockers actually encountered.
