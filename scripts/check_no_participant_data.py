#!/usr/bin/env python3
"""Fail if git-tracked files contain per-participant NHANES rows or respondent identifiers.

Aggregate summaries (counts, medians, no row-level SEQN) are allowed. See README.md policy.
"""
from __future__ import annotations

import gzip
import io
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FORBIDDEN_PATH = re.compile(
    r"(?i)(^data/|/fits\.csv$|\.xpt$|\.sas7bdat$|\.sav$|\.dta$|\.parquet$|\.feather$|"
    r"\.csv\.gz$|\.tsv\.gz$|\.dat$)"
)
SEQN_LITERAL = re.compile(r"(?i)\bseqn\b\s*[,:=\t]\s*(\d+)")
SEQN_HEADER = re.compile(r"(?i)(^|[,\t])seqn($|[,\t])")
BARE_ID_LINE = re.compile(r"^\d{5,7}\s*$")
NOTEBOOK_SEQN = re.compile(r'(?i)"[^"]*seqn[^"]*"\s*:\s*(\d+)')

ROW_TABLE_SUFFIXES = (".csv", ".tsv", ".txt", ".dat")


def git_ls_files() -> list[str]:
    out = subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True)
    return [line.strip() for line in out.splitlines() if line.strip()]


def scan_path_rules(rel: str) -> list[str]:
    if FORBIDDEN_PATH.search(rel.replace("\\", "/")):
        return [f"forbidden tracked path or extension: {rel}"]
    return []


def scan_text_content(rel: str, text: str) -> list[str]:
    errs: list[str] = []
    for i, line in enumerate(text.splitlines(), 1):
        m = SEQN_LITERAL.search(line)
        if m:
            errs.append(f"{rel}:{i}: SEQN/respondent literal ({m.group(1)})")
    if rel.lower().endswith(ROW_TABLE_SUFFIXES):
        lines = text.splitlines()
        if lines and SEQN_HEADER.search(lines[0]):
            if len(lines) > 1:
                errs.append(f"{rel}: row-level table with seqn/respondent column header")
        if len(lines) >= 3:
            bare = sum(1 for ln in lines if BARE_ID_LINE.match(ln))
            if bare >= 3 and bare / len(lines) >= 0.5:
                errs.append(f"{rel}: file looks like a list of bare respondent numbers")
    if rel.lower().endswith(".ipynb"):
        try:
            nb = json.loads(text)
        except json.JSONDecodeError:
            return errs
        blob = json.dumps(nb)
        for m in NOTEBOOK_SEQN.finditer(blob):
            errs.append(f"{rel}: notebook JSON contains seqn value {m.group(1)}")
    return errs


def scan_bytes(rel: str, raw: bytes) -> list[str]:
    errs = scan_path_rules(rel)
    if errs:
        return errs
    low = rel.lower()
    if low.endswith((".csv.gz", ".tsv.gz")):
        try:
            text = gzip.decompress(raw).decode("utf-8", errors="replace")
        except OSError:
            return [f"{rel}: gzip row store (cannot decompress)"]
        return scan_text_content(rel, text)
    if low.endswith(".parquet"):
        try:
            import pyarrow.parquet as pq
        except ImportError:
            return [f"{rel}: parquet row store (install pyarrow to inspect)"]
        table = pq.read_table(io.BytesIO(raw))
        if any(c.lower() == "seqn" for c in table.column_names):
            return [f"{rel}: parquet contains seqn column"]
        return []
    if low.endswith(".feather"):
        try:
            import pyarrow.feather as feather
        except ImportError:
            return [f"{rel}: feather row store"]
        table = feather.read_table(io.BytesIO(raw))
        if any(c.lower() == "seqn" for c in table.column_names):
            return [f"{rel}: feather contains seqn column"]
        return []
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        if low.endswith(ROW_TABLE_SUFFIXES):
            return [f"{rel}: non-text row table in tracked paths"]
        return []
    return scan_text_content(rel, text)


def scan_file(rel: str) -> list[str]:
    path = ROOT / rel
    if not path.is_file():
        return []
    errs = scan_path_rules(rel)
    if errs:
        return errs
    return scan_bytes(rel, path.read_bytes())


def main() -> int:
    errors: list[str] = []
    for rel in git_ls_files():
        errors.extend(scan_file(rel))
    if errors:
        print("Per-participant data must not be committed (see README.md).", file=sys.stderr)
        for e in errors:
            print(e, file=sys.stderr)
        return 1
    print("OK: no per-participant data in tracked files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
