"""OLED TV model database with peak brightness and calibration parameters.

Organized hierarchically: Brand -> Series -> Model -> Size
"""

# Paper white (reference white) by max TML in nits
PAPER_WHITE = {
    800: 172,
    1000: 203,
    1500: 276,
    2000: 330,  # Tandem OLED (G5/M5 55-83")
}

# SDR brightness slider percentage for Auto HDR profiles
# Formula: round((paper_white - 50 - 80) / 4)
# The ~50 nit boost from Auto HDR is compensated by undershooting
AUTO_HDR_SDR_BRIGHTNESS = {
    800: 11,
    1000: 18,
    1500: 37,
    2000: 50,
}

# ---------------------------------------------------------------------------
# Hierarchical TV database: BRANDS -> series -> models
# Each model has: year, sizes, max_tml (int or {size: int})
# ---------------------------------------------------------------------------

TV_DATABASE = {
    "LG": {
        "B Series": {
            "B1": {
                "year": 2021,
                "sizes": ["55", "65", "77"],
                "max_tml": 800,
            },
            "B2": {
                "year": 2022,
                "sizes": ["55", "65", "77"],
                "max_tml": 800,
            },
            "B3": {
                "year": 2023,
                "sizes": ["55", "65", "77"],
                "max_tml": 800,
            },
            "B4": {
                "year": 2024,
                "sizes": ["48", "55", "65", "77"],
                "max_tml": 800,
            },
            "B5": {
                "year": 2025,
                "sizes": ["48", "55", "65", "83"],
                "max_tml": 800,
            },
        },
        "C Series": {
            "CX": {
                "year": 2020,
                "sizes": ["48", "55", "65", "77"],
                "max_tml": 800,
            },
            "C1": {
                "year": 2021,
                "sizes": ["48", "55", "65", "77", "83"],
                "max_tml": 800,
            },
            "C2": {
                "year": 2022,
                "sizes": ["42", "48", "55", "65", "77", "83"],
                "max_tml": 800,
            },
            "C3": {
                "year": 2023,
                "sizes": ["42", "48", "55", "65", "77", "83"],
                "max_tml": 800,
            },
            "C4": {
                "year": 2024,
                "sizes": ["42", "48", "55", "65", "77", "83"],
                "max_tml": {
                    "42": 800, "48": 800,
                    "55": 1000, "65": 1000, "77": 1000, "83": 1000,
                },
            },
            "C5": {
                "year": 2025,
                "sizes": ["42", "48", "55", "65", "77", "83"],
                "max_tml": {
                    "42": 800, "48": 800,
                    "55": 1000, "65": 1000, "77": 1000, "83": 1000,
                },
            },
        },
        "G Series": {
            "G1": {
                "year": 2021,
                "sizes": ["55", "65", "77"],
                "max_tml": 800,
            },
            "G2": {
                "year": 2022,
                "sizes": ["55", "65", "77", "83"],
                "max_tml": {"55": 1000, "65": 1000, "77": 800, "83": 800},
            },
            "G3": {
                "year": 2023,
                "sizes": ["55", "65", "77", "83"],
                "max_tml": {"55": 1000, "65": 1000, "77": 1500, "83": 1500},
            },
            "G4": {
                "year": 2024,
                "sizes": ["55", "65", "77", "83", "97"],
                "max_tml": {
                    "55": 1500, "65": 1500, "77": 1500, "83": 1500,
                    "97": 1000,
                },
            },
            "G5": {
                "year": 2025,
                "sizes": ["48", "55", "65", "77", "83", "97"],
                "max_tml": {
                    "48": 1000,
                    "55": 2000, "65": 2000, "77": 2000, "83": 2000,
                    "97": 1000,
                },
            },
        },
        "M Series": {
            "M3": {
                "year": 2023,
                "sizes": ["77", "83", "97"],
                "max_tml": 1500,
            },
            "M4": {
                "year": 2024,
                "sizes": ["77", "83", "97"],
                "max_tml": 1500,
            },
            "M5": {
                "year": 2025,
                "sizes": ["65", "77", "83", "97"],
                "max_tml": {
                    "65": 2000, "77": 2000, "83": 2000,
                    "97": 1500,
                },
            },
        },
    },
    "Sony": {
        "A80 Series": {
            "A80J": {
                "year": 2021,
                "sizes": ["55", "65", "77"],
                "max_tml": 800,
            },
            "A80K": {
                "year": 2022,
                "sizes": ["55", "65", "77"],
                "max_tml": 800,
            },
            "A80L": {
                "year": 2023,
                "sizes": ["55", "65", "77", "83"],
                "max_tml": 800,
            },
        },
        "A90 Series": {
            "A90J": {
                "year": 2021,
                "sizes": ["55", "65", "83"],
                "max_tml": 800,
            },
            "A90K": {
                "year": 2022,
                "sizes": ["42", "48"],
                "max_tml": 800,
            },
        },
        "A95 Series (QD-OLED)": {
            "A95K": {
                "year": 2022,
                "sizes": ["55", "65"],
                "max_tml": 1000,
            },
            "A95L": {
                "year": 2023,
                "sizes": ["55", "65", "77"],
                "max_tml": 1500,
            },
        },
        "Bravia Series": {
            "Bravia 8": {
                "year": 2024,
                "sizes": ["55", "65", "77"],
                "max_tml": 800,
            },
            "Bravia 8 II": {
                "year": 2025,
                "sizes": ["55", "65", "77"],
                "max_tml": 1500,  # QD-OLED
            },
        },
    },
    "Samsung": {
        "S90 Series": {
            "S90C": {
                "year": 2023,
                "sizes": ["55", "65", "77", "83"],
                "max_tml": {
                    "55": 1000, "65": 1000, "77": 1000,  # QD-OLED
                    "83": 800,                             # W-OLED (LG panel)
                },
            },
            "S90D": {
                "year": 2024,
                "sizes": ["42", "48", "55", "65", "77", "83"],
                "max_tml": {
                    "42": 800, "48": 800,                  # W-OLED (LG panel)
                    "55": 1000, "65": 1000, "77": 1000,    # QD-OLED
                    "83": 800,                              # W-OLED (LG panel)
                },
            },
            "S90F": {
                "year": 2025,
                "sizes": ["42", "48", "55", "65", "77", "83"],
                "max_tml": {
                    "42": 800, "48": 800,                  # W-OLED
                    "55": 1000, "65": 1000, "77": 1000,    # QD-OLED
                    "83": 1000,
                },
            },
        },
        "S95 Series (QD-OLED)": {
            "S95B": {
                "year": 2022,
                "sizes": ["55", "65"],
                "max_tml": 1000,
            },
            "S95C": {
                "year": 2023,
                "sizes": ["55", "65", "77"],
                "max_tml": 1500,
            },
            "S95D": {
                "year": 2024,
                "sizes": ["55", "65", "77"],
                "max_tml": 1500,
            },
            "S95F": {
                "year": 2025,
                "sizes": ["55", "65", "77", "83"],
                "max_tml": 2000,
            },
        },
    },
}

# Profile definitions
PROFILE_DEFS = [
    {
        "id": "native_hdr",
        "name": "Native HDR - sRGB + 80 nits",
        "gamma": None,
        "sdr_brightness": 0,
        "needs_gamma_lut": False,
        "description": "Native HDR games, HDR video, sRGB-mastered SDR games",
    },
    {
        "id": "vsdr_22",
        "name_template": "Virtual SDR - 2.2 + 120 nits",
        "gamma": 2.2,
        "ref_white": 120,
        "sdr_brightness": 10,
        "needs_gamma_lut": True,
        "description": "SDR games mastered to gamma 2.2 (most games)",
    },
    {
        "id": "vsdr_24",
        "name_template": "Virtual SDR - 2.4 + 100 nits",
        "gamma": 2.4,
        "ref_white": 100,
        "sdr_brightness": 5,
        "needs_gamma_lut": True,
        "description": "SDR video or games mastered to gamma 2.4 / BT.1886",
    },
    {
        "id": "ahdr_22",
        "name_template": "Auto HDR - 2.2 + {paper_white} nits",
        "gamma": 2.2,
        "sdr_brightness": "auto_hdr",
        "needs_gamma_lut": True,
        "description": "Auto HDR games originally mastered to gamma 2.2",
    },
    {
        "id": "ahdr_24",
        "name_template": "Auto HDR - 2.4 + {paper_white} nits",
        "gamma": 2.4,
        "sdr_brightness": "auto_hdr",
        "needs_gamma_lut": True,
        "description": "Auto HDR games originally mastered to gamma 2.4",
    },
    {
        "id": "ahdr_srgb",
        "name_template": "Auto HDR - sRGB + {paper_white} nits",
        "gamma": None,
        "sdr_brightness": "auto_hdr",
        "needs_gamma_lut": False,
        "description": "Auto HDR with sRGB gamma (no correction), HDR brightness only",
    },
]


# ---------------------------------------------------------------------------
# Accessor helpers
# ---------------------------------------------------------------------------

def get_brands() -> list[str]:
    """Return list of brand names."""
    return list(TV_DATABASE.keys())


def get_series(brand: str) -> list[str]:
    """Return list of series for a brand."""
    return list(TV_DATABASE.get(brand, {}).keys())


def get_models(brand: str, series: str) -> list[str]:
    """Return list of model names within a series, sorted by year."""
    models = TV_DATABASE.get(brand, {}).get(series, {})
    return sorted(models.keys(), key=lambda m: models[m]["year"])


def get_model_data(brand: str, series: str, model: str) -> dict:
    """Return the model dict (year, sizes, max_tml)."""
    return TV_DATABASE[brand][series][model]


def get_sizes(brand: str, series: str, model: str) -> list[str]:
    """Return available sizes for a model."""
    return get_model_data(brand, series, model)["sizes"]


def get_max_tml(brand: str, series: str, model: str, size: str) -> int:
    """Get the max tone map luminance for a specific model + size."""
    tml = get_model_data(brand, series, model)["max_tml"]
    if isinstance(tml, dict):
        return tml[size]
    return tml


def get_display_name(brand: str, series: str, model: str) -> str:
    """Human-readable display name like 'LG G4 OLED (2024)'."""
    data = get_model_data(brand, series, model)
    return f"{brand} {model} OLED ({data['year']})"


def get_paper_white(max_tml: int) -> int:
    """Get the paper white (reference white) for a given max TML."""
    return PAPER_WHITE.get(max_tml, 172)


def get_auto_hdr_sdr_brightness(max_tml: int) -> int:
    """Get the SDR brightness slider value for Auto HDR profiles."""
    return AUTO_HDR_SDR_BRIGHTNESS.get(max_tml, 11)


def get_profile_params(profile_def: dict, max_tml: int,
                       tv_model: str = "") -> dict:
    """Compute concrete profile parameters for a given max TML.

    Args:
        tv_model: Short model name like "LG G4" to prepend to profile names.
    """
    paper_white = get_paper_white(max_tml)
    prefix = f"{tv_model} " if tv_model else ""

    # Profile name
    if "name_template" in profile_def:
        name = prefix + profile_def["name_template"].format(paper_white=paper_white)
    else:
        name = prefix + profile_def["name"]

    # Reference white for ICC profile
    if profile_def["needs_gamma_lut"]:
        if profile_def["sdr_brightness"] == "auto_hdr":
            ref_white = paper_white
        else:
            ref_white = profile_def.get("ref_white", 80)
    else:
        ref_white = paper_white if profile_def["sdr_brightness"] == "auto_hdr" else 80

    # SDR brightness slider
    if profile_def["sdr_brightness"] == "auto_hdr":
        sdr_brightness = get_auto_hdr_sdr_brightness(max_tml)
    else:
        sdr_brightness = profile_def["sdr_brightness"]

    # ICC filename
    icc_filename = f"{name}.icm"
    if not profile_def["needs_gamma_lut"] and profile_def["gamma"] is None:
        if profile_def["id"] == "native_hdr":
            icc_filename = f"{prefix}HDR Calibration {max_tml} nits.icc"
        else:
            icc_filename = f"{name}.icc"

    return {
        "id": profile_def["id"],
        "name": name,
        "gamma": profile_def["gamma"],
        "ref_white": ref_white,
        "sdr_brightness": sdr_brightness,
        "needs_gamma_lut": profile_def["needs_gamma_lut"],
        "max_tml": max_tml,
        "paper_white": paper_white,
        "icc_filename": icc_filename,
        "description": profile_def["description"],
    }
