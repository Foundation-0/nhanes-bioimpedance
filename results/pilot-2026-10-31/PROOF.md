# Pilot refit, 31 October 2026 — **VERIFIED** (finite replay)

## Statement

Independent refit of all completed NHANES 1999–2004 whole-body bioimpedance spectra (13,276 exams)
against CDC’s published Cole parameters, using aggregate tables only in git.

## Scope

- Input: CDC BIX and DEMO public-use files for 1999–2004 (`pilot/fetch.py`, size and SHA-256 pinned).
- Output: aggregate stdout from `pilot/refit.py` and column aggregates of local `data/fits.csv` (not committed).
- **Not** a tolerance certificate on every tail error; README medians summarize typical agreement. Max relative
  errors on excellent-fit rows remain wide in the tails (see grk-proof review on PR #7).

## Evidence

Full human-readable log: [../pilot-2026-10-31.md](../pilot-2026-10-31.md).

`certificate.json` locks aggregate stdout numbers and, for each fitted Cole column, sum/median/mean/min/max/std,
sum of squares, and p1/p5/p95/p99, plus counts of spectra outside plausibility bands (`pilot/fits_verify.py`).
Each aggregate has its own absolute tolerance: **3×** the cross-platform drift measured on GitHub Actions run
**41746542087** where applicable (fc sum 2.77 kHz, fc mean 2.1×10⁻⁴ kHz, Cm max 1.0×10⁻⁴ nF), otherwise **3×**
a `%.6f` CSV round-trip floor. Input files remain byte-pinned in `pilot/fetch.py`.

## CI note (CONJECTURE)

GitHub Actions run **41729837412** failed the old `fits.csv` SHA-256 check when the pilot ran after
`r-lib/actions/setup-r`; run **41732773657** passed after PR #9 reordered steps. That reorder is **PROVEN**
empirically. A comment in PR #9 blamed R’s OpenBLAS on `LD_LIBRARY_PATH`; grk-proof (orda-aska) tested that
path and could not confirm it (**CONJECTURE**). The workflow still runs pilot verify before R.

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
- Associations in later outcomes work are separate results (`results/outcomes-2026-10-31/` on PR #8).
