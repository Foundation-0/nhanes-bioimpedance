#!/usr/bin/env python3
"""Record Cole refit sensitivity to OpenBLAS CORETYPE (not a CI gate).

Run locally after fetch: python3 results/pilot-2026-10-31/kernel_robustness.py
Requires ~4 minutes per kernel tested.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "pilot"))
from fits_csv import COLE_COLUMNS  # noqa: E402
from fits_verify import OPENBLAS_CORETYPE_PIN, pilot_blas_env  # noqa: E402

KERNELS = ("Haswell", "Sandybridge", "Prescott")
OUT_MD = Path(__file__).resolve().parent / "kernel-robustness.md"
OUT_JSON = Path(__file__).resolve().parent / "kernel-robustness.json"
FIT_COLS = list(COLE_COLUMNS) + ["rms_log_grid", "phase_50k_deg"]


def parse_headlines(text: str) -> dict[str, str | int | float]:
    out: dict[str, str | int | float] = {}
    m = re.search(r"Spectra refitted: (\d+)", text)
    out["spectra_refitted"] = int(m.group(1))
    m = re.search(r"log grid in (\d+)% of spectra", text)
    out["log_grid_better_pct"] = int(m.group(1))
    m = re.search(
        r"excellent\s+(\d+)\s+(\d+\.\d+)%\s+\d+\.\d+%\s+(\d+\.\d+)%\s+\d+\.\d+%\s+(\d+\.\d+)%",
        text,
    )
    out["excellent_n"] = int(m.group(1))
    out["excellent_re_med_pct"] = float(m.group(2))
    out["excellent_ri_med_pct"] = float(m.group(3))
    out["excellent_fc_med_pct"] = float(m.group(4))
    m = re.search(r"Phase angle at the 50 kHz label: median ([0-9.]+) degrees \(IQR ([0-9.]+)-([0-9.]+)\)", text)
    out["phase_median_deg"] = float(m.group(1))
    out["phase_iqr_lo"] = float(m.group(2))
    out["phase_iqr_hi"] = float(m.group(3))
    return out


def run_refit(coretype: str) -> tuple[pd.DataFrame, str, dict]:
    env = os.environ.copy()
    env.update(pilot_blas_env({"OPENBLAS_CORETYPE": coretype}))
    proc = subprocess.run(
        [sys.executable, str(ROOT / "pilot" / "refit.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
        env=env,
    )
    df = pd.read_csv(ROOT / "data" / "fits.csv")
    return df, proc.stdout, parse_headlines(proc.stdout)


def compare_fits(base: pd.DataFrame, other: pd.DataFrame) -> dict[str, dict[str, float | int]]:
    stats: dict[str, dict[str, float | int]] = {}
    for col in FIT_COLS:
        a = base[col].astype(float).to_numpy()
        b = other[col].astype(float).to_numpy()
        changed = int(np.sum(a != b))
        stats[col] = {
            "rows_changed": changed,
            "max_abs_delta": float(np.max(np.abs(b - a))) if changed else 0.0,
        }
    return stats


def main() -> int:
    subprocess.run([sys.executable, str(ROOT / "pilot" / "fetch.py")], check=True, cwd=ROOT)
    baseline_core = OPENBLAS_CORETYPE_PIN
    runs: dict[str, dict] = {}
    base_df, base_stdout, base_head = run_refit(baseline_core)
    runs[baseline_core] = {
        "headlines": base_head,
        "per_column": {c: {"rows_changed": 0, "max_abs_delta": 0.0} for c in FIT_COLS},
    }
    for core in KERNELS:
        if core == baseline_core:
            continue
        df, stdout, head = run_refit(core)
        runs[core] = {"headlines": head, "per_column": compare_fits(base_df, df)}

    payload = {
        "generated_on": date.today().isoformat(),
        "baseline_coretype": baseline_core,
        "kernels": list(KERNELS),
        "numpy_show_config": subprocess.check_output(
            [sys.executable, "-c", "import numpy; numpy.show_config()"],
            text=True,
        ),
        "runs": runs,
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2) + "\n")

    lines = [
        "# OpenBLAS kernel robustness (not a verify gate)",
        "",
        "**VERIFIED** sensitivity record: same pinned Python deps, `OPENBLAS_NUM_THREADS=1`,",
        f"baseline verify pin `OPENBLAS_CORETYPE={baseline_core}`. Compared refits for",
        ", ".join(f"`{k}`" for k in KERNELS) + ".",
        "",
        "Cause of GitHub Actions run **41746542087** aggregate drift remains **CONJECTURE**",
        "(consistent with a different OpenBLAS kernel before this pin).",
        "",
        f"Generated {payload['generated_on']} by `kernel_robustness.py`.",
        "",
        "## Headline pilot statistics vs baseline",
        "",
        "| Kernel | Spectra | Label grid better | Excellent n | Re med % | Ri med % | fc med % | Phase median (IQR) |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    bh = runs[baseline_core]["headlines"]
    lines.append(
        f"| **{baseline_core}** (baseline) | {bh['spectra_refitted']} | {bh['log_grid_better_pct']}% | "
        f"{bh['excellent_n']} | {bh['excellent_re_med_pct']} | {bh['excellent_ri_med_pct']} | "
        f"{bh['excellent_fc_med_pct']} | {bh['phase_median_deg']} ({bh['phase_iqr_lo']}-{bh['phase_iqr_hi']}) |"
    )
    for core in KERNELS:
        if core == baseline_core:
            continue
        h = runs[core]["headlines"]
        lines.append(
            f"| {core} | {h['spectra_refitted']} | {h['log_grid_better_pct']}% | {h['excellent_n']} | "
            f"{h['excellent_re_med_pct']} | {h['excellent_ri_med_pct']} | {h['excellent_fc_med_pct']} | "
            f"{h['phase_median_deg']} ({h['phase_iqr_lo']}-{h['phase_iqr_hi']}) |"
        )
    lines.extend(["", "## Per-column fit changes vs baseline", ""])
    header = "| Kernel | " + " | ".join(FIT_COLS) + " |"
    sep = "|---|" + "|".join("---:" for _ in FIT_COLS) + "|"
    lines.extend([header, sep])
    for core in KERNELS:
        if core == baseline_core:
            continue
        pc = runs[core]["per_column"]
        cells = [f"{pc[c]['rows_changed']} / {pc[c]['max_abs_delta']:.6g}" for c in FIT_COLS]
        lines.append(f"| {core} | " + " | ".join(cells) + " |")
    lines.append("")
    lines.append("Each cell is `rows changed / max |Δ|` vs the Haswell baseline refit.")
    OUT_MD.write_text("\n".join(lines) + "\n")
    print(f"wrote {OUT_MD}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
