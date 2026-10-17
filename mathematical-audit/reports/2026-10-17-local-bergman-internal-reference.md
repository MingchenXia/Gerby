# POME-DEP-012 / POME-LOC-001 (2026-10-17)

Reviewed main: 66f8176be2a006b9404ae6db49ee15621dea5523.

POME-DEP-012 — verified internal replacement, low severity (not a false theorem). In docs/sections/plurisubharmonic-functions-and-singularities--the-local-bergman-estimates/index.html (blob f600e35c55753ac073bce3d7b369f1f9a442da52), introductory text before Proposition 5.35.1 (tag DBEB8E0E0318) cites DemAM11 for generators/division. Pome already proves the relevant claim: Lemma 6.15.1 (C2732E72E566) supplies ideal generators and bounded division; Lemma 6.15.3 (09CBB2B6BA0F) proves K_m comparable to a squared finite generator norm. Corollary 6.5.8 (33DEA3F4EDB8) supplies point extension; Theorem 6.15.4 (5AEABFD276A6) supplies the exact local inequalities, L1 convergence and Lelong bounds. Same hypothesis: bounded pseudoconvex domain, psh weight, exp(-m u). Proposed patch: cite the internal results and retain DemAM11 as historical attribution. The OT proof remains an active dependency, not certified by this change.

POME-LOC-001 — verified model check: for u=a log|z|^2 on the unit ball in C^n, a degree-k monomial is exp(-m u)-integrable exactly when k+n>ma. Thus k_min=max(0,floor(ma-n)+1), and nu((1/m)log K_m,0)=k_min/m lies between a-n/m and a. Exact-rational script passed 7,038 cases; finite tests are not full formal verification.

Open: POME-REG-001/002/009, POME-DEP-010/011, POME-XREF-001; no build, publication or source edit. Next: 6.8.9 ideal-generation dependencies and varying-scale OT constants.