# Fact-check, 31 October 2026

Claims from the literature survey ([literature-survey-2026-10-31.md](literature-survey-2026-10-31.md)) that the
scouting agent re-checked against the source before using them, with the result.

| Claim | Checked against | Result |
|---|---|---|
| NHANES 1999–2000 used a Xitron Hydra 4200 at 50 frequencies from 5 kHz to 1 MHz, with resistance (BIXS…) and reactance (BIXC…) at each, Cole outputs BIDRECF, BIDRICF, BIDCM, BIDTD, BIDALPHA, BIDFC and fit code BIDFIT | [CDC BIX documentation](https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/1999/DataFiles/BIX.htm) | Confirmed. 4,269 completed exams in 1999–2000, ages 8–49; fit codes 0–5 and 7 as listed. |
| About 13,300 completed exams across 1999–2004 (4,269, 4,709, 4,298) | The three BIX files themselves | Confirmed: 13,276. |
| The frequencies are "logarithmically spaced" | Variable labels in the CDC documentation, and fits of all spectra | Approximate. The labels differ from an exact log grid below 16 kHz and at 50, 100, 200 and 500 kHz, and the labelled grid fits 85% of spectra better. |
| CRCNS tes-1: 14 subjects, 1,846 intracranial electrodes, fitted voltage magnitudes, MRI and segmentations; free account; raw ECoG not included | [CRCNS tes-1](https://crcns.org/data-sets/methods/tes-1/about-tes-1) | Confirmed. Dataset DOI 10.6080/K0XW4GQ1; paper Huang et al. 2017, eLife 6:e18834. No licence is stated. |
| The IFAC/webnir mirror serves Gabriel's 1996 measured data as CSV/TXT for 41 tissues, under CC BY-NC-SA 4.0 | [webnir Gabriel page](https://webnir.eu/04-Dosimetry/04-Gabriel.php?lang=gb) | Partly confirmed. The page lists "41 with experimental data" and offers CSV/TXT per series; CC BY-NC-SA 4.0 is the website's licence, with no separate data licence. Animal tissue was mostly ovine, used within two hours of death; human autopsy material was 24–48 h after death. The bladder's species is not stated. |
| Puonti et al. 2020 used the 14-patient intracranial dataset to compare pipelines | Crossref and the abstract | Confirmed: NeuroImage 208:116431, authors Puonti, Saturnino, Madsen and Thielscher. It found segmentation differences to be a major factor. |
| McCann et al. 2019, Brain Topography | Crossref | Confirmed: 32:825–858. The weighted-mean values in the survey were not re-checked. |
| Christ et al. 2025, in vivo human skin 15–110 GHz | Crossref | The title "Human Skin Model From 15 GHz to 110 GHz" and the authors were confirmed. The volunteer counts were not re-checked. |
| All other DOIs cited in the scouting reports resolve | doi.org | Confirmed for the 11 DOIs the reports rely on. |

Not re-checked: the tool defaults (SimNIBS, ROAST, FieldTrip, Brainstorm), the ICNIRP 2020 Table 10 values, the
six NHANES papers found by PubMed search, and the MR-EPT challenge numbers.
