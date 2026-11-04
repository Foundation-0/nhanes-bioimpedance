"""Aggregate replay checks for local data/fits.csv (not committed)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from fits_csv import AUX_NUMERIC_COLUMNS, COLE_COLUMNS

# GitHub Actions run that first exposed cross-platform aggregate drift (PR #10, verify job).
CALIBRATION_GITHUB_RUN = 41746542087
AGGREGATE_TOLERANCE_MARGIN = 3

# |Δ| between reference certificate host and run CALIBRATION_GITHUB_RUN (from CI log).
CALIBRATED_AGGREGATE_DRIFT: dict[tuple[str, str], float] = {
    ("fc_khz", "sum"): 2.767758,
    ("fc_khz", "mean"): 2.08478e-4,
    ("cm_nf", "max"): 1.04e-4,
}

# When a stat was not measurable on that run, bound drift from %.6f CSV round-trip (n = 13,276).
CSV6_AGGREGATE_FLOOR: dict[str, float] = {
    "sum": 0.00664,
    "median": 5e-7,
    "mean": 5e-7,
    "min": 5e-7,
    "max": 5e-7,
    "std": 1e-6,
    "sumsq": 0.01,
    "p1": 1e-6,
    "p5": 1e-6,
    "p95": 1e-6,
    "p99": 1e-6,
}

AGG_STATS = ("sum", "median", "mean", "min", "max", "std", "sumsq", "p1", "p5", "p95", "p99")
CHECK_COLUMNS = COLE_COLUMNS + AUX_NUMERIC_COLUMNS
AGGREGATE_REL_TOL = 1e-9


@dataclass(frozen=True)
class PlausibilityBand:
    low: float
    high: float
    label: str  # KNOWN | CONJECTURE


# Fit bounds from pilot/cole.py least_squares (Re, Ri, fc Hz, alpha, Td s).
PLAUSIBILITY_BANDS: dict[str, PlausibilityBand] = {
    "re": PlausibilityBand(1.0, 50_000.0, "KNOWN"),
    "ri": PlausibilityBand(1.0, 500_000.0, "KNOWN"),
    "fc_khz": PlausibilityBand(1.0, 1000.0, "KNOWN"),
    "alpha": PlausibilityBand(0.3, 1.0, "KNOWN"),
    "td_ns": PlausibilityBand(-100.0, 100.0, "KNOWN"),
    # Cm = 1/(2π fc (Re+Ri)); wide cap for pathological fits (CONJECTURE).
    "cm_nf": PlausibilityBand(0.01, 500.0, "CONJECTURE"),
    "rms": PlausibilityBand(0.0, 2.0, "CONJECTURE"),
    "max_abs": PlausibilityBand(0.0, 5.0, "CONJECTURE"),
    "rms_log_grid": PlausibilityBand(0.0, 2.0, "CONJECTURE"),
    "phase_50k_deg": PlausibilityBand(0.0, 45.0, "CONJECTURE"),
}


def aggregate_abs_tolerance(column: str, stat: str) -> float:
    drift = CALIBRATED_AGGREGATE_DRIFT.get((column, stat), 0.0)
    floor = CSV6_AGGREGATE_FLOOR[stat]
    return AGGREGATE_TOLERANCE_MARGIN * max(drift, floor)


def aggregate_tolerance_table() -> dict[str, Any]:
    return {
        "calibration_github_run": CALIBRATION_GITHUB_RUN,
        "safety_margin": AGGREGATE_TOLERANCE_MARGIN,
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


def smallest_detectable_fc_shift_khz(
    df: pd.DataFrame,
    ref: dict[str, Any],
    band_counts_ref: dict[str, int],
    n_expected: int,
    *,
    row_index: int,
    delta_low: float = 0.0,
    delta_high: float = 200.0,
) -> float:
    """Binary-search the minimum fc_khz increment on one row that fails verify_fits_aggregates."""
    base = df.copy()
    if verify_fits_aggregates(base, ref, band_counts_ref, n_expected):
        raise ValueError("baseline fits do not match reference")

    def fails(delta: float) -> bool:
        trial = base.copy()
        trial.loc[row_index, "fc_khz"] = float(trial.loc[row_index, "fc_khz"]) + delta
        return bool(verify_fits_aggregates(trial, ref, band_counts_ref, n_expected))

    if not fails(delta_high):
        return float("inf")
    lo, hi = delta_low, delta_high
    for _ in range(40):
        mid = (lo + hi) / 2
        if fails(mid):
            hi = mid
        else:
            lo = mid
    return hi
