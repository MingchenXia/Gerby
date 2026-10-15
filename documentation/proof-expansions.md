# Proof expansions

The shared reading edition adds proofs where a source statement previously referred the reader elsewhere. An earlier proof already present in Pome can be used as an internal dependency; the additional argument identifies its hypotheses and the change of notation. Short independent arguments are written out at the statement. Named results, bibliographic references, and the original source records remain available. Book titles are not repeated beside every theorem or reading chunk.

The first increment contains 53 proofs and three qualifications. It covers distributional representatives, holomorphic pullbacks, local integrability, envelopes, multiplier ideals, Lelong numbers, approximation, Bedford–Taylor products, non-pluripolar products, capacity comparison, convex duality, and convex bodies. The proofs of Blaschke selection, Hausdorff convergence, Minkowski-sum continuity, and the multiplicative Brunn–Minkowski inequality are included directly. Longer analytic results use earlier fully stated results within the collection rather than another citation to an external book.

Three qualifications are necessary:

- SGPT Proposition 1.5.4 needs connectedness or a separate lower normalization on each component. The addition gives the counterexample on a disconnected compact manifold and proves the qualified version.
- The analytic clause of SGPT Theorem 1.4.15 must test the total pole divisor on a log resolution, including nonexceptional components. The identity resolution of `log |z|²` gives a counterexample to an exceptional-divisors-only test. The addition supplies the change-of-variables proof of the corrected finite test and specifies the local scope of the general germ criterion.
- SGPT Theorem A.4.4 gives convergence against compactly supported continuous functions. The addition explains the distinction from convergence against all bounded continuous functions and exhibits mass escaping to infinity.

These additions do not assert that every external dependency has been eliminated. `proofs/open-dependencies.json` records the outstanding candidates from the first audit, including results that require additional source reading. A citation occurring in a proof is a review candidate, not by itself proof that the argument is incomplete. The jointly proved Remmert–Stein and proper-image results and duplicate source versions with an existing canonical proof are distinguished from unresolved cases. Resolution and principalization remain the permitted Hironaka inputs.

## Editing and verification

The registry targets exact source labels and records both the mathematical statement fingerprint and the original proof hash. A changed statement, changed source proof, missing target, missing internal dependency, or circular chain among the additions stops the build. The supplements are inserted in both entry fragments and their enclosing continuous sections. A supplied partial proof is replaced in the reading edition; the original source repository is unchanged. The added proof carries its own `data-proof-expansion` marker, while formalization badges continue to describe their original mathematical statements; an expanded informal proof does not create formal-verification evidence.

The mathematical review checked the source statements, their chart and connectedness assumptions, extended-valued convex functions, the normalization `ddᶜ = i/(2π) ∂∂̄`, the multiplier weight `exp(-φ)`, and the lattice factor `n!`. The second read corrected the direction of the local domination inequality and supplied the necessary qualifications above. Local software checks separately verify guarded insertion, propagation to enclosing sections, source-proof replacement, dependency failures, and retained badge markers. Compilation and rendering checks are not mathematical verification.

Further changes go through pull requests. Completed increments are merged into `main` and published from prebuilt `docs/`. Tests and manuscript rendering run locally; GitHub Actions CI remains skipped.
