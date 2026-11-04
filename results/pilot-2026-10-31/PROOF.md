# Pilot refit, 31 October 2026 — **VERIFIED** (finite replay)

## Statement

Independent refit of all completed NHANES 1999–2004 whole-body bioimpedance spectra (13,276 exams)
against CDC’s published Cole parameters, using aggregate tables only in git.

## Scope

- Input: CDC BIX and DEMO public-use files for 1999–2004 (`pilot/fetch.py`, size and SHA-256 pinned).
- Output: aggregate stdout from `pilot/refit.py` and column aggregates of local `data/fits.csv` (not committed).

## What the check tolerates (**CONJECTURE** on cause)

GitHub Actions run **41746542087** once produced aggregate drift vs the committed certificate (fc sum
**−2.767758 kHz**, fc mean **−2.08478×10⁻⁴ kHz**, Cm max **+1.04×10⁻⁴ nF**). The cause is **unknown**; the
same drift does **not** reproduce on a fresh VM with pinned deps (all 110 aggregates match exactly).

The verifier tolerates that drift class via `pilot/fits_verify.py`: perturb fc (uniform offset, single-row at
median fc, single-row at max Cm, Gaussian noise σ = **10⁻⁴–10⁻³ kHz** on 20 seeds), recompute Cm from
perturbed fc, take the worst |Δ| per aggregate, multiply by **3**, and compare every stat (sum/median/mean/min/max/std/sumsq/p1/p5/p95/p99) on fc and Cm plus exact replay on Re/Ri/α/Td/rms columns. Plausibility-band outlier counts must match the certificate (bands **KNOWN** from `pilot/cole.py` bounds where noted, else **CONJECTURE**).

## What the check catches (**VERIFIED** in tests)

- A **+10 kHz** or **+130 kHz** shift on one interior fc spectrum still **fails** (sum/median/Cm aggregates and tests in `tests/test_pilot_fits_verify.py`).
- Smallest failing single-spectrum fc shift with committed tolerances: about **0.0097 kHz** on a row near the cohort **median** fc, about **7.8 kHz** on a row near the cohort **mean** fc (binding stats differ by row).

## Evidence

Full human-readable log: [../pilot-2026-10-31.md](../pilot-2026-10-31.md).

## Reproduce

```bash
pip install -r requirements.txt
make verify-pilot-2026-10-31
pytest -q tests/test_pilot_fits_verify.py
```

## Prior art

CDC/NCHS NHANES BIX documentation and published fit codes (see `NOTICE.md`).

## Limits

- CDC’s fitting algorithm is proprietary; we compare to their published parameters, not to ground truth.
- This is not a per-spectrum tolerance certificate on tail errors; README medians summarize typical agreement.
