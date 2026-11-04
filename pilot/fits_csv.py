"""Shared settings for local data/fits.csv (not committed; per-participant rows stay out of git)."""

# Six fractional digits: Re/Ri are hundreds–thousands of Ω (CDC publishes ~1 Ω); fc is tens–hundreds of
# kHz (CDC whole kHz); α is unitless ~0.7; Td is a few ns; rms relative residuals are ~10⁻³. At this
# scale, 10⁻⁶ on Re is 0.001 Ω — below CDC read resolution and far below scientific or verification
# tolerances — while keeping CSV text stable across platforms.
FLOAT_FORMAT = "%.6f"

# Fitted Cole parameters and derived quantities written by pilot/refit.py (one row per spectrum).
COLE_COLUMNS = ("re", "ri", "fc_khz", "alpha", "td_ns", "cm_nf", "rms", "max_abs")

# Other numeric columns included in aggregate replay checks.
AUX_NUMERIC_COLUMNS = ("rms_log_grid", "phase_50k_deg")
