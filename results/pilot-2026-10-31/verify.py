#!/usr/bin/env python3
"""Deterministic verifier for results/pilot-2026-10-31 (BIX refit aggregates)."""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RESULT = ROOT / "results" / "pilot-2026-10-31"
CERT_PATH = RESULT / "certificate.json"
DATA = ROOT / "data"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


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
        r"excellent\s+(\d+)\s+(\d+\.\d+)%\s+\d+\.\d+%\s+(\d+\.\d+)%\s+\d+\.\d+%\s+(\d+\.\d+)%",
        text,
    )
    if not m:
        raise ValueError("missing excellent agreement row")
    out["excellent_n"] = int(m.group(1))
    out["excellent_re_median_rel_pct"] = float(m.group(2))
    out["excellent_ri_median_rel_pct"] = float(m.group(3))
    out["excellent_fc_median_rel_pct"] = float(m.group(4))
    m = re.search(r"Phase angle at the 50 kHz label: median ([0-9.]+) degrees", text)
    out["phase_50k_median_deg"] = float(m.group(1))
    return out


def near(a: float, b: float, tol: float) -> bool:
    return abs(a - b) <= tol


def main() -> int:
    os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    os.environ.setdefault("MKL_NUM_THREADS", "1")
    cert = json.loads(CERT_PATH.read_text())
    tol_i = cert["checks"]["abs_int_tolerance"]
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
    fits = DATA / "fits.csv"
    if sha256_file(fits) != cert["fits_csv_sha256"]:
        print("fits.csv sha256 mismatch", file=sys.stderr)
        return 1
    for key in (
        "spectra_refitted",
        "completed_exams_with_all_frequencies",
        "excellent_n",
    ):
        if int(got[key]) != int(cert[key]):
            print(f"{key}: got {got[key]} cert {cert[key]}", file=sys.stderr)
            return 1
    for key in (
        "log_grid_better_fraction",
        "excellent_re_median_rel_pct",
        "excellent_ri_median_rel_pct",
        "excellent_fc_median_rel_pct",
        "phase_50k_median_deg",
    ):
        if not near(float(got[key]), float(cert[key]), tol_f):
            print(f"{key}: got {got[key]} cert {cert[key]}", file=sys.stderr)
            return 1
    print(f"OK pilot-2026-10-31 n={cert['spectra_refitted']} fits_sha={cert['fits_csv_sha256'][:16]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
