#!/usr/bin/env python3
"""Deterministic verifier for results/pilot-2026-10-31 (BIX refit aggregates)."""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
CERT_PATH = ROOT / "results" / "pilot-2026-10-31" / "certificate.json"
DATA = ROOT / "data"

sys.path.insert(0, str(ROOT / "pilot"))
from fits_csv import AUX_NUMERIC_COLUMNS, COLE_COLUMNS  # noqa: E402

# Fixed per-spectrum absolute tolerances for fitted columns (not tuned to CI BLAS drift).
# Excellent-fit Re agreement in the pilot is ~0.2% (~1 Ω on ~500 Ω); these are orders of magnitude tighter.
FIT_COLUMN_ABS_TOL: dict[str, float] = {
    "re": 0.05,
    "ri": 0.05,
    "fc_khz": 1e-4,
    "alpha": 1e-6,
    "td_ns": 1e-3,
    "cm_nf": 1e-5,
    "rms": 1e-7,
    "max_abs": 1e-6,
    "rms_log_grid": 1e-7,
    "phase_50k_deg": 1e-4,
}
FIT_COLUMN_REL_TOL = 1e-9
AGG_STATS = ("sum", "median", "mean", "min", "max")
CHECK_COLUMNS = COLE_COLUMNS + AUX_NUMERIC_COLUMNS


def parse_refit(text: str) -> dict:
    out: dict = {}
    m = re.search(r"completed exams: (\d+); with all 100 values: (\d+)", text)
    if not m:
        raise ValueError("missing exam counts in refit stdout")
    out["completed_exams_with_all_frequencies"] = int(m.group(2))
    m = re.search(r"Spectra refitted: (\d+)", text)
    out["spectra_refitted"] = int(m.group(1))
    m = re.search(r"log grid in (\d+)% of spectra", text)
    out["log_grid_better_fraction"] = int(m.group(1)) / 100.0
    m = re.search(
        r"median rms residual ([0-9.]+) vs ([0-9.]+)",
        text,
    )
    if not m:
        raise ValueError("missing log-grid median rms line")
    out["label_grid_median_rms"] = float(m.group(1))
    out["log_grid_median_rms"] = float(m.group(2))
    m = re.search(
        r"excellent\s+(\d+)\s+(\d+\.\d+)%\s+\d+\.\d+%\s+(\d+\.\d+)%\s+\d+\.\d+%\s+(\d+\.\d+)%",
        text,
    )
    if not m:
        raise ValueError("missing excellent agreement row")
    out["excellent_n"] = int(m.group(1))
    out["excellent_re_median_rel_pct"] = float(m.group(2))
    out["excellent_ri_median_rel_pct"] = float(m.group(3))
    out["excellent_fc_median_rel_pct"] = float(m.group(4))
    m = re.search(
        r"CDC 'excellent' spectra: median ([0-9.]+), 95th percentile ([0-9.]+), above 0.01 for (\d+)",
        text,
    )
    if not m:
        raise ValueError("missing excellent rms summary")
    out["excellent_rms_median"] = float(m.group(1))
    out["excellent_rms_p95"] = float(m.group(2))
    out["excellent_rms_above_0_01"] = int(m.group(3))
    m = re.search(
        r"could not fit \(code 5\): (\d+)\. Our fit: median rms ([0-9.]+); rms below 0.01 for (\d+)",
        text,
    )
    if not m:
        raise ValueError("missing code-5 summary")
    out["code5_n"] = int(m.group(1))
    out["code5_median_rms"] = float(m.group(2))
    out["code5_rms_below_0_01"] = int(m.group(3))
    m = re.search(
        r"Time delay Td \(ns\): CDC median ([0-9.]+), ours ([0-9.]+); CDC Td below 0 for (\d+)",
        text,
    )
    if not m:
        raise ValueError("missing Td summary")
    out["cdc_td_median_ns"] = float(m.group(1))
    out["ours_td_median_ns"] = float(m.group(2))
    out["cdc_td_negative_n"] = int(m.group(3))
    m = re.search(r"Phase angle at the 50 kHz label: median ([0-9.]+) degrees", text)
    out["phase_50k_median_deg"] = float(m.group(1))
    m = re.search(r"IQR ([0-9.]+)-([0-9.]+)", text)
    if not m:
        raise ValueError("missing phase IQR")
    out["phase_50k_iqr_low_deg"] = float(m.group(1))
    out["phase_50k_iqr_high_deg"] = float(m.group(2))
    return out


def stat_close(got: float, ref: float, abs_tol: float, rel_tol: float) -> bool:
    scale = max(abs(ref), 1e-30)
    return abs(got - ref) <= abs_tol + rel_tol * scale


def sum_close(got: float, ref: float, n: int, abs_per_spec: float, rel_tol: float) -> bool:
    scale = max(abs(ref), 1e-30)
    return abs(got - ref) <= abs_per_spec * n + rel_tol * scale


def column_aggregates(series: pd.Series) -> dict[str, float]:
    s = series.astype(float)
    return {
        "sum": float(s.sum()),
        "median": float(s.median()),
        "mean": float(s.mean()),
        "min": float(s.min()),
        "max": float(s.max()),
    }


def verify_fits_columns(df: pd.DataFrame, ref: dict, n: int) -> list[str]:
    errors: list[str] = []
    if len(df) != n:
        errors.append(f"fits rows: got {len(df)} cert {n}")
    for col in CHECK_COLUMNS:
        if col not in df.columns:
            errors.append(f"fits.csv missing column {col}")
            continue
        got = column_aggregates(df[col])
        want = ref["columns"][col]
        abs_tol = FIT_COLUMN_ABS_TOL[col]
        for stat in AGG_STATS:
            if stat == "sum":
                ok = sum_close(got[stat], float(want[stat]), n, abs_tol, FIT_COLUMN_REL_TOL)
            else:
                ok = stat_close(got[stat], float(want[stat]), abs_tol, FIT_COLUMN_REL_TOL)
            if not ok:
                errors.append(f"fits.{col}.{stat}: got {got[stat]} cert {want[stat]}")
    return errors


def main() -> int:
    os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    os.environ.setdefault("MKL_NUM_THREADS", "1")
    cert = json.loads(CERT_PATH.read_text())
    tol_f = cert["checks"]["abs_float_tolerance"]
    subprocess.run([sys.executable, str(ROOT / "pilot" / "fetch.py")], check=True, cwd=ROOT)
    proc = subprocess.run(
        [sys.executable, str(ROOT / "pilot" / "refit.py")],
        check=True,
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    got = parse_refit(proc.stdout)
    df = pd.read_csv(DATA / "fits.csv")
    fit_errors = verify_fits_columns(df, cert["fits_column_reference"], cert["spectra_refitted"])
    if fit_errors:
        for msg in fit_errors:
            print(msg, file=sys.stderr)
        return 1
    for key in (
        "spectra_refitted",
        "completed_exams_with_all_frequencies",
        "excellent_n",
        "code5_n",
        "code5_rms_below_0_01",
        "excellent_rms_above_0_01",
        "cdc_td_negative_n",
    ):
        if int(got[key]) != int(cert[key]):
            print(f"{key}: got {got[key]} cert {cert[key]}", file=sys.stderr)
            return 1
    float_keys = (
        "log_grid_better_fraction",
        "label_grid_median_rms",
        "log_grid_median_rms",
        "excellent_re_median_rel_pct",
        "excellent_ri_median_rel_pct",
        "excellent_fc_median_rel_pct",
        "excellent_rms_median",
        "excellent_rms_p95",
        "code5_median_rms",
        "cdc_td_median_ns",
        "ours_td_median_ns",
        "phase_50k_median_deg",
        "phase_50k_iqr_low_deg",
        "phase_50k_iqr_high_deg",
    )
    for key in float_keys:
        if not stat_close(float(got[key]), float(cert[key]), tol_f, FIT_COLUMN_REL_TOL):
            print(f"{key}: got {got[key]} cert {cert[key]}", file=sys.stderr)
            return 1
    print(f"OK pilot-2026-10-31 n={cert['spectra_refitted']} fits_columns={len(CHECK_COLUMNS)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
