"""Download the NHANES 1999-2004 bioimpedance (BIX) and demographics (DEMO) files into data/ (not committed).

NHANES public-use files are published by the US National Center for Health Statistics (CDC/NCHS).
Usage: python3 pilot/fetch.py
"""
import hashlib
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
BASE = "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public"
FILES = {  # file: (survey cycle folder, size in bytes when fetched on 31 Oct 2026)
    "BIX.xpt": ("1999", 4903040), "BIX_B.xpt": ("2001", 5490000), "BIX_C.xpt": ("2003", 4919600),
    "DEMO.xpt": ("1999", 11500560), "DEMO_B.xpt": ("2001", 3273520), "DEMO_C.xpt": ("2003", 3569840),
}
UA = "Foundation0 nhanes-bioimpedance (https://github.com/Foundation-0/nhanes-bioimpedance)"


def main():
    DATA.mkdir(exist_ok=True)
    for name, (cycle, size) in FILES.items():
        path = DATA / name
        if not path.exists():
            req = urllib.request.Request(f"{BASE}/{cycle}/DataFiles/{name}", headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=120) as r:
                path.write_bytes(r.read())
        got = path.stat().st_size
        sha = hashlib.sha256(path.read_bytes()).hexdigest()
        flag = "" if got == size else f"  (size differs from {size}: CDC may have revised the file)"
        print(f"{name:12s} {got:>9d} bytes  sha256 {sha[:16]}{flag}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
