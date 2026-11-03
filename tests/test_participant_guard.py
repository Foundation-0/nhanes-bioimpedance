"""Tests for scripts/check_no_participant_data.py — bypass cases and clean-repo check."""
from __future__ import annotations

import gzip
import io
import json
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import check_no_participant_data as guard  # noqa: E402


def _bypass_csv_seqn() -> str:
    return "seqn,re,ri\n62161,668,980\n"


def _bypass_short_literal() -> str:
    tag = "SEQ" + "N"
    return f"meta {tag}=123 end\n"


def test_old_bypass_seqn_lowercase_csv():
    errs = guard.scan_text_content("results/fits_summary.csv", _bypass_csv_seqn())
    assert any("row-level" in e or "62161" in e for e in errs)


def test_old_bypass_short_seqn_literal():
    errs = guard.scan_text_content("notes/foo.txt", _bypass_short_literal())
    assert any("123" in e for e in errs)


def test_respondent_id_header_bypass_closed():
    text = "respondent_id,re,ri\n62161,668,980\n"
    errs = guard.scan_text_content("results/summary.csv", text)
    assert any("participant id column" in e for e in errs)


def test_json_row_bypass_closed():
    key = "seq" + "n"
    text = json.dumps([{key: 62161, "re": 668}])
    errs = guard.scan_text_content("results/out.json", text)
    assert errs


def test_jsonl_bypass_closed():
    key = "seq" + "n"
    text = json.dumps({key: 62161}) + "\n"
    errs = guard.scan_text_content("results/out.jsonl", text)
    assert errs


def test_zip_csv_bypass_closed():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("inside.csv", _bypass_csv_seqn())
    errs = guard.scan_bytes("results/foo.zip", buf.getvalue())
    assert errs


def test_parquet_gz_bypass_closed():
    pa = pytest.importorskip("pyarrow")
    import pyarrow.parquet as pq

    table = pa.table({("seq" + "n"): [62161], "re": [668.0]})
    pq_buf = io.BytesIO()
    pq.write_table(table, pq_buf)
    raw = gzip.compress(pq_buf.getvalue())
    errs = guard.scan_bytes("results/foo.parquet.gz", raw)
    assert errs


def test_xlsx_path_blocked():
    assert guard.scan_path_rules("results/foo.xlsx")


def test_old_bypass_bare_id_list():
    text = "62161\n62162\n62163\n62164\n"
    errs = guard.scan_text_content("certificates/ids.csv", text)
    assert any("bare respondent" in e for e in errs)


def test_parquet_with_seqn_column():
    pa = pytest.importorskip("pyarrow")
    import pyarrow.parquet as pq

    table = pa.table({("seq" + "n"): [62161], "re": [668.0]})
    buf = io.BytesIO()
    pq.write_table(table, buf)
    errs = guard.scan_bytes("results/foo.parquet", buf.getvalue())
    assert errs


def test_csv_gz_with_seqn():
    raw = gzip.compress(_bypass_csv_seqn().encode())
    errs = guard.scan_bytes("results/foo.csv.gz", raw)
    assert errs


def test_utf8_bom_csv():
    raw = b"\xef\xbb\xbfseqn,re\n62161,1\n"
    errs = guard.scan_bytes("results/bom.csv", raw)
    assert any("row-level" in e for e in errs)


def test_semicolon_delimited_header():
    key = "seq" + "n"
    text = f"{key};re\n62161;668\n"
    errs = guard.scan_text_content("results/euro.csv", text)
    assert any("row-level" in e for e in errs)


def test_pipe_delimited_header():
    key = "seq" + "n"
    text = f"{key}|re\n62161|668\n"
    errs = guard.scan_text_content("results/pipe.tsv", text)
    assert any("row-level" in e for e in errs)


def test_invalid_utf8_extensionless_latin1_fallback():
    key = "seq" + "n"
    raw = b"\xff\n" + f"{key},re\n62161,1\n".encode()
    errs = guard.scan_bytes("participant_export", raw)
    assert any("row-level" in e for e in errs)


def test_invalid_utf8_binary_fail_closed():
    raw = bytes(range(256))
    errs = guard.scan_bytes("results/binary_blob", raw)
    assert any("fail-closed" in e or "binary" in e for e in errs)


def test_extensionless_root_export():
    errs = guard.scan_text_content("participant_export", _bypass_csv_seqn())
    assert any("row-level" in e for e in errs)


def test_json_file_with_embedded_csv():
    errs = guard.scan_bytes("docs/data.json", _bypass_csv_seqn().encode())
    assert any("row-level" in e for e in errs)


def test_readme_extra_md_with_csv():
    errs = guard.scan_text_content("README_extra.md", _bypass_csv_seqn())
    assert any("row-level" in e for e in errs)


def test_legitimate_readme_passes():
    text = (ROOT / "README.md").read_text()
    assert not guard.scan_text_content("README.md", text)


def test_legitimate_notice_passes():
    text = (ROOT / "NOTICE.md").read_text()
    assert not guard.scan_text_content("NOTICE.md", text)


def test_legitimate_proof_md_passes():
    path = ROOT / "results" / "pilot-2026-10-31" / "PROOF.md"
    if path.exists():
        assert not guard.scan_text_content(str(path.relative_to(ROOT)), path.read_text())


def test_aggregate_pilot_md_passes():
    md = (ROOT / "results" / "pilot-2026-10-31.md").read_text()
    errs = guard.scan_text_content("results/pilot-2026-10-31.md", md)
    assert not errs


def test_script_passes_on_clean_repo():
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_no_participant_data.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout


def test_script_catches_staged_bypass_in_temp_repo(tmp_path: Path):
    repo = tmp_path / "r"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "t@t.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=repo, check=True)
    (repo / "results").mkdir()
    (repo / "results" / "bad.csv").write_text(_bypass_csv_seqn())
    script = ROOT / "scripts" / "check_no_participant_data.py"
    (repo / "scripts").mkdir()
    (repo / "scripts" / "check_no_participant_data.py").write_text(script.read_text())
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    proc = subprocess.run(
        [sys.executable, "scripts/check_no_participant_data.py"],
        cwd=repo,
        capture_output=True,
        text=True,
    )
    assert proc.returncode != 0


def _minimal_png() -> bytes:
    return b"\x89PNG\r\n\x1a\n" + b"\x00" * 8


def _minimal_jpeg() -> bytes:
    return b"\xff\xd8\xff\xe0" + b"\x00" * 4


def _minimal_gif() -> bytes:
    return b"GIF89a" + b"\x00" * 8


def _minimal_ico() -> bytes:
    return b"\x00\x00\x01\x00" + b"\x00" * 12


def _minimal_woff2() -> bytes:
    return b"wOF2" + b"\x00" * 8


def _minimal_woff() -> bytes:
    return b"wOFF" + b"\x00" * 8


def _minimal_webp() -> bytes:
    return b"RIFF" + b"\x00" * 4 + b"WEBP" + b"\x00" * 4


@pytest.mark.parametrize(
    "rel,body",
    [
        ("og.png", _minimal_png()),
        ("og.jpg", _minimal_jpeg()),
        ("favicon.ico", _minimal_ico()),
        ("site/font.woff2", _minimal_woff2()),
        ("site/font.woff", _minimal_woff()),
        ("img/logo.webp", _minimal_webp()),
    ],
)
def test_standard_web_binary_allowed(rel: str, body: bytes):
    assert not guard.scan_bytes(rel, body)


@pytest.mark.parametrize(
    "rel,body",
    [
        ("og.png", b"seqn,re\n62161,1\n"),
        ("og.png", b"fakepng-content-without-magic"),
        ("og.jpg", b"not jpeg"),
        ("favicon.ico", b"ICO"),
        ("site/font.woff2", b"woff2 fake"),
    ],
)
def test_standard_web_binary_suffix_magic_mismatch_fails(rel: str, body: bytes):
    errs = guard.scan_bytes(rel, body)
    assert errs


def test_latin1_leading_byte_glued_to_seqn_header():
    key = "seq" + "n"
    raw = b"\xff" + f"{key},re\n62161,1\n".encode()
    errs = guard.scan_bytes("participant_export", raw)
    assert any("row-level" in e for e in errs)

