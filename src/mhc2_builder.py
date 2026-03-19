"""MHC2 tag builder for Windows HDR ICC profiles.

The MHC2 (Monitor Hardware Calibration v2) tag provides Windows with
per-channel 1D LUTs and a 3x4 color matrix for HDR tone mapping.

Structure:
  - Signature 'MHC2' (4 bytes)
  - Reserved (4 bytes)
  - LUT size (4 bytes, uint32)
  - MinCLL (4 bytes, s15Fixed16)
  - MaxCLL (4 bytes, s15Fixed16)
  - Matrix offset (4 bytes, uint32, relative to tag start)
  - LUT0 offset (4 bytes, uint32)
  - LUT1 offset (4 bytes, uint32)
  - LUT2 offset (4 bytes, uint32)
  - 3x4 matrix (48 bytes, s15Fixed16)
  - 3x LUTs: each has 'sf32' signature (4 bytes) + N s15Fixed16 entries
"""

import struct
from .tone_curves import pq_forward, pq_inverse, linear_to_srgb


def _s15f16(value: float) -> bytes:
    """Pack a float as s15Fixed16Number (big-endian)."""
    return struct.pack(">i", int(round(value * 65536)))


def _u32(value: int) -> bytes:
    """Pack an unsigned 32-bit integer (big-endian)."""
    return struct.pack(">I", value)


def build_identity_mhc2(min_cll: float, max_cll: float) -> bytes:
    """Build a minimal MHC2 tag with 2-entry identity LUTs.

    Used for Native HDR and Auto HDR sRGB profiles where
    no gamma correction is needed.
    """
    lut_size = 2
    header_size = 36  # sig(4) + res(4) + lutSize(4) + minCLL(4) + maxCLL(4) + matOff(4) + 3*lutOff(4)
    matrix_size = 48  # 3x4 s15Fixed16
    lut_entry_size = 4 + lut_size * 4  # sf32(4) + N*s15f16(4)

    matrix_offset = header_size
    lut0_offset = matrix_offset + matrix_size
    lut1_offset = lut0_offset + lut_entry_size
    lut2_offset = lut1_offset + lut_entry_size

    data = bytearray()

    # Header
    data += b"MHC2"
    data += _u32(0)  # reserved
    data += _u32(lut_size)
    data += _s15f16(min_cll)
    data += _s15f16(max_cll)
    data += _u32(matrix_offset)
    data += _u32(lut0_offset)
    data += _u32(lut1_offset)
    data += _u32(lut2_offset)

    # Identity matrix (3x4)
    identity = [
        1, 0, 0, 0,
        0, 1, 0, 0,
        0, 0, 1, 0,
    ]
    for v in identity:
        data += _s15f16(v)

    # Three identical identity LUTs: [0.0, 1.0]
    for _ in range(3):
        data += b"sf32"
        data += _s15f16(0.0)
        data += _s15f16(1.0)

    return bytes(data)


def _generate_gamma_lut(sdr_max_brightness: float, gamma: float,
                        n: int = 1024) -> list[float]:
    """Generate the gamma correction LUT.

    Algorithm (reverse-engineered from ColorControl MHC2Gen):
    For each PQ signal level:
      1. Decode PQ to absolute nits
      2. Normalize to [0,1] based on SDRMaxBrightness
      3. Encode with sRGB OETF to get the original SDR signal
      4. Apply target gamma EOTF (signal^gamma) to get corrected linear
      5. Scale back to nits using SDRMaxBrightness
      6. Encode to PQ signal
    For nits > SDRMaxBrightness: passthrough (identity)
    """
    lut = []
    for i in range(n):
        pq_in = i / (n - 1)
        nits = pq_inverse(pq_in)

        if nits <= 0:
            lut.append(0.0)
            continue

        norm = nits / sdr_max_brightness
        if norm <= 1.0:
            # Convert to sRGB signal domain
            sig = linear_to_srgb(norm)
            # Apply target gamma EOTF
            corrected_linear = sig ** gamma
            # Scale back to nits
            out_nits = corrected_linear * sdr_max_brightness
        else:
            # HDR headroom: passthrough
            out_nits = nits

        lut.append(pq_forward(out_nits))
    return lut


def build_gamma_mhc2(min_cll: float, max_cll: float,
                     sdr_max_brightness: float, gamma: float,
                     lut_size: int = 1024) -> bytes:
    """Build an MHC2 tag with gamma correction LUTs.

    Used for Virtual SDR and Auto HDR profiles that apply gamma correction.
    """
    lut_values = _generate_gamma_lut(sdr_max_brightness, gamma, lut_size)

    header_size = 36
    matrix_size = 48
    lut_entry_size = 4 + lut_size * 4  # sf32 sig + N entries

    matrix_offset = header_size
    lut0_offset = matrix_offset + matrix_size
    lut1_offset = lut0_offset + lut_entry_size
    lut2_offset = lut1_offset + lut_entry_size

    data = bytearray()

    # Header
    data += b"MHC2"
    data += _u32(0)
    data += _u32(lut_size)
    data += _s15f16(min_cll)
    data += _s15f16(max_cll)
    data += _u32(matrix_offset)
    data += _u32(lut0_offset)
    data += _u32(lut1_offset)
    data += _u32(lut2_offset)

    # Identity matrix (3x4)
    identity = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0]
    for v in identity:
        data += _s15f16(v)

    # Three identical gamma correction LUTs
    for _ in range(3):
        data += b"sf32"
        for v in lut_values:
            data += _s15f16(v)

    return bytes(data)
