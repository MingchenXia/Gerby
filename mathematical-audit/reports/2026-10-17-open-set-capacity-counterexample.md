# POME-CAP-001: bounded monotone convergence need not be global capacity convergence

Date: 17 October 2026. Status: **confirmed error in the statement as written**. Severity: high.

Reviewed main: `66f8176be2a006b9404ae6db49ee15621dea5523`.
Audit branch at the start of this pass: `91f48c1323d7c717c53204a6bc3b3d362010b726`.

## Scope change

The author expressly requested on 17 October 2026 that the audit skip Demailly approximation and inspect the rest of Pome. Earlier regularization priorities are superseded. Existing regularization notes remain historical, deferred-by-user rather than resolved. This report begins the new broad-scope pass; it does not use or reopen that programme.

## Exact locations and hypotheses

- Proposition 13.12.7: permanent tag `D56D6D4A5E94`, source tag `606EEC85`; `docs/tag/D56D6D4A5E94/index.html`, blob `607490740d21c3c1c6fa524af8ab3bf662dd6311`. Its decreasing alternative allows any open U in X and a decreasing net in PSH(U,theta) with psh pointwise limit, and concludes convergence in capacity.
- Definition 13.12.6: permanent tag `F7490AE48EAC`. Its exceptional-set capacities are taken on all of U, not on each compact subset of U.
- Definition 13.12.1: permanent tag `C96BE5099B6A`. Capacity is the global theta-capacity, using potentials between V_theta-1 and V_theta.
- All three occur in `docs/sections/non-pluripolar-products--quasi-continuous-functions/index.html`, blob `e6e4112ba820be7f74ab4b5a2a3490eb731f162d`. The section assumes X compact Kahler and theta smooth closed in a big class. Its paragraph after Proposition 13.12.7 cites GZ17, Proposition 4.25, and asserts that the proof also works for nets. That citation does not repair the global-versus-local issue below.

The counterexample is already a **sequence of uniformly bounded smooth functions**. Neither replacing nets by sequences nor adding uniform boundedness repairs the assertion.

## Complete counterexample

Use Pome's normalization dd^c = i/(2 pi) partial bar-partial. Let X be the projective line. In its affine coordinate z put

\[
\theta=\omega_{\rm FS}=dd^c\log(1+|z|^2),\qquad
U=\{|z|<1\},\qquad u_j(z)=|z|^{2j},\quad j\geq1.
\]

The form theta is smooth, positive and closed on X, and its total mass is one: its affine density is dx dy/[pi(1+|z|^2)^2], so its integral is the integral of 2r/(1+r^2)^2 from zero to infinity, namely one. Also V_theta=0: zero itself is an admissible theta-psh function bounded above by zero.

Each u_j is smooth and subharmonic, because Delta |z|^{2j}=4j^2|z|^{2j-2}>=0. Consequently u_j belongs to PSH(U,theta). We have 0<=u_j<=1 and u_j decreases pointwise to zero on U. These satisfy the decreasing alternative of the proposition, including stronger boundedness and smoothness than required.

Nevertheless,

\[
\boxed{\operatorname{Cap}_\theta\{z\in U:u_j(z)>1/2\}=1
\quad\text{for every }j\geq1.}
\]

### A global admissible capacity test with mass on a circle

For 3/4<=R^2<1 define

\[
f_R(z)=\log\max\{|z|^2,R^2\},\qquad
v_R(z)=f_R(z)-\log(1+|z|^2).
\]

For large |z|, v_R=-log(1+|1/z|^2), so it extends smoothly across infinity with value zero. It is continuous at |z|=R. It decreases radially up to that circle and increases afterwards. Therefore

\[
\log\frac{R^2}{1+R^2}\leq v_R\leq0.
\]

The lower bound is at least log(3/7)>-1: e>1+1+1/2>7/3 proves the last inequality. Thus -1<=v_R<=0 on X.

Let sigma_R be normalized angular measure on |z|=R. Direct distributional differentiation gives

\[
\theta+dd^cv_R=dd^cf_R=\sigma_R.
\]

To check the normalization, dd^cf=(Delta f)/(4 pi) dx dy. The function r f_R'(r) is zero for r<R and two for r>R, so its radial derivative is 2 delta_R. For every smooth test function a supported in the affine chart this gives

\[
\int a\,dd^cf_R=\frac1{2\pi}\int_0^{2\pi}a(Re^{it})\,dt.
\]

There is no extra mass at infinity, since theta+dd^cv_R vanishes in its neighbourhood. Positivity is explicit, and locally v_R is a subharmonic function minus a smooth function. Since v_R is bounded, its degree-one non-pluripolar product is the ordinary current above. Thus v_R is admissible for Definition 13.12.1.

### The exceptional annulus has full capacity

Set R_j^2=1-1/(4j). Then 3/4<=R_j^2<1, and on |z|=R_j,

\[
u_j(z)=\left(1-\frac1{4j}\right)^j\geq1-\frac{j}{4j}=\frac34>\frac12.
\]

The inequality (1-t)^j>=1-jt for 0<=t<=1 follows by induction: multiplying the inductive bound by 1-t yields 1-(j+1)t+jt^2>=1-(j+1)t. The whole circle supporting sigma_{R_j} lies in E_j={u_j>1/2}. Consequently

\[
\operatorname{Cap}_\theta(E_j)\geq
\int_{E_j}(\theta+dd^cv_{R_j})=1.
\]

Every admissible capacity test v is bounded, and its positive degree-one current has total mass one: dd^cv paired with the constant function one vanishes on the compact manifold. Thus Cap_theta(E_j)<=1 as well. The boxed equality follows and disproves the statement with the definition actually printed.

## Diagnosis and proposed repair

The annuli escape every compact subset of U while retaining global capacity. Small area does not imply small capacity; continuity under decreasing arbitrary open sets cannot be assumed here.

In this very example, for K compactly contained in U and q=max_K |z|^2<1, sup_K u_j<=q^j. For each positive threshold the exceptional set on K is eventually empty. This is exactly the distinction between local convergence in capacity and the definition testing all of U.

Proposed correction: formulate Proposition 13.12.7 with **local** capacity convergence, testing

\[
\operatorname{Cap}_\theta\bigl(K\cap\{\varphi_i>\varphi+\delta\}\bigr),
\qquad
\operatorname{Cap}_\theta\bigl(K\cap\{\varphi_i<\varphi-\delta\}\bigr)
\]

for each K compactly contained in U and delta>0, and supply the corresponding proof, including the net version. Alternatively separate a compact global statement with U=X from the local open-set statement. This report proves the counterexample and its local behaviour, not the entire corrected theorem for arbitrary increasing and decreasing nets.

Do not silently change Definition 13.12.6 everywhere: some downstream uses may genuinely require global capacity convergence. Inspect uses of `D56D6D4A5E94` on arbitrary U, distinguishing compactly supported current tests from estimates on all of U. The complete dependent list has not been enumerated. Preserve tags and propose source/integration repairs separately; this audit does not modify published statements.

## Additional coverage and verification limits

The complete mathematical body of Section 13.12 was read. Adjacent Theorem 13.12.8 (`272876B00528`, blob `3851c76d7b72a1da80c3864b3dc57e9a0220ddc3`) has no proof attached in the inspected tag or enclosing section; the latter cites GZ17, Theorem 4.26. An internal replacement still needs locating. This is an observed citation-dependent presentation, not a counterexample to that weighted current-convergence theorem.

No claim of whole-project review, project tests, site build, or formal verification is made. The mathematical result is the explicit analytic counterexample above; no numerical experiment substitutes for its proof. Continue the broad coverage pass through envelopes, energy, Hermitian geometry, and the other chapters. Demailly approximation remains excluded by the author.
