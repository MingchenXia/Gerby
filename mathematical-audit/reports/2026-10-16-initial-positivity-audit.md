# Initial audit: positivity control, proof dependencies, and precise scope

Date: 16 October 2026 (UTC+08:00).

Reviewed Pome baseline: `66f8176be2a006b9404ae6db49ee15621dea5523` on `main`.

This is a first, limited audit increment. It records concrete reading, an independent calculation, a conditional corollary, and the next verification obligations. It does **not** certify the full Demailly approximation theorem, assert that an unread proof is missing, or claim to have checked all duplicates in Pome.

## 1. Material actually inspected

The repository policies were read in `AGENTS.md`, `README.md`, `books.json`, and `documentation/proof-expansions.md`. The initial registry and external-dependency records were inspected only in part; no exhaustive count or classification is asserted.

Mathematical texts inspected:

| Integrated result | Stable tag / path | Extent |
| --- | --- | --- |
| Replacement proof of SGPT `thm:qequi` | `proofs/thm-qequi.html` | Complete fragment; redirects to the gentle approximation theorem. |
| Theorem 6.17.6 | `docs/tag/080EF8C715CF/index.html` | Complete statement and proof. |
| Lemma 6.17.1 | `docs/tag/EFA6E7FF99E6/index.html` | Statement and proof Steps 1–2, and the displayed beginning of Step 3. The remainder was not fully retrieved in this pass. |
| Lemma 6.17.3 | `docs/tag/C32B34A0713B/index.html` | Complete statement and proof. |
| Lemma 6.16.2 | `docs/tag/82376665E5F7/index.html` | Complete statement and proof; earlier atlas and L2 prerequisites not all audited. |
| Theorem 6.16.3 | `docs/tag/E9EBCA5A681D/index.html` | Complete statement and proof; patching lemma prerequisite not audited. |
| Lemma 6.15.7 | `docs/tag/365648DE5857/index.html` | Complete statement and proof; extension theorem prerequisite not audited. |
| Theorem 6.4.9 | `docs/tag/88735CB0C076/index.html` | Complete singular-weight reduction; underlying smooth-weight theorem not yet audited. |

For reproducibility, the corresponding retrieved blob SHAs include:

```text
proofs/thm-qequi.html                       032b9a682d47bd3b3a8e3c2f6d75bd3e81217a1e
docs/tag/080EF8C715CF/index.html            9eb7c073afc2dab82951deeff81edccf443092ff
docs/tag/C32B34A0713B/index.html            7e966fe8bcd072fc05d392c9f056775bccd51d3f
docs/tag/82376665E5F7/index.html            a92a84051765f0c3ee98ab0bbfb1da0835e67f10
docs/tag/E9EBCA5A681D/index.html            a63da4cba777a39522d15d90fbdcf0f47fdb9168
docs/tag/365648DE5857/index.html            9a803b4f1bfad7f1f3765eca4923ba7cdebca6ff
docs/tag/88735CB0C076/index.html            9e8f19515a02170cc9ed35357bf8db9e2b9c0ed6
```

## 2. POME-REG-001: distinguish vanishing negativity from retention of a prescribed lower bound

**Priority:** high. **Status:** requested-strengthening / scope audit, not a counterexample to the existing theorem.

At tag `080EF8C715CF`, Theorem 6.17.6 assumes a smooth **closed** real form `theta` and `phi in PSH(X,theta)`. Its conclusion and proof explicitly give

\[
\theta+dd^c\Phi_j\geq-c'2^{-j}\omega.
\]

The theorem also claims decreasing approximation, the analytic type `(2^{-j}, I(2^j phi))`, L1 convergence, Lelong estimates, and multiplier-ideal inclusions. Thus it would be inaccurate to describe this current statement as containing no control of positivity loss. The actual questions are whether its proof chain is valid and whether it supplies the strength needed in later applications.

For applications beginning with

\[
T=\theta+dd^c\varphi\geq\gamma,
\]

record separately the desired conclusion

\[
T_j=\theta+dd^c\varphi_j\geq\gamma-\varepsilon_j\omega,
\qquad\varepsilon_j\longrightarrow0.
\]

The latter retains the specified lower bound. The displayed conclusion with lower bound zero, by itself, does not retain a nonzero `gamma`.

### Proposed explicit corollary for a closed lower bound

**Status:** the following deduction is checked, conditional on Theorem 6.17.6 itself.

Suppose `gamma` is a smooth closed real (1,1)-form and `theta+dd^c phi >= gamma`. Put `beta=theta-gamma`. Then `beta` is smooth and closed, and `phi in PSH(X,beta)`. Apply Theorem 6.17.6 to `(beta,phi)` rather than `(theta,phi)`. Its approximants satisfy

\[
\beta+dd^c\Phi_j\geq-c'2^{-j}\omega.
\]

Adding `gamma` gives

\[
\theta+dd^c\Phi_j\geq\gamma-c'2^{-j}\omega.
\]

The same potential and multiplier ideals occur, so the asserted analytic type, convergence, Lelong estimates, and ideal inclusions are inherited from that application. The stated geometry-only dependence of the base constant gives the same form of rate. This last dependence remains subject to the upstream audit.

**Suggested correction/addition:** put this short corollary immediately after the base approximation theorem and use it explicitly in applications with a closed lower bound. It prevents silently discarding a positive margin.

### Why this does not settle a nonclosed lower bound

When `gamma` is not closed, `theta-gamma` is not closed, so this substitution falls outside the hypothesis of Theorem 6.17.6. In particular, the local-potential step used in Lemma 6.16.2 cannot simply be repeated: a form represented as `dd^c g` is closed. A general Hermitian lower bound cannot be treated as though it possessed such local potentials.

**Next obligation:** search the rest of the integrated collection for the precise arbitrary-lower-bound version. Where needed, write the local approximation and patching estimates with their scale, modulus-of-continuity, and Bergman-parameter dependence, and explicitly choose parameters making the loss tend to zero. Do not prescribe an `O(1/m)` rate for this stronger setting without proving it. No claim of global absence of such a theorem is made by this limited pass.

## 3. POME-REG-002: the quantitative proof chain, not just its final citation

**Priority:** high. **Status:** partly checked; transitive verification open. This is not a demonstrated defect.

The currently inspected dependency chain is:

```text
SGPT thm:qequi replacement
  -> 080EF8C715CF, gentle approximation
     -> EFA6E7FF99E6, smooth cutoff sum and singularity type
        -> 82376665E5F7, uniform comparison of overlapping kernels
           -> 88735CB0C076, singular-weight L2 solution
              -> F85650C9CE6A, smooth-weight L2 solution [next]
     -> C32B34A0713B, convergence, Lelong estimates, doubling
        -> 365648DE5857, kernel doubling
           -> 33DEA3F4EDB8, extension from a linear subspace [next]
              -> D315377B239D, extension theorem [next]
     -> 7EFB7FFA3AB8, multiplier-ideal transfer [next]
```

The analytic-type arguments also require auditing tag `09CBB2B6BA0F`, its generation/comparison properties for the Bergman kernel, and the log-resolution remainder argument. Resolution is an allowed input; uniform analytic estimates do not become consequences of Hironaka merely because a resolution is used.

### Independently checked smooth cutoff calculation

Use the normalization actually appearing in the text,

\[
dd^c=\frac{i}{2\pi}\partial\bar\partial.
\]

Let `chi_j` be finitely many smooth nonnegative cutoffs and `w_j` smooth real functions. Write

\[
S=\sum_{j=1}^J\chi_j^2e^{w_j}>0,
\qquad\alpha_j=\chi_j\partial w_j+2\partial\chi_j.
\]

Direct differentiation gives

\[
\partial(\chi_j^2e^{w_j})=\chi_je^{w_j}\alpha_j
\]

and

\[
\partial\bar\partial(\chi_j^2e^{w_j})
=e^{w_j}\bigl(\alpha_j\wedge\bar\alpha_j
+\chi_j^2\partial\bar\partial w_j
+2\chi_j\partial\bar\partial\chi_j
-2\partial\chi_j\wedge\bar\partial\chi_j\bigr).
\]

Substituting into the derivative of `log S` and grouping each pair of distinct indices yields

\[
\begin{aligned}
dd^c\log S={}&\frac{i}{2\pi S^2}
\sum_{j<l}e^{w_j+w_l}
(\chi_j\alpha_l-\chi_l\alpha_j)
\wedge\overline{(\chi_j\alpha_l-\chi_l\alpha_j)}\\
&+\frac{\sum_j\chi_j^2e^{w_j}dd^cw_j}{S}\\
&+2\frac{\sum_je^{w_j}
(\chi_jdd^c\chi_j-\frac{i}{2\pi}\partial\chi_j\wedge\bar\partial\chi_j)}{S}.
\end{aligned}
\]

The first term is semipositive. Suppose `dd^c w_j >= -m theta`, each cutoff expression in the last numerator is at least `-A omega`, and at each point there is an index `i` with `chi_i=1` and `e^{w_j} <= exp(C_B)e^{w_i}` for every active cutoff. Then `S >= e^{w_i}`, so each active ratio `e^{w_j}/S <= exp(C_B)`. If `chi_j=0`, its first derivative is zero, since it is nonnegative; the cutoff expression at that point vanishes. The middle term is a convex combination of the lower bounds. Consequently

\[
\theta+\frac1m dd^c\log S
\geq-\frac{2JAe^{C_B}}m\omega.
\]

This verifies the algebra and the constant in the **smooth, conditionally comparable** situation used in Step 2 of Lemma 6.17.1. It does not by itself establish the uniform kernel comparison, the singular limiting argument, or the gentle analytic type. Those must be checked separately.

### Monotonicity arithmetic checked

Conditional on `G_{2m} <= G_m+D/m`, define `Phi_j=G_{2^j}+2D/2^j`. With `m=2^j`,

\[
\Phi_{j+1}=G_{2m}+D/m\leq G_m+2D/m=\Phi_j.
\]

Thus no arithmetic error was found in this step. The remaining obligation is the actual uniform doubling inequality, whose proof invokes extension from the diagonal; naming Bergman approximation alone would not establish it.

## 4. POME-DEP-001: self-containedness must be audited transitively

**Priority:** high. **Status:** review pending, no blanket finding of missing proofs.

The fragment `proofs/thm-qequi.html` is a redirect to an internal theorem. Such a redirect is appropriate if the referenced theorem is proved with the needed hypotheses. It is not an independent certificate that all external inputs have disappeared. The L2 and extension results above are the first analytic dependency units to audit next.

Keep bibliographical attribution. Classify an external reference as a genuine unproved input only after checking the argument and the available internal replacements. In particular, the initial `proofs/open-dependencies.json` expressly lists review candidates rather than established errors. Its old statuses must not be promoted to confirmed defects without reading the actual statements and proofs.

The replacement mechanism guards the source statement and original proof with fingerprints. Proposed proof repairs therefore need matching source-label/statement review; they must not be made by editing only one generated tag page. Verify the complete source and integration workflow before any eventual reading-edition patch.

## 5. Coverage and verification limits

No duplicate pair has been substantively adjudicated in this initial pass. No theorem is newly declared false. The unresolved items above remain open. The elementary calculation and closed-lower-bound corollary are useful verified components, not a declaration that the full approximation construction is now complete.

The GitHub connector successfully provided the listed current texts. A direct local clone failed because the container could not resolve `github.com`; no source checkout, Python/JavaScript test suite, complete build, or browser rendering check was run. The work in this increment is textual and mathematical audit only, and the commit contains Markdown notes only. There is no claim of a successful build or of publication to the website.

Continue from the ordered review units in the audit README, recording new checked coverage and precise defects or repairs rather than repeating this baseline.
