"""Cause-specific mortality vs 50 kHz phase angle and the full spectrum (issue #6).

Cause-specific Cox models censor competing deaths; these are cause-specific hazards, not Fine-Gray
subdistribution hazards. Design-based 95% intervals for hazard ratios use R **survey::svycoxph** (Taylor linearisation on the
NHANES design). A Python delete-one-PSU jackknife is also computed for cross-check; it can disagree on
CI bounds (see PROOF.md). Held-out **C-index** uses training-cycle-only standardization (fix commit
873c087 on this branch; grk-proof / PR #8 review).
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from mortality_load import (  # noqa: E402
    CAUSE_SPECS,
    cause_specific_event,
    load_outcomes_frame,
    mortality_cohort,
)
from survey_cox import cindex, cox_fit, cox_vcov_design  # noqa: E402

RNG = np.random.default_rng(20261031)
NBOOT = 300
RESULT_DIR = ROOT / "results" / "cause-specific-mortality"
RSCRIPT = Path("/tmp/miniforge/bin/Rscript")

MODELS = {
    "age_sex": ["age", "male"],
    "phase50": ["age", "male", "pha50"],
    "full_spectrum": ["age", "male", "pha50", "pha5", "pha200", "alpha", "log_fc", "log_ri_re"],
}


def boot_idx(test, rng):
    idx = []
    for _, g in test.groupby("strata"):
        psus = g.psu.unique()
        pick = rng.choice(psus, size=len(psus), replace=True)
        for p in pick:
            idx.append(g.index[g.psu == p].values)
    return np.concatenate(idx)


def fit_hr_pha50(df, cause, rng=None):
    """Pooled-cohort cause-specific HR per SD of 50 kHz phase angle (age, sex adjusted)."""
    cols = ["age", "male", "pha50"]
    raw = df[cols].to_numpy(float)
    mu, sd = raw.mean(0), raw.std(0, ddof=1)
    X = (raw - mu) / sd
    w = df.w.to_numpy(float) / df.w.mean()
    t = df.months.to_numpy(float)
    e = cause_specific_event(df, cause)
    beta, hess = cox_fit(X, t, e, w)
    vc = cox_vcov_design(X, t, e, w, df.strata.to_numpy(int), df.psu.to_numpy(int), beta, hess)
    se = np.sqrt(np.diag(vc))
    ix = 2
    hr = float(np.exp(beta[ix]))
    lo = float(np.exp(beta[ix] - 1.96 * se[ix]))
    hi = float(np.exp(beta[ix] + 1.96 * se[ix]))
    boot_lo = boot_hi = None
    if rng is not None:
        hrs = []
        dtmp = df.reset_index(drop=True)
        for _ in range(NBOOT):
            i = boot_idx(dtmp, rng)
            wb = dtmp.w.values[i]
            wb = wb / wb.mean()
            b, _ = cox_fit(X[i], t[i], e[i], wb)
            hrs.append(np.exp(b[ix]))
        boot_lo, boot_hi = [float(x) for x in np.percentile(hrs, [2.5, 97.5])]
    return {
        "hr_per_sd_pha50": hr,
        "jackknife_ci95": [lo, hi],
        "bootstrap_ci95": [boot_lo, boot_hi] if boot_lo is not None else None,
        "events": int(e.sum()),
        "standardization": {
            "scope": "pooled_all_cycles",
            "method": "unweighted_sample_mean_and_sd",
            "ddof": 1,
            "note": "Same as R scale() on age, male, pha50; not survey-weighted.",
        },
    }


def held_out_cindex(df, cause):
    cols_full = MODELS["full_spectrum"]
    cols_base = MODELS["phase50"]
    d = df.dropna(subset=cols_full).reset_index(drop=True)
    e_all = cause_specific_event(d, cause)
    rows = []
    for cycle in sorted(d.cycle.unique()):
        trm, tem = (d.cycle != cycle).values, (d.cycle == cycle).values
        tr = d.loc[trm]
        te = d[tem].reset_index(drop=True)
        e = e_all[tem]
        risks = {}
        for name, cols in (
            ("age_sex", MODELS["age_sex"]),
            ("phase50", cols_base),
            ("full_spectrum", cols_full),
        ):
            raw_tr = tr[cols].to_numpy(float)
            mu = raw_tr.mean(0)
            sd = raw_tr.std(0, ddof=1)
            sd = np.where(sd == 0, 1.0, sd)
            Xtr = (raw_tr - mu) / sd
            Xte = (te[cols].to_numpy(float) - mu) / sd
            b, _ = cox_fit(
                Xtr,
                tr.months.to_numpy(float),
                e_all[trm],
                tr.w.to_numpy(float) / tr.w.mean(),
            )
            risks[name] = Xte @ b
        t, w = te.months.to_numpy(float), te.w.to_numpy(float)
        cs = {k: cindex(risks[k], t, e, w) for k in risks}
        diffs = []
        for _ in range(NBOOT):
            i = boot_idx(te, RNG)
            diffs.append(cindex(risks["full_spectrum"][i], t[i], e[i], w[i]) - cindex(risks["phase50"][i], t[i], e[i], w[i]))
        lo, hi = np.percentile(diffs, [2.5, 97.5])
        rows.append(
            {
                "cycle": cycle,
                "n": int(len(te)),
                "events": int(e.sum()),
                "cindex_age_sex": float(cs["age_sex"]),
                "cindex_phase50": float(cs["phase50"]),
                "cindex_full_spectrum": float(cs["full_spectrum"]),
                "full_minus_phase50": float(cs["full_spectrum"] - cs["phase50"]),
                "full_minus_phase50_boot_ci95": [float(lo), float(hi)],
                "standardization": "train_cycles_only_unweighted_mean_sd_ddof1",
            }
        )
    return rows


def run_svycoxph_reference():
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    rscript = RSCRIPT if RSCRIPT.exists() else Path("Rscript")
    cmd = [str(rscript), str(ROOT / "pilot" / "compare_svycoxph.R"), str(ROOT)]
    subprocess.run(cmd, check=True, cwd=ROOT)


def build_certificate():
    df = mortality_cohort(load_outcomes_frame())
    out = {
        "status": "claimed",
        "seed": 20261031,
        "n": int(len(df)),
        "all_cause_deaths": int(df.mortstat.sum()),
        "median_followup_years": float(df.months.median() / 12),
        "note": "Associations only; not causal; not clinical guidance. Cause-specific hazards, not subdistribution.",
        "causes": {},
    }
    for cause, meta in CAUSE_SPECS.items():
        out["causes"][cause] = {
            "label": meta["label"],
            "hr_age_sex_pha50": fit_hr_pha50(df, cause, rng=RNG),
            "held_out_cindex": held_out_cindex(df, cause),
        }
    run_svycoxph_reference()
    ref = json.loads((RESULT_DIR / "svycoxph_reference.json").read_text())
    for cause in CAUSE_SPECS:
        hr = out["causes"][cause]["hr_age_sex_pha50"]
        rr = ref[cause]
        hr["design_ci95"] = [rr["ci95_lo"], rr["ci95_hi"]]
        hr["design_ci95_method"] = "survey::svycoxph"
        gap = max(
            abs(hr["jackknife_ci95"][0] - rr["ci95_lo"]),
            abs(hr["jackknife_ci95"][1] - rr["ci95_hi"]),
        )
        hr["jackknife_vs_svycoxph_max_abs_ci_gap"] = float(gap)
        hr["jackknife_ci95_method"] = "delete_one_PSU_jackknife"
    out["holdout_scaling"] = {
        "method": "train_cycles_only_unweighted_mean_sd_ddof1",
        "fixed_in_commit": "873c087dedbcfb0c25bfd985aa2876215f60f970",
    }
    return out


def main():
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    cert = build_certificate()
    (RESULT_DIR / "certificate.json").write_text(json.dumps(cert, indent=2, sort_keys=True) + "\n")
    summary_lines = [
        f"N={cert['n']}, all-cause deaths={cert['all_cause_deaths']}, "
        f"median follow-up {cert['median_followup_years']:.1f} y",
        "",
    ]
    for cause, block in cert["causes"].items():
        hr = block["hr_age_sex_pha50"]
        summary_lines.append(
            f"{cause}: events={hr['events']}, HR per SD phase50={hr['hr_per_sd_pha50']:.3f} "
            f"design CI svycoxph ({hr['design_ci95'][0]:.3f}, {hr['design_ci95'][1]:.3f}) "
            f"jackknife ({hr['jackknife_ci95'][0]:.3f}, {hr['jackknife_ci95'][1]:.3f}) "
            f"bootstrap ({hr['bootstrap_ci95'][0]:.3f}, {hr['bootstrap_ci95'][1]:.3f})"
        )
    (RESULT_DIR / "summary.txt").write_text("\n".join(summary_lines) + "\n")
    print("\n".join(summary_lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
