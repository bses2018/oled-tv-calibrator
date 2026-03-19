"""Orchestrates profile generation for a given TV model and max TML."""

import os
from .icc_builder import build_simple_profile, build_gamma_profile
from .tv_database import PROFILE_DEFS, get_profile_params


def generate_profiles(max_tml: int, output_dir: str,
                      tv_model: str = "") -> list[dict]:
    """Generate all ICC profiles for a given max TML.

    Args:
        max_tml: Peak brightness in nits.
        output_dir: Directory to save ICC files.
        tv_model: Short model name like "LG G4" to prepend to profile names.

    Returns a list of profile info dicts with keys:
        id, name, gamma, ref_white, sdr_brightness, max_tml,
        paper_white, icc_filename, icc_path, description
    """
    os.makedirs(output_dir, exist_ok=True)
    results = []

    for profile_def in PROFILE_DEFS:
        params = get_profile_params(profile_def, max_tml, tv_model=tv_model)

        if params["needs_gamma_lut"]:
            # Complex profile with gamma correction
            icc_data = build_gamma_profile(
                description=params["name"],
                max_tml=float(max_tml),
                gamma=params["gamma"],
                ref_white=float(params["ref_white"]),
            )
        else:
            # Simple profile (identity LUT)
            icc_data = build_simple_profile(
                description=params["name"],
                max_tml=float(max_tml),
            )

        icc_path = os.path.join(output_dir, params["icc_filename"])
        with open(icc_path, "wb") as f:
            f.write(icc_data)

        params["icc_path"] = icc_path
        results.append(params)

    return results
