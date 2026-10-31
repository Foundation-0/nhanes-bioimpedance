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
FILES = {  # file: (URL, size in bytes when fetched on 31 Oct 2026)
    "BIX.xpt": (f"{BASE}/1999/DataFiles/BIX.xpt", 4903040),
    "BIX_B.xpt": (f"{BASE}/2001/DataFiles/BIX_B.xpt", 5490000),
    "BIX_C.xpt": (f"{BASE}/2003/DataFiles/BIX_C.xpt", 4919600),
    "DEMO.xpt": (f"{BASE}/1999/DataFiles/DEMO.xpt", 11500560),
    "DEMO_B.xpt": (f"{BASE}/2001/DataFiles/DEMO_B.xpt", 3273520),
    "DEMO_C.xpt": (f"{BASE}/2003/DataFiles/DEMO_C.xpt", 3569840),
    "BMX.xpt": (f"{BASE}/1999/DataFiles/BMX.xpt", 2827840),
    "BMX_B.xpt": (f"{BASE}/2001/DataFiles/BMX_B.xpt", 2183680),
    "BMX_C.xpt": (f"{BASE}/2003/DataFiles/BMX_C.xpt", 2551120),
    # DXA, released as five multiple imputations per participant
    "DXX.xpt": (f"{DXA}/1999/datafiles/dxx.xpt", 24737440),
    "DXX_B.xpt": (f"{DXA}/2001/datafiles/dxx_b.xpt", 32695200),
    "DXX_C.xpt": (f"{DXA}/2003/datafiles/dxx_c.xpt", 30371680),
    # NCHS public-use Linked Mortality Files, follow-up to 31 Dec 2019
    "NHANES_1999_2000_MORT_2019_PUBLIC.dat": (f"{LMF}/NHANES_1999_2000_MORT_2019_PUBLIC.dat", 487666),
    "NHANES_2001_2002_MORT_2019_PUBLIC.dat": (f"{LMF}/NHANES_2001_2002_MORT_2019_PUBLIC.dat", 540362),
    "NHANES_2003_2004_MORT_2019_PUBLIC.dat": (f"{LMF}/NHANES_2003_2004_MORT_2019_PUBLIC.dat", 495722),
}
UA = "Foundation0 nhanes-bioimpedance (https://github.com/Foundation-0/nhanes-bioimpedance)"


def main():
    DATA.mkdir(exist_ok=True)
    for name, (url, size) in FILES.items():
        path = DATA / name
        if not path.exists():
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=600) as r:
                path.write_bytes(r.read())
        got = path.stat().st_size
        sha = hashlib.sha256(path.read_bytes()).hexdigest()
        flag = "" if got == size else f"  (size differs from {size}: CDC may have revised the file)"
        print(f"{name:12s} {got:>9d} bytes  sha256 {sha[:16]}{flag}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
