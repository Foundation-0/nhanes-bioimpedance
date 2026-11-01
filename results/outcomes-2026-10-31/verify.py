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

# Pre-declared at verify time (not fitted from observed gaps).
SVYCOXPH_REPLAY_CI_ABS_TOL = 0.01


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
    m = re.search(r"survey::svycoxph ([0-9.]+)-([0-9.]+)", text)
    if not m:
        raise ValueError("missing primary svycoxph CI line")
    out["design_ci95_lo"] = float(m.group(1))
    out["design_ci95_hi"] = float(m.group(2))
    m = re.search(
        r"Secondary Python delete-one-PSU jackknife 95% CI ([0-9.]+)-([0-9.]+).*gap vs svycoxph CI bounds ([0-9.]+)",
        text,
    )
    if not m:
        raise ValueError("missing secondary jackknife line")
    out["jackknife_ci95_lo"] = float(m.group(1))
    out["jackknife_ci95_hi"] = float(m.group(2))
    out["jackknife_gap"] = float(m.group(3))
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


def ci_gap(a: list[float], b: list[float]) -> float:
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


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
    pooled = cert["hr_pha50_per_degree_pooled"]
    tol_f = cert["checks"]["abs_float_tolerance"]
    if not (ROOT / "data" / "fits.csv").exists():
        subprocess.run([sys.executable, str(ROOT / "pilot" / "fetch.py")], check=True, cwd=ROOT)
        subprocess.run([sys.executable, str(ROOT / "pilot" / "refit.py")], check=True, cwd=ROOT)

    rscript = find_rscript()
    ref_before = json.loads(REF_PATH.read_text()) if REF_PATH.exists() else None
    subprocess.run([str(rscript), str(ROOT / "pilot" / "compare_svycoxph_outcomes.R"), str(ROOT)], check=True, cwd=ROOT)
    ref = json.loads(REF_PATH.read_text())
    if ref_before is not None:
        drift = max(
            abs(ref["hr_pha50_per_degree"] - ref_before["hr_pha50_per_degree"]),
            ci_gap([ref["ci95_lo"], ref["ci95_hi"]], [ref_before["ci95_lo"], ref_before["ci95_hi"]]),
        )
        if drift > SVYCOXPH_REPLAY_CI_ABS_TOL:
            print(f"svycoxph_reference.json drift {drift} > {SVYCOXPH_REPLAY_CI_ABS_TOL}", file=sys.stderr)
            return 1

    design_gap = ci_gap(pooled["design_ci95"], [ref["ci95_lo"], ref["ci95_hi"]])
    if design_gap > SVYCOXPH_REPLAY_CI_ABS_TOL:
        print(f"certificate design_ci95 vs svycoxph gap {design_gap} > {SVYCOXPH_REPLAY_CI_ABS_TOL}", file=sys.stderr)
        return 1

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
        "cindex_holdout_1999_2000_full_minus_pha50",
        "cindex_holdout_2001_2002_full_minus_pha50",
        "cindex_holdout_2003_2004_full_minus_pha50",
    ):
        tol = 0.05 if key == "o3_median_followup_years" else tol_f
        if not near(float(got[key]), float(cert[key]), tol):
            print(f"{key}: got {got[key]} cert {cert[key]}", file=sys.stderr)
            return 1
    jk_cert = pooled["jackknife_ci95"]
    if not near(got["jackknife_ci95_lo"], jk_cert[0], tol_f) or not near(got["jackknife_ci95_hi"], jk_cert[1], tol_f):
        print("jackknife CI replay mismatch", file=sys.stderr)
        return 1
    if not near(got["jackknife_gap"], pooled["jackknife_vs_svycoxph_max_abs_ci_gap"], tol_f):
        print("jackknife gap replay mismatch", file=sys.stderr)
        return 1
    if not near(got["design_ci95_lo"], pooled["design_ci95"][0], tol_f) or not near(
        got["design_ci95_hi"], pooled["design_ci95"][1], tol_f
    ):
        print("stdout design CI does not match certificate", file=sys.stderr)
        return 1

    print(
        f"OK outcomes-2026-10-31 N={cert['o3_n']} "
        f"HR={pooled['hr_per_degree']:.3f} svycoxph CI ({pooled['design_ci95'][0]:.3f},{pooled['design_ci95'][1]:.3f}) "
        f"jackknife gap={pooled['jackknife_vs_svycoxph_max_abs_ci_gap']:.4f} (informational)"
    )
    print(f"svycoxph replay max CI gap={design_gap:.6f} (tol={SVYCOXPH_REPLAY_CI_ABS_TOL})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
