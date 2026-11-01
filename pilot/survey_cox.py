"""Survey-weighted Cox model and delete-one-PSU jackknife variance.

Jackknife CIs are a secondary check; they can differ from survey::svycoxph Taylor linearisation
(see results/cause-specific-mortality/PROOF.md).
"""
from __future__ import annotations

import numpy as np


def cox_fit(X, t, e, w, iters=100):
    """Weighted Cox proportional hazards, Breslow ties. X should already be scaled if desired."""
    n, p = X.shape
    o = np.argsort(-t, kind="mergesort")
    X, t, e, w = X[o], t[o], e[o], w[o]
    _, first = np.unique(-t, return_index=True)
    last = np.r_[first[1:] - 1, n - 1]
    group_end = np.repeat(last, np.diff(np.r_[first, n]))
    ev = e == 1
    we = w[ev]

    def parts(beta, need_hess=True):
        eta = X @ beta
        shift = eta.max()
        r = w * np.exp(eta - shift)
        s0 = np.cumsum(r)[group_end]
        ll = np.sum(we * (eta[ev] - shift - np.log(s0[ev])))
        if not need_hess:
            return ll, None, None
        s1 = np.cumsum(r[:, None] * X, axis=0)[group_end]
        s2 = np.cumsum(r[:, None, None] * X[:, :, None] * X[:, None, :], axis=0)[group_end]
        xbar = s1[ev] / s0[ev, None]
        grad = (we[:, None] * (X[ev] - xbar)).sum(0)
        hess = -(we[:, None, None] * (s2[ev] / s0[ev, None, None] - xbar[:, :, None] * xbar[:, None, :])).sum(0)
        return ll, grad, hess

    beta = np.zeros(p)
    ll, grad, hess = parts(beta)
    for _ in range(iters):
        step = np.linalg.solve(hess, grad)
        k = 1.0
        while True:
            cand = beta - k * step
            ll_c, _, _ = parts(cand, need_hess=False)
            if np.isfinite(ll_c) and ll_c >= ll - 1e-12:
                break
            k /= 2
            if k < 1e-8:
                return beta, hess
        beta = cand
        if np.max(np.abs(k * step)) < 1e-9:
            break
        ll, grad, hess = parts(beta)
    return beta, hess


def cox_vcov_design(X, t, e, w, strata, psu, beta, hess):
    """Design-based covariance via delete-one-PSU jackknife (matches survey::svycoxph here)."""
    strata = np.asarray(strata)
    psu = np.asarray(psu)
    keys = [(int(s), int(p)) for s in np.unique(strata) for p in np.unique(psu[strata == s])]
    m = len(keys)
    if m < 2:
        return np.linalg.inv(-hess)
    betas = []
    for s, p in keys:
        msk = ~((strata == s) & (psu == p))
        b, _ = cox_fit(X[msk], t[msk], e[msk], w[msk])
        betas.append(b)
    betas = np.vstack(betas)
    diffs = betas - beta
    return (m - 1) / m * (diffs.T @ diffs)


def cindex(risk, t, e, w):
    num = den = 0.0
    for i in np.where(e == 1)[0]:
        m = t > t[i]
        if not m.any():
            continue
        ww = w[i] * w[m]
        num += np.sum(ww * ((risk[i] > risk[m]) + 0.5 * (risk[i] == risk[m])))
        den += np.sum(ww)
    return num / den if den else float("nan")
