# Third-party data and software

## NHANES public-use files (CDC/NCHS)

This repository downloads survey files from the US National Center for Health Statistics
(NHANES 1999–2004 bioimpedance, demographics, and related public-use releases). Those
files are **not** committed to git; `pilot/fetch.py` retrieves them into `data/`, which
is gitignored.

- Source: https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/
- Licence: public-use data; follow NCHS/CDC citation and redistribution rules for any
  redistribution of the raw files themselves.
- Do not strip NCHS file headers or documentation when redistributing downloaded files.

## NCHS public-use Linked Mortality Files

Outcomes analyses (pull requests stacked on the pilot) use the NCHS Linked Mortality
Files (LMF), follow-up through 31 December 2019, via URLs documented in `pilot/fetch.py`.

- Source: https://www.cdc.gov/nchs/data-linkage/mortality-public.htm
- Restrictions: public-use LMF; see NCHS data-linkage documentation for permitted use
  and citation. This repo stores **aggregate** mortality results only in git.

## Python and R packages

Runtime pins are in `requirements.txt` and (where R checks are used) `requirements-r.txt`.
Versions are chosen for reproducible numerics on CI (single-threaded BLAS).

## No implied clinical use

NHANES and LMF data support **research associations** in this repo. Nothing here is
clinical guidance or causal advice about individuals.
