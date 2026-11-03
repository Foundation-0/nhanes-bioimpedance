# Draft: question to NCHS about the BIX frequency labels

**Status: draft. Not sent. A person reads it, re-runs the check, and decides whether and how to send it**
(issue 4). NHANES questions go through the NCHS contact form or the NHANES information line listed on the NHANES
website.

---

Subject: NHANES 1999–2004 bioimpedance (BIX, BIX_B, BIX_C): measurement frequencies

Dear NHANES team,

We are re-analysing the 50-frequency bioimpedance spectra published in BIX, BIX_B and BIX_C, and have a question
about the frequencies.

The documentation describes 50 logarithmically spaced frequencies from 5 kHz to 1 MHz. The variable names and labels
(BIXS005K … BIXS1M) give 5, 6, 7 … 16 kHz in 1 kHz steps, then values close to a logarithmic grid. At 50, 100, 200
and 500 kHz they show round numbers where an exact logarithmic grid would give 48.4, 103.2, 197.5 and 522.7 kHz.

When we fit the Cole model used by the Hydra 4200 to all 13,276 spectra, the labelled frequencies give a lower
residual than an exact logarithmic grid in 85% of spectra. They also reproduce the published Cole parameters
(BIDRECF, BIDRICF, BIDFC) more closely. So the labels appear to be the true frequencies. Could you confirm which
frequencies the analyser used?

With thanks,
[Name], Foundation0 (https://fdn0.org)

[The analysis was done by an AI agent (Claude) working for the sender, and checked by the sender.]

---

Before sending:

- [ ] Re-run `python3 pilot/fetch.py && python3 pilot/refit.py` and confirm the 85% figure.
- [ ] Fill in the name and decide whether to link the repository.
