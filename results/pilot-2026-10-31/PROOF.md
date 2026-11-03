# Pilot refit, 31 October 2026 — **VERIFIED** (finite replay)

## Statement

Independent refit of all completed NHANES 1999–2004 whole-body bioimpedance spectra (13,276 exams)
against CDC’s published Cole parameters, using aggregate tables only in git.

## Scope

- Input: CDC BIX and DEMO public-use files for 1999–2004 (`pilot/fetch.py`, size and SHA-256 pinned).
- Output: aggregate stdout from `pilot/refit.py` and SHA-256 of local `data/fits.csv` (not committed).
- **Not** a tolerance certificate on every tail error; README medians summarize typical agreement. Max relative
  errors on excellent-fit rows remain wide in the tails (see grk-proof review on PR #7).

## Evidence

Full human-readable log: [../pilot-2026-10-31.md](../pilot-2026-10-31.md).

Locked numbers in `certificate.json` are replay-checked by `verify.py` with declared float tolerance
(`checks.abs_float_tolerance`), not environment metadata.

## Reproduce

```bash
pip install -r requirements.txt
make verify-pilot-2026-10-31
```

## Prior art

CDC/NCHS NHANES BIX documentation and published fit codes (see `NOTICE.md`).

## Limits

- CDC’s fitting algorithm is proprietary; we compare to their published parameters, not to ground truth.
- Associations in later outcomes work are separate results (`results/outcomes-2026-10-31/` on PR #8).
