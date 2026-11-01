# Cause-specific mortality (issue #6)

**Status: claimed.** Not peer reviewed. Not causal and not clinical guidance.

## Statement (VERIFIED)

In NHANES 1999–2004 adults aged 20–49 at the exam with usable bioimpedance spectra (refit relative
residual below 2%), we fit **cause-specific** Cox proportional hazards models for death from (1)
diseases of heart, (2) malignant neoplasms, and (3) all other leading causes (UCOD_LEADING 003–010),
censoring participants who die from competing causes. Covariates: age, sex, and 50 kHz phase angle
(per within-cohort standard deviation). Survey design: combined 1999–2004 MEC weights
(2/3×WTMEC4YR for 1999–2002 and 1/3×WTMEC2YR for 2003–04), SDMVSTRA and SDMVPSU. **Reported design 95% CIs**
use R **`survey::svycoxph`** (Taylor linearisation on the survey design). A Python delete-one-PSU jackknife
is stored for comparison; it does not match `svycoxph` within 0.01 on CI bounds for heart and other causes
(see below). Held-out **C-index** by survey cycle compares age+sex, +50 kHz phase angle, and +full-spectrum
models; bootstrap intervals resample PSUs within strata in the test cycle (same scheme as `pilot/outcomes.py`).
**Feature scaling for held-out C-index:** mean and SD of each covariate are computed on the **training cycles
only** (commit `873c087dedbcfb0c25bfd985aa2876215f60f970`, credit grk-proof PR #8 review).

## Hazard ratio scaling (VERIFIED)

Pooled all-cycle Cox models report hazard ratio **per 1 SD increase** in 50 kHz phase angle (adjusted for age
and sex). SD and mean are **unweighted** sample statistics (`ddof=1`), matching R `scale()` on the analysis
cohort — **not** survey-weighted moments. The same convention as `pilot/compare_svycoxph.R` (`age_z`, `male_z`,
`pha50_z`). Survey design enters through **weights** in the partial likelihood and in the design-based variance,
not through weighted standardization.

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

**Design CI methods (VERIFIED):** `certificate.json` stores `design_ci95` from **`survey::svycoxph`**
(pinned R package **survey 4.5-1** in CI). Python **`jackknife_ci95`** refits the Cox model deleting one
PSU at a time; that is a different variance approximation than the Taylor linearisation inside
`svycoxph`, so bounds can differ even when point HRs match. Documented max absolute gap on CI bounds
(jackknife vs svycoxph): heart **0.108**, cancer **0.0005**, other **0.028**. Cancer agrees within 0.01;
heart and other do not — the jackknife is **not** used as the reported design interval.

**Verify tolerances (pre-declared in `verify.py`, not reverse-fitted):** recomputing
`compare_svycoxph.R` must match committed `design_ci95` within **0.01** on each CI bound; jackknife gaps
are recomputed and must match the certificate; if a gap exceeds **0.01**, the certificate must keep
`design_ci95_method` = `survey::svycoxph` (not jackknife).

**Interpretation (claimed):** Cancer and “other” show HR point estimates below 1 with design intervals
excluding 1 for cancer (svycoxph). Heart disease has only 53 events; intervals are wide and include
1. Bootstrap intervals are narrower because the PSU bootstrap does not match the full design-based
Cox variance (see [results/outcomes-2026-10-31.md](../outcomes-2026-10-31.md)). Low power for
cause-specific contrasts; report null/weak findings honestly.

Full held-out C-index tables are in `certificate.json`.

## Held-out C-index by cause (VERIFIED)

Train on two cycles, evaluate on the third. Covariates standardized with **training-cycle-only** unweighted
mean and SD (`ddof=1`) before fitting Cox on the training set. Cause-specific events on the test cycle.

**Holdout leakage fix (credit grk-proof, PR #8 review):** Corrected in commit
`873c087dedbcfb0c25bfd985aa2876215f60f970` — `held_out_cindex` computes μ/σ on **training cycles only**
(`pilot/cause_mortality.py`, loop over held-out cycle). On this cohort the committed C-index values are
**unchanged** after the fix (test-set linear predictors stay perfectly rank-correlated; Harrell’s C is
rank-based), but the procedure now matches proper cycle holdout.

### Heart (53 events total)

| Test cycle | Events | C (age+sex) | C (+phase50) | C (+full) | Full − phase50 | 95% CI (bootstrap) |
|---|---:|---:|---:|---:|---:|---|
| 1999–2000 | 17 | 0.588 | 0.581 | 0.663 | +0.082 | (+0.019, +0.184) |
| 2001–2002 | 25 | 0.607 | 0.611 | 0.686 | +0.075 | (+0.004, +0.162) |
| 2003–2004 | 11 | 0.741 | 0.768 | 0.708 | −0.060 | (−0.121, −0.010) |

### Cancer (83 events total)

| Test cycle | Events | C (age+sex) | C (+phase50) | C (+full) | Full − phase50 | 95% CI (bootstrap) |
|---|---:|---:|---:|---:|---:|---|
| 1999–2000 | 36 | 0.680 | 0.690 | 0.680 | −0.010 | (−0.026, +0.006) |
| 2001–2002 | 28 | 0.694 | 0.720 | 0.721 | +0.001 | (−0.015, +0.018) |
| 2003–2004 | 19 | 0.700 | 0.719 | 0.707 | −0.012 | (−0.039, +0.025) |

### Other (150 events total)

| Test cycle | Events | C (age+sex) | C (+phase50) | C (+full) | Full − phase50 | 95% CI (bootstrap) |
|---|---:|---:|---:|---:|---:|---|
| 1999–2000 | 57 | 0.686 | 0.612 | 0.638 | +0.027 | (+0.017, +0.037) |
| 2001–2002 | 60 | 0.627 | 0.639 | 0.616 | −0.023 | (−0.058, +0.004) |
| 2003–2004 | 33 | 0.656 | 0.699 | 0.688 | −0.011 | (−0.033, +0.005) |

Before/after the train-only scaling fix, every cell above matched the prior (leaky) implementation to
machine precision on this dataset.

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
# R survey 4.5-1 (see requirements-r.txt):
#   Rscript -e 'install.packages("remotes"); remotes::install_version("survey","4.5-1", repos="https://cloud.r-project.org")'
python3 pilot/fetch.py && python3 pilot/refit.py && make verify
```

`make verify` regenerates `certificate.json` (must match committed file byte-for-byte), re-runs
`pilot/compare_svycoxph.R`, and checks **numeric** agreement of `design_ci95` with fresh `svycoxph`
within the fixed **0.01** bound. R `survey` version strings in `svycoxph_reference.json` are not
compared byte-for-byte. Jackknife gaps are recomputed independently and checked against stored values.

## Open obligations

- Peer review and a person’s sign-off before any external claim.
- Fine-Gray subdistribution hazards were not estimated.
- Competing risk of other causes is handled only through cause-specific censoring.

## Data credit (KNOWN)

NHANES public-use files and NCHS Linked Mortality Files downloaded by exact URL in `pilot/fetch.py`.
Analysis code builds on `pilot/outcomes.py` (PR #8) and the spectrum refit (PR #7).
