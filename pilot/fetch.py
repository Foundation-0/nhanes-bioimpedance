"""Download the NHANES 1999-2004 files this project reads into data/ (not committed): bioimpedance (BIX),
demographics and survey design (DEMO), body measures (BMX), DXA (DXX) and the public-use Linked Mortality Files.

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
LMF = "https://ftp.cdc.gov/pub/Health_Statistics/NCHS/datalinkage/linked_mortality"
DXA = "https://wwwn.cdc.gov/nchs/data/nhanes/public"
# file: (url, size bytes, sha256 as fetched 31 Oct 2026)
FILES = {
    "BIX.xpt": (f"{BASE}/1999/DataFiles/BIX.xpt", 4903040, "71eb96363436a2834effa5d3d010c45f40e37a8e702797d231c16e3e5fb0acc6"),
    "BIX_B.xpt": (f"{BASE}/2001/DataFiles/BIX_B.xpt", 5490000, "09465cfb496006799b9a0430a42137a59ceaa16ea7b81a0ebde49242ecbffcf7"),
    "BIX_C.xpt": (f"{BASE}/2003/DataFiles/BIX_C.xpt", 4919600, "e1699e68a4103b9cba23c714691b70bdd61bf239b6881949b019b1fc9959df69"),
    "DEMO.xpt": (f"{BASE}/1999/DataFiles/DEMO.xpt", 11500560, "a17bd1ebfd6007b8dc93f16259cb090678eb6c467a39363b7e932bba15febf89"),
    "DEMO_B.xpt": (f"{BASE}/2001/DataFiles/DEMO_B.xpt", 3273520, "6458dc2307cee244ab6ba26f70ec78c7b842ffc68e668bc43f0ab6b9737937d9"),
    "DEMO_C.xpt": (f"{BASE}/2003/DataFiles/DEMO_C.xpt", 3569840, "2a2fdb88263337bfa06f0516bfb419631595f0a0ee88fb96069bed13d1857c6f"),
    "BMX.xpt": (f"{BASE}/1999/DataFiles/BMX.xpt", 2827840, "6b9bc4d998c0004fc42b213cc7f5bf347df937707f46d6d25fab926723a60500"),
    "BMX_B.xpt": (f"{BASE}/2001/DataFiles/BMX_B.xpt", 2183680, "55715d4387960f88e48a2adf44da0b270a83290b1edf7c8e4ecc0eb2c29c59cf"),
    "BMX_C.xpt": (f"{BASE}/2003/DataFiles/BMX_C.xpt", 2551120, "b3d3e431b5964ea8b5807035044322fcf32f3878d814d4a844204e51c793f090"),
    "DXX.xpt": (f"{DXA}/1999/datafiles/dxx.xpt", 24737440, "9567c94c4a2efd3bb67817f051bec4e778c648c9a2dd222a894fe0ca78598d37"),
    "DXX_B.xpt": (f"{DXA}/2001/datafiles/dxx_b.xpt", 32695200, "6eeb2dabff1fc4a33df2dfe2b46e86eb6f0986319f238f1cb8066e7d695852f6"),
    "DXX_C.xpt": (f"{DXA}/2003/datafiles/dxx_c.xpt", 30371680, "8840fcaa518d7ee0c3c64e826dfb512cf0ac9be5cd00b1895a9782cb885c91df"),
    "NHANES_1999_2000_MORT_2019_PUBLIC.dat": (
        f"{LMF}/NHANES_1999_2000_MORT_2019_PUBLIC.dat",
        487666,
        "562bd367107add0b2b40fed36a062d8b194fca31e11aab897a0efad4bebc8b26",
    ),
    "NHANES_2001_2002_MORT_2019_PUBLIC.dat": (
        f"{LMF}/NHANES_2001_2002_MORT_2019_PUBLIC.dat",
        540362,
        "2788c8c8a02995ea5686882b5fe65b4b9cd415016031525f8a3c1a3646c47f1b",
    ),
    "NHANES_2003_2004_MORT_2019_PUBLIC.dat": (
        f"{LMF}/NHANES_2003_2004_MORT_2019_PUBLIC.dat",
        495722,
        "639f6b3292a55b112fbfc842954af3d8d32bcce287cd8ae49319e5aca1c033c0",
    ),
}
UA = "Foundation0 nhanes-bioimpedance (https://github.com/Foundation-0/nhanes-bioimpedance)"


def main():
    DATA.mkdir(exist_ok=True)
    err = 0
    for name, (url, size, want_sha) in FILES.items():
        path = DATA / name
        if not path.exists():
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=600) as r:
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
