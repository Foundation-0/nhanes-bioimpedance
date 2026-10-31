# Literature survey: electrical properties of human tissue, 31 October 2026

This is the complete report of a research agent (Claude) that surveyed the field for Foundation0's scouting of
31 October 2026, kept as written. It is model output. Treat a fact as checked only if [fact-check.md](fact-check.md)
confirms it. The agent marked items it saw only as search snippets with [snippet]; items marked [PubMed] came from
PubMed metadata.

---

SCOUTING REPORT: Electrical properties of human tissue (excluding the IT'IS V5.0 and Gabriel 4-Cole-Cole audits). Date 31 Oct 2026.
Verification: I opened the primary page or abstract for every item unless it is marked [snippet], meaning I saw only search snippets or secondary citations. Items marked [PubMed] came from PubMed metadata, and their DOIs are given.

1. IN VIVO vs EX VIVO
- In porcine grey matter (10 pigs), conductivity fell about 15% at 900 MHz and about 11% at 1800 MHz within 1 h of death. Permittivity fell 3–4%. https://doi.org/10.1002/bem.10122 [PubMed]
- In human grey matter (20 brains measured less than 10 h post-mortem at 18–25 °C), σ was 1.13±0.12 S/m at 800 MHz and 2.09±0.16 S/m at 2450 MHz. The authors say values at body temperature exceed the accepted values, which come from tissue more than 24 h post-mortem. https://doi.org/10.1002/bem.10123 [PubMed]. The human samples in Gabriel 1996 came from autopsies 24–48 h after death (https://webnir.eu/04-Dosimetry/04-Gabriel.php?lang=gb).
- At 7T, EPT in 12 volunteers gave "consistently" higher σ and εr in white and grey matter than tabulated ex vivo probe values. https://doi.org/10.1016/j.mri.2019.08.003 [PubMed]
- Paillart et al. 2026 (16 subjects, 3T): replacing database brain σ with in vivo literature values cut the B1 phase error by 48%. The brain SAR discrepancy between simulation and experiment fell from 62% to 22%. https://doi.org/10.1002/nbm.70335 [PubMed]
- Huang et al. 2017 eLife (10 epilepsy patients analysed): after the correction, maximum cortical E is about 0.8 V/m at 2 mA. The correction was needed because a peak-to-peak vs zero-to-peak mix-up meant all fields had to be doubled. Calibrated median σ: bone 0.03, skin 0.29, WM 0.38, GM 0.82 S/m, against literature values of 0.01, 0.465, 0.126 and 0.276. The authors call these "calibration values". https://elifesciences.org/articles/18834 and https://pmc.ncbi.nlm.nih.gov/articles/PMC5814148/
- The Huang data are public as CRCNS "tes-1" (free account needed): 14 subjects, 1,846 intracranial electrodes, fitted voltage magnitudes, MRI (NIfTI), tissue segmentations and electrode coordinates. Raw ECoG is not included. https://crcns.org/data-sets/methods/tes-1/about-tes-1
- Koessler et al. 2017 (15 patients, 1,421 SEEG measurements at 50 kHz): GM 0.26, WM 0.17, epileptogenic zone 0.29 S/m. The paper has no data statement. https://doi.org/10.1002/hbm.23431. A follow-up on 3 patients found the estimates change with stimulation site, measurement site and modality. https://arxiv.org/abs/2203.05191

Open: there is no public SEEG impedance dataset and no per-tissue table of in vivo/ex vivo ratios.
Crowding: moderate. Recent work includes Paillart 2026; Lee, Falchier and Opitz 2026 on laminar effective σ in non-human primates (https://doi.org/10.1016/j.brs.2026.103060); and a 2026 bioRxiv preprint deriving cortical DC σ from electron microscopy (https://doi.org/10.64898/2026.03.23.713806).

2. MR-EPT
- ADEPT: 25 brain models augmented to 120 (84 healthy, 36 with tumour), simulated only. https://doi.org/10.1002/mrm.29904. It is less open than described: on DataverseNL it has a custom UMC Utrecht licence, and 134 of its 140 files (7 GB) are restricted behind an access request. https://doi.org/10.34894/V0HBJ8
- Open in vivo data: UNSW (Cao and Rae) "brain phase-based MREPT" collection, GPL licence, 5 healthy subjects with repeated bFFE/TSE scans. The ISMRM guideline cites it. https://doi.org/10.26190/M3F9-1N36. The UNSW page returned 403, so details are [snippet]. I found no Utrecht in vivo release.
- Reconstruction challenge: 52 registered and 39 submitted. Phase 1 showed "large variability". Phase 3 used measured data (a cylindrical phantom, a 3D-printed brain phantom and 1 volunteer); 38 submitted and the results showed "large variations". No public data release is confirmed. https://archive.ismrm.org/2024/0182.html and https://archive.ismrm.org/2025/3425.html
- The ISMRM acquisition guideline (JMRI 2026) recommends 3T for brain and names eddy currents as a cause of one-sided σ bias. It gives no quantitative in vivo accuracy. https://pmc.ncbi.nlm.nih.gov/articles/PMC12706680/. There are also a standardization guideline (https://doi.org/10.1002/jmri.70230) and a clinical review (https://doi.org/10.1002/jmri.70279) [PubMed].
- Meerbothe et al. 2025 note that reconstructed values "show large variability in vivo". They propose checking a reconstruction by forward-predicting B1 from it. https://doi.org/10.1002/mrm.30520 [PubMed]
- TiCEPT (2025) estimates 50–600 MHz properties from 1H/23Na/39K MRI. Phantom errors were 7.9% for εr and 4.0% for σ, and σ varied 29% between subjects (6 volunteers). https://doi.org/10.1002/mrm.70139 [PubMed]

Crowding: high, but within a small community. PubMed has about 18 hits from May 2025 to Oct 2026, including Korean clinical-correlation studies (hypertension, cognitive impairment, fMRI).

3. LOW-FREQUENCY TENSOR / CTI / MREIT
- Tuch 2001: σ/d ≈ 0.844±0.0545 S·s/mm³ (r²=0.945). White-matter anisotropy "on the order of ten" is cited from earlier reports. https://doi.org/10.1073/pnas.171473898
- Hakhu et al. 2025 applied NODDI, SANDI and SMT to public diffusion data. The resulting CTI σ predictions disagree substantially. SMT came closest to experimental values, and none matched spectroscopic models. https://doi.org/10.3389/fradi.2025.1492479 [PubMed]
- Mosayebi-Samani et al. 2025: for cortical tES targets, uncertainty in ohmic σ dominates and DTI anisotropy adds little. MREIT is only weakly sensitive to anisotropy. https://doi.org/10.1162/imag_a_00481 [PubMed]
- In vivo CTI: 5 brains at 3T, GM about 0.20–0.30 S/m (ISMRM 2020 abstract) [snippet]. https://cds.ismrm.org/protected/20MProceedings/PDFfiles/3183.html
- Muscle in vivo (10 volunteers): 0.13 S/m perpendicular vs 0.56 S/m parallel below 10 kHz; 0.65 vs 0.78 S/m at 1 MHz. Fat is about 0.21–0.22 S/m. A supplementary xlsx table is available. https://doi.org/10.1002/bem.22541. The 2022 study found the lateral/longitudinal ratio rises from 37% to 64% between 10 kHz and 1 MHz. https://doi.org/10.1088/1361-6560/ac9a1e

Open: no one has tested the diffusion-to-σ models against direct in vivo measurements.
Crowding: low to moderate (for example CTI-ALPS 2026, https://doi.org/10.3389/fnagi.2026.1794175).

4. PUBLIC BIOIMPEDANCE DATA
- NHANES BIX, BIX_B and BIX_C (1999–2004) used the Xitron Hydra 4200 at 50 log-spaced frequencies from 5 kHz to 1 MHz.
  - Raw data: resistance (BIXS005K…BIXS1M) and reactance (BIXC…) at every frequency.
  - Cole outputs: Re (BIDRECF), Ri (BIDRICF), Cm (BIDCM), Td (BIDTD), alpha (BIDALPHA) and fc (BIDFC), plus a fit-quality code (BIDFIT).
  - Derived values: ECF, ICF, TBW, FFM and fat. DXA was done in the same exam.
  - Completed exams: 4,269 (1999–2000), 4,709 (2001–02) and 4,298 (2003–04), about 13,300 people aged 8–49.
  - Exclusions: pregnancy, metal implants, weight over 300 lb.
  - Documentation: https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/1999/DataFiles/BIX.htm, https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2001/DataFiles/BIX_B.htm, https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2003/DataFiles/BIX_C.htm
- These data look under-used. PubMed finds only 6 papers that use them [PubMed]:
  - Kuchnia 2016: phase angle and 200/5 kHz impedance-ratio cut-points, n=6,237. https://doi.org/10.1177/0148607116670378
  - Stagi 2022 and Marini 2024: BIVA (bioimpedance vector analysis). https://doi.org/10.1016/j.clnu.2022.01.021 and https://doi.org/10.1016/j.clnu.2024.01.024
  - Johnson 2017: Chamney body-composition model.
  - Xia 2025: 50 kHz phase angle vs mortality; 6,338 adults, 307 deaths, HR 0.73. https://doi.org/10.1038/s41598-025-86825-y
  - Lafontant 2026: reference values for Cm and fc. https://doi.org/10.1080/27697061.2026.2665157
  All six use 50 kHz or two-frequency features, or CDC's Cole outputs. I found none that refits the raw 50-point spectra; a keyword search may have missed some.
- UK Biobank: Tanita BC418MA. Field 23106 (whole-body impedance) covers 492,557 participants, with arm and leg impedances alongside. Access is controlled. The UK Biobank document does not state the frequency; the single-frequency 50 kHz figure is unverified. https://biobank.ndph.ox.ac.uk/ukb/field.cgi?id=23106 and https://biobank.ctsu.ox.ac.uk/ukb/ukb/docs/Anthropometry.pdf
- Other: an IEEE DataPort upper-body set (20 subjects, 10 frequencies from 10–100 kHz, artefact labels) [snippet].

Crowding for spectral analysis: low.

5. TUMOUR vs NORMAL
- Lazebnik 2007: 319 measurements from 196 patients, of which 155 samples from 119 patients were analysed (85 normal, 60 cancer, 10 benign), at 0.5–20 GHz. Malignant vs adipose-dominated contrast reaches up to 10:1. Malignant vs glandular/fibroconnective contrast is "no more than about 10%". Only one-pole Cole–Cole fits are published; I found no per-sample spectra. https://doi.org/10.1088/0031-9155/52/20/002
- Lung (Farina 2023; 12 patients, 112 points): at 2.45 GHz, tumour εr 52.0 and σ 1.9 S/m vs non-neoplastic 28.3 and 1.0. Dense fibrosis (49.3, 1.8) is about the same as tumour. Data are only "within article". https://doi.org/10.3390/cancers15143738
- Glioma (Ye 2025; 14 patients, 128 samples): at 128 MHz, σ 0.78 vs 0.62 S/m and εr 72.4 vs 63.1 against surrounding tissue. Data are "available from the authors". https://doi.org/10.3389/fphy.2025.1553958
- Liver (O'Rourke 2007) and skin (Mirbeik-Sabzevari 2022, 101 samples up to about 50 GHz) [snippet].

Pattern: the contrast mostly reflects water content and collapses against water-matched tissue.
Open: no public raw spectra. Crowding: low to moderate.

6. SKULL AND HEAD MODELS
- McCann 2019: 3,121 papers screened, 56 included. Weighted means: scalp 0.41, whole skull 0.02, spongiform layer 0.048, CSF 1.71, GM 0.47, WM 0.22 S/m; brain-to-skull ratio 50.4. Variation was tied to method and demographics. https://doi.org/10.1007/s10548-019-00710-2
- Tool defaults:
  - SimNIBS 4.6: WM 0.126, GM 0.275, CSF 1.654, bone 0.01 (compact 0.008, spongy 0.025), scalp 0.465 S/m. https://simnibs.github.io/simnibs/build/html/documentation/conductivity.html
  - ROAST: 0.126, 0.276, 1.65, 0.01, 0.465 S/m; gel 0.3 S/m. https://github.com/andypotatohy/roast
  - FieldTrip: 0.33, 0.0042, 0.33 S/m (1/80), with CSF 1.79 in the 4-shell model. https://www.fieldtriptoolbox.org/faq/source/conductivity_defaults/
  - Brainstorm/OpenMEEG: relative 1, 0.0125, 1 (forum-level only). https://neuroimage.usc.edu/forums/t/conductivity-values-for-head-model/16489
  So the implied skull:brain ratio is about 1:27 in SimNIBS/ROAST, 1:80 in FieldTrip/Brainstorm, and about 1:50 in the meta-analysis.
- 2025–26 work [PubMed]:
  - EEG/MEG skull-σ estimation cuts localization uncertainty from cm to under 1 cm. https://doi.org/10.1088/1741-2552/ae2f01
  - Reduced-order pEIT. https://doi.org/10.1088/1741-2552/adab20
  - 100 HCP head models with variable σ. https://doi.org/10.1038/s41597-025-04886-0
  - ROAST sutures modelled at 0.32 S/m. https://doi.org/10.1097/YCT.0000000000001154

Crowding: moderate.

7. SAFETY STANDARDS
- ICNIRP 2010 (1 Hz–100 kHz) gives no σ table of its own. Reference levels come from Dimbylow 2005/2006 voxel dosimetry, plus an "additional reduction factor of 3… for dosimetric uncertainty". https://www.icnirp.org/cms/upload/publications/ICNIRPLFgdl.pdf. Dimbylow's σ set (Gabriel-based, modified skin) is [snippet].
- ICNIRP 2020: Table 10 gives dermis values from Sasaki 2014/2017 (6 GHz: εr 36, σ 4.0 S/m, 8.1 mm; 30 GHz: 18, 27 S/m, 0.92 mm; 100 GHz: 7.3, 46 S/m, 0.35 mm). It cites Gabriel 1996 for skin properties. https://www.icnirp.org/cms/upload/publications/ICNIRPrfgdl2020.pdf. Sasaki 2014 used porcine skin in vitro at 0.5–110 GHz [snippet].
- IEEE C95.1-2019: I could not open the standard. Secondary sources say the IEEE low-frequency limits use homogeneous ellipsoids (from C95.6), while ICNIRP uses anatomical models [snippet].
- In vivo human skin at 15–110 GHz (44 + 37 volunteers) depends strongly on stratum corneum thickness. No data are shared. https://doi.org/10.1002/bem.70025

8. AI's ROLE (peer-reviewed)
- 3D vision transformer with a Canny edge mask (MRM 2025): in vivo whole-head averages near literature values; code on GitHub. https://doi.org/10.1002/mrm.30338
- Patch-CNN trained on 210 simulated pelvises (MRM 84:2772, 2020): in vivo medians match Helmholtz EPT, with higher precision [snippet].
- Physics-constrained three-plane DL (NeuroImage 2025): trained on simulation, reported to generalize in vivo. https://doaj.org/article/ce7cc0c65a1545d28311843904eaa02f
- Physics priors in DL-EPT (EMBC 2025): reliability is still the limit. https://doi.org/10.1109/EMBC58623.2025.11254469

Caveat: no in vivo ground truth exists, so "validation" means agreement with ex vivo literature values.

9. OTHER RAW DIELECTRIC DATA
- The Gabriel 1996 experimental data are now downloadable. The IFAC/webnir mirror serves CSV/TXT for 41 tissues from the report's tables and figures (figure digitisation median deviation about 0.8–3%), "reproduced as published, without correction". Licence is CC BY-NC-SA 4.0. The calculator covers 10 Hz–100 GHz. https://webnir.eu/04-Dosimetry/04-Gabriel.php?lang=gb
- NICT (Sasaki group): measured-data CSV per tissue plus Cole–Cole CSV, 1 MHz–100 GHz at 30–37 °C. https://www2.nict.go.jp/cgi-bin/202303080003/public_html/index.py
- Ischemic rat brain time series: 0.5–10 GHz, 37 °C, CSV, June 2026. Requires an IEEE DataPort subscription. https://doi.org/10.21227/ksdq-5332
- Peyman age data (rat, 130 MHz–10 GHz): no raw data found. The in vivo porcine 0.5–26.5 GHz study used one animal and has no separate dataset. https://doi.org/10.1109/ACCESS.2019.2903481

MOST PROMISING OVERLOOKED, CHECKABLE LEADS
1. NHANES raw 50-frequency BIS (about 13,300 people, mortality-linked). Why overlooked: every paper uses 50 kHz or CDC's Cole outputs. Task: refit the raw spectra, reproduce CDC's Re/Ri/fc, quantify BIDFIT failures and Td artefacts, then test whether full-spectrum features beat 50 kHz phase angle for mortality. Check: hold out one survey cycle; anyone can rerun.
2. CRCNS tes-1 scoreboard. Task: run SimNIBS and ROAST defaults, the McCann means and Huang's calibrated values against 14 subjects' measured intracranial voltages. Why overlooked: defaults are almost never scored against human in vivo data. Check: error metrics against measured voltages.
3. Gabriel 1996 CSV and NICT CSV vs parametric model and database values. Task: per-tissue, per-band residuals, flagging tissue that is post-mortem human (24–48 h) or ovine. This feeds directly into your audit. Check: deterministic recomputation.
4. Recompute ICNIRP 2020 Table 10 from the NICT dermis CSV, then compare against the in vivo human skin model (Christ 2025). Why overlooked: the limits rest on porcine in vitro skin. Check: penetration depths reproducible to 2 significant figures.
5. Ground-truth-free EPT repeatability on the UNSW public in vivo scans. Run open methods (EPTlib, the ViT code, Meerbothe's forward check) and report test-retest ICC. Why overlooked: open in vivo data is rarely used outside the source group.
6. Tumour contrast vs water and fibrosis. Pool the published tables (Lazebnik Cole–Cole fits, Farina, Ye) to test whether a water-content covariate explains the "contrast". Check: reproducible from the published numbers alone.
