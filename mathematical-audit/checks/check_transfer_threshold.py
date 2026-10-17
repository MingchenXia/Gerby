#!/usr/bin/env python3
"""Exact arithmetic checks for the 2026-10-16 second Pome audit.

These checks supplement the written proof. They do not verify the global
Demailly theorem, the L2 analytic inputs, or the website build.
Python 3.10+; standard library only; no network or repository writes.
"""
from fractions import Fraction as Q
import json


def critical(lam: Q, lam_prime: Q) -> Q:
    if not (0 < lam < lam_prime):
        raise ValueError("Require 0 < lambda < lambda_prime")
    return lam * lam_prime / (lam_prime - lam)


def counterexample(lam: Q, lam_prime: Q, m: Q) -> dict[str, str]:
    """u=A log|z|^2, v=B log|z|^2; f=1 violates transfer below threshold."""
    if not (0 < m < critical(lam, lam_prime)):
        raise ValueError("Require 0 < m < the transfer threshold")
    a = 1 / lam
    low = max(Q(0), a - 1 / m)
    high = 1 / lam_prime
    assert low < high
    b = (low + high) / 2
    assert 0 < b < a
    assert m * (a - b) < 1  # exp(m(v-u)) locally integrable in C.
    assert lam_prime * b < 1  # 1 is in I(lambda_prime v).
    assert lam * a == 1  # 1 is not in I(lambda u): logarithmic divergence.
    return {"lambda": str(lam), "lambda_prime": str(lam_prime),
            "m": str(m), "A": str(a), "B": str(b),
            "m(A-B)": str(m * (a - b)),
            "lambda_prime_B": str(lam_prime * b),
            "lambda_A": str(lam * a)}


def main() -> None:
    sharp_count = 0
    threshold_count = 0
    for lam in map(Q, ["1/3", "1/2", "1", "3/2", "2", "5"]):
        for ratio in map(Q, ["6/5", "3/2", "2", "4"]):
            lam_prime = ratio * lam
            bound = critical(lam, lam_prime)
            for factor in map(Q, ["1/5", "1/2", "9/10", "99/100"]):
                counterexample(lam, lam_prime, factor * bound)
                sharp_count += 1
            for factor in map(Q, ["1", "3/2", "2", "7"]):
                m = factor * bound
                coefficient = m * (ratio - 1) - lam * ratio
                assert m > lam and coefficient >= 0
                assert (coefficient == 0) == (factor == 1)
                threshold_count += 1
    l2_count = 0
    for k in range(1, 10):
        root_a = Q(k, 10)
        a = root_a ** 2
        t = 1 + 1 / root_a
        lhs = t / (t - 1) * (1 + t * a / (1 - a))
        assert lhs == (1 + root_a) / (1 - root_a)
        l2_count += 1
    print(json.dumps({
        "status": "PASS",
        "arithmetic": "exact fractions; no floating-point tests",
        "below_threshold_counterexamples": sharp_count,
        "at_or_above_threshold_coefficient_checks": threshold_count,
        "twisted_L2_constant_checks": l2_count,
        "example": counterexample(Q(1), Q(2), Q(1)),
        "scope": "Arithmetic constraints only; see the written analytic proof."
    }, indent=2))


if __name__ == "__main__":
    main()
