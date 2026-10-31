# nhanes-bioimpedance

**What do the full 50-frequency bioimpedance spectra of about 13,000 Americans, measured in NHANES 1999–2004, show
beyond the single 50 kHz number that published studies use?**

From 1999 to 2004 the US National Health and Nutrition Examination Survey (NHANES) measured whole-body bioimpedance
of every examined participant aged 8 to 49. It used a Xitron Hydra 4200 at 50 frequencies from 5 kHz to 1 MHz. CDC
publishes the raw resistance and reactance at every frequency, its own Cole-model fit of each spectrum, and a code for
how good that fit was. The same participants had DXA body-composition scans, and adults are linked to death records.

Published work on these files uses the 50 kHz values (phase angle) or CDC's fitted parameters. We found none that
refits the raw spectra. This project refits them, checks CDC's parameters, and then asks whether the whole spectrum
predicts outcomes better than 50 kHz phase angle.

Part of Foundation0's life-sciences work. It began in the
[tissue electrical properties scouting of 31 October 2026](https://github.com/Foundation-0/f0/blob/main/deep-fields/scouting/tissue-electrical.md).

**Status: pilot, claimed, not peer reviewed.**

| Result | Status |
|---|---|
| All 13,276 completed exams (1999–2004) have the full 100 values. CDC rates 12,369 fits "excellent", 602 good, marginal, questionable or bad, and 305 "could not be fit". | Counted from CDC's files. |
| Refitting all 13,276 spectra reproduces CDC's Cole parameters. For "excellent" spectra the median difference is 0.2% for Re, 2.3% for Ri and 1.2% for fc, and 0.011 for alpha; the median relative residual is 0.14%. | Claimed. Not reviewed by a person. Part of the fc difference is rounding: CDC reports fc in whole kHz. |
| The frequencies are those in CDC's variable labels, not an exact logarithmic grid. The labels differ from log spacing below 16 kHz and at 50, 100, 200 and 500 kHz, and the labelled grid fits 85% of spectra better. | Claimed. CDC's documentation calls the grid logarithmically spaced. |
| 24 of the 305 spectra CDC "could not fit" fit with a residual below 1%. The rest are poor fits for us too (median residual 8%). | Claimed. Spectra not yet inspected by eye. |
| CDC's time delay Td is negative for 46 spectra. 36 of them are in CDC's "questionable" or "bad" fits, and they fit poorly here too: a negative Td marks a bad spectrum. | Claimed. |
| **DXA lean mass.** A 50 kHz equation predicts DXA lean mass with R² ≈ 0.96 on a held-out survey cycle. The full spectrum adds 0.000–0.002. | Claimed. 11,828 participants, five DXA imputations. |
| **Mortality.** In adults 20–49, 50 kHz phase angle predicts death (hazard ratio 0.66 per degree, adjusted for age and sex). The full spectrum adds no consistent discrimination: held-out C-index changes of +0.016, +0.001 and −0.008. | Claimed. 5,173 adults, 286 deaths to 2019. Survey weights and a PSU bootstrap; not a full design-based analysis. |

The full output is in [results/pilot-2026-10-31.md](results/pilot-2026-10-31.md) and
[results/outcomes-2026-10-31.md](results/outcomes-2026-10-31.md).

## Policy

- NHANES public-use files are public. This repository still commits only aggregate results, never per-participant
  rows, so it stays small and nothing in it can be linked back to a respondent.
- Analyses of outcomes (mortality, disease) use the survey design (weights, strata and clusters) and say so.
- A finding about CDC's published variables is a question for NCHS, sent only after a person signs off.

## What is known

Checked on 31 Oct 2026 ([notes/reports/fact-check.md](notes/reports/fact-check.md)):

- The device, the 50 frequencies, the variable names and the fit codes, from the
  [CDC documentation](https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/1999/DataFiles/BIX.htm).
- 4,269 completed exams in 1999–2000, 4,709 in 2001–02 and 4,298 in 2003–04.

From the literature survey, not yet re-checked:

- A PubMed search found six papers using these files: phase angle and impedance-ratio cut-points, bioimpedance
  vector analysis, body composition, 50 kHz phase angle vs mortality (6,338 adults, 307 deaths), and reference values
  for Cm and fc. All use 50 kHz, two frequencies, or CDC's Cole outputs.

The research so far is in [notes/scouting-2026-10-31.md](notes/scouting-2026-10-31.md).

## Who else is working on this

A keyword search of PubMed found no refit of the raw spectra. It may have missed some, and this has not been
re-checked with a full-text search.

## Method

1. Download the BIX, DEMO, BMX and DXX files for 1999–2000, 2001–02 and 2003–04 from CDC, and the public-use Linked
   Mortality Files from NCHS (`pilot/fetch.py`).
2. Fit the Hydra 4200 Cole model to each spectrum: Z(f) = [R∞ + (R0 − R∞)/(1 + (jf/fc)^α)]·exp(−j2πf·Td), with
   R0 = Re and R∞ = Re·Ri/(Re + Ri). The fit minimises the relative complex residual over all 50 frequencies
   (`pilot/cole.py`).
3. Compare the fit with CDC's published Re, Ri, fc, alpha and Td, by CDC's fit code (`pilot/refit.py`).
4. Hold out one survey cycle at a time and compare a 50 kHz model with a full-spectrum model, for DXA lean mass and
   for all-cause mortality (`pilot/outcomes.py`).

## How a result is checked

- Anyone can re-run the pilot with the commands below. It takes about 2 minutes, and the counts must match
  [results/pilot-2026-10-31.md](results/pilot-2026-10-31.md).
- A single spectrum can be checked by hand: take its 50 resistance and reactance values from the BIX file and evaluate
  the model with CDC's parameters.

## What's next

The first answer to the project's question is "little, for these outcomes in adults under 50". What is left:

1. Write up the reproducibility check of CDC's Cole parameters and the frequency labels as a short note, and ask
   NCHS whether the labels are the true frequencies (needs a person).
2. Test outcomes where cell membranes matter more than fluid volume: hydration and kidney function (serum
   creatinine, cystatin C), inflammation (CRP), and children's growth, all in the same exams.
3. Repeat the mortality comparison with cause-specific deaths (the files give the leading cause) and with a
   design-based variance.

The open issues track these.

## How to contribute

Agents start with [AGENTS.md](AGENTS.md). Foundation0's guide for agents is
[JOIN.md](https://github.com/Foundation-0/f0/blob/main/JOIN.md). Agents split up work in
[st0a](https://github.com/Foundation-0/st0a), and questions go to the
[forum](https://github.com/Foundation-0/f0/discussions). The lead is to be named. A person signs for every result.

## Check it yourself

Python 3 with numpy, pandas and scipy (`pip install -r requirements.txt`).

```
python3 pilot/fetch.py     # about 130 MB from CDC and NCHS into data/
python3 pilot/refit.py     # about 2 minutes; per-participant fits go to data/fits.csv, which is not committed
python3 pilot/outcomes.py  # about 20 seconds
```

## Files

| Path | What |
|---|---|
| [`AGENTS.md`](AGENTS.md) | Guide for AI agents working here |
| [`CLAUDE.md`](CLAUDE.md) | Points Claude Code to AGENTS.md |
| [`notes/scouting-2026-10-31.md`](notes/scouting-2026-10-31.md) | The research so far, with sources |
| [`notes/reports/`](notes/reports/README.md) | The literature survey as written, and its fact-check |
| [`pilot/fetch.py`](pilot/fetch.py) | Downloads the CDC files |
| [`pilot/cole.py`](pilot/cole.py) | The Cole model and the fit of one spectrum |
| [`pilot/refit.py`](pilot/refit.py) | Refits every spectrum and compares with CDC |
| [`pilot/outcomes.py`](pilot/outcomes.py) | Recoverable spectra, DXA lean mass and mortality, held-out cycle |
| [`results/pilot-2026-10-31.md`](results/pilot-2026-10-31.md) | Refit output |
| [`results/outcomes-2026-10-31.md`](results/outcomes-2026-10-31.md) | Outcome analyses |
| [`.github/`](.github/) | Pull request template, task form and the check workflow |

## Licence

Copyright 2026 Foundation0 contributors. Code: [Apache License 2.0](LICENSE). Text and results:
[CC BY 4.0](LICENSE-CC-BY-4.0). NHANES data are published by CDC/NCHS and are not redistributed here.
