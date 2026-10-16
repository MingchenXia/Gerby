# Second audit: nonclosed lower bounds, a sharp transfer threshold, and a misplaced equation

Date: 16 October 2026 (UTC+08:00).

Reviewed reading-edition baseline: `66f8176be2a006b9404ae6db49ee15621dea5523` on `main`. Starting audit checkpoint: `42055964550ee47683c3beb376b45ace1974387c` on `review/mathematical-audit`, draft PR #9. The first report remains historical and is not overwritten.

## Summary and status

- **Confirmed editorial defect:** an equation belonging to the canonical Definition 6.17.5 is still numbered and navigated as Equation 5.18.9. This is a placement/numbering defect, not a false mathematical formula.
- **Verified proposed lemma:** smooth cutoff sums preserve an arbitrary continuous, not necessarily closed, common curvature lower bound, with an explicit `C/m` loss, provided the local potentials satisfy a uniform overlap comparison. The proof below includes the singular limiting step without inventing a local potential for a nonclosed form.
- **Verified mathematical check:** the threshold in Lemma 6.17.4 is sufficient and sharp under its stated assumptions. A complete one-variable family of counterexamples is supplied below for every smaller threshold.
- **Verified canonicalization check:** the two versions of the quasi-equisingular definition are equivalent under their monotonicity and compactness assumptions. The difference between “some index” and “all sufficiently large indices” is not an error here.
- **Still open:** the full construction retaining a prescribed nonclosed lower bound, the complete transitive L2/extension audit, and the whole-project duplicate/external-dependency audit. No existing theorem is newly declared false in this increment.

The new gluing lemma does not construct the required local Bergman approximants or prove their overlap estimates for a prescribed lower bound. It therefore does not close POME-REG-001.

## 1. POME-XREF-001: a canonical parent's equation retains a different section

**Status:** confirmed editorial defect. **Severity:** medium. **Repair:** proposed, not integrated.

Exact baseline evidence:

1. `docs/tag/165F88FAE668/index.html`, SGPT alternative of Definition 6.17.5, fourth clause: the equation with source tag `CE89C52A` and permanent Pome tag `EF5655B5F536` displays `5.18.9`.
2. `docs/tag/EF5655B5F536/index.html`: its heading is `Equation 5.18.9`; previous/next navigation points to Theorem 5.18.8 and Definition 5.18.10.
3. `documentation/integration-layout.md`, “Generated locators”, requires subordinate blocks to use their containing Pome section and deduplicated variants to share the canonical entry's number. This equation is visibly inside the alternative wording of Definition 6.17.5, not a citation to an independent formula proved in Section 5.18.

The mathematical formula is the multiplier-ideal inclusion itself. The stable tag and formula should be retained.

**Suggested repair:** review the placement of equation and clause descendants when a source statement is canonicalized into a different section. Reattach the equation to the canonical parent's reading section before assigning numbers, then regenerate all relevant locators from the common map. The new prefix should be `6.17`; its final block ordinal must be generated, not hard-coded. Update the alternative statement, the independent equation page, breadcrumbs, previous/next navigation, search, and any structured HTML/TeX references together. Do not patch only the generated HTML or change the permanent tag.

`scripts/numbering.py::assign_numbers` assigns numbers using each entry's current `topic`. That function was read, but the upstream placement/canonicalization pipeline was not completely traced. The stale-descendant-placement explanation is therefore an implementation hypothesis, not a proven identification of the responsible function.

**Regression obligation:** for this exact canonical definition, check that the embedded equation and its independent page use the canonical parent's section prefix and agree with each other. A test checking only agreement with an already stale numbering map would not catch this defect.

## 2. POME-REG-003: cutoff gluing with a continuous, possibly nonclosed, lower bound

**Status:** verified proposed lemma; no claim of formal verification. **Priority:** high. **Purpose:** isolate and prove the patching component needed by POME-REG-001.

Throughout, `dd^c = i/(2 pi) partial bar-partial` as in Pome. Let `(X,omega)` be a compact complex manifold with a smooth positive Hermitian form; closedness of `omega` is not required for this lemma. Fix a finite nested cover and smooth cutoffs as in Section 6.16:

\[
U_j\Subset U'_j\Subset B_j,\qquad X=\bigcup_{j=1}^J U_j,
\qquad 0\leq\chi_j\leq1,\quad
\operatorname{Supp}\chi_j\Subset U'_j,\quad \chi_j=1\text{ on }U_j.
\]

Let `eta` be a continuous real `(1,1)`-form on `X`, not necessarily closed, and fix `m>0`. Suppose that `w_j` is quasi-plurisubharmonic on `B_j` and

\[
dd^cw_j\geq m\eta,
\qquad w_j\leq w_l+C_B\quad\text{on }U'_j\cap U'_l
\]

for a common `C_B>=0` and every pair. Quasi-plurisubharmonic functions here are locally integrable, in particular not identically minus infinity on an open component. Define each summand below to be zero where its cutoff vanishes, and put

\[
S=\sum_j\chi_j^2e^{w_j},\qquad G=\frac1m\log S,
\]

with `log 0=-infinity`. Choose `A>=0` such that

\[
H_j:=\chi_jdd^c\chi_j-\frac{i}{2\pi}\partial\chi_j\wedge\bar\partial\chi_j
\geq-A\omega\qquad(1\leq j\leq J).
\]

Then `G` is quasi-plurisubharmonic and

\[
\boxed{\quad dd^cG\geq\eta-\frac{2JAe^{C_B}}m\omega.\quad}
\]

The constant depends on the cutoffs, their number, the comparison constant, and the background used to measure their derivatives. In particular, an application with changing chart scale must track these quantities again; this lemma does not assert scale-independent constants.

### Proof: smooth inputs

For smooth `w_j`, use the differential identity proved in Lemma 6.17.1(2), also independently expanded in the first audit report. Its first term is semipositive; its second term is the convex combination of the forms `dd^c w_j` with coefficients `chi_j^2 e^{w_j}/S`. Consequently the second term is at least `m eta`.

At a point `x`, choose `i` with `x in U_i`. Since `chi_i(x)=1`, `S(x)>=e^{w_i(x)}>0`. For each index with `chi_j(x)>0`, the overlap comparison yields

\[
\frac{e^{w_j(x)}}{S(x)}\leq e^{C_B}.
\]

If `chi_j(x)=0`, then `partial chi_j(x)=0`, because `chi_j` is smooth and nonnegative, and hence `H_j(x)=0`. Thus the cutoff term is at least `-2JAe^{C_B} omega`. Dividing the identity by `m` gives the desired inequality. Nothing in this pointwise calculation requires a closed lower bound.

### Proof: singular inputs and preservation of the exact lower bound

Fix `x_0` and choose `i` with `x_0 in U_i`. Shrink to a relatively compact coordinate ball `W` contained in `U_i` and in every `U'_j` for which `x_0 in Supp chi_j`, and disjoint from all other cutoff supports. This is possible because there are only finitely many closed supports, and each is compactly contained in its `U'_j`. On `W` all active functions are defined and their pairwise comparison inequalities hold throughout `W`.

Put `q(z)=|z|^2` in these coordinates. On a slightly smaller ball, choose `L_0` so large that every active `w_j+L_0q` is plurisubharmonic. This is possible from the common continuous lower bound (and also directly from quasi-plurisubharmonicity). Use the same nonnegative smooth radial convolution kernel `rho_delta` of integral one for all active functions, and set

\[
w_{j,\delta}=(w_j+L_0q)*\rho_\delta-L_0q.
\]

On a fixed smaller ball these are smooth and decrease to `w_j` as `delta` decreases to zero. Indeed, radial averages of a plurisubharmonic, hence subharmonic, function increase with the averaging radius, and converge to its upper-semicontinuous representative; subtracting the fixed smooth `L_0q` preserves this monotonicity. The facts used here are the local submean/convolution facts, not a global regularization theorem.

The same convolution for all indices preserves comparison:

\[
w_{j,\delta}-w_{l,\delta}=(w_j-w_l)*\rho_\delta\leq C_B.
\]

Since `dd^c q` has constant coefficients, distributional differentiation and convolution give

\[
dd^cw_{j,\delta}=(dd^cw_j)*\rho_\delta
\geq m\eta_\delta,\qquad \eta_\delta=\eta*\rho_\delta.
\]

Here convolution of a form means convolution of its coefficients in the fixed coordinates. Positivity of currents is preserved by positive averaging. Continuity of `eta` gives local uniform convergence `eta_delta -> eta`.

Apply the smooth calculation to

\[
G_\delta=\frac1m\log\sum_j\chi_j^2e^{w_{j,\delta}}.
\]

It yields

\[
dd^cG_\delta\geq\eta_\delta-\frac{2JAe^{C_B}}m\omega.
\]

The right side has a uniform lower bound on a smaller coordinate ball. Choose `L_1` so that `G_delta+L_1q` is plurisubharmonic there for every sufficiently small `delta`. These functions decrease to `G+L_1q`, and their limit is not identically minus infinity: on this ball `chi_i=1`, so `G>=w_i/m`. Decreasing convergence of plurisubharmonic functions gives local L1 convergence. Therefore `dd^cG_delta -> dd^cG` as currents. The displayed lower inequalities pass to the limit, using local uniform convergence of `eta_delta` and closedness of the cone of positive currents. This proves the stated inequality with the original `eta`, not with an enlarged error. It also proves that `G` is quasi-plurisubharmonic. The argument is local at each point, so the inequality holds on `X`. QED.

### Application boundary

For a target `theta+dd^c phi>=gamma`, set `eta=gamma-theta` in this lemma. If local candidate potentials `v_{j,m}` satisfy `theta+dd^c v_{j,m}>=gamma` and `m v_{j,m}` satisfy the overlap comparison, then their cutoff sum has

\[
\theta+dd^cG_m\geq\gamma-\frac{2JAe^{C_B}}m\omega.
\]

The statement also allows a common lower bound `eta_m=gamma-theta-delta_m omega`, adding `delta_m` to the final loss. This isolates precisely what a local Bergman construction must supply.

**What is not proved here:** that the required local candidates exist with that lower bound; that their comparison constants remain controlled as the atlas shrinks; that an appropriate diagonal choice makes every error vanish; or that the resulting sequence has analytic/gentle singularities, is monotone in `m`, and has the required ideal inclusions. These are separate obligations. The present proof must not be substituted for the entire stronger Demailly theorem.

### Check against the existing Kähler proof

Section 6.16 explicitly assumes `(X,omega)` compact Kähler. Thus the local potential for `theta+(c'/m)omega` invoked in Step 3 of Lemma 6.17.1 is legitimate under the existing hypotheses. It is **not** a newly found error. That step would fail after an unqualified change to a nonclosed Hermitian background, since `dd^c` of a function is closed. The convolution-and-current-limit proof above is the proposed replacement needed in that generalization.

## 3. POME-REG-004: the multiplier-ideal transfer threshold is sharp

**Status:** verified existing implication and verified sharpness supplement. **Priority:** medium. **Source:** Lemma 6.17.4, tag `7EFB7FFA3AB8`.

Write

\[
M(\lambda,\lambda')=\frac{\lambda\lambda'}{\lambda'-\lambda},
\qquad 0<\lambda<\lambda'.
\]

The existing proof is correct: after normalizing `v<=0`, put `p=lambda'/lambda`. On `u>=pv`, the integrable quantity `|f|^2 exp(-lambda' v)` dominates `|f|^2 exp(-lambda u)`. On the complement,

\[
(m-\lambda)u-mv\leq\bigl(m(p-1)-\lambda p\bigr)v\leq0
\]

provided `m>=M(lambda,lambda')`. Since a holomorphic germ `f` is bounded on a sufficiently small neighborhood, integrability of `exp(m(v-u))` handles that complement. The argument includes equality at the threshold.

**Sharpness, with a complete local counterexample.** Fix any `0<m<M(lambda,lambda')`. Set

\[
a=\frac1\lambda,\qquad
b=\frac12\left(\max\{0,a-1/m\}+\frac1{\lambda'}\right).
\]

The strict inequality on `m` is exactly what ensures

\[
\max\{0,a-1/m\}<b<\frac1{\lambda'}<a.
\]

On the unit disc put `u=a log|z|^2` and `v=b log|z|^2`. Both are plurisubharmonic. A polar-coordinate integral shows that `|z|^{-2c}` is locally integrable in complex dimension one exactly when `c<1`. Therefore

\[
 e^{m(v-u)}=|z|^{-2m(a-b)}\in L^1_{\rm loc},
\]

because `m(a-b)<1`. However,

\[
1\in\mathcal I(\lambda'v)_0\quad\text{since }\lambda'b<1,
\qquad
1\notin\mathcal I(\lambda u)_0\quad\text{since }\lambda a=1.
\]

Thus no smaller universal threshold follows from the assumptions of Lemma 6.17.4. For example, `lambda=1`, `lambda'=2`, `m=1`, `a=1`, `b=1/4` has exactly these properties.

**Suggested addition:** retain the dependence on both multiplier parameters explicitly; the dyadic sufficient index in Theorem 6.17.6 can be written as `j>=max(1,ceil(log_2 M(lambda,lambda')))`. Add the disc example as a warning against silently making this index uniform over all multiplier parameters. There is no defect in the actual quantifiers of the theorem inspected here.

## 4. POME-DUP-001: adjudication of the two quasi-equisingular definitions

**Status:** equivalent canonical variants; retain the canonicalization. **Sources:** the two variants under `165F88FAE668`.

The Foundations wording asks for the multiplier-ideal inclusion for every sufficiently large index; the SGPT wording asks for one index for each pair `lambda<lambda'`. Since both require a decreasing sequence, an inclusion at `j_0` implies, for `j>=j_0`,

\[
\mathcal I(\lambda'\Phi_j)\subseteq\mathcal I(\lambda'\Phi_{j_0})
\subseteq\mathcal I(\lambda\varphi).
\]

The converse is immediate. SGPT allows a Kähler background form to be chosen, whereas Foundations fixes one in the section. On a compact manifold, if `omega_0` is the chosen positive form, `omega_0<=C omega` for a finite constant `C`; multiplying the errors by `C` preserves their decrease to zero. Thus this difference also does not change the definition. This pair is not an unresolved mathematical duplication. Its descendant equation placement is the separate defect POME-XREF-001.

## 5. Expanded dependency coverage

The fixed atlas construction in Section 6.16 was read, including its auxiliary metric, Lebesgue-number argument, nested balls, cutoff supports, and definition of fixed geometry. Its pairwise containing-chart condition is supplied, not merely assumed without discussion.

Lemma 6.16.2 was read in full. The gauge change to a common local weight, cutoff correction, logarithmic pole forcing the correction to vanish at the chosen point, and norm comparison were checked conditional on the singular-weight L2 theorem. In that argument the bound `u<=M` is used only to force a zero by a divergent local integral; it does not enter the operator-norm constant. This distinction supports the claimed independence from `theta`, `phi`, and `m` at this step.

Lemma 6.17.1 was now read in full, including Steps 3 and 4. Its nontrivial prerequisites must still be maintained in the dependency graph:

```text
EFA6E7FF99E6 (cutoff sum and gentle type)
  -> 82376665E5F7 (overlap comparison)
     -> 88735CB0C076 (singular L2)
        -> F85650C9CE6A (smooth L2)
  -> 09CBB2B6BA0F (analytic kernel and smooth factor after resolution)
     -> C2732E72E566 (Hilbert generation and bounded division)
        -> FE623FA661C4 (coherence and generation)
        -> 3B37857D5B64 (bounded division)
```

Lemma 6.15.3 was read in full. Its Hilbert-valued Taylor-series argument proves smoothness after division by the resolved ideal; Hironaka alone would not supply that estimate. Lemma 6.15.1 was read in full. The first assertion of Lemma 6.8.10 was checked via its explicit Baire-category proof: the coefficient-bounded representation sets are closed by normal-family compactness, cover the Hilbert space, and have a member with interior; translating and scaling gives uniformly bounded division coefficients on one neighborhood. Its second assertion still depends on the point-extension theorem.

Lemma 6.17.3 and Theorem 6.17.6 were reread in full. In particular, the integrability argument uses finite local generators on compact cutoff supports; it does not incorrectly integrate the full infinite-dimensional Bergman kernel over its entire domain. The overlap comparison and diagonal-extension input remain separately tracked.

Lemmas 6.5.2 and 6.5.3 were read in full. The minimal-solution argument was checked conditional on the L2 theorem, and the scalar differentiation and estimates in the logarithmic weight construction were checked. The exact arithmetic in the final optimization was independently replayed. Theorem 6.5.4 and Theorem 6.4.7 were read only in part in this increment; their concluding passages and all prerequisite operator-domain/exhaustion arguments have **not** been certified. Theorem 6.8.9 was also read only in part. These partial reads must not be recorded as completed transitive verification.

### Reproducibility anchors

All paths below are relative to the pinned Pome baseline; abbreviated extents above govern the review claim.

| Path | Blob SHA |
| --- | --- |
| `docs/tag/EFA6E7FF99E6/index.html` | `89d19cafc26d2eabb435e07e45f0f0ec392e29ff` |
| `docs/tag/82376665E5F7/index.html` | `a92a84051765f0c3ee98ab0bbfb1da0835e67f10` |
| `docs/tag/09CBB2B6BA0F/index.html` | `355a18d57a101d067b67457b1d10939c371ffc9b` |
| `docs/tag/C2732E72E566/index.html` | `7e2fb4ae5451f2cf1595b8400b2afe6628d93884` |
| `docs/tag/3B37857D5B64/index.html` | `cb880c7cce628118018f4b60ff68587ae3f5aed8` |
| `docs/tag/0822DB927561/index.html` | `dc488c3380c50ffd76de25795acf3fa146b2d1b4` |
| `docs/tag/EE99921A3F33/index.html` | `b3c68688ce0291e1e41a962c351ae27888f709c6` |
| `docs/tag/7EFB7FFA3AB8/index.html` | `b3144911336690408e94c9a5f2e11913775fe96e` |
| `docs/tag/165F88FAE668/index.html` | `9afd5b3aa641c15aa15c71c9d875ba9d90507acb` |
| `docs/tag/EF5655B5F536/index.html` | `4b55bb1dea6355d96974edce6f57b51b8fbe77ff` |
| `scripts/numbering.py` | `227acd07c81de12363675ab68b5ebe76b6586d88` |

## 6. Checks performed and remaining work

The standard-library script `../checks/check_transfer_threshold.py` was executed locally with exact rational arithmetic. Results:

```json
{
  "status": "PASS",
  "below_threshold_counterexamples": 96,
  "at_or_above_threshold_coefficient_checks": 96,
  "twisted_L2_constant_checks": 9
}
```

`python -m py_compile` also passed. These are arithmetic and syntax checks, not formal verification of the analytic lemmas. The proofs above, rather than the finite test grid, establish the universal mathematical claims.

A direct pinned public-HTML download was attempted in this session and failed because the container could not resolve `raw.githubusercontent.com`. The GitHub connector supplied the actual texts. No full checkout, Python/JavaScript project suite, complete site build, or desktop/mobile browser test was run. The numbering defect was verified in actual generated HTML, not in a locally rebuilt site. Only audit notes and the small independent check script are being committed; the reading edition is unchanged.

Next work: finish the singular/smooth L2 and extension chain, including their operator-domain and exhaustion inputs; construct and estimate the local Bergman inputs for a prescribed continuous lower bound, tracking chart-scale dependence and diagonal choices; and trace POME-XREF-001 through canonicalization/placement before proposing a production patch. Preserve the distinction between a repaired component and a fully proved approximation theorem.

## Sources: target comparison, not an imported proof

J.-P. Demailly, *Analytic Methods in Algebraic Geometry*, Section 14, Theorem 14.12 and Corollary 14.13, printed pp. 142–143, were inspected in the author's publicly available manuscript, including rendered pages. They identify the target with a continuous prescribed lower form on a compact complex manifold. This external source is used only to check scope and attribution, not as a replacement for the missing internal proof. Its normalization differs from Pome's; no coefficient or rate has been transferred without conversion.

Author's manuscript: https://www-fourier.univ-grenoble-alpes.fr/~demailly/manuscripts/analmeth_book.pdf
