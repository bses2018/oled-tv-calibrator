# OLED TV Calibrator

**Automatically generate HDR color profiles for OLED TVs.**

Eliminates the tedious manual process of creating ICC profiles and ColorControl presets for HDR gaming on OLED displays. Select your TV model, click generate, and get a complete set of calibrated profiles ready to install.

![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)
![License](https://img.shields.io/badge/license-MIT-green)

---

## What It Does

The app generates **6 ICC color profiles** tailored to your specific TV's peak brightness:

| Profile | Use Case | Gamma | Reference White |
|---------|----------|-------|-----------------|
| **Native HDR** | HDR games, HDR video, sRGB SDR games | sRGB | 80 nits |
| **Virtual SDR 2.2** | Most SDR games (mastered to gamma 2.2) | 2.2 | 120 nits |
| **Virtual SDR 2.4** | SDR video, gamma 2.4 / BT.1886 content | 2.4 | 100 nits |
| **Auto HDR 2.2** | Auto HDR games originally mastered to gamma 2.2 | 2.2 | Per TV |
| **Auto HDR 2.4** | Auto HDR games originally mastered to gamma 2.4 | 2.4 | Per TV |
| **Auto HDR sRGB** | Auto HDR with sRGB gamma, no correction | sRGB | Per TV |

Each profile contains:
- A valid **ICC v4 profile** with MHC2 tag for Windows HDR tone mapping
- Correct **MinCLL / MaxCLL** values for your display
- **Gamma correction LUTs** (1024-entry per-channel) where applicable
- **scrd metadata** compatible with ColorControl's MHC2Gen format

## Supported TVs

### LG (CX through G5, 2020-2025)
B Series, C Series, G Series, M Series — all sizes with per-size peak brightness where applicable.

### Sony (A80J through Bravia 8 II, 2021-2025)
A80 Series (W-OLED), A90 Series, A95 Series (QD-OLED), Bravia 8 / 8 II.

### Samsung (S90C through S95F, 2022-2025)
S90 Series (QD-OLED + W-OLED hybrid), S95 Series (QD-OLED).

**35 models** across 3 brands with accurate per-size peak brightness data.

## Features

- **Cascading TV selector** — Brand > Series > Model > Size, auto-fills peak brightness
- **One-click generation** — creates all 6 profiles in seconds
- **Install to Windows** — copies profiles to the system color directory and associates with your display via Windows Color Management API
- **ColorControl integration** — exports NvPresets.json directly to ColorControl's config directory with backup
- **Game library import** — scans Steam and Epic Games libraries, bulk-imports games into ColorControl's game launcher
- **Display auto-detection** — queries Windows WMI to find connected displays
- **Setup guide** — built-in step-by-step instructions customized to your TV brand and brightness values
- **Custom icon** — generated OLED-themed app icon

## Requirements

- **Windows 10/11** with HDR-capable display
- **Python 3.10+**
- **NVIDIA GPU** (for ColorControl integration — ICC profiles work with any GPU)

## Installation

```bash
git clone https://github.com/yourusername/oled-tv-calibrator.git
cd oled-tv-calibrator
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

### Quick Start

1. **Select your TV** — pick brand, series, model, and screen size
2. **Generate** — click "Generate ICC Profiles"
3. **Detect display** — click "Detect" to find your TV
4. **Install** — click "Install to Windows" (run as Administrator)
5. **Done** — your Native HDR profile is now active

### ColorControl Users

After installing profiles:

1. Click **"Export NvPresets"** — presets are saved directly to ColorControl's config
2. **Restart ColorControl** — profiles appear in the Nvidia controller tab
3. Assign profiles to **Quick Access** for fast switching
4. Click **"Import Games"** to bulk-add your Steam/Epic library to the game launcher

### Without ColorControl

The ICC profiles work standalone through Windows Color Management:
- Open `colorcpl` (Color Management) to switch between profiles
- Or use any other ICC profile switching utility
- Adjust SDR content brightness in Windows Display Settings per profile

## How It Works

### ICC Profile Generation

The app generates two types of ICC v4 profiles:

**Simple profiles** (Native HDR, Auto HDR sRGB):
- Identity MHC2 LUT (2 entries) — no gamma correction
- Sets MinCLL=0 and MaxCLL to your TV's peak brightness
- Replaces the Windows HDR Calibration app

**Gamma correction profiles** (Virtual SDR, Auto HDR with gamma):
- 1024-entry per-channel MHC2 LUT
- Algorithm: `PQ_fwd(sRGB_encode(PQ_inv(signal) / ref_white) ^ gamma * ref_white)`
- Passthrough for signals above reference white (preserves HDR headroom)
- scrd metadata with SDRTransferFunction, Gamma, SDRMaxBrightness

### Peak Brightness Tiers

| Max TML | Paper White | Auto HDR SDR% | Example TVs |
|---------|-------------|---------------|-------------|
| 800 nits | 172 nits | 11% | LG C1-C3, Sony A80 series |
| 1000 nits | 203 nits | 18% | LG C4-C5 55"+, Samsung S90 QD-OLED |
| 1500 nits | 276 nits | 37% | LG G3-G4, Sony A95L, Samsung S95C-D |
| 2000 nits | 330 nits | 50% | LG G5 55-83", Samsung S95F |

### Profile Accuracy

Generated profiles were validated against reference profiles created by ColorControl's MHC2Gen:
- **Max LUT error: 0.18%** (< 0.5 in 8-bit, imperceptible)
- **MSE: ~0.000001** across all 1024 LUT entries

## Project Structure

```
oled-tv-calibrator/
  main.py                          Entry point
  requirements.txt                 Dependencies
  src/
    tone_curves.py                 PQ (ST.2084), sRGB, gamma transfer functions
    colorimetry.py                 sRGB primaries, D50/D65 white points, Bradford
    tv_database.py                 35 TV models, 3 brands, per-size brightness
    icc_builder.py                 ICC v4 binary profile builder
    mhc2_builder.py                MHC2 HDR tone mapping LUT builder
    profile_generator.py           Orchestrates all 6 profiles per TV
    colorcontrol_export.py         NvPresets.json + display detection
    windows_color.py               ICC install + display association via WCS API
    game_scanner.py                Steam + Epic game library scanner
    gui/
      app.py                       customtkinter dark-mode GUI
      icon.py                      Programmatic OLED-themed icon generator
```

## Adding New TV Models

Edit `src/tv_database.py` and add entries under the appropriate brand and series:

```python
"Brand": {
    "Series Name": {
        "Model": {
            "year": 2025,
            "sizes": ["55", "65", "77"],
            "max_tml": 1000,  # or {"55": 800, "65": 1000} for per-size
        },
    },
},
```

The app automatically computes paper white, SDR brightness, and all profile parameters from the max TML value.

## Acknowledgments

- **ColorControl by maasoft** — the ICC profile format and NvPreset structure were reverse-engineered from ColorControl's MHC2Gen output
- **HDR calibration methodology** — based on community research into Windows HDR pipeline, ST.2084 PQ encoding, and sRGB/gamma correction for OLED displays

## License

MIT License. See [LICENSE](LICENSE) for details.
