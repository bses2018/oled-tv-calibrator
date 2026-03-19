"""Scan Steam and Epic Games libraries for installed games."""

import os
import re
import json
import hashlib


# Exe names to skip when searching for the main game executable
_SKIP_EXES = {
    "unins000.exe", "uninstall.exe", "setup.exe", "installer.exe",
    "unitycrashhandler64.exe", "unitycrashhandler32.exe",
    "crashreportclient.exe", "crashhandler.exe",
    "ue4prereqsetup_x64.exe", "ue4prereqsetup.exe",
    "dxsetup.exe", "vcredist_x64.exe", "vcredist_x86.exe",
    "dotnetfx35.exe", "ndpxxxx.exe",
    "launch_game.exe",  # some launchers
}

# Steam apps to skip (redistributables, tools, etc.)
_SKIP_STEAM_APPS = {
    "228980",  # Steamworks Common Redistributables
    "1070560",  # Steam Linux Runtime
}


def _parse_vdf_simple(text: str) -> dict:
    """Minimal VDF parser for libraryfolders.vdf and appmanifest files."""
    result = {}
    stack = [result]
    key = None

    for token in re.findall(r'"[^"]*"|\{|\}', text):
        if token == "{":
            child = {}
            stack[-1][key] = child
            stack.append(child)
            key = None
        elif token == "}":
            stack.pop()
        else:
            val = token[1:-1]  # strip quotes
            if key is None:
                key = val
            else:
                stack[-1][key] = val
                key = None

    return result


def _find_main_exe(game_dir: str, game_name: str = "") -> str | None:
    """Find the most likely main game executable in a directory."""
    candidates = []

    for root, dirs, files in os.walk(game_dir):
        # Don't go too deep
        depth = root.replace(game_dir, "").count(os.sep)
        if depth > 3:
            dirs.clear()
            continue

        # Skip known non-game directories
        dirs[:] = [d for d in dirs if d.lower() not in {
            "_commonredist", "redist", "directx", "vcredist",
            "__installer", "_installer", "support", "tools",
        }]

        for f in files:
            if not f.lower().endswith(".exe"):
                continue
            if f.lower() in _SKIP_EXES:
                continue
            full = os.path.join(root, f)
            try:
                size = os.path.getsize(full)
            except OSError:
                continue
            # Skip very small exes (likely launchers/stubs)
            if size < 500_000:
                continue
            candidates.append((full, f, size, depth))

    if not candidates:
        return None

    # Score candidates
    def score(item):
        full, name, size, depth = item
        s = 0
        name_lower = name.lower().replace(".exe", "").replace(" ", "").replace("-", "")
        game_lower = game_name.lower().replace(" ", "").replace("-", "")

        # Prefer exe name matching game name
        if game_lower and game_lower in name_lower:
            s += 1000
        # Prefer Win64 binaries
        if "win64" in full.lower():
            s += 500
        # Prefer shallower depth
        s -= depth * 100
        # Prefer larger files (actual game binaries)
        s += min(size // 1_000_000, 200)
        # Penalize "shipping" type names less
        if "shipping" in name_lower:
            s += 100
        return s

    candidates.sort(key=score, reverse=True)
    return candidates[0][0]


def scan_steam() -> list[dict]:
    """Scan all Steam library folders for installed games.

    Returns list of dicts with: name, exe_path, source
    """
    games = []

    # Find Steam install
    steam_path = r"C:\Program Files (x86)\Steam"
    vdf_path = os.path.join(steam_path, "steamapps", "libraryfolders.vdf")

    if not os.path.exists(vdf_path):
        return games

    with open(vdf_path, "r", encoding="utf-8", errors="replace") as f:
        vdf = _parse_vdf_simple(f.read())

    # Get all library paths
    lib_folders = vdf.get("libraryfolders", {})
    library_paths = []
    for key, val in lib_folders.items():
        if isinstance(val, dict) and "path" in val:
            library_paths.append(val["path"])

    # Scan each library for appmanifest files
    for lib_path in library_paths:
        steamapps = os.path.join(lib_path, "steamapps")
        if not os.path.isdir(steamapps):
            continue

        for fname in os.listdir(steamapps):
            if not fname.startswith("appmanifest_") or not fname.endswith(".acf"):
                continue

            appid = fname.replace("appmanifest_", "").replace(".acf", "")
            if appid in _SKIP_STEAM_APPS:
                continue

            acf_path = os.path.join(steamapps, fname)
            try:
                with open(acf_path, "r", encoding="utf-8", errors="replace") as f:
                    manifest = _parse_vdf_simple(f.read())
            except OSError:
                continue

            app_state = manifest.get("AppState", {})
            name = app_state.get("name", "")
            installdir = app_state.get("installdir", "")

            if not name or not installdir:
                continue

            # Skip tools/redists
            if any(skip in name.lower() for skip in [
                "redistributable", "runtime", "proton", "steamworks",
                "dedicated server",
            ]):
                continue

            game_dir = os.path.join(steamapps, "common", installdir)
            if not os.path.isdir(game_dir):
                continue

            exe = _find_main_exe(game_dir, name)
            if exe:
                games.append({
                    "name": name,
                    "exe_path": exe,
                    "source": "Steam",
                })

    return games


def scan_epic() -> list[dict]:
    """Scan Epic Games launcher for installed games.

    Returns list of dicts with: name, exe_path, source
    """
    games = []
    manifests_dir = os.path.join(
        os.environ.get("PROGRAMDATA", r"C:\ProgramData"),
        "Epic", "EpicGamesLauncher", "Data", "Manifests",
    )

    if not os.path.isdir(manifests_dir):
        return games

    for fname in os.listdir(manifests_dir):
        if not fname.endswith(".item"):
            continue

        item_path = os.path.join(manifests_dir, fname)
        try:
            with open(item_path, "r", encoding="utf-8", errors="replace") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError):
            continue

        name = data.get("DisplayName", "")
        install_loc = data.get("InstallLocation", "")
        launch_exe = data.get("LaunchExecutable", "")

        if not name or not install_loc or not launch_exe:
            continue

        exe_path = os.path.join(install_loc, launch_exe)
        if os.path.exists(exe_path):
            games.append({
                "name": name,
                "exe_path": exe_path,
                "source": "Epic",
            })

    return games


def scan_all() -> list[dict]:
    """Scan both Steam and Epic libraries. Sorted by name."""
    games = scan_steam() + scan_epic()
    games.sort(key=lambda g: g["name"].lower())
    return games


def _make_game_id(name: str) -> int:
    h = hashlib.md5(name.encode()).hexdigest()
    return int(h[:8], 16) & 0x7FFFFFFF


def build_game_preset(game: dict, preset_name: str,
                      finalize_preset: str) -> dict:
    """Build a single ColorControl GamePreset entry."""
    return {
        "Path": game["exe_path"],
        "Parameters": "",
        "RunAsAdministrator": False,
        "PreLaunchSteps": [f"NvPreset({preset_name})"],
        "PostLaunchSteps": [],
        "FinalizeSteps": [f"NvPreset({finalize_preset})"],
        "ProcessAffinityMask": 0,
        "ProcessPriorityClass": 0,
        "PathExists": os.path.exists(game["exe_path"]),
        "GameProcessPriorityClass": 0,
        "AutoSettings": {
            "AllowAutoApply": True,
            "ProcessAutoAction": 0,
        },
        "name": game["name"],
        "shortcut": "",
        "Triggers": [],
        "Steps": [],
        "Description": None,
        "ShowInQuickAccess": True,
        "LastUsed": None,
        "IdOrName": game["name"],
        "id": _make_game_id(game["name"]),
    }


def export_game_presets(games: list[dict], preset_name: str,
                        finalize_preset: str,
                        merge_existing: bool = True) -> str:
    """Generate or merge GamePresets.json for ColorControl.

    Args:
        games: List of game dicts from scan_all()
        preset_name: NvPreset name to apply on launch
        finalize_preset: NvPreset name to apply when game closes
        merge_existing: If True, merge with existing GamePresets.json

    Returns path to the written file.
    """
    cc_dir = os.path.join(
        os.environ.get("APPDATA", ""),
        "Maassoft", "ColorControl")
    cc_path = os.path.join(cc_dir, "GamePresets.json")

    existing = []
    if merge_existing and os.path.exists(cc_path):
        try:
            with open(cc_path, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except (json.JSONDecodeError, OSError):
            pass

    # Index existing by exe path (case-insensitive) to avoid duplicates
    existing_paths = {
        e.get("Path", "").lower() for e in existing
    }

    new_presets = []
    for game in games:
        if game["exe_path"].lower() not in existing_paths:
            new_presets.append(
                build_game_preset(game, preset_name, finalize_preset))

    merged = existing + new_presets

    # Back up existing
    if os.path.exists(cc_path):
        import shutil
        shutil.copy2(cc_path, cc_path + ".backup")

    with open(cc_path, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)

    return cc_path, len(new_presets), len(existing)
