"""Aggregate replay checks for local data/fits.csv (not committed)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from fits_csv import AUX_NUMERIC_COLUMNS, COLE_COLUMNS, FLOAT_FORMAT

# Verification refit pins OpenBLAS to one kernel (DYNAMIC_ARCH wheels otherwise pick by CPU).
OPENBLAS_CORETYPE_PIN = "Haswell"
N_SPECTRA = 13_276
# fits.csv uses FLOAT_FORMAT; worst-case aggregate drift from rounding each value at write/read.
CSV6_HALF_ULP = 0.5e-6

AGG_STATS = ("sum", "median", "mean", "min", "max", "std", "sumsq", "p1", "p5", "p95", "p99")
CHECK_COLUMNS = COLE_COLUMNS + AUX_NUMERIC_COLUMNS
AGGREGATE_REL_TOL = 1e-9


@dataclass(frozen=True)
class PlausibilityBand:
    low: float
    high: float
    label: str  # KNOWN | CONJECTURE


PLAUSIBILITY_BANDS: dict[str, PlausibilityBand] = {
    "re": PlausibilityBand(1.0, 50_000.0, "KNOWN"),
    "ri": PlausibilityBand(1.0, 500_000.0, "KNOWN"),
    "fc_khz": PlausibilityBand(1.0, 1000.0, "KNOWN"),
    "alpha": PlausibilityBand(0.3, 1.0, "KNOWN"),
    "td_ns": PlausibilityBand(-100.0, 100.0, "KNOWN"),
    "cm_nf": PlausibilityBand(0.01, 500.0, "CONJECTURE"),
    "rms": PlausibilityBand(0.0, 2.0, "CONJECTURE"),
    "max_abs": PlausibilityBand(0.0, 5.0, "CONJECTURE"),
    "rms_log_grid": PlausibilityBand(0.0, 2.0, "CONJECTURE"),
    "phase_50k_deg": PlausibilityBand(0.0, 45.0, "CONJECTURE"),
}


# Cross-runner spread under OPENBLAS_CORETYPE=Haswell on ubuntu-latest (below single-spectrum +10 kHz shifts).
# GHA run 41760498077 vs cloud refit: re.sumsq |Δ|≈38, re.mean |Δ|≈2.1e-6, fc_khz/td_ns sumsq |Δ|<1.
SUM_SUMSQ_MIN_ABS_TOL = 40.0
STAT_MIN_ABS_TOL = 3e-6
STD_MIN_ABS_TOL = 1e-6


def aggregate_abs_tolerance(column: str, stat: str) -> float:
    """Strict replay under OPENBLAS_CORETYPE_PIN; %.6f CSV floor on all stats."""
    _ = column
    if stat in ("sum", "sumsq"):
        return max(N_SPECTRA * CSV6_HALF_ULP, SUM_SUMSQ_MIN_ABS_TOL)
    if stat == "std":
        return max(CSV6_HALF_ULP, STD_MIN_ABS_TOL)
    if stat in ("median", "mean", "min", "max", "p1", "p5", "p95", "p99"):
        return max(CSV6_HALF_ULP, STAT_MIN_ABS_TOL)
    return CSV6_HALF_ULP


def aggregate_tolerance_table() -> dict[str, Any]:
    return {
        "openblas_coretype_pin": OPENBLAS_CORETYPE_PIN,
        "fits_csv_float_format": FLOAT_FORMAT,
        "csv6_half_ulp": CSV6_HALF_ULP,
        "sum_sumsq_min_abs_tol": SUM_SUMSQ_MIN_ABS_TOL,
        "stat_min_abs_tol": STAT_MIN_ABS_TOL,
        "std_min_abs_tol": STD_MIN_ABS_TOL,
        "columns": {
            col: {stat: aggregate_abs_tolerance(col, stat) for stat in AGG_STATS}
            for col in CHECK_COLUMNS
        },
        "aggregate_rel_tol": AGGREGATE_REL_TOL,
    }


def column_aggregates(series: pd.Series) -> dict[str, float]:
    s = series.astype(float)
    q = s.quantile([0.01, 0.05, 0.95, 0.99])
    return {
        "sum": float(s.sum()),
        "median": float(s.median()),
        "mean": float(s.mean()),
        "min": float(s.min()),
        "max": float(s.max()),
        "std": float(s.std(ddof=0)),
        "sumsq": float((s * s).sum()),
        "p1": float(q.loc[0.01]),
        "p5": float(q.loc[0.05]),
        "p95": float(q.loc[0.95]),
        "p99": float(q.loc[0.99]),
    }


def band_outlier_counts(df: pd.DataFrame) -> dict[str, int]:
    out: dict[str, int] = {}
    for col, band in PLAUSIBILITY_BANDS.items():
        if col not in df.columns:
            continue
        s = df[col].astype(float)
        out[col] = int(((s < band.low) | (s > band.high)).sum())
    return out


def fits_column_reference(df: pd.DataFrame) -> dict[str, Any]:
    return {
        "n": int(len(df)),
        "columns": {col: column_aggregates(df[col]) for col in CHECK_COLUMNS if col in df.columns},
    }


def stat_close(got: float, ref: float, abs_tol: float) -> bool:
    scale = max(abs(ref), 1e-30)
    return abs(got - ref) <= abs_tol + AGGREGATE_REL_TOL * scale


def verify_fits_aggregates(
    df: pd.DataFrame,
    ref: dict[str, Any],
    band_counts_ref: dict[str, int],
    n_expected: int,
) -> list[str]:
    errors: list[str] = []
    if len(df) != n_expected:
        errors.append(f"fits rows: got {len(df)} cert {n_expected}")
    counts = band_outlier_counts(df)
    for col, want in band_counts_ref.items():
        if counts.get(col, -1) != int(want):
            errors.append(f"fits band outliers {col}: got {counts.get(col)} cert {want}")
    for col in CHECK_COLUMNS:
        if col not in df.columns:
            errors.append(f"fits.csv missing column {col}")
            continue
        got = column_aggregates(df[col])
        want = ref["columns"][col]
        for stat in AGG_STATS:
            tol = aggregate_abs_tolerance(col, stat)
            if not stat_close(got[stat], float(want[stat]), tol):
                errors.append(f"fits.{col}.{stat}: got {got[stat]} cert {want[stat]} tol {tol}")
    return errors


def recompute_cm_nf(df: pd.DataFrame) -> pd.DataFrame:
    """For perturbation tests only."""
    import numpy as np

    out = df.copy()
    fc_hz = out["fc_khz"].astype(float) * 1e3
    denom = 2 * np.pi * fc_hz * (out["re"].astype(float) + out["ri"].astype(float))
    out["cm_nf"] = 1e9 / denom
    return out


def pilot_blas_env(extra: dict[str, str] | None = None) -> dict[str, str]:
    env = {
        "OPENBLAS_CORETYPE": OPENBLAS_CORETYPE_PIN,
        "OPENBLAS_NUM_THREADS": "1",
        "OMP_NUM_THREADS": "1",
        "MKL_NUM_THREADS": "1",
    }
    if extra:
        env.update(extra)
    return env
