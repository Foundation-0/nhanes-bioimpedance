"""What the full bioimpedance spectrum adds: DXA lean mass and all-cause mortality, against 50 kHz phase angle.

Run after pilot/fetch.py and pilot/refit.py (which writes data/fits.csv). Prints aggregate tables only.

  O1  The spectra CDC could not fit but we can, and the fits with a negative time delay.
  O2  DXA lean mass (kg) predicted from a classic 50 kHz equation vs the same plus full-spectrum features.
  O3  All-cause mortality (NCHS public-use Linked Mortality Files, to 31 Dec 2019), adults 20-49 at the exam:
      Cox models of age and sex, + 50 kHz phase angle, + full-spectrum features.

Both O2 and O3 hold out one survey cycle at a time: fit on two cycles, test on the third. Survey design: the
combined 1999-2004 MEC weight (2/3 x WTMEC4YR for 1999-2002, 1/3 x WTMEC2YR for 2003-04, as NCHS advises for
combining cycles) weights the model fits and the test statistics. Confidence intervals come from a bootstrap that
resamples primary sampling units within strata (SDMVSTRA, SDMVPSU) in the test cycle.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cole import LABEL_KHZ, R_COLS, X_COLS  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CYCLES = [("1999-2000", "", "1999_2000"), ("2001-2002", "_B", "2001_2002"), ("2003-2004", "_C", "2003_2004")]
RNG = np.random.default_rng(20261031)
NBOOT = 300


def phase_deg(R, X, khz):
    k = LABEL_KHZ.index(khz)
    return np.degrees(np.arctan2(np.abs(X[:, k]), R[:, k]))


def load():
    frames = []
    for cycle, sfx, lmf in CYCLES:
        bix = pd.read_sas(DATA / f"BIX{sfx}.xpt", format="xport")
        bix = bix[bix.BIAEXSTS.round() == 1]
        R, X = bix[R_COLS].to_numpy(float), bix[X_COLS].to_numpy(float)
        b = pd.DataFrame({"SEQN": bix.SEQN.astype(int).values, "R50": R[:, LABEL_KHZ.index(50)],
                          "pha5": phase_deg(R, X, 5), "pha50": phase_deg(R, X, 50), "pha200": phase_deg(R, X, 200)})
        demo = pd.read_sas(DATA / f"DEMO{sfx}.xpt", format="xport")
        w = demo.WTMEC4YR * 2 / 3 if "WTMEC4YR" in demo else demo.WTMEC2YR / 3
        d = pd.DataFrame({"SEQN": demo.SEQN.astype(int), "male": (demo.RIAGENDR == 1).astype(float),
                          "age": np.where(demo.RIDAGEEX.notna(), demo.RIDAGEEX / 12, demo.RIDAGEYR),
                          "w": w, "strata": demo.SDMVSTRA, "psu": demo.SDMVPSU})
        bmx = pd.read_sas(DATA / f"BMX{sfx}.xpt", format="xport")[["SEQN", "BMXHT", "BMXWT"]]
        bmx["SEQN"] = bmx.SEQN.astype(int)
        dxx = pd.read_sas(DATA / f"DXX{sfx}.xpt", format="xport")[["SEQN", "_MULT_", "DXDTOLE"]]
        dxx = dxx.pivot_table(index="SEQN", columns="_MULT_", values="DXDTOLE") / 1000  # kg, one column per imputation
        dxx.columns = [f"lean{int(c)}" for c in dxx.columns]
        dxx.index = dxx.index.astype(int)
        mort = pd.read_fwf(DATA / f"NHANES_{lmf}_MORT_2019_PUBLIC.dat",
                           colspecs=[(0, 6), (14, 15), (15, 16), (45, 48)],
                           names=["SEQN", "eligstat", "mortstat", "months"], na_values=["."])
        x = b.merge(d, on="SEQN").merge(bmx, on="SEQN", how="left").merge(dxx, left_on="SEQN", right_index=True, how="left")
        x = x.merge(mort, on="SEQN", how="left")
        x["cycle"] = cycle
        frames.append(x)
    df = pd.concat(frames, ignore_index=True)
    fits = pd.read_csv(DATA / "fits.csv")
    df = df.merge(fits[["SEQN", "cdc_fit", "re", "ri", "fc_khz", "alpha", "td_ns", "rms", "cdc_td"]], on="SEQN")
    df["ht2_R50"] = df.BMXHT ** 2 / df.R50
    df["ht2_Re"] = df.BMXHT ** 2 / df.re
    df["ht2_Ri"] = df.BMXHT ** 2 / df.ri
    df["log_ri_re"] = np.log(df.ri / df.re)
    df["log_fc"] = np.log(df.fc_khz)
    return df


# ---------------------------------------------------------------- O1
def o1(df):
    print("O1. Spectra CDC could not fit, and negative time delays")
    rec = df[(df.cdc_fit == 5) & (df.rms < 0.01)]
    ok = df[df.cdc_fit == 0]
    print(f"   CDC code 5 with our relative rms residual below 1%: {len(rec)}. Their fitted parameters against CDC's "
          f"'excellent' spectra (median [5th-95th percentile]):")
    for c, lab in (("re", "Re (ohm)"), ("ri", "Ri (ohm)"), ("alpha", "alpha"), ("fc_khz", "fc (kHz)"), ("td_ns", "Td (ns)")):
        q = ok[c].quantile([.05, .5, .95]).values
        inside = ((rec[c] >= q[0]) & (rec[c] <= q[2])).sum()
        print(f"     {lab:9s} recoverable median {rec[c].median():8.2f}; excellent {q[1]:8.2f} [{q[0]:.2f}-{q[2]:.2f}]; "
              f"{inside} of {len(rec)} inside that range")
    neg = df[df.cdc_td < 0]
    print(f"   CDC Td < 0: {len(neg)} spectra; CDC fit codes {neg.cdc_fit.value_counts().sort_index().to_dict()}; "
          f"our Td for them: median {neg.td_ns.median():.2f} ns, below 0 for {int((neg.td_ns < 0).sum())}; "
          f"our rms median {neg.rms.median():.4f} (all spectra {df.rms.median():.4f}).")
    print()


# ---------------------------------------------------------------- shared
def wls(X, y, w):
    A = np.column_stack([np.ones(len(X)), X])
    sw = np.sqrt(w)
    beta, *_ = np.linalg.lstsq(A * sw[:, None], y * sw, rcond=None)
    return beta


def wr2(y, yhat, w):
    ybar = np.average(y, weights=w)
    return 1 - np.sum(w * (y - yhat) ** 2) / np.sum(w * (y - ybar) ** 2)


def boot_idx(test):
    """Resample PSUs within strata."""
    idx = []
    for _, g in test.groupby("strata"):
        psus = g.psu.unique()
        pick = RNG.choice(psus, size=len(psus), replace=True)
        for p in pick:
            idx.append(g.index[g.psu == p].values)
    return np.concatenate(idx)


# ---------------------------------------------------------------- O2
def o2(df):
    base = ["male", "age", "BMXWT", "ht2_R50"]
    full = base + ["ht2_Re", "ht2_Ri", "alpha", "log_fc", "pha5", "pha200"]
    leans = [c for c in df.columns if c.startswith("lean")]
    d = df.dropna(subset=base + full + leans + ["w"])
    d = d[(d.rms < 0.02) & (d.w > 0)]
    print(f"O2. DXA lean mass excluding bone (kg), {len(d)} participants aged 8-49 with BIA, DXA and body measures; "
          f"held-out cycle; weighted R2 and RMSE averaged over the 5 DXA imputations")
    print(f"   {'test cycle':10s} {'n':>5s}  {'50 kHz model R2':>15s} {'RMSE':>6s}  {'+ full spectrum R2':>18s} {'RMSE':>6s}  "
          f"{'gain in R2 (95% CI)':>22s}")
    for cycle in d.cycle.unique():
        tr, te = d[d.cycle != cycle], d[d.cycle == cycle].reset_index(drop=True)
        res = {}
        for name, cols in (("base", base), ("full", full)):
            r2s, rmses, preds = [], [], []
            for lean in leans:
                beta = wls(tr[cols].to_numpy(float), tr[lean].to_numpy(float), tr.w.to_numpy(float))
                yhat = beta[0] + te[cols].to_numpy(float) @ beta[1:]
                preds.append(yhat)
                r2s.append(wr2(te[lean].to_numpy(float), yhat, te.w.to_numpy(float)))
                rmses.append(np.sqrt(np.average((te[lean] - yhat) ** 2, weights=te.w)))
            res[name] = (np.mean(r2s), np.mean(rmses), np.mean(preds, axis=0))
        y = te[leans].mean(axis=1).to_numpy(float)
        gains = []
        for _ in range(NBOOT):
            i = boot_idx(te)
            gains.append(wr2(y[i], res["full"][2][i], te.w.values[i]) - wr2(y[i], res["base"][2][i], te.w.values[i]))
        lo, hi = np.percentile(gains, [2.5, 97.5])
        print(f"   {cycle:10s} {len(te):5d}  {res['base'][0]:15.3f} {res['base'][1]:6.2f}  {res['full'][0]:18.3f} "
              f"{res['full'][1]:6.2f}  {res['full'][0] - res['base'][0]:+8.3f} ({lo:+.3f}, {hi:+.3f})")
    print()


# ---------------------------------------------------------------- O3
def cox_fit(X, t, e, w, iters=100):
    """Weighted Cox proportional hazards, Breslow ties, Newton-Raphson with step halving.
    Returns beta for the columns of X (standardise X first)."""
    n, p = X.shape
    o = np.argsort(-t, kind="mergesort")
    X, t, e, w = X[o], t[o], e[o], w[o]
    # the risk set at time t is everyone with time >= t: up to the last index of t's tie group (descending order)
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
                return beta
        beta = cand
        if np.max(np.abs(k * step)) < 1e-9:
            break
        ll, grad, hess = parts(beta)
    return beta


def cindex(risk, t, e, w):
    """Harrell's C, each comparable pair weighted by the product of survey weights."""
    num = den = 0.0
    for i in np.where(e == 1)[0]:
        m = t > t[i]
        if not m.any():
            continue
        ww = w[i] * w[m]
        num += np.sum(ww * ((risk[i] > risk[m]) + 0.5 * (risk[i] == risk[m])))
        den += np.sum(ww)
    return num / den


def o3(df):
    sets = {
        "age + sex": ["age", "male"],
        "+ 50 kHz phase angle": ["age", "male", "pha50"],
        "+ full spectrum": ["age", "male", "pha50", "pha5", "pha200", "alpha", "log_fc", "log_ri_re"],
    }
    d = df[(df.age >= 20) & (df.eligstat == 1) & df.mortstat.notna() & df.months.notna() & (df.rms < 0.02) & (df.w > 0)]
    d = d.dropna(subset=sorted({c for v in sets.values() for c in v})).reset_index(drop=True)
    print(f"O3. All-cause mortality to 31 Dec 2019, adults 20-49 at the exam: {len(d)} participants, "
          f"{int(d.mortstat.sum())} deaths, median follow-up {d.months.median() / 12:.1f} years")
    allX = {k: d[v].to_numpy(float) for k, v in sets.items()}
    mu = {k: v.mean(0) for k, v in allX.items()}
    sd = {k: v.std(0) for k, v in allX.items()}
    beta_all = cox_fit((allX["+ 50 kHz phase angle"] - mu["+ 50 kHz phase angle"]) / sd["+ 50 kHz phase angle"],
                       d.months.to_numpy(float), d.mortstat.to_numpy(int), d.w.to_numpy(float) / d.w.mean())
    hr = np.exp(beta_all[2] / sd["+ 50 kHz phase angle"][2])
    print(f"   All cycles, weighted Cox of age, sex and 50 kHz phase angle: hazard ratio {hr:.2f} per degree of phase angle")
    print(f"   {'test cycle':10s} {'n':>5s} {'deaths':>6s}  " + "  ".join(f"{k:>20s}" for k in sets) +
          f"  {'full minus 50 kHz (95% CI)':>28s}")
    for cycle in d.cycle.unique():
        trm, tem = (d.cycle != cycle).values, (d.cycle == cycle).values
        te = d[tem].reset_index(drop=True)
        risks = {}
        for k in sets:
            X = (allX[k] - mu[k]) / sd[k]
            b = cox_fit(X[trm], d.months.values[trm], d.mortstat.values[trm].astype(int), d.w.values[trm] / d.w.values[trm].mean())
            risks[k] = X[tem] @ b
        t, e, w = te.months.to_numpy(float), te.mortstat.to_numpy(int), te.w.to_numpy(float)
        cs = {k: cindex(risks[k], t, e, w) for k in sets}
        diffs = []
        for _ in range(NBOOT):
            i = boot_idx(te)
            diffs.append(cindex(risks["+ full spectrum"][i], t[i], e[i], w[i]) -
                         cindex(risks["+ 50 kHz phase angle"][i], t[i], e[i], w[i]))
        lo, hi = np.percentile(diffs, [2.5, 97.5])
        print(f"   {cycle:10s} {len(te):5d} {int(e.sum()):6d}  " + "  ".join(f"{cs[k]:20.3f}" for k in sets) +
              f"  {cs['+ full spectrum'] - cs['+ 50 kHz phase angle']:+14.3f} ({lo:+.3f}, {hi:+.3f})")
    print()


def main():
    df = load()
    o1(df)
    o2(df)
    o3(df)
    return 0


if __name__ == "__main__":
    sys.exit(main())
