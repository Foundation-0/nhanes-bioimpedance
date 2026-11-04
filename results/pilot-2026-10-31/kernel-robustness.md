# OpenBLAS kernel robustness (not a verify gate)

**VERIFIED** sensitivity record: same pinned Python deps, `OPENBLAS_NUM_THREADS=1`,
baseline verify pin `OPENBLAS_CORETYPE=Haswell`. Compared refits for
`Haswell`, `Sandybridge`, `Prescott`.

Cause of GitHub Actions run **41746542087** aggregate drift remains **CONJECTURE**
(consistent with a different OpenBLAS kernel before this pin).

Generated 2026-11-04 by `kernel_robustness.py`.

## Headline pilot statistics vs baseline

| Kernel | Spectra | Label grid better | Excellent n | Re med % | Ri med % | fc med % | Phase median (IQR) |
|---|---:|---:|---:|---:|---:|---:|---|
| **Haswell** (baseline) | 13276 | 85% | 12369 | 0.2 | 2.3 | 1.2 | 6.58 (5.98-7.28) |
| Sandybridge | 13276 | 85% | 12369 | 0.2 | 2.3 | 1.2 | 6.58 (5.98-7.28) |
| Prescott | 13276 | 85% | 12369 | 0.2 | 2.3 | 1.2 | 6.58 (5.98-7.28) |

## Per-column fit changes vs baseline

| Kernel | re | ri | fc_khz | alpha | td_ns | cm_nf | rms | max_abs | rms_log_grid | phase_50k_deg |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Sandybridge | 3882 / 0.243841 | 10765 / 3.80554 | 2412 / 2.82224 | 57 / 0.000797 | 818 / 0.048973 | 169 / 0.00237 | 1 / 1e-06 | 18 / 7.3e-05 | 0 / 0 | 0 / 0 |
| Prescott | 3879 / 0.243841 | 10772 / 3.80554 | 2420 / 2.82224 | 57 / 0.000797 | 833 / 0.048973 | 169 / 0.00237 | 1 / 1e-06 | 16 / 7.3e-05 | 1 / 1e-06 | 0 / 0 |

Each cell is `rows changed / max |Δ|` vs the Haswell baseline refit.
