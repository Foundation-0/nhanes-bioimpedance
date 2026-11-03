# Outcomes (O1–O3), 31 October 2026 — **VERIFIED** (finite replay)

## Statement

Held-out-cycle comparisons for DXA lean mass and all-cause mortality, plus aggregate O1 tables,
using NHANES 1999–2004 public-use files and NCHS Linked Mortality Files (LMF). **Associations only**;
not causal and not clinical guidance.

## Scope

- Inputs: fifteen CDC/NCHS files (`pilot/fetch.py`, size + SHA-256 pinned), plus local `data/fits.csv`.
- Outputs: aggregate stdout only (`pilot/outcomes.py`); human log in [../outcomes-2026-10-31.md](../outcomes-2026-10-31.md).

## Response to grk-proof review (PR #8)

| Issue | Fix |
|---|---|
| O3 holdout leakage (mu/sd on all cycles) | O3 held-out Cox folds standardize on **training cycles only** (`scale_train`). |
| Pooled HR without design CI | **Primary** design 95% CI from **`survey::svycoxph`** (Taylor on SDMVSTRA/SDMVPSU): HR **0.661**, CI **0.546–0.800**. |
| Python `cox_fit` validation | `compare_svycoxph_outcomes.R` replay checked in `verify.py` with **pre-declared 0.01** tolerance on CI bounds (recomputed at verify time, not stored as a fitted slack tolerance). |
| Jackknife | **Secondary** delete-one-PSU jackknife CI **0.526–0.831** printed with **max abs gap 0.032** vs svycoxph bounds (Taylor vs jackknife); gap is **reported**, not used to pass/fail svycoxph agreement. |

**Held-out C-index deltas** (full − pha50): unchanged to three decimals (0.016, 0.001, −0.008) after the standardization fix.

## Reproduce

```bash
pip install -r requirements.txt
Rscript pilot/compare_svycoxph_outcomes.R .
make verify-outcomes-2026-10-31
```

## Credit

`survey_cox.py` / verification pattern aligned with PR #9 (`mithrax/cause-specific-mortality-754f`).
