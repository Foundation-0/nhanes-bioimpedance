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
| O3 holdout leakage (mu/sd on all cycles) | O3 held-out Cox folds now standardize covariates using **training cycles only** (`scale_train` in `pilot/survey_cox.py`). |
| Pooled HR 0.66 without design CI | Delete-one-PSU jackknife on SDMVSTRA/SDMVPSU reported with pooled HR. |
| `cox_fit` vs `survey::svycoxph` | `pilot/compare_svycoxph_outcomes.R` + numeric check in `verify.py` (pre-declared tolerances, not metadata). |

**Before/after (O3 held-out C-index deltas, three test cycles):** unchanged to three decimals after the
standardization fix (0.016, 0.001, −0.008). Affine rescaling within a fold preserves risk ranks for these
unpenalized Cox linear predictors on the test cycle.

**Pooled HR:** still **0.66 per degree** (display); full precision **0.661** with design CI **0.53–0.83**
(Python jackknife) vs **0.661** with **0.55–0.80** (`survey::svycoxph` Taylor); `verify.py` allows
**0.035** absolute gap on each CI bound (declared in `certificate.json`, not fitted from this run).

## Reproduce

```bash
pip install -r requirements.txt
# optional: apt install r-base; R -e 'install.packages(c("survey","haven","jsonlite"), repos="https://cloud.r-project.org")'
make verify-outcomes-2026-10-31
```

## Credit

`survey_cox.py` / jackknife pattern adapted from PR #9 (`mithrax/cause-specific-mortality-754f`).
