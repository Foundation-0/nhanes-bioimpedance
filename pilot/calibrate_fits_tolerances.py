#!/usr/bin/env python3
"""Print FIT_AGGREGATE_ABS_TOL = margin × worst drift over the run-41746542087 model (paste into fits_verify.py)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pilot"))
from fits_verify import (  # noqa: E402
    AGGREGATE_TOLERANCE_MARGIN,
    AGG_STATS,
    CHECK_COLUMNS,
    DRIFT_GAUSSIAN_SIGMA_KHZ,
    DRIFT_MODEL_SEEDS,
    apply_run_41746542087_reproductions,
    column_aggregates,
    gaussian_fc_noise,
)


def main() -> int:
    df = pd.read_csv(ROOT / "data" / "fits.csv")
    refcols = {col: column_aggregates(df[col]) for col in CHECK_COLUMNS}
    worst = {(col, stat): 0.0 for col in CHECK_COLUMNS for stat in AGG_STATS}
    for mode in ("uniform", "median_row", "max_cm_row"):
        trial = apply_run_41746542087_reproductions(df, mode)
        for col in CHECK_COLUMNS:
            got = column_aggregates(trial[col])
            for stat in AGG_STATS:
                worst[(col, stat)] = max(worst[(col, stat)], abs(got[stat] - refcols[col][stat]))
    for sigma in DRIFT_GAUSSIAN_SIGMA_KHZ:
        for seed in DRIFT_MODEL_SEEDS:
            trial = gaussian_fc_noise(df, sigma, seed)
            for col in CHECK_COLUMNS:
                got = column_aggregates(trial[col])
                for stat in AGG_STATS:
                    worst[(col, stat)] = max(worst[(col, stat)], abs(got[stat] - refcols[col][stat]))
    tol = {
        col: {stat: AGGREGATE_TOLERANCE_MARGIN * worst[(col, stat)] for stat in AGG_STATS}
        for col in CHECK_COLUMNS
    }
    print(json.dumps({"margin": AGGREGATE_TOLERANCE_MARGIN, "tolerances": tol}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
