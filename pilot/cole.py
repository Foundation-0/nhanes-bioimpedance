"""The Cole model with a time delay, as used by the Xitron Hydra 4200, and a least-squares fit of one spectrum.

Z(f) = [R_inf + (R0 - R_inf) / (1 + (j f / fc)^alpha)] * exp(-j 2 pi f Td),  with R0 = Re and R_inf = Re Ri / (Re + Ri).

CDC's variables use these names: BIDRECF = Re, BIDRICF = Ri, BIDFC = fc (kHz), BIDALPHA = alpha, BIDTD = Td (ns),
BIDCM = Cm (nF). In the data, 1 / (2 pi fc) = Cm (Re + Ri).
"""
import numpy as np
from scipy.optimize import least_squares

# Measurement frequencies as labelled in CDC's variable names (BIXS005K ... BIXS1M), in Hz. CDC's documentation calls
# them logarithmically spaced; below 16 kHz and at 50, 100, 200 and 500 kHz the labels differ from an exact log grid,
# and the labelled grid fits the spectra better (see results/pilot-2026-10-31.md).
LABEL_KHZ = [5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 18, 20, 23, 25, 28, 31, 35, 39, 43, 50, 54, 60, 67, 75, 83, 93,
             100, 115, 128, 143, 159, 177, 200, 220, 245, 273, 304, 339, 378, 421, 469, 500, 582, 649, 723, 806, 898,
             1000]
F_LABEL = np.array(LABEL_KHZ, float) * 1e3
F_LOG = 5e3 * 200 ** (np.arange(50) / 49)
R_COLS = [f"BIXS{k:03d}K" if k < 1000 else "BIXS1M" for k in LABEL_KHZ]
X_COLS = [c.replace("BIXS", "BIXC") for c in R_COLS]


def cole_z(f, re, ri, fc, alpha, td):
    r_inf = re * ri / (re + ri)
    z = r_inf + (re - r_inf) / (1 + (1j * np.asarray(f) / fc) ** alpha)
    return z * np.exp(-1j * 2 * np.pi * np.asarray(f) * td)


def fit_spectrum(f, R, X):
    """Fit one spectrum. R and X are CDC's resistance and reactance (reactance is reported as a positive number).

    Minimises the relative complex residual over all 50 frequencies. Returns a dict, or None if the data are not finite
    and positive.
    """
    R = np.asarray(R, float)
    X = np.asarray(X, float)
    if not (np.all(np.isfinite(R)) and np.all(np.isfinite(X))) or np.any(R <= 0):
        return None
    z = R - 1j * np.abs(X)
    k = int(np.argmax(np.abs(X)))
    re0, r_inf0 = R[0] * 1.03, R[-1] * 0.97
    ri0 = re0 * r_inf0 / max(re0 - r_inf0, 1e-3)

    def residual(p):
        d = (cole_z(f, *p) - z) / np.abs(z)
        return np.concatenate([d.real, d.imag])

    lo, hi = np.array([1, 1, 1e3, 0.3, -1e-7]), np.array([5e4, 5e5, 1e6, 1.0, 1e-7])
    # Malformed spectra (resistance rising with frequency) give a starting point outside the bounds; clamp it.
    p0 = np.clip([re0, ri0, f[k], 0.7, 0.0], lo + 1e-9 * (hi - lo), hi - 1e-9 * (hi - lo))
    try:
        r = least_squares(residual, p0, bounds=(lo, hi), x_scale=[100, 100, 1e4, 0.1, 1e-9])
    except (ValueError, FloatingPointError):
        return None
    re, ri, fc, alpha, td = r.x
    return dict(re=re, ri=ri, fc_khz=fc / 1e3, alpha=alpha, td_ns=td * 1e9,
                cm_nf=1e9 / (2 * np.pi * fc * (re + ri)), rms=float(np.sqrt(np.mean(r.fun ** 2))),
                max_abs=float(np.max(np.abs(r.fun))), converged=bool(r.success))
