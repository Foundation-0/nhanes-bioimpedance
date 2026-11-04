"""Refit every NHANES 1999-2004 bioimpedance spectrum and compare with CDC's published Cole parameters.

Writes per-participant fits to data/fits.csv (not committed) and prints the aggregate tables that go into
results/pilot-2026-10-31.md. Usage: python3 pilot/fetch.py && python3 pilot/refit.py
Takes a few minutes on one core.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cole import F_LABEL, F_LOG, R_COLS, X_COLS, fit_spectrum  # noqa: E402
from fits_csv import FLOAT_FORMAT  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CYCLES = {"1999-2000": "BIX.xpt", "2001-2002": "BIX_B.xpt", "2003-2004": "BIX_C.xpt"}
FIT_CODES = {0: "excellent", 1: "good", 2: "marginal", 3: "questionable", 4: "bad", 5: "could not be fit",
             7: "no BIA data"}


def load():
    frames = []
    for cycle, name in CYCLES.items():
        df = pd.read_sas(DATA / name, format="xport")
        df["cycle"] = cycle
        frames.append(df)
    df = pd.concat(frames, ignore_index=True)
    df["BIDFIT"] = df["BIDFIT"].round()  # SAS transport stores 0 as 5.4e-79
    return df


def main():
    df = load()
    exam = df[df.BIAEXSTS.round() == 1].copy()
    has_spec = exam[R_COLS + X_COLS].notna().all(axis=1)
    print(f"Participants in BIX files: {len(df)}; completed exams: {len(exam)}; with all 100 values: {int(has_spec.sum())}")
    print()
    print("CDC fit code among completed exams")
    for cycle in CYCLES:
        e = exam[exam.cycle == cycle]
        counts = e.BIDFIT.value_counts().reindex(sorted(FIT_CODES), fill_value=0)
        print(f"  {cycle}: " + ", ".join(f"{FIT_CODES[k]} {int(v)}" for k, v in counts.items()))
    print()

    rows = []
    for _, r in exam[has_spec].iterrows():
        R, X = r[R_COLS].to_numpy(float), r[X_COLS].to_numpy(float)
        a = fit_spectrum(F_LABEL, R, X)
        b = fit_spectrum(F_LOG, R, X)
        if a is None:
            continue
        rows.append(dict(SEQN=int(r.SEQN), cycle=r.cycle, cdc_fit=int(r.BIDFIT), rms_log_grid=b["rms"] if b else np.nan,
                         cdc_re=r.BIDRECF, cdc_ri=r.BIDRICF, cdc_fc=r.BIDFC, cdc_alpha=r.BIDALPHA, cdc_td=r.BIDTD,
                         cdc_cm=r.BIDCM, phase_50k_deg=float(np.degrees(np.arctan2(X[21], R[21]))), **a))
    fits = pd.DataFrame(rows)
    fits.to_csv(DATA / "fits.csv", index=False, float_format=FLOAT_FORMAT)

    print(f"Spectra refitted: {len(fits)}")
    print(f"Labelled frequency grid fits better than an exact log grid in "
          f"{100 * (fits.rms < fits.rms_log_grid).mean():.0f}% of spectra "
          f"(median rms residual {fits.rms.median():.4f} vs {fits.rms_log_grid.median():.4f}).")
    print()
    print("Agreement with CDC's Cole parameters, by CDC fit code (median and 95th percentile of |relative difference|)")
    print(f"  {'CDC fit code':18s} {'n':>5s}  {'Re':>13s}  {'Ri':>13s}  {'fc':>13s}  {'alpha (abs)':>13s}  {'our rms':>8s}")
    for code in (0, 1, 2, 3, 4):
        g = fits[fits.cdc_fit == code]
        if not len(g):
            continue
        cells = []
        for ours, cdc in (("re", "cdc_re"), ("ri", "cdc_ri"), ("fc_khz", "cdc_fc")):
            d = ((g[ours] - g[cdc]) / g[cdc]).abs()
            cells.append(f"{100 * d.median():5.1f}% {100 * d.quantile(.95):5.1f}%")
        d = (g.alpha - g.cdc_alpha).abs()
        cells.append(f"{d.median():6.3f} {d.quantile(.95):6.3f}")
        print(f"  {FIT_CODES[code]:18s} {len(g):5d}  " + "  ".join(cells) + f"  {g.rms.median():8.4f}")
    print()
    bad = fits[fits.cdc_fit == 5]
    if len(bad):
        print(f"Spectra CDC could not fit (code 5): {len(bad)}. Our fit: median rms {bad.rms.median():.4f}; "
              f"rms below 0.01 for {int((bad.rms < 0.01).sum())}; CDC Re present for {int(bad.cdc_re.notna().sum())}.")
    good = fits[fits.cdc_fit == 0]
    print(f"Our rms residual for CDC 'excellent' spectra: median {good.rms.median():.4f}, "
          f"95th percentile {good.rms.quantile(.95):.4f}, above 0.01 for {int((good.rms > 0.01).sum())}.")
    print(f"Time delay Td (ns): CDC median {fits.cdc_td.median():.2f}, ours {fits.td_ns.median():.2f}; "
          f"CDC Td below 0 for {int((fits.cdc_td < 0).sum())} spectra.")
    fc = fits.cdc_fc.dropna()
    whole = np.isclose(fc, np.round(fc)).mean()
    print(f"CDC's fc is a whole number of kHz in {100 * whole:.0f}% of the {len(fc)} spectra it fitted, so fc agreement is limited to about "
          f"1 kHz in 50; Cm has two decimals (nF).")
    print(f"Phase angle at the 50 kHz label: median {fits.phase_50k_deg.median():.2f} degrees "
          f"(IQR {fits.phase_50k_deg.quantile(.25):.2f}-{fits.phase_50k_deg.quantile(.75):.2f}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
