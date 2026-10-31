#!/usr/bin/env python3
"""Deterministic verifier for results/cause-specific-mortality (issue #6)."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RESULT = ROOT / "results" / "cause-specific-mortality"
CERT = RESULT / "certificate.json"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def find_rscript() -> Path:
    for cand in (Path("/tmp/miniforge/bin/Rscript"), Path("Rscript")):
        if cand.exists() or cand.name == "Rscript":
            try:
                subprocess.run([str(cand), "--version"], check=True, capture_output=True)
                return cand
            except (OSError, subprocess.CalledProcessError):
                continue
    raise SystemExit("Rscript not found; install r-base and r-survey (see PROOF.md).")


def main() -> int:
    os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    os.environ.setdefault("MKL_NUM_THREADS", "1")
    if not (ROOT / "data" / "fits.csv").exists():
        subprocess.run([sys.executable, str(ROOT / "pilot" / "fetch.py")], check=True, cwd=ROOT)
        subprocess.run([sys.executable, str(ROOT / "pilot" / "refit.py")], check=True, cwd=ROOT)
    before = CERT.read_text() if CERT.exists() else None
    subprocess.run([sys.executable, str(ROOT / "pilot" / "cause_mortality.py")], check=True, cwd=ROOT)
    after = CERT.read_text()
    if before is not None and before != after:
        print("certificate.json changed after regeneration", file=sys.stderr)
        return 1
    cert = json.loads(after)
    tol = cert["svycoxph_check"]["tolerance_abs_hr_ci"]
    for cause, chk in cert["svycoxph_check"]["per_cause"].items():
        gap = chk["max_abs_gap_vs_svycoxph"]
        if gap > tol:
            print(f"svycoxph gap for {cause} {gap} > {tol}", file=sys.stderr)
            return 1
    rscript = find_rscript()
    ref_path = RESULT / "svycoxph_reference.json"
    ref_before = ref_path.read_bytes()
    subprocess.run([str(rscript), str(ROOT / "pilot" / "compare_svycoxph.R"), str(ROOT)], check=True, cwd=ROOT)
    if ref_path.read_bytes() != ref_before:
        print("svycoxph_reference.json changed on re-run", file=sys.stderr)
        return 1
    digest = sha256_file(CERT)
    print(f"OK cause-specific-mortality certificate sha256={digest[:16]}")
    print(f"N={cert['n']} deaths={cert['all_cause_deaths']} survey={cert['svycoxph_check']['r_survey']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
