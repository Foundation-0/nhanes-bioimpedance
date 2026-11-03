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
REF = RESULT / "svycoxph_reference.json"

# Pre-declared bounds (not read from certificate.json).
# svycoxph is the reported design CI; re-running compare_svycoxph.R must match committed values.
SVYCOXPH_REPLAY_CI_ABS_TOL = 0.01
# Python delete-one-PSU jackknife is secondary; documented gaps may exceed this (heart/other).
JACKKNIFE_VS_SVYCOXPH_EXPECTED_MAX_GAP = 0.01

sys.path.insert(0, str(ROOT / "pilot"))


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
    raise SystemExit("Rscript not found; install r-base and r-survey 4.5 (see PROOF.md).")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def ci_gap(a: list[float], b: list[float]) -> float:
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def recompute_jackknife_gaps(cert: dict) -> dict[str, float]:
    from cause_mortality import fit_hr_pha50  # noqa: WPS433
    from mortality_load import load_outcomes_frame, mortality_cohort  # noqa: WPS433

    df = mortality_cohort(load_outcomes_frame())
    gaps = {}
    for cause in cert["causes"]:
        hr = fit_hr_pha50(df, cause, rng=None)
        ref_ci = cert["causes"][cause]["hr_age_sex_pha50"]["design_ci95"]
        gaps[cause] = ci_gap(hr["jackknife_ci95"], ref_ci)
    return gaps


def compare_svycoxph_numbers(ref: dict, cert: dict) -> float:
    worst = 0.0
    for cause in ("heart", "cancer", "other"):
        cert_ci = cert["causes"][cause]["hr_age_sex_pha50"]["design_ci95"]
        ref_ci = [ref[cause]["ci95_lo"], ref[cause]["ci95_hi"]]
        worst = max(worst, ci_gap(cert_ci, ref_ci))
    return worst


def compare_ref_files(a: dict, b: dict) -> float:
    worst = 0.0
    for cause in ("heart", "cancer", "other"):
        ci_a = [a[cause]["ci95_lo"], a[cause]["ci95_hi"]]
        ci_b = [b[cause]["ci95_lo"], b[cause]["ci95_hi"]]
        worst = max(worst, ci_gap(ci_a, ci_b))
        worst = max(worst, abs(a[cause]["hr_pha50_per_sd"] - b[cause]["hr_pha50_per_sd"]))
    return worst


def main() -> int:
    os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    os.environ.setdefault("MKL_NUM_THREADS", "1")
    if not (ROOT / "data" / "fits.csv").exists():
        subprocess.run([sys.executable, str(ROOT / "pilot" / "fetch.py")], check=True, cwd=ROOT)
        subprocess.run([sys.executable, str(ROOT / "pilot" / "refit.py")], check=True, cwd=ROOT)

    before = CERT.read_text() if CERT.exists() else None
    ref_before = load_json(REF) if REF.exists() else None
    subprocess.run([sys.executable, str(ROOT / "pilot" / "cause_mortality.py")], check=True, cwd=ROOT)
    after = CERT.read_text()
    if before is not None and before != after:
        print("certificate.json changed after regeneration", file=sys.stderr)
        return 1

    cert = load_json(CERT)
    rscript = find_rscript()
    subprocess.run([str(rscript), str(ROOT / "pilot" / "compare_svycoxph.R"), str(ROOT)], check=True, cwd=ROOT)
    ref_after = load_json(REF)

    if ref_before is not None:
        ref_drift = compare_ref_files(ref_before, ref_after)
        if ref_drift > SVYCOXPH_REPLAY_CI_ABS_TOL:
            print(f"svycoxph_reference.json numeric drift {ref_drift} > {SVYCOXPH_REPLAY_CI_ABS_TOL}", file=sys.stderr)
            return 1

    replay_gap = compare_svycoxph_numbers(ref_after, cert)
    if replay_gap > SVYCOXPH_REPLAY_CI_ABS_TOL:
        print(f"certificate design_ci95 vs fresh svycoxph gap {replay_gap} > {SVYCOXPH_REPLAY_CI_ABS_TOL}", file=sys.stderr)
        return 1

    fresh_jk_gaps = recompute_jackknife_gaps(cert)
    for cause, gap in fresh_jk_gaps.items():
        stored = cert["causes"][cause]["hr_age_sex_pha50"]["jackknife_vs_svycoxph_max_abs_ci_gap"]
        if abs(gap - stored) > 1e-9:
            print(f"jackknife gap replay mismatch for {cause}: {gap} vs stored {stored}", file=sys.stderr)
            return 1
        method = cert["causes"][cause]["hr_age_sex_pha50"]["design_ci95_method"]
        if gap > JACKKNIFE_VS_SVYCOXPH_EXPECTED_MAX_GAP and method != "survey::svycoxph":
            print(f"{cause}: jackknife gap {gap} > {JACKKNIFE_VS_SVYCOXPH_EXPECTED_MAX_GAP} but primary method wrong", file=sys.stderr)
            return 1

    digest = sha256_file(CERT)
    print(f"OK cause-specific-mortality certificate sha256={digest[:16]}")
    print(f"N={cert['n']} deaths={cert['all_cause_deaths']}")
    print(f"svycoxph replay max CI gap={replay_gap:.6f} (tol={SVYCOXPH_REPLAY_CI_ABS_TOL})")
    for cause in ("heart", "cancer", "other"):
        hr = cert["causes"][cause]["hr_age_sex_pha50"]
        print(
            f"  {cause}: HR={hr['hr_per_sd_pha50']:.4f} "
            f"svycoxph CI ({hr['design_ci95'][0]:.3f},{hr['design_ci95'][1]:.3f}) "
            f"jackknife CI ({hr['jackknife_ci95'][0]:.3f},{hr['jackknife_ci95'][1]:.3f}) "
            f"jk gap={hr['jackknife_vs_svycoxph_max_abs_ci_gap']:.4f}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
