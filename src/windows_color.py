"""Windows Color Management: install and associate ICC profiles with displays."""

import ctypes
import ctypes.wintypes
import os
import shutil


class DISPLAY_DEVICE(ctypes.Structure):
    _fields_ = [
        ("cb", ctypes.wintypes.DWORD),
        ("DeviceName", ctypes.c_wchar * 32),
        ("DeviceString", ctypes.c_wchar * 128),
        ("StateFlags", ctypes.wintypes.DWORD),
        ("DeviceID", ctypes.c_wchar * 128),
        ("DeviceKey", ctypes.c_wchar * 128),
    ]


def get_display_devices() -> list[dict]:
    """Enumerate active display devices and their monitors.

    Returns list of dicts with keys:
        adapter_name, adapter_string, monitor_name, monitor_device_id, short_id
    """
    user32 = ctypes.windll.user32
    displays = []
    i = 0
    while True:
        dd = DISPLAY_DEVICE()
        dd.cb = ctypes.sizeof(dd)
        if not user32.EnumDisplayDevicesW(None, i, ctypes.byref(dd), 0):
            break
        active = dd.StateFlags & 1  # DISPLAY_DEVICE_ATTACHED_TO_DESKTOP
        if active:
            md = DISPLAY_DEVICE()
            md.cb = ctypes.sizeof(md)
            user32.EnumDisplayDevicesW(dd.DeviceName, 0, ctypes.byref(md), 0)
            # Extract short ID from device ID: MONITOR\GSM82CD\{...} -> GSM82CD
            parts = md.DeviceID.split("\\")
            short_id = parts[1] if len(parts) >= 2 else ""
            displays.append({
                "adapter_name": dd.DeviceName,
                "adapter_string": dd.DeviceString,
                "monitor_name": md.DeviceName,
                "monitor_device_id": md.DeviceID,
                "short_id": short_id,
            })
        i += 1
    return displays


def install_and_associate(profile_path: str, device_id: str = "") -> dict:
    """Install an ICC profile and optionally associate it with a display.

    Args:
        profile_path: Full path to the ICC/ICM file.
        device_id: Short display ID like "GSM82CD" to associate with.
                   If empty, profile is installed but not associated.

    Returns dict with keys: installed (bool), associated (bool), error (str|None)
    """
    result = {"installed": False, "associated": False, "error": None}

    profile_name = os.path.basename(profile_path)
    color_dir = os.path.join(os.environ.get("SYSTEMROOT", r"C:\Windows"),
                             "System32", "spool", "drivers", "color")
    dest = os.path.join(color_dir, profile_name)

    # Step 1: Copy to system color directory
    try:
        shutil.copy2(profile_path, dest)
        result["installed"] = True
    except PermissionError:
        result["error"] = "Access denied - run as Administrator"
        return result
    except Exception as e:
        result["error"] = str(e)
        return result

    # Step 2: Register with Windows Color Management
    try:
        mscms = ctypes.windll.mscms
        mscms.InstallColorProfileW(None, dest)
    except Exception:
        pass  # Copy succeeded, registration is optional

    # Step 3: Associate with display if device_id provided
    if device_id and result["installed"]:
        displays = get_display_devices()
        target = None
        for d in displays:
            if d["short_id"] == device_id:
                target = d
                break

        if target:
            try:
                mscms = ctypes.windll.mscms
                ok = mscms.AssociateColorProfileWithDeviceW(
                    None, dest, target["monitor_device_id"]
                )
                result["associated"] = bool(ok)
            except Exception as e:
                result["error"] = f"Association failed: {e}"
        else:
            result["error"] = f"Display '{device_id}' not found"

    return result


def install_profiles(profile_paths: list[str], device_id: str = "",
                     primary_profile: str = "") -> list[dict]:
    """Install multiple ICC profiles and associate one as primary.

    Args:
        profile_paths: List of ICC file paths to install.
        device_id: Short display ID to associate with.
        primary_profile: Filename of the profile to associate with the display.
                        If empty, the first profile is associated.

    Returns list of result dicts per profile.
    """
    results = []
    for path in profile_paths:
        filename = os.path.basename(path)
        # Only associate the primary profile with the display
        should_associate = (
            device_id and
            (filename == primary_profile or
             (not primary_profile and path == profile_paths[0]))
        )
        r = install_and_associate(
            path,
            device_id=device_id if should_associate else "",
        )
        r["filename"] = filename
        r["is_primary"] = should_associate
        results.append(r)
    return results
