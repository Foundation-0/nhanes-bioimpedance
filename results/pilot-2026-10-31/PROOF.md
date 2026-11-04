# Pilot refit, 31 October 2026 — **VERIFIED** (finite replay)

## Statement

Independent refit of all completed NHANES 1999–2004 whole-body bioimpedance spectra (13,276 exams)
against CDC’s published Cole parameters, using aggregate tables only in git.

## Verify gate (strict)

- Input: CDC public-use files (`pilot/fetch.py`, byte-pinned SHA-256).
- Refit: `pilot/refit.py` with **`OPENBLAS_CORETYPE=Haswell`** (see Makefile / CI) and thread count 1.
- Output check: aggregate statistics of local `data/fits.csv` must match `certificate.json` within the
  **`%.6f` CSV floor** (half-ulp per value; sum/sumsq use n × half-ulp). Plausibility-band outlier counts
  must match exactly. Stdout headline numbers use `abs_float_tolerance` 0.02.

Run **41746542087** showed fc/Cm aggregate drift without this pin; the cause is **CONJECTURE** (consistent
with a different OpenBLAS kernel on DYNAMIC_ARCH wheels). The pin makes CI and local verify deterministic on
`ubuntu-latest` (see CI logs: `lscpu`, `numpy.show_config()`).

## Kernel robustness (not a gate)

**VERIFIED** record: [kernel-robustness.md](kernel-robustness.md) from `kernel_robustness.py` — same deps,
refitting under Haswell, Sandybridge and Prescott `OPENBLAS_CORETYPE` values shows ~10⁴-row changes per column
and whether headline statistics move at published precision.

## Reproduce

```bash
sha256sum --strict -c commitment/SHA256SUMS
make verify-pilot-2026-10-31
pytest -q tests/test_pilot_fits_verify.py
```

## Prior art

CDC/NCHS NHANES BIX documentation (see `NOTICE.md`).

## Limits

- Not a per-spectrum tail-error certificate; README medians summarize typical agreement.
- CDC’s fitting algorithm is proprietary.
