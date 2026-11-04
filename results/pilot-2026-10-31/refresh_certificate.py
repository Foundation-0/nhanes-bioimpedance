#!/usr/bin/env python3
"""Regenerate results/pilot-2026-10-31/certificate.json from local data/fits.csv and refit stdout."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "pilot"))
from fits_verify import (  # noqa: E402
    PLAUSIBILITY_BANDS,
    aggregate_tolerance_table,
    band_outlier_counts,
    fits_column_reference,
)

CERT = ROOT / "results" / "pilot-2026-10-31" / "certificate.json"


def parse_refit(text: str) -> dict:
    out: dict = {}
    m = re.search(r"completed exams: (\d+); with all 100 values: (\d+)", text)
    out["completed_exams_with_all_frequencies"] = int(m.group(2))
    m = re.search(r"Spectra refitted: (\d+)", text)
    out["spectra_refitted"] = int(m.group(1))
    m = re.search(r"log grid in (\d+)% of spectra", text)
    out["log_grid_better_fraction"] = int(m.group(1)) / 100.0
    m = re.search(r"median rms residual ([0-9.]+) vs ([0-9.]+)", text)
    out["label_grid_median_rms"] = float(m.group(1))
    out["log_grid_median_rms"] = float(m.group(2))
    m = re.search(
        r"excellent\s+(\d+)\s+(\d+\.\d+)%\s+\d+\.\d+%\s+(\d+\.\d+)%\s+\d+\.\d+%\s+(\d+\.\d+)%",
        text,
    )
    out["excellent_n"] = int(m.group(1))
    out["excellent_re_median_rel_pct"] = float(m.group(2))
    out["excellent_ri_median_rel_pct"] = float(m.group(3))
    out["excellent_fc_median_rel_pct"] = float(m.group(4))
    m = re.search(
        r"CDC 'excellent' spectra: median ([0-9.]+), 95th percentile ([0-9.]+), above 0.01 for (\d+)",
        text,
    )
    out["excellent_rms_median"] = float(m.group(1))
    out["excellent_rms_p95"] = float(m.group(2))
    out["excellent_rms_above_0_01"] = int(m.group(3))
    m = re.search(
        r"could not fit \(code 5\): (\d+)\. Our fit: median rms ([0-9.]+); rms below 0.01 for (\d+)",
        text,
    )
    out["code5_n"] = int(m.group(1))
    out["code5_median_rms"] = float(m.group(2))
    out["code5_rms_below_0_01"] = int(m.group(3))
    m = re.search(
        r"Time delay Td \(ns\): CDC median ([0-9.]+), ours ([0-9.]+); CDC Td below 0 for (\d+)",
        text,
    )
    out["cdc_td_median_ns"] = float(m.group(1))
    out["ours_td_median_ns"] = float(m.group(2))
    out["cdc_td_negative_n"] = int(m.group(3))
    m = re.search(r"Phase angle at the 50 kHz label: median ([0-9.]+) degrees", text)
    out["phase_50k_median_deg"] = float(m.group(1))
    m = re.search(r"IQR ([0-9.]+)-([0-9.]+)", text)
    out["phase_50k_iqr_low_deg"] = float(m.group(1))
    out["phase_50k_iqr_high_deg"] = float(m.group(2))
    return out


def main() -> int:
    import pandas as pd

    proc = subprocess.run(
        [sys.executable, str(ROOT / "pilot" / "refit.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    parsed = parse_refit(proc.stdout)
    df = pd.read_csv(ROOT / "data" / "fits.csv")
    cert = {
        "result_id": "pilot-2026-10-31",
        "evidence_label": "VERIFIED",
        "scope": "Aggregate refit of NHANES 1999-2004 BIX spectra vs CDC Cole parameters; no row-level data.",
        **parsed,
        "fits_column_reference": fits_column_reference(df),
        "fits_plausibility_outliers": band_outlier_counts(df),
        "fits_plausibility_bands": {
            col: {"low": b.low, "high": b.high, "label": b.label}
            for col, b in PLAUSIBILITY_BANDS.items()
        },
        "checks": {
            "abs_int_tolerance": 0,
            "abs_float_tolerance": 0.02,
            "fits_aggregate_abs_tol": aggregate_tolerance_table(),
        },
    }
    CERT.write_text(json.dumps(cert, indent=2) + "\n")
    print(f"wrote {CERT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
