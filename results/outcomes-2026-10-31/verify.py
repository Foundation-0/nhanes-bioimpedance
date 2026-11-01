#!/usr/bin/env python3
"""Deterministic verifier for results/outcomes-2026-10-31."""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RESULT = ROOT / "results" / "outcomes-2026-10-31"
CERT_PATH = RESULT / "certificate.json"
REF_PATH = RESULT / "svycoxph_reference.json"

SVYCOXPH_REPLAY_HR_ABS_TOL = 0.01
SVYCOXPH_REPLAY_CI_BOUND_ABS_TOL = 0.035


def parse_outcomes(text: str) -> dict:
    out: dict = {}
    m = re.search(
        r"adults 20-49 at the exam: (\d+) participants, (\d+) deaths, median follow-up ([0-9.]+) years",
        text,
    )
    if not m:
        raise ValueError("missing O3 header")
    out["o3_n"] = int(m.group(1))
    out["o3_deaths"] = int(m.group(2))
    out["o3_median_followup_years"] = float(m.group(3))
    m = re.search(
        r"hazard ratio ([0-9.]+) per degree.*?95% CI ([0-9.]+)-([0-9.]+)",
        text,
    )
    if not m:
        raise ValueError("missing pooled HR line")
    out["hr_pha50_per_degree"] = float(m.group(1))
    out["hr_pha50_ci95_lo"] = float(m.group(2))
    out["hr_pha50_ci95_hi"] = float(m.group(3))
    rows = re.findall(
        r"^\s*(1999-2000|2001-2002|2003-2004)\s+\d+\s+\d+.*?([+-]?[0-9.]+)\s+\(",
        text,
        re.M,
    )
    for cycle, delta in rows:
        key = "cindex_holdout_" + cycle.replace("-", "_") + "_full_minus_pha50"
        out[key] = float(delta)
    return out


def near(a: float, b: float, tol: float) -> bool:
    return abs(a - b) <= tol


def find_rscript() -> Path:
    for cand in (Path("/tmp/miniforge/bin/Rscript"), Path("Rscript")):
        try:
            subprocess.run([str(cand), "--version"], check=True, capture_output=True)
            return cand
        except (OSError, subprocess.CalledProcessError):
            continue
    raise SystemExit("Rscript not found (need survey, haven, jsonlite; see requirements-r.txt)")


def main() -> int:
    os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    os.environ.setdefault("MKL_NUM_THREADS", "1")
    cert = json.loads(CERT_PATH.read_text())
    tol_i = cert["checks"]["abs_int_tolerance"]
    tol_f = cert["checks"]["abs_float_tolerance"]
    if not (ROOT / "data" / "fits.csv").exists():
        subprocess.run([sys.executable, str(ROOT / "pilot" / "fetch.py")], check=True, cwd=ROOT)
        subprocess.run([sys.executable, str(ROOT / "pilot" / "refit.py")], check=True, cwd=ROOT)
    proc = subprocess.run(
        [sys.executable, str(ROOT / "pilot" / "outcomes.py")],
        check=True,
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    got = parse_outcomes(proc.stdout)
    for key in ("o3_n", "o3_deaths"):
        if int(got[key]) != int(cert[key]):
            print(f"{key} mismatch", file=sys.stderr)
            return 1
    for key in (
        "o3_median_followup_years",
        "hr_pha50_per_degree",
        "hr_pha50_ci95_lo",
        "hr_pha50_ci95_hi",
        "cindex_holdout_1999_2000_full_minus_pha50",
        "cindex_holdout_2001_2002_full_minus_pha50",
        "cindex_holdout_2003_2004_full_minus_pha50",
    ):
        if not near(float(got[key]), float(cert[key]), tol_f if key != "o3_median_followup_years" else 0.05):
            print(f"{key}: got {got[key]} cert {cert[key]}", file=sys.stderr)
            return 1
    rscript = find_rscript()
    ref_before = REF_PATH.read_bytes() if REF_PATH.exists() else b""
    subprocess.run([str(rscript), str(ROOT / "pilot" / "compare_svycoxph_outcomes.R"), str(ROOT)], check=True, cwd=ROOT)
    ref = json.loads(REF_PATH.read_text())
    if ref_before and REF_PATH.read_bytes() != ref_before:
        print("svycoxph_reference.json changed on re-run", file=sys.stderr)
        return 1
    chk = cert["svycoxph_check"]
    hr_tol = SVYCOXPH_REPLAY_HR_ABS_TOL
    ci_tol = SVYCOXPH_REPLAY_CI_BOUND_ABS_TOL
    if not near(got["hr_pha50_per_degree"], ref["hr_pha50_per_degree"], hr_tol):
        print("HR gap vs svycoxph exceeds tolerance", file=sys.stderr)
        return 1
    if not near(got["hr_pha50_ci95_lo"], ref["ci95_lo"], ci_tol):
        print("CI low gap vs svycoxph exceeds tolerance", file=sys.stderr)
        return 1
    if not near(got["hr_pha50_ci95_hi"], ref["ci95_hi"], ci_tol):
        print("CI high gap vs svycoxph exceeds tolerance", file=sys.stderr)
        return 1
    print(
        f"OK outcomes-2026-10-31 N={cert['o3_n']} HR={got['hr_pha50_per_degree']:.2f} "
        f"svycoxph_gap_ci<={ci_tol}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
