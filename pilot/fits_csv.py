"""Shared settings for local data/fits.csv (not committed; per-participant rows stay out of git)."""

# Six fractional digits: Re/Ri are hundreds–thousands of Ω (CDC ~1 Ω); fc tens–hundreds of kHz (CDC whole kHz);
# α ~0.7; Td a few ns; rms ~10⁻³. 10⁻⁶ relative on Re is 0.001 Ω — below CDC resolution and verification atol.
FLOAT_FORMAT = "%.6f"

# Fitted Cole parameters and derived quantities written by pilot/refit.py (one row per spectrum).
COLE_COLUMNS = ("re", "ri", "fc_khz", "alpha", "td_ns", "cm_nf", "rms", "max_abs")

# Other numeric columns included in aggregate replay checks.
AUX_NUMERIC_COLUMNS = ("rms_log_grid", "phase_50k_deg")
