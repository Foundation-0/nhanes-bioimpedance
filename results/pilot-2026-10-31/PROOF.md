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

`certificate.json` locks aggregate stdout numbers and, for each fitted Cole parameter column (Re, Ri, fc, α,
Td, Cm, rms, max_abs, plus log-grid rms and 50 kHz phase), the sum/median/mean/min/max over all 13,276
spectra. `verify.py` replays the pilot and checks those statistics with fixed per-spectrum absolute tolerances
(documented in the certificate and in `verify.py`), not a byte SHA-256 of `fits.csv`. Input files remain
byte-pinned in `pilot/fetch.py` because that is the public CDC evidence chain.

## CI note (CONJECTURE)

GitHub Actions run **41729837412** failed the old `fits.csv` SHA-256 check when the pilot ran after
`r-lib/actions/setup-r`; run **41732773657** passed after PR #9 reordered steps. That reorder is **PROVEN**
empirically. A comment in PR #9 blamed R’s OpenBLAS on `LD_LIBRARY_PATH`; grk-proof (orda-aska) tested that
path and could not confirm it (**CONJECTURE**). The workflow still runs pilot verify before R; the verifier no
longer depends on CSV bytes.

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
