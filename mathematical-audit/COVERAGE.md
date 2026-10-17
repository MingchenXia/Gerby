# Broad-scope coverage ledger — 17 October 2026

## Governing scope

The author's 17 October request supersedes the Demailly priority in older README/checkpoint text. Skip Demailly approximation and its dedicated Bergman/L2/extension/atlas proof-completion programme. Retain historical work as deferred-by-user, not resolved. Audit the rest of Pome across chapters; do not remain indefinitely in one prerequisite chain. If an unrelated proof invokes regularization, log that dependency without reopening it.

The table records the NEW broad-scope pass, not a denial of historical targeted checks. Chapter names were read from the actual navigation at main `66f8176be2a006b9404ae6db49ee15621dea5523`. Queued means not yet substantively reviewed in this new pass. Reading a section is not certification of its dependencies or chapter. No entire chapter is certified.

| Chapter | Subject | New-pass coverage |
| --- | --- | --- |
| 1 | Conventions | Queued; track normalization and terminology across sources. |
| 2 | Measures, distributions, and convergence | Queued; limits, nets, tightness and testing classes. |
| 3 | Harmonic and subharmonic functions | Queued outside the deferred regularization programme. |
| 4 | Energy, capacity, and fine topology | Queued; distinguish local/global capacities. |
| 5 | Plurisubharmonic functions and positive currents | Queued outside Demailly/Bergman approximation. |
| 6 | Lelong numbers, multiplier ideals, and regularization | Dedicated approximation and prerequisite-completion work deferred; other independent material remains eligible. |
| 7 | Local Monge–Ampere theory and capacity | Queued; Bedford–Taylor products and comparison/convergence. |
| 8 | Complex Hessian equations | Queued. |
| 9 | Complex spaces and modifications | Queued. |
| 10 | Cohomology, positivity, and geometric loci | Queued. |
| 11 | Hermitian geometry, torsion, and Gauduchon duality | Queued. |
| 12 | Gauduchon variational volume | Queued. |
| 13 | Non-pluripolar measures and mass | Section 13.12 mathematical body read; POME-CAP-001 confirmed below. Remaining sections queued. |
| 14 | Monge–Ampere equations and stability | Queued. |
| 15 | Monge–Ampere equations with prescribed singularities | Queued. |
| 16 | Singularity types, envelopes, and models | Next unreviewed chapter: envelope order/limits and actual proof dependencies. |
| 17 | Energy, geodesics, rays, and test curves | Queued; endpoint assumptions and limiting operations. |
| 18 | Multiplier-ideal models and partial equilibrium | Queued outside the excluded approximation programme. |
| 19 | Sections, graded series, and Okounkov bodies | Queued. |
| 20 | B-divisors and restriction | Queued. |
| 21 | Toric and convex geometry | Queued. |
| 22 | Non-Archimedean pluripotential theory | Queued. |
| 23 | Hopf and locally conformally Kahler geometry | Queued. |
| 24 | Problems in pluripotential theory | Queued; do not confuse stated questions with proved results. |
| 25 | Historical and bibliographical notes | Queued; retain attribution, separate it from proof inputs. |

## First review unit: Section 13.12

Report: [Open-set capacity counterexample](reports/2026-10-17-open-set-capacity-counterexample.md).

- `D56D6D4A5E94`, Proposition 13.12.7: **POME-CAP-001, confirmed error**. With the printed whole-open-set capacity definition, decreasing bounded smooth local psh sequences need not converge in capacity. The report gives an explicit projective-line counterexample with every exceptional set of capacity exactly one.
- `F7490AE48EAC` and `C96BE5099B6A`: capacity-convergence and global-capacity definitions read to establish the exact scope of the counterexample.
- `272876B00528`, Theorem 13.12.8: statement read in both standalone and enclosing pages. Proof is deferred to GZ17 in the enclosing page. Internal replacement not yet located; no assertion that this theorem is false.
- Other statements of Section 13.12: body read, but replacement-proof dependencies not transitively certified.

## Carry-forward actions

Keep POME-CAP-001 open until a reviewed correction is integrated. Distinguish local convergence on compact subsets from genuine global capacity control; adding uniform boundedness does not fix this counterexample. Locate actual downstream uses without silently weakening their hypotheses. The net version of a proposed local replacement still requires proof.

Continue next with Chapter 16, then Chapter 7 and Chapter 17, while expanding the matrix to exact section/tag coverage. Other chapters remain part of the mandate. Historical findings and unsynced material remain in their existing reports; defer only the excluded programme, not the general audit. No automatic main edits, merging, website publication, or CI is authorized.
