"""Color math: sRGB primaries, white points, Bradford adaptation."""

# sRGB primary chromaticities (CIE 1931 xy)
SRGB_RED = (0.64, 0.33)
SRGB_GREEN = (0.30, 0.60)
SRGB_BLUE = (0.15, 0.06)

# CIE illuminant white points (xy)
D65_XY = (0.3127, 0.3290)
D50_XY = (0.3457, 0.3585)

# D50 PCS illuminant XYZ (ICC standard)
D50_XYZ = (0.9642, 1.0000, 0.8249)

# sRGB primaries XYZ, Bradford-adapted to D50 PCS
# (these are the standard ICC values for sRGB)
SRGB_RXYZ_D50 = (0.4360747, 0.2225045, 0.0139322)
SRGB_GXYZ_D50 = (0.3850649, 0.7168786, 0.0971045)
SRGB_BXYZ_D50 = (0.1430804, 0.0606169, 0.7141733)

# Bradford chromatic adaptation matrix D65 -> D50
BRADFORD_D65_TO_D50 = [
    [1.0479, 0.0229, -0.0502],
    [0.0296, 0.9904, -0.0171],
    [-0.0092, 0.0150, 0.7519],
]

# sRGB chromaticity values for ICC chrm tag
# Stored as u16Fixed16 in (x, y) pairs
SRGB_CHROMATICITIES = [
    SRGB_RED,
    SRGB_GREEN,
    SRGB_BLUE,
]
