"""ICC v4 profile builder for HDR color calibration.

Generates two profile formats:
1. Simple (MSFT-style): For Native HDR / Auto HDR sRGB
   - curv TRC, small identity MHC2, MSCA metadata
2. Complex (lcms-style): For Virtual SDR / Auto HDR with gamma correction
   - para TRC, 1024-entry MHC2 LUT, scrd metadata, chrm/bkpt tags
"""

import struct
import json
import time
from . import colorimetry as cm
from .mhc2_builder import build_identity_mhc2, build_gamma_mhc2


def _u16(v: int) -> bytes:
    return struct.pack(">H", v & 0xFFFF)


def _u32(v: int) -> bytes:
    return struct.pack(">I", v & 0xFFFFFFFF)


def _s15f16(v: float) -> bytes:
    return struct.pack(">i", int(round(v * 65536)))


def _pad4(data: bytes) -> bytes:
    """Pad data to 4-byte boundary."""
    rem = len(data) % 4
    if rem:
        data += b"\x00" * (4 - rem)
    return data


def _build_xyz_tag(x: float, y: float, z: float) -> bytes:
    """Build an XYZ type tag."""
    return b"XYZ " + _u32(0) + _s15f16(x) + _s15f16(y) + _s15f16(z)


def _build_curv_tag_gamma(gamma: float) -> bytes:
    """Build a curv tag with a single gamma value (u8Fixed8Number)."""
    gamma_u8f8 = int(round(gamma * 256))
    return b"curv" + _u32(0) + _u32(1) + _u16(gamma_u8f8) + b"\x00\x00"


def _build_para_tag_type3(g: float, a: float, b: float,
                          c: float, d: float) -> bytes:
    """Build a parametric curve tag (type 3).

    f(x) = (ax + b)^g     for x >= d
    f(x) = cx              for x < d
    """
    data = b"para" + _u32(0) + _u16(3) + _u16(0)  # type 3, reserved
    data += _s15f16(g)
    data += _s15f16(a)
    data += _s15f16(b)
    data += _s15f16(c)
    data += _s15f16(d)
    return data


def _build_mluc_tag(text: str) -> bytes:
    """Build a multi-localized Unicode string tag."""
    encoded = text.encode("utf-16-be")
    data = b"mluc" + _u32(0)
    data += _u32(1)   # number of records
    data += _u32(12)  # record size
    # Record: language 'en', country 'US', string length, string offset
    data += b"enUS"
    data += _u32(len(encoded))
    data += _u32(28)  # offset from tag start to string data
    data += encoded
    return _pad4(data)


def _build_text_tag(text: str) -> bytes:
    """Build a text type tag (ASCII)."""
    encoded = text.encode("ascii") + b"\x00"
    data = b"text" + _u32(0) + encoded
    return _pad4(data)


def _build_desc_tag(text: str) -> bytes:
    """Build an old-style 'desc' type tag with ASCII text."""
    encoded = text.encode("ascii") + b"\x00"
    data = b"desc" + _u32(0) + _u32(len(encoded)) + encoded
    # Unicode and ScriptCode counts (set to 0)
    data += _u32(0) + _u16(0) + b"\x00" * 67
    return _pad4(data)


def _build_sf32_tag(values: list[list[float]]) -> bytes:
    """Build an sf32 tag (array of s15Fixed16 values)."""
    data = b"sf32" + _u32(0)
    for row in values:
        for v in row:
            data += _s15f16(v)
    return data


def _build_chrm_tag() -> bytes:
    """Build a chromaticity tag for sRGB."""
    data = b"chrm" + _u32(0)
    data += _u16(3)   # number of channels
    data += _u16(0)   # phosphor type (unknown)
    for x, y in cm.SRGB_CHROMATICITIES:
        data += _s15f16(x)  # using s15f16 for u16f16 (values < 1.0, works fine)
        data += _s15f16(y)
    return data


def _build_header(profile_size: int, cmm: bytes, version: bytes,
                  creator: bytes) -> bytes:
    """Build the 128-byte ICC profile header."""
    now = time.gmtime()
    header = bytearray(128)

    struct.pack_into(">I", header, 0, profile_size)
    header[4:8] = cmm
    header[8:12] = version
    header[12:16] = b"mntr"  # device class: monitor
    header[16:20] = b"RGB "  # color space
    header[20:24] = b"XYZ "  # PCS
    # Date/time (12 bytes at offset 24)
    struct.pack_into(">HHH", header, 24, now.tm_year, now.tm_mon, now.tm_mday)
    struct.pack_into(">HHH", header, 30, now.tm_hour, now.tm_min, now.tm_sec)
    header[36:40] = b"acsp"  # signature
    header[40:44] = b"MSFT"  # platform
    # Flags, manufacturer, model = 0
    struct.pack_into(">I", header, 64, 1)  # rendering intent: relative colorimetric
    # PCS illuminant (D50)
    struct.pack_into(">i", header, 68, int(round(cm.D50_XYZ[0] * 65536)))
    struct.pack_into(">i", header, 72, int(round(cm.D50_XYZ[1] * 65536)))
    struct.pack_into(">i", header, 76, int(round(cm.D50_XYZ[2] * 65536)))
    header[80:84] = creator

    return bytes(header)


def _assemble_profile(header_params: dict,
                      tags: list[tuple[bytes, bytes]]) -> bytes:
    """Assemble a complete ICC profile from header params and tag data."""
    tag_count = len(tags)
    tag_table_size = 4 + tag_count * 12  # count(4) + N*(sig(4)+offset(4)+size(4))
    data_offset = 128 + tag_table_size

    # Compute tag offsets, handling shared tags (same data = same offset)
    tag_entries = []
    tag_data_blocks = []
    seen_data = {}  # id(data) -> offset
    current_offset = data_offset

    for sig, tag_data in tags:
        data_id = id(tag_data)
        if data_id in seen_data:
            tag_entries.append((sig, seen_data[data_id], len(tag_data)))
        else:
            padded = _pad4(tag_data)
            seen_data[data_id] = current_offset
            tag_entries.append((sig, current_offset, len(tag_data)))
            tag_data_blocks.append(padded)
            current_offset += len(padded)

    profile_size = current_offset

    # Build header
    header = _build_header(profile_size, **header_params)

    # Build tag table
    table = _u32(tag_count)
    for sig, offset, size in tag_entries:
        table += sig + _u32(offset) + _u32(size)

    # Combine
    profile = bytearray(header)
    profile += table
    for block in tag_data_blocks:
        profile += block

    # Update profile size in header
    struct.pack_into(">I", profile, 0, len(profile))

    return bytes(profile)


def build_simple_profile(description: str, max_tml: float,
                         gamma: float = 2.2) -> bytes:
    """Build a simple MSFT-style ICC profile (Native HDR / Auto HDR sRGB).

    Features:
    - curv TRC with sRGB-like gamma
    - Small identity MHC2 (2 entries)
    - MSCA metadata tag
    """
    # Shared TRC
    trc = _build_curv_tag_gamma(gamma)

    # MSCA metadata
    msca_json = "{'Appversion':'1.0.0.0','D65Adapted':True}"
    msca = _build_text_tag(msca_json)

    # MHC2
    mhc2 = build_identity_mhc2(0, max_tml)

    # sRGB primaries in D65 XYZ (not Bradford-adapted, matching MSFT style)
    # These are the standard sRGB primaries scaled for the display
    # The MSFT profiles use D65-adapted values with identity chad
    rx, ry, rz = 0.906464, 0.421524, 0.025101
    gx, gy, gz = 0.381454, 0.919586, 0.094009
    bx, by, bz = 0.187546, 0.054947, 0.980713
    wx, wy, wz = 0.540390, 0.569092, 0.619766

    tags = [
        (b"cprt", _build_mluc_tag("Generated by OLED TV Calibrator")),
        (b"rTRC", trc),
        (b"gTRC", trc),  # shared with rTRC
        (b"bTRC", trc),  # shared with rTRC
        (b"chad", _build_sf32_tag([[1, 0, 0], [0, 1, 0], [0, 0, 1]])),
        (b"rXYZ", _build_xyz_tag(rx, ry, rz)),
        (b"gXYZ", _build_xyz_tag(gx, gy, gz)),
        (b"bXYZ", _build_xyz_tag(bx, by, bz)),
        (b"wtpt", _build_xyz_tag(wx, wy, wz)),
        (b"MSCA", msca),
        (b"lumi", _build_xyz_tag(max_tml, max_tml, max_tml)),
        (b"MHC2", mhc2),
        (b"desc", _build_mluc_tag(description)),
    ]

    return _assemble_profile(
        header_params={
            "cmm": b"SICC",
            "version": b"\x04\x40\x00\x00",
            "creator": b"MSFT",
        },
        tags=tags,
    )


def build_gamma_profile(description: str, max_tml: float,
                        gamma: float, ref_white: float,
                        sdr_transfer_function: int = 1) -> bytes:
    """Build a complex lcms-style ICC profile with gamma correction LUT.

    Features:
    - para type 3 TRC (sRGB piecewise)
    - 1024-entry MHC2 LUT with gamma correction
    - scrd metadata tag with profile settings
    - chrm and bkpt tags
    """
    # sRGB piecewise TRC (para type 3)
    g, a, b, c, d = 2.4, 1.0/1.055, 0.055/1.055, 1.0/12.92, 0.04045
    trc = _build_para_tag_type3(g, a, b, c, d)

    # MHC2 with gamma correction LUT
    mhc2 = build_gamma_mhc2(0, max_tml, ref_white, gamma)

    # scrd metadata (JSON embedded in desc tag)
    metadata = {
        "SDRTransferFunction": sdr_transfer_function,
        "Gamma": gamma,
        "SDRMinBrightness": 0,
        "SDRMaxBrightness": int(ref_white),
        "SDRBrightnessBoost": 0,
        "ShadowDetailBoost": 0,
        "ShadowDetailRange": 30,
        "RedGain": 0,
        "GreenGain": 0,
        "BlueGain": 0,
        "TargetGamut": 0,
        "ToneMappingFromLuminance": 400,
        "ToneMappingToLuminance": 400,
        "HdrGammaMultiplier": 1,
        "HdrBrightnessMultiplier": 1,
    }
    scrd = _build_desc_tag(json.dumps(metadata, indent=2))

    # D50-adapted sRGB primaries
    rx, ry, rz = cm.SRGB_RXYZ_D50
    gx, gy, gz = cm.SRGB_GXYZ_D50
    bx, by, bz = cm.SRGB_BXYZ_D50

    tags = [
        (b"desc", _build_mluc_tag(description)),
        (b"cprt", _build_mluc_tag("No copyright, use freely")),
        (b"wtpt", _build_xyz_tag(*cm.D50_XYZ)),
        (b"chad", _build_sf32_tag(cm.BRADFORD_D65_TO_D50)),
        (b"rXYZ", _build_xyz_tag(rx, ry, rz)),
        (b"bXYZ", _build_xyz_tag(bx, by, bz)),
        (b"gXYZ", _build_xyz_tag(gx, gy, gz)),
        (b"rTRC", trc),
        (b"gTRC", trc),  # shared
        (b"bTRC", trc),  # shared
        (b"chrm", _build_chrm_tag()),
        (b"lumi", _build_xyz_tag(0, max_tml, 0)),
        (b"bkpt", _build_xyz_tag(0, 0, 0)),
        (b"scrd", scrd),
        (b"MHC2", mhc2),
    ]

    return _assemble_profile(
        header_params={
            "cmm": b"lcms",
            "version": b"\x04\x30\x00\x00",
            "creator": b"lcms",
        },
        tags=tags,
    )
