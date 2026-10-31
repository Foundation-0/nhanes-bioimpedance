"""Load the NHANES 1999-2004 analysis cohort used in outcome scripts (aggregate use only)."""
from pathlib import Path

import numpy as np
import pandas as pd

from cole import LABEL_KHZ, R_COLS, X_COLS

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CYCLES = [("1999-2000", "", "1999_2000"), ("2001-2002", "_B", "2001_2002"), ("2003-2004", "_C", "2003_2004")]

# NCHS public-use LMF: UCOD_LEADING columns 17-19 (1-based), see Public-use Data Dictionary.
MORT_COLSPECS = [(0, 6), (14, 15), (15, 16), (16, 19), (45, 48)]
MORT_NAMES = ["SEQN", "eligstat", "mortstat", "ucod_leading", "months"]


def phase_deg(R, X, khz):
    k = LABEL_KHZ.index(khz)
    return np.degrees(np.arctan2(np.abs(X[:, k]), R[:, k]))


def load_mortality(lmf_suffix: str) -> pd.DataFrame:
    return pd.read_fwf(
        DATA / f"NHANES_{lmf_suffix}_MORT_2019_PUBLIC.dat",
        colspecs=MORT_COLSPECS,
        names=MORT_NAMES,
        na_values=["."],
    )


def load_outcomes_frame() -> pd.DataFrame:
    """Adults 20-49 with BIA, survey design, mortality follow-up, and refit features."""
    frames = []
    for cycle, sfx, lmf in CYCLES:
        bix = pd.read_sas(DATA / f"BIX{sfx}.xpt", format="xport")
        bix = bix[bix.BIAEXSTS.round() == 1]
        R, X = bix[R_COLS].to_numpy(float), bix[X_COLS].to_numpy(float)
        b = pd.DataFrame(
            {
                "SEQN": bix.SEQN.astype(int).values,
                "R50": R[:, LABEL_KHZ.index(50)],
                "pha5": phase_deg(R, X, 5),
                "pha50": phase_deg(R, X, 50),
                "pha200": phase_deg(R, X, 200),
            }
        )
        demo = pd.read_sas(DATA / f"DEMO{sfx}.xpt", format="xport")
        w = demo.WTMEC4YR * 2 / 3 if "WTMEC4YR" in demo else demo.WTMEC2YR / 3
        d = pd.DataFrame(
            {
                "SEQN": demo.SEQN.astype(int),
                "male": (demo.RIAGENDR == 1).astype(float),
                "age": np.where(demo.RIDAGEEX.notna(), demo.RIDAGEEX / 12, demo.RIDAGEYR),
                "w": w,
                "strata": demo.SDMVSTRA.astype(int),
                "psu": demo.SDMVPSU.astype(int),
            }
        )
        bmx = pd.read_sas(DATA / f"BMX{sfx}.xpt", format="xport")[["SEQN", "BMXHT", "BMXWT"]]
        bmx["SEQN"] = bmx.SEQN.astype(int)
        mort = load_mortality(lmf)
        mort["SEQN"] = mort.SEQN.astype(int)
        mort["ucod_leading"] = pd.to_numeric(mort.ucod_leading, errors="coerce")
        x = b.merge(d, on="SEQN").merge(bmx, on="SEQN", how="left").merge(mort, on="SEQN", how="left")
        x["cycle"] = cycle
        frames.append(x)
    df = pd.concat(frames, ignore_index=True)
    fits = pd.read_csv(DATA / "fits.csv")
    df = df.merge(
        fits[["SEQN", "cdc_fit", "re", "ri", "fc_khz", "alpha", "td_ns", "cdc_td", "rms"]],
        on="SEQN",
    )
    df["log_ri_re"] = np.log(df.ri / df.re)
    df["log_fc"] = np.log(df.fc_khz)
    return df


def mortality_cohort(df: pd.DataFrame) -> pd.DataFrame:
    cols = ["age", "male", "pha50", "pha5", "pha200", "alpha", "log_fc", "log_ri_re"]
    d = df[
        (df.age >= 20)
        & (df.eligstat == 1)
        & df.mortstat.notna()
        & df.months.notna()
        & (df.rms < 0.02)
        & (df.w > 0)
    ].copy()
    return d.dropna(subset=cols).reset_index(drop=True)


CAUSE_SPECS = {
    "heart": {"ucod": 1, "label": "Diseases of heart (UCOD_LEADING 001)"},
    "cancer": {"ucod": 2, "label": "Malignant neoplasms (UCOD_LEADING 002)"},
    "other": {"ucod": None, "label": "All other underlying causes (UCOD_LEADING 003-010)"},
}


def cause_specific_event(df: pd.DataFrame, cause: str) -> np.ndarray:
    """Cause-specific event indicator: 1 if death from target cause, 0 if censored (incl. competing death)."""
    mort = df.mortstat.to_numpy(int)
    ucod = df.ucod_leading.to_numpy(float)
    spec = CAUSE_SPECS[cause]["ucod"]
    if spec is not None:
        return ((mort == 1) & (ucod == spec)).astype(int)
    return ((mort == 1) & (ucod >= 3) & (ucod <= 10)).astype(int)
