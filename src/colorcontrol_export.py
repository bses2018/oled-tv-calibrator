"""Generate ColorControl NvPresets.json for import."""

import json
import os
import hashlib


def _make_preset_id(name: str) -> int:
    """Generate a deterministic preset ID from the name."""
    h = hashlib.md5(name.encode()).hexdigest()
    return int(h[:8], 16) & 0x7FFFFFFF


def _build_preset(profile: dict, display_name: str, display_id: str,
                  refresh_rate_num: int = 119880,
                  refresh_rate_den: int = 1000) -> dict:
    """Build a single NvPreset entry."""
    return {
        "applyColorData": False,
        "colorData": {
            "ColorDepth": 3,        # 10-bit
            "ColorFormat": 0,
            "Colorimetry": 8,
            "DesktopColorDepth": 0,
            "DynamicRange": 0,
            "SelectionPolicy": 0,
            "UseDefaultSettings": False,
        },
        "ApplyColorEnhancements": False,
        "ColorEnhancementSettings": {
            "DigitalVibranceLevel": 50,
            "HueAngle": 0,
        },
        "applyHDR": True,
        "HDREnabled": True,
        "toggleHDR": False,
        "applyDithering": True,
        "ditheringEnabled": True,
        "DisplayConfig": {
            "ApplyResolution": False,
            "Resolution": {
                "ActiveWidth": 3840,
                "ActiveHeight": 2160,
                "VirtualWidth": 3840,
                "VirtualHeight": 2160,
            },
            "ApplyRefreshRate": True,
            "RefreshRate": {
                "Numerator": refresh_rate_num,
                "Denominator": refresh_rate_den,
            },
            "Scaling": 1,
            "Rotation": 1,
            "IsPrimary": True,
        },
        "primaryDisplay": True,
        "displayName": display_name,
        "DisplayId": display_id,
        "ditheringBits": 1,    # 8-bit
        "ditheringMode": 4,    # temporal
        "applyOther": True,
        "SDRBrightness": profile["sdr_brightness"],
        "scaling": 3,
        "applyDriverSettings": False,
        "driverSettings": {},
        "DriverProfileName": None,
        "applyOverclocking": False,
        "ocSettings": [],
        "applyHdmiSettings": False,
        "HdmiInfoFrameSettings": {
            "ColorFormat": 7,
            "Colorimetry": 7,
            "ExtendedColorimetry": None,
            "RGBQuantization": 7,
            "YCCQuantization": 7,
            "ContentMode": 3,
            "ContentType": 7,
        },
        "ColorProfileSettings": {
            "ProfileName": profile["icc_filename"],
        },
        "HdrSettings": {
            "OutputMode": 1,       # HDR10
            "DisplayOutputMode": 1,
        },
        "ApplyNovideoSettings": False,
        "NovideoSettings": {
            "ApplyClamp": False,
            "ColorSpace": 0,
        },
        "DpiScaling": {
            "ApplyScaling": False,
            "Percentage": 200,
        },
        "DdcSettings": {
            "ApplyDdc": False,
            "Settings": [],
            "RemoveOutOfRangeOsd": False,
        },
        "SetDitherRegistryKey": False,
        "RestartDriver": False,
        "IsDisplayPreset": False,
        "DitherState": 1,
        "MonitorConnectionType": 0,
        "HasApplicableSettings": True,
        "name": profile["name"],
        "shortcut": "",
        "Triggers": [],
        "Steps": [],
        "Description": None,
        "ShowInQuickAccess": True,
        "LastUsed": None,
        "IdOrName": profile["name"],
        "id": _make_preset_id(profile["name"]),
    }


def generate_nvpresets(profiles: list[dict],
                       display_name: str = "",
                       display_id: str = "",
                       refresh_rate: float = 119.88,
                       output_dir: str = ".") -> str:
    """Generate NvPresets.json for ColorControl import.

    Args:
        profiles: List of profile info dicts from generate_profiles()
        display_name: Display name as shown in ColorControl (e.g., "LG TV SSCR2 (GSM961A)")
        display_id: Display ID string (e.g., "GSM961A")
        refresh_rate: Display refresh rate in Hz
        output_dir: Where to save the JSON file

    Returns:
        Path to the generated NvPresets.json
    """
    rate_num = int(round(refresh_rate * 1000))
    rate_den = 1000

    presets = []
    for profile in profiles:
        preset = _build_preset(
            profile=profile,
            display_name=display_name,
            display_id=display_id,
            refresh_rate_num=rate_num,
            refresh_rate_den=rate_den,
        )
        presets.append(preset)

    output_path = os.path.join(output_dir, "NvPresets.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(presets, f, indent=2, ensure_ascii=False)

    return output_path


def read_existing_display_info(config_path: str = None) -> dict:
    """Read display name/ID from existing ColorControl NvPresets.json."""
    if config_path is None:
        config_path = os.path.join(
            os.environ.get("APPDATA", ""),
            "Maassoft", "ColorControl", "NvPresets.json"
        )

    if not os.path.exists(config_path):
        return {"display_name": "", "display_id": "", "driver_settings": {}}

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            presets = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {"display_name": "", "display_id": "", "driver_settings": {}}

    if presets:
        first = presets[0]
        return {
            "display_name": first.get("displayName", ""),
            "display_id": first.get("DisplayId", ""),
            "driver_settings": first.get("driverSettings", {}),
        }

    return {"display_name": "", "display_id": "", "driver_settings": {}}


def detect_windows_displays() -> list[dict]:
    """Detect connected displays directly from Windows WMI.

    Returns a list of dicts with keys:
        manufacturer, name, device_id, display_name (formatted for ColorControl)
    """
    import subprocess

    try:
        result = subprocess.run(
            ["powershell", "-Command",
             "Get-CimInstance -Namespace root\\wmi -ClassName WmiMonitorID "
             "| ForEach-Object { "
             "$name = ($_.UserFriendlyName | Where-Object {$_ -ne 0} "
             "| ForEach-Object {[char]$_}) -join ''; "
             "$mfr = ($_.ManufacturerName | Where-Object {$_ -ne 0} "
             "| ForEach-Object {[char]$_}) -join ''; "
             "$id = $_.InstanceName -replace '.*\\\\\\\\(\\w+)\\\\\\\\.*','$1'; "
             "Write-Output \"$mfr|$name|$id\" "
             "}"],
            capture_output=True, text=True, timeout=10,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return []

    displays = []
    for line in result.stdout.strip().splitlines():
        parts = line.strip().split("|")
        if len(parts) >= 3:
            mfr, name, instance_path = parts[0], parts[1], parts[2]
            # Extract short device ID from instance path
            # e.g. "DISPLAY\GSM82CD\5&1ca..." -> "GSM82CD"
            path_parts = instance_path.split("\\")
            short_id = path_parts[1] if len(path_parts) >= 2 else instance_path
            # Format like ColorControl: "Name (ID)"
            formatted = f"{name} ({short_id})" if name else short_id
            displays.append({
                "manufacturer": mfr,
                "name": name,
                "device_id": short_id,
                "display_name": formatted,
            })

    return displays
