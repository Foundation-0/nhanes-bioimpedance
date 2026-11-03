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
# (URL path cycle folder, size bytes, sha256 as of 31 Oct 2026 fetch)
FILES = {
    "BIX.xpt": ("1999", 4903040, "71eb96363436a2834effa5d3d010c45f40e37a8e702797d231c16e3e5fb0acc6"),
    "BIX_B.xpt": ("2001", 5490000, "09465cfb496006799b9a0430a42137a59ceaa16ea7b81a0ebde49242ecbffcf7"),
    "BIX_C.xpt": ("2003", 4919600, "e1699e68a4103b9cba23c714691b70bdd61bf239b6881949b019b1fc9959df69"),
    "DEMO.xpt": ("1999", 11500560, "a17bd1ebfd6007b8dc93f16259cb090678eb6c467a39363b7e932bba15febf89"),
    "DEMO_B.xpt": ("2001", 3273520, "6458dc2307cee244ab6ba26f70ec78c7b842ffc68e668bc43f0ab6b9737937d9"),
    "DEMO_C.xpt": ("2003", 3569840, "2a2fdb88263337bfa06f0516bfb419631595f0a0ee88fb96069bed13d1857c6f"),
}
UA = "Foundation0 nhanes-bioimpedance (https://github.com/Foundation-0/nhanes-bioimpedance)"


def main():
    DATA.mkdir(exist_ok=True)
    err = 0
    for name, (cycle, size, want_sha) in FILES.items():
        path = DATA / name
        if not path.exists():
            req = urllib.request.Request(f"{BASE}/{cycle}/DataFiles/{name}", headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=120) as r:
                path.write_bytes(r.read())
        raw = path.read_bytes()
        got = len(raw)
        sha = hashlib.sha256(raw).hexdigest()
        if got != size:
            print(f"{name:12s} size {got} differs from pinned {size} (CDC may have revised the file)", file=sys.stderr)
            err = 1
        if sha != want_sha:
            print(f"{name:12s} sha256 mismatch: got {sha}, want {want_sha}", file=sys.stderr)
            err = 1
        print(f"{name:12s} {got:>9d} bytes  sha256 {sha[:16]}")
    return err


if __name__ == "__main__":
    sys.exit(main())
