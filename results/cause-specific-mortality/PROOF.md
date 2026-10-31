# Cause-specific mortality (issue #6)

**Status: claimed.** Not peer reviewed. Not causal and not clinical guidance.

## Statement (VERIFIED)

In NHANES 1999–2004 adults aged 20–49 at the exam with usable bioimpedance spectra (refit relative
residual below 2%), we fit **cause-specific** Cox proportional hazards models for death from (1)
diseases of heart, (2) malignant neoplasms, and (3) all other leading causes (UCOD_LEADING 003–010),
censoring participants who die from competing causes. Covariates: age, sex, and 50 kHz phase angle
(per within-cohort standard deviation). Survey design: combined 1999–2004 MEC weights
(2/3×WTMEC4YR for 1999–2002 and 1/3×WTMEC2YR for 2003–04), SDMVSTRA and SDMVPSU. Hazard ratio
intervals use a **design-based delete-one-PSU jackknife** in Python (cross-checked against R
`survey::svycoxph`, which applies Taylor linearisation for this design). Held-out **C-index** by
survey cycle compares age+sex, +50 kHz phase angle, and +full-spectrum models; bootstrap intervals
resample PSUs within strata in the test cycle (same scheme as `pilot/outcomes.py`).

## Cohort (VERIFIED)

| Quantity | Value |
|---|---|
| Participants | 5,173 |
| All-cause deaths to 31 Dec 2019 | 286 |
| Median follow-up | 17.8 years |
| Heart deaths (UCOD 001) | 53 |
| Cancer deaths (UCOD 002) | 83 |
| Other deaths (UCOD 003–010) | 150 |

Death counts sum to 286 and match the all-cause count in [results/outcomes-2026-10-31.md](../outcomes-2026-10-31.md).

## Hazard ratios per SD of 50 kHz phase angle (age + sex adjusted)

Cause-specific hazard, not subdistribution. HR below 1 means higher phase angle associates with lower
cause-specific hazard in this sample.

| Cause | Events | HR | Design 95% CI (svycoxph) | Design 95% CI (Python JK) | Bootstrap 95% CI (PSU) |
|---|---:|---:|---|---|---|
| Heart | 53 | 0.80 | 0.45 – 1.43 | 0.42 – 1.54 | 0.57 – 1.11 |
| Cancer | 83 | 0.66 | 0.49 – 0.89 | 0.49 – 0.89 | 0.53 – 0.85 |
| Other | 150 | 0.65 | 0.48 – 0.90 | 0.46 – 0.92 | 0.53 – 0.81 |

**Interpretation (claimed):** Cancer and “other” show HR point estimates below 1 with design intervals
excluding 1 for cancer (svycoxph). Heart disease has only 53 events; intervals are wide and include
1. Bootstrap intervals are narrower because the PSU bootstrap does not match the full design-based
Cox variance (see [results/outcomes-2026-10-31.md](../outcomes-2026-10-31.md)). Low power for
cause-specific contrasts; report null/weak findings honestly.

Full held-out C-index tables are in `certificate.json`.

## Prior art (KNOWN / not found)

Searches on 31 Oct 2026 (PubMed-style, recorded in [notes/reports/literature-survey-2026-10-31.md](../../notes/reports/literature-survey-2026-10-31.md)):

| Reference | What they did | Relation |
|---|---|---|
| Xia et al., *Sci Rep* 2025, [doi:10.1038/s41598-025-86825-y](https://doi.org/10.1038/s41598-025-86825-y) | NHANES 1999–2004, 50 kHz phase angle, **all-cause** mortality, 6,338 adults / 307 deaths, HR ≈ 0.73 | KNOWN; broader age range; not cause-specific |
| Barbosa-Silva et al., *Clin Nutr* 2012 (cited in survey) | Phase angle and mortality in older adults | KNOWN; different cohort |
| PubMed keyword search “NHANES bioimpedance phase angle cause-specific mortality UCOD” (31 Oct 2026) | No hit using full 50-frequency BIX files and UCOD_LEADING cause-specific models in adults 20–49 | **Not found in this search** — does not imply novelty |

## How it is checked (VERIFIED)

```bash
pip install -r requirements.txt
# R: conda install -c conda-forge r-base=4.4 r-survey=4.5 r-haven r-jsonlite
python3 pilot/fetch.py && python3 pilot/refit.py && make verify
```

`make verify` regenerates `certificate.json` and requires `git diff` empty afterward. It also re-runs
`pilot/compare_svycoxph.R` and requires Python jackknife intervals to agree with `svycoxph` within
the tolerance recorded in the certificate (widest gap on heart disease upper bound).

## Open obligations

- Peer review and a person’s sign-off before any external claim.
- Fine-Gray subdistribution hazards were not estimated.
- Competing risk of other causes is handled only through cause-specific censoring.

## Data credit (KNOWN)

NHANES public-use files and NCHS Linked Mortality Files downloaded by exact URL in `pilot/fetch.py`.
Analysis code builds on `pilot/outcomes.py` (PR #8) and the spectrum refit (PR #7).
