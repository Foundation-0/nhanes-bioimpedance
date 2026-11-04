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
from fits_verify import (  # noqa: E402
    AGGREGATE_REL_TOL,
    pilot_blas_env,
    verify_fits_aggregates,
)

STDOUT_FLOAT_ABS_TOL = 0.02


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


def stat_close(got: float, ref: float, abs_tol: float) -> bool:
    scale = max(abs(ref), 1e-30)
    return abs(got - ref) <= abs_tol + AGGREGATE_REL_TOL * scale


def main() -> int:
    env = pilot_blas_env()
    os.environ.update(env)
    cert = json.loads(CERT_PATH.read_text())
    subprocess.run([sys.executable, str(ROOT / "pilot" / "fetch.py")], check=True, cwd=ROOT, env={**os.environ, **env})
    proc = subprocess.run(
        [sys.executable, str(ROOT / "pilot" / "refit.py")],
        check=True,
        cwd=ROOT,
        capture_output=True,
        text=True,
        env={**os.environ, **env},
    )
    got = parse_refit(proc.stdout)
    df = pd.read_csv(DATA / "fits.csv")
    fit_errors = verify_fits_aggregates(
        df,
        cert["fits_column_reference"],
        cert["fits_plausibility_outliers"],
        cert["spectra_refitted"],
    )
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
        if not stat_close(float(got[key]), float(cert[key]), STDOUT_FLOAT_ABS_TOL):
            print(f"{key}: got {got[key]} cert {cert[key]}", file=sys.stderr)
            return 1
    print(f"OK pilot-2026-10-31 n={cert['spectra_refitted']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
