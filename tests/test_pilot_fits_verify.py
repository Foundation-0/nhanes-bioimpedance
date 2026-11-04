"""Regression tests for pilot/fits_verify aggregate replay checks."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pilot"))
from fits_verify import (  # noqa: E402
    band_outlier_counts,
    fits_column_reference,
    smallest_detectable_fc_shift_khz,
    verify_fits_aggregates,
)

CERT_PATH = ROOT / "results" / "pilot-2026-10-31" / "certificate.json"
DATA_FITS = ROOT / "data" / "fits.csv"
needs_fits = pytest.mark.skipif(not DATA_FITS.is_file(), reason="needs data/fits.csv from refit")


@pytest.fixture(scope="module")
def certificate() -> dict:
    return json.loads(CERT_PATH.read_text())


def _interior_fc_row(df: pd.DataFrame) -> int:
    interior = df[(df["fc_khz"] > 10) & (df["fc_khz"] < 900)]
    return int(interior["fc_khz"].sub(interior["fc_khz"].median()).abs().idxmin())


@needs_fits
def test_large_fc_perturbation_fails(certificate: dict):
    df = pd.read_csv(DATA_FITS)
    ref = certificate["fits_column_reference"]
    bands = certificate["fits_plausibility_outliers"]
    n = certificate["spectra_refitted"]
    row = _interior_fc_row(df)
    trial = df.copy()
    trial.loc[row, "fc_khz"] += 130.0
    assert verify_fits_aggregates(trial, ref, bands, n)


@needs_fits
def test_moderate_fc_perturbation_fails(certificate: dict):
    df = pd.read_csv(DATA_FITS)
    ref = certificate["fits_column_reference"]
    bands = certificate["fits_plausibility_outliers"]
    n = certificate["spectra_refitted"]
    row = _interior_fc_row(df)
    trial = df.copy()
    trial.loc[row, "fc_khz"] += 10.0
    assert verify_fits_aggregates(trial, ref, bands, n)


@needs_fits
def test_smallest_detectable_fc_shift(certificate: dict):
    df = pd.read_csv(DATA_FITS)
    ref = certificate["fits_column_reference"]
    bands = certificate["fits_plausibility_outliers"]
    n = certificate["spectra_refitted"]
    row = _interior_fc_row(df)
    delta = smallest_detectable_fc_shift_khz(df, ref, bands, n, row_index=row)
    # Interior spectrum: first failure is fc_khz.sumsq (~1.7 mHz shift); +10 kHz fails via sum/mean.
    assert 0.001 < delta < 0.003


def test_sum_tolerance_does_not_scale_with_n():
    """Guard against n × per-spectrum atol on sums (+130 kHz must fail)."""
    n = 100
    df = pd.DataFrame(
        {
            "re": np.full(n, 500.0),
            "ri": np.full(n, 1000.0),
            "fc_khz": np.full(n, 50.0),
            "alpha": np.full(n, 0.7),
            "td_ns": np.full(n, 4.0),
            "cm_nf": np.full(n, 1.6),
            "rms": np.full(n, 0.001),
            "max_abs": np.full(n, 0.004),
            "rms_log_grid": np.full(n, 0.002),
            "phase_50k_deg": np.full(n, 6.5),
        }
    )
    ref = fits_column_reference(df)
    bands = band_outlier_counts(df)
    trial = df.copy()
    trial.loc[0, "fc_khz"] += 130.0
    assert verify_fits_aggregates(trial, ref, bands, n)
