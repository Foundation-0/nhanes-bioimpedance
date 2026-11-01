#!/usr/bin/env python3
"""Fail if git-tracked files contain per-participant NHANES rows or respondent identifiers.

Aggregate summaries (counts, medians, no row-level participant IDs) are allowed. See README.md policy.
"""
from __future__ import annotations

import gzip
import io
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Tracked paths must not hold row-level or binary survey microdata.
FORBIDDEN_SUFFIX = re.compile(
    r"(?i)(\.xpt$|\.sas7bdat$|\.sav$|\.dta$|\.rds$|\.parquet$|\.feather$|\.arrow$|\.pkl$|\.pickle$|"
    r"\.npz$|\.npy$|\.xlsx$|\.xls$|\.ods$|\.csv\.gz$|\.tsv\.gz$|\.parquet\.gz$|\.feather\.gz$|"
    r"\.json\.gz$|\.jsonl\.gz$|\.dat$|/fits\.csv$|^data/)"
)

BINARY_TABULAR_UNDER = re.compile(r"(?i)^(?:results|certificates|commitment)/")

SEQN_LITERAL = re.compile(r"(?i)\bseqn\b\s*[,:=\t]\s*(\d+)")
BARE_ID_LINE = re.compile(r"^\d{5,7}\s*$")
NOTEBOOK_SEQN = re.compile(r'(?i)"[^"]*seqn[^"]*"\s*:\s*(\d+)')
JSON_ID_KEY = re.compile(
    r'(?i)"(?:seqn|respondent_id|participant_id|sequence_number|nhanes_id)"\s*:\s*(\d+)'
)

ID_HEADER = re.compile(
    r"(?i)^(seqn|respondent[_\s-]?id|participant[_\s-]?id|sequence[_\s-]?number|nhanes[_\s-]?id)$"
)

TEXT_TABLE_SUFFIXES = (".csv", ".tsv", ".txt", ".json", ".jsonl", ".ipynb")


def is_pilot_python(rel: str) -> bool:
    n = norm_rel(rel)
    return n.startswith("pilot/") and n.endswith(".py")


def is_utf8_text(raw: bytes) -> bool:
    if b"\x00" in raw[:8192]:
        return False
    try:
        raw.decode("utf-8")
        return True
    except UnicodeDecodeError:
        return False


def scan_row_table_rules(rel: str, text: str) -> list[str]:
    """Detect row-level participant tables in any UTF-8 text (any path or suffix)."""
    errs: list[str] = []
    blobs = [text]
    if "\\n" in text:
        blobs.append(text.replace("\\n", "\n"))
    seen: set[str] = set()
    for blob in blobs:
        if blob in seen:
            continue
        seen.add(blob)
        lines = blob.splitlines()
        if not lines:
            continue
        if header_has_participant_id(lines[0]) and len(lines) > 1:
            errs.append(f"{rel}: row-level table with participant id column header")
        for i, line in enumerate(lines[:-1]):
            if header_has_participant_id(line) and lines[i + 1].strip():
                errs.append(f"{rel}: row-level table with participant id column header")
                break
        if len(lines) >= 3:
            bare = sum(1 for ln in lines if BARE_ID_LINE.match(ln))
            if bare >= 3 and bare / len(lines) >= 0.5:
                errs.append(f"{rel}: file looks like a list of bare respondent numbers")
    return errs


def git_ls_files() -> list[str]:
    out = subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True)
    return [line.strip() for line in out.splitlines() if line.strip()]


def norm_rel(rel: str) -> str:
    return rel.replace("\\", "/")


def scan_path_rules(rel: str) -> list[str]:
    n = norm_rel(rel)
    if FORBIDDEN_SUFFIX.search(n):
        return [f"forbidden tracked path or extension: {rel}"]
    low = n.lower()
    if BINARY_TABULAR_UNDER.match(n) and low.endswith(".zip"):
        return [f"zip archive under results/certificates/commitment: {rel}"]
    return []


def split_header(line: str) -> list[str]:
    if "\t" in line and "," not in line:
        return [c.strip() for c in line.split("\t")]
    return [c.strip() for c in line.split(",")]


def header_has_participant_id(header_line: str) -> bool:
    cols = split_header(header_line)
    return any(ID_HEADER.match(c) for c in cols)


def scan_text_content(rel: str, text: str) -> list[str]:
    if is_pilot_python(rel):
        return []
    errs: list[str] = []
    n = norm_rel(rel)
    for i, line in enumerate(text.splitlines(), 1):
        m = SEQN_LITERAL.search(line)
        if m:
            errs.append(f"{rel}:{i}: SEQN/respondent literal ({m.group(1)})")
        for m in JSON_ID_KEY.finditer(line):
            errs.append(f"{rel}:{i}: JSON participant id ({m.group(1)})")
    errs.extend(scan_row_table_rules(rel, text))
    low = n.lower()
    if low.endswith(".json"):
        try:
            obj = json.loads(text)
        except json.JSONDecodeError:
            pass
        else:
            errs.extend(_scan_json_object(rel, obj))
    if low.endswith(".jsonl"):
        for i, line in enumerate(text.splitlines(), 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            errs.extend(f"{rel}:{i}: {e}" for e in _scan_json_object("", obj))
    if low.endswith(".ipynb"):
        try:
            nb = json.loads(text)
        except json.JSONDecodeError:
            return errs
        for m in NOTEBOOK_SEQN.finditer(json.dumps(nb)):
            errs.append(f"{rel}: notebook JSON contains seqn value {m.group(1)}")
    return errs


def _scan_json_object(rel: str, obj, prefix: str = "") -> list[str]:
    errs: list[str] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(k, str) and ID_HEADER.match(k.strip()) and isinstance(v, (int, float)):
                errs.append(f"JSON participant id key {k!r} value {v}")
            elif isinstance(k, str) and k.lower() == "seqn" and isinstance(v, (int, float)):
                errs.append(f"JSON seqn value {v}")
            else:
                errs.extend(_scan_json_object(rel, v, prefix))
    elif isinstance(obj, list):
        for item in obj[:50]:
            errs.extend(_scan_json_object(rel, item, prefix))
    return [f"{rel}: {e}" if rel else e for e in errs]


def _scan_parquet_bytes(rel: str, raw: bytes) -> list[str]:
    try:
        import pyarrow.parquet as pq
    except ImportError:
        return [f"{rel}: parquet row store (install pyarrow to inspect)"]
    table = pq.read_table(io.BytesIO(raw))
    for c in table.column_names:
        if ID_HEADER.match(c.strip().replace(" ", "_")) or c.lower() == "seqn":
            return [f"{rel}: parquet contains participant id column {c!r}"]
    return []


def _scan_feather_bytes(rel: str, raw: bytes) -> list[str]:
    try:
        import pyarrow.feather as feather
    except ImportError:
        return [f"{rel}: feather row store"]
    table = feather.read_table(io.BytesIO(raw))
    for c in table.column_names:
        if ID_HEADER.match(c.strip().replace(" ", "_")) or c.lower() == "seqn":
            return [f"{rel}: feather contains participant id column {c!r}"]
    return []


def scan_bytes(rel: str, raw: bytes) -> list[str]:
    errs = scan_path_rules(rel)
    if errs:
        return errs
    n = norm_rel(rel)
    low = n.lower()

    if raw[:2] == b"\x1f\x8b":
        try:
            inner = gzip.decompress(raw)
        except OSError:
            return [f"{rel}: gzip payload (cannot decompress)"]
        inner_name = low[:-3] if low.endswith(".gz") else rel + ".decompressed"
        return scan_bytes(inner_name, inner)

    if raw[:2] == b"PK":
        try:
            with zipfile.ZipFile(io.BytesIO(raw)) as zf:
                for name in zf.namelist():
                    if name.endswith("/"):
                        continue
                    payload = zf.read(name)
                    inner_rel = f"{rel}:{name}"
                    errs.extend(scan_bytes(inner_rel, payload))
            return errs
        except zipfile.BadZipFile:
            return [f"{rel}: zip archive"]

    if raw[:4] == b"PAR1":
        return _scan_parquet_bytes(rel, raw)

    if low.endswith(".feather") or (len(raw) > 8 and raw[:8] == b"ARROW1\x00"):
        return _scan_feather_bytes(rel, raw)

    if BINARY_TABULAR_UNDER.match(n) and not low.endswith(TEXT_TABLE_SUFFIXES):
        if low.endswith((".csv", ".tsv")):
            pass
        elif _looks_binary(raw):
            return [f"{rel}: binary content under results/certificates/commitment"]

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        if low.endswith((".csv", ".tsv", ".txt", ".json", ".jsonl")):
            return [f"{rel}: non-text tabular file"]
        return []
    return scan_text_content(rel, text)


def _looks_binary(raw: bytes) -> bool:
    if not raw:
        return False
    if b"\x00" in raw[:8192]:
        return True
    textish = sum(1 for b in raw[:4096] if 32 <= b <= 126 or b in (9, 10, 13))
    return textish / min(len(raw), 4096) < 0.85


def scan_file(rel: str) -> list[str]:
    path = ROOT / rel
    if not path.is_file():
        return []
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
