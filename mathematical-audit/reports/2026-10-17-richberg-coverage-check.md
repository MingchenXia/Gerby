# POME-DEP-009 — Richberg/psh primitive coverage (2026-10-17)

Reviewed main `66f8176be2a006b9404ae6db49ee15621dea5523`. **Status:** verified local deductions; lower analytic primitives still pending. **Severity:** medium foundational dependency; no confirmed false statement.

Actual integrated proof paths: `docs/tag/52930869627B/index.html` (Richberg 6.3.3, blob `8a0196fe306afd9b83ae5df30b449ff2f6069e74`), `docs/tag/5898ED42C26F/index.html` (disc test, blob `89213fdd72b7bc47f7066ceb6363ce8181144fcb`), and `docs/tag/06C722B7D837/index.html` (psh convolution, blob `6f18f54e9e0c9e3e2210616c54614cedb3eac61d`).

With `eta=delta*r^2/6`, the Richberg bump is `>=2eta` on radius `r/3`, `<-2eta` outside radius `sqrt(7)r/3`, and the local upper error is `<7delta*r^2/9`; `delta<a/2` preserves the Hessian bound `aI/2`. Convex regularized maximum retains that bound; the outer-shell deletion rule and local finiteness make gluing smooth. Fejer polynomial majorants prove the disc criterion. Radial convolutions decrease to their subharmonic input.

**Actual check:** 64 exact-fraction bump-budget cases and `py_compile` passed. No Pome tests/build. Remaining: spherical means, fundamental potential, Weyl, distribution primitives, and variable-scale Bergman dependencies. Proposed production changes: none.