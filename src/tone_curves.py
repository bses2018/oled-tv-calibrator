"""Transfer functions: PQ (ST.2084), sRGB, gamma power curves."""

import math

# ST.2084 (PQ) constants
_M1 = 2610.0 / 16384.0       # 0.1593017578125
_M2 = 2523.0 / 4096.0 * 128  # 78.84375
_C1 = 3424.0 / 4096.0        # 0.8359375
_C2 = 2413.0 / 4096.0 * 32   # 18.8515625
_C3 = 2392.0 / 4096.0 * 32   # 18.6875


def pq_forward(nits: float) -> float:
    """Convert absolute luminance (nits/cd/m2) to PQ signal (0-1)."""
    if nits <= 0:
        return 0.0
    Y = nits / 10000.0
    Ym1 = Y ** _M1
    return ((_C1 + _C2 * Ym1) / (1.0 + _C3 * Ym1)) ** _M2


def pq_inverse(signal: float) -> float:
    """Convert PQ signal (0-1) to absolute luminance (nits/cd/m2)."""
    if signal <= 0:
        return 0.0
    Nm = signal ** (1.0 / _M2)
    t = max(Nm - _C1, 0.0) / (_C2 - _C3 * Nm)
    return 10000.0 * max(t, 0.0) ** (1.0 / _M1)


def srgb_to_linear(s: float) -> float:
    """sRGB EOTF: signal to linear light."""
    s = max(s, 0.0)
    if s <= 0.04045:
        return s / 12.92
    return ((s + 0.055) / 1.055) ** 2.4


def linear_to_srgb(L: float) -> float:
    """sRGB inverse EOTF (OETF): linear light to signal."""
    L = max(L, 0.0)
    if L <= 0.0031308:
        return min(12.92 * L, 1.0)
    return min(1.055 * L ** (1.0 / 2.4) - 0.055, 1.0)


# sRGB parametric curve constants (ICC para type 3)
SRGB_PARA_PARAMS = (2.4, 1.0 / 1.055, 0.055 / 1.055, 1.0 / 12.92, 0.04045)
