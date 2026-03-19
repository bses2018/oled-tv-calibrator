"""Main GUI application for OLED TV Calibrator."""

import os
import sys
import subprocess
import threading
import customtkinter as ctk

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.tv_database import (
    PROFILE_DEFS, get_brands, get_series, get_models, get_model_data,
    get_sizes, get_max_tml, get_paper_white, get_profile_params,
    get_display_name,
)
from src.profile_generator import generate_profiles
from src.colorcontrol_export import (
    generate_nvpresets, read_existing_display_info, detect_windows_displays,
)
from src.windows_color import install_profiles
from src.game_scanner import scan_all, export_game_presets

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


# Accent colors
ACCENT = "#2d7dd2"
ACCENT_HOVER = "#1b6abf"
SUCCESS = "#2eaa4f"
SUCCESS_HOVER = "#239940"
WARN = "#e07b28"


class OLEDCalibratorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("OLED TV Calibrator")
        self.geometry("1060x700")
        self.minsize(900, 580)

        # Set window icon
        from src.gui.icon import get_icon_path
        icon = get_icon_path()
        if icon:
            self.iconbitmap(icon)

        self._profiles_generated = []
        self._existing_display = {}  # filled by Detect button, not stale config

        self._build_ui()
        self._cascade_from_brand()

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header banner
        header = ctk.CTkFrame(self, height=44, fg_color=ACCENT,
                              corner_radius=0)
        header.grid(row=0, column=0, columnspan=2, sticky="ew")
        header.grid_propagate(False)
        ctk.CTkLabel(
            header, text="OLED TV Calibrator",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="white",
        ).pack(side="left", padx=14, pady=6)
        ctk.CTkLabel(
            header, text="HDR Profile Generator",
            font=ctk.CTkFont(size=13),
            text_color="#b0d4f1",
        ).pack(side="left", padx=(0, 10), pady=6)
        ctk.CTkLabel(
            header,
            text="Run as Administrator for Install to Windows",
            font=ctk.CTkFont(size=10),
            text_color="#7ab0de",
        ).pack(side="right", padx=14, pady=6)

        self._build_left_panel()
        self._build_right_panel()

    def _build_left_panel(self):
        P = 12  # standard horizontal padding
        left = ctk.CTkScrollableFrame(self, width=310)
        left.grid(row=1, column=0, sticky="nsew", padx=(8, 4), pady=(6, 8))

        SML = ctk.CTkFont(size=12)
        HDR = ctk.CTkFont(size=15, weight="bold")

        # ---- TV Selection ----
        ctk.CTkLabel(left, text="TV Selection", font=HDR).pack(
            padx=P, pady=(10, 4), anchor="w")

        # Brand + Series
        row1 = ctk.CTkFrame(left, fg_color="transparent")
        row1.pack(padx=P, pady=(2, 0), fill="x")
        row1.grid_columnconfigure(1, weight=1)
        row1.grid_columnconfigure(3, weight=2)
        self._brand_var = ctk.StringVar()
        self._series_var = ctk.StringVar()
        ctk.CTkLabel(row1, text="Brand:", font=SML).grid(
            row=0, column=0, sticky="w")
        self._brand_menu = ctk.CTkOptionMenu(
            row1, variable=self._brand_var, values=get_brands(),
            command=self._on_brand_change, height=30, dynamic_resizing=False)
        self._brand_menu.grid(row=0, column=1, padx=(4, 8), sticky="ew")
        ctk.CTkLabel(row1, text="Series:", font=SML).grid(
            row=0, column=2, sticky="w")
        self._series_menu = ctk.CTkOptionMenu(
            row1, variable=self._series_var, values=["--"],
            command=self._on_series_change, height=30, dynamic_resizing=False)
        self._series_menu.grid(row=0, column=3, padx=(4, 0), sticky="ew")

        # Model + Size
        row2 = ctk.CTkFrame(left, fg_color="transparent")
        row2.pack(padx=P, pady=(6, 0), fill="x")
        row2.grid_columnconfigure(1, weight=1)
        self._model_var = ctk.StringVar()
        self._size_var = ctk.StringVar()
        ctk.CTkLabel(row2, text="Model:", font=SML).grid(
            row=0, column=0, sticky="w")
        self._model_menu = ctk.CTkOptionMenu(
            row2, variable=self._model_var, values=["--"],
            command=self._on_model_change, height=30, dynamic_resizing=False)
        self._model_menu.grid(row=0, column=1, padx=(4, 8), sticky="ew")
        ctk.CTkLabel(row2, text="Size:", font=SML).grid(
            row=0, column=2, sticky="w")
        self._size_menu = ctk.CTkOptionMenu(
            row2, variable=self._size_var, values=["--"],
            command=self._on_size_change, width=75, height=30)
        self._size_menu.grid(row=0, column=3, padx=(4, 0))

        # TML + Paper White
        row3 = ctk.CTkFrame(left, fg_color="transparent")
        row3.pack(padx=P, pady=(6, 0), fill="x")
        row3.grid_columnconfigure(1, weight=1)
        row3.grid_columnconfigure(3, weight=1)
        self._tml_var = ctk.StringVar(value="800")
        self._pw_var = ctk.StringVar(value="172")
        ctk.CTkLabel(row3, text="Max TML:", font=SML).grid(
            row=0, column=0, sticky="w")
        self._tml_entry = ctk.CTkEntry(
            row3, textvariable=self._tml_var, height=30)
        self._tml_entry.grid(row=0, column=1, padx=(4, 8), sticky="ew")
        self._tml_var.trace_add("write", lambda *_: self._update_preview())
        ctk.CTkLabel(row3, text="Paper White:", font=SML).grid(
            row=0, column=2, sticky="w")
        self._pw_entry = ctk.CTkEntry(
            row3, textvariable=self._pw_var, height=30)
        self._pw_entry.grid(row=0, column=3, padx=(4, 0), sticky="ew")

        # ---- Output ----
        self._add_separator(left)
        ctk.CTkLabel(left, text="Output", font=HDR).pack(
            padx=P, pady=(0, 4), anchor="w")
        out_frame = ctk.CTkFrame(left, fg_color="transparent")
        out_frame.pack(padx=P, fill="x")
        default_out = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "output")
        self._output_var = ctk.StringVar(value=default_out)
        out_entry = ctk.CTkEntry(out_frame, textvariable=self._output_var,
                                 height=30)
        out_entry.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(out_frame, text="...", width=32, height=30,
                       command=self._browse_output).pack(
            side="left", padx=(4, 0))
        ctk.CTkButton(out_frame, text="Open", width=50, height=30,
                       command=self._open_output_folder).pack(
            side="left", padx=(4, 0))

        # ---- Target Display ----
        self._add_separator(left)
        ctk.CTkLabel(left, text="Target Display", font=HDR).pack(
            padx=P, pady=(0, 1), anchor="w")
        ctk.CTkLabel(left, text="Required for Install to Windows",
                     font=ctk.CTkFont(size=10), text_color="gray55").pack(
            padx=P, pady=(0, 4), anchor="w")

        self._detected_displays = []
        self._display_picker_var = ctk.StringVar(value="")
        picker_frame = ctk.CTkFrame(left, fg_color="transparent")
        picker_frame.pack(padx=P, fill="x")
        self._display_picker = ctk.CTkOptionMenu(
            picker_frame, variable=self._display_picker_var,
            values=["(click Detect)"],
            command=self._on_display_picked, height=30, dynamic_resizing=False)
        self._display_picker.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(picker_frame, text="Detect", width=70, height=30,
                       command=self._detect_displays).pack(
            side="left", padx=(4, 0))

        self._display_name_var = ctk.StringVar(value="")
        self._display_id_var = ctk.StringVar(value="")
        info_frame = ctk.CTkFrame(left, fg_color="transparent")
        info_frame.pack(padx=P, pady=(4, 0), fill="x")
        ctk.CTkLabel(info_frame, text="Name:", font=SML).grid(
            row=0, column=0, sticky="w")
        ctk.CTkLabel(info_frame, textvariable=self._display_name_var,
                     font=SML, text_color="gray70").grid(
            row=0, column=1, sticky="w", padx=(6, 0))
        ctk.CTkLabel(info_frame, text="ID:", font=SML).grid(
            row=1, column=0, sticky="w")
        ctk.CTkLabel(info_frame, textvariable=self._display_id_var,
                     font=SML, text_color="gray70").grid(
            row=1, column=1, sticky="w", padx=(6, 0))

        # ---- ColorControl (Optional) ----
        self._add_separator(left)
        ctk.CTkLabel(left, text="ColorControl Export (Optional)", font=HDR).pack(
            padx=P, pady=(0, 4), anchor="w")
        rr_frame = ctk.CTkFrame(left, fg_color="transparent")
        rr_frame.pack(padx=P, pady=(0, 6), fill="x")
        ctk.CTkLabel(rr_frame, text="Refresh Rate (Hz):", font=SML).pack(
            side="left")
        self._refresh_var = ctk.StringVar(value="119.88")
        ctk.CTkEntry(rr_frame, textvariable=self._refresh_var,
                     width=80, height=30).pack(side="left", padx=(6, 0))

    def _build_right_panel(self):
        right = ctk.CTkFrame(self)
        right.grid(row=1, column=1, sticky="nsew", padx=(4, 8), pady=(6, 8))
        right.grid_rowconfigure(1, weight=1)
        right.grid_columnconfigure(0, weight=1)

        # Selected TV label
        self._tv_label = ctk.CTkLabel(
            right, text="Profile Preview",
            font=ctk.CTkFont(size=15, weight="bold"))
        self._tv_label.grid(row=0, column=0, padx=12, pady=(10, 4), sticky="w")

        # Profile table
        self._table_frame = ctk.CTkScrollableFrame(right)
        self._table_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 6))
        self._table_frame.grid_columnconfigure(0, weight=1)

        # ---- Buttons: Generate / Install / Export / Guide ----
        btn_frame = ctk.CTkFrame(right, fg_color="transparent")
        btn_frame.grid(row=2, column=0, padx=10, pady=(0, 2), sticky="ew")

        self._gen_btn = ctk.CTkButton(
            btn_frame, text="1. Generate ICC Profiles",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=36, command=self._on_generate,
            fg_color=SUCCESS, hover_color=SUCCESS_HOVER,
        )
        self._gen_btn.pack(fill="x", padx=4, pady=(0, 3))

        btn_row = ctk.CTkFrame(btn_frame, fg_color="transparent")
        btn_row.pack(fill="x")

        self._install_btn = ctk.CTkButton(
            btn_row, text="2a. Install to Windows",
            font=ctk.CTkFont(size=12), height=32,
            command=self._on_install, state="disabled",
            fg_color=ACCENT, hover_color=ACCENT_HOVER,
        )
        self._install_btn.pack(side="left", padx=4, pady=2, fill="x", expand=True)

        self._export_btn = ctk.CTkButton(
            btn_row, text="2b. Export NvPresets",
            font=ctk.CTkFont(size=12), height=32,
            command=self._on_export, state="disabled",
            fg_color=ACCENT, hover_color=ACCENT_HOVER,
        )
        self._export_btn.pack(side="left", padx=4, pady=2, fill="x", expand=True)

        self._guide_btn = ctk.CTkButton(
            btn_row, text="Setup Guide",
            font=ctk.CTkFont(size=11), height=32,
            fg_color="#3a3a3a", hover_color="#4a4a4a",
            command=self._show_setup_guide,
        )
        self._guide_btn.pack(side="left", padx=4, pady=2)

        self._games_btn = ctk.CTkButton(
            btn_row, text="Import Games",
            font=ctk.CTkFont(size=11), height=32,
            fg_color="#3a3a3a", hover_color="#4a4a4a",
            command=self._show_game_import,
        )
        self._games_btn.pack(side="left", padx=4, pady=2)

        self._step2_hint = ctk.CTkLabel(
            btn_frame,
            text="Generate first, then select display and install.",
            font=ctk.CTkFont(size=10), text_color="gray50",
        )
        self._step2_hint.pack(padx=6, pady=(2, 0), anchor="w")

        # Status log
        self._log = ctk.CTkTextbox(right, height=120, state="disabled",
                                    font=ctk.CTkFont(family="Consolas", size=11))
        self._log.grid(row=3, column=0, sticky="nsew", padx=10, pady=(4, 10))
        right.grid_rowconfigure(3, weight=0, minsize=120)

    def _add_separator(self, parent):
        ctk.CTkFrame(parent, height=1, fg_color=ACCENT).pack(
            fill="x", padx=12, pady=8)

    # ------------------------------------------------------------------
    # Cascading dropdown logic
    # ------------------------------------------------------------------

    def _cascade_from_brand(self):
        brands = get_brands()
        if not brands:
            return
        self._brand_var.set(brands[0])
        self._on_brand_change(brands[0])

    def _on_brand_change(self, _):
        brand = self._brand_var.get()
        series_list = get_series(brand)
        self._series_menu.configure(values=series_list)
        if series_list:
            self._series_var.set(series_list[0])
            self._on_series_change(series_list[0])

    def _on_series_change(self, _):
        brand = self._brand_var.get()
        series = self._series_var.get()
        models = get_models(brand, series)
        display = [f"{m} ({get_model_data(brand, series, m)['year']})" for m in models]
        self._model_menu.configure(values=display)
        if display:
            self._model_var.set(display[0])
            self._on_model_change(display[0])

    def _on_model_change(self, _):
        brand = self._brand_var.get()
        series = self._series_var.get()
        model = self._parse_model_key()
        if model is None:
            return
        sizes = get_sizes(brand, series, model)
        display_sizes = [f'{s}"' for s in sizes]
        self._size_menu.configure(values=display_sizes)
        if display_sizes:
            self._size_var.set(display_sizes[0])
            self._on_size_change(display_sizes[0])

    def _on_size_change(self, _):
        brand = self._brand_var.get()
        series = self._series_var.get()
        model = self._parse_model_key()
        size = self._size_var.get().replace('"', '')
        if model is None:
            return
        try:
            tml = get_max_tml(brand, series, model, size)
        except (KeyError, TypeError):
            tml = 800
        self._tml_var.set(str(tml))
        self._pw_var.set(str(get_paper_white(tml)))
        self._tv_label.configure(
            text=f"{get_display_name(brand, series, model)} -- {size}\"")
        self._update_preview()

    def _parse_model_key(self) -> str | None:
        val = self._model_var.get()
        if not val or val == "--":
            return None
        return val.split(" (")[0]

    # ------------------------------------------------------------------
    # Preview table
    # ------------------------------------------------------------------

    def _get_tml(self) -> int:
        try:
            return int(self._tml_var.get())
        except ValueError:
            return 800

    def _get_tv_model(self) -> str:
        brand = self._brand_var.get()
        model_key = self._parse_model_key() or ""
        return f"{brand} {model_key}" if model_key else ""

    def _update_preview(self):
        for widget in self._table_frame.winfo_children():
            widget.destroy()

        max_tml = self._get_tml()
        tv_model = self._get_tv_model()

        # Header row
        header_frame = ctk.CTkFrame(self._table_frame, fg_color="gray25")
        header_frame.pack(fill="x", pady=(0, 2))
        headers = ["Profile", "Gamma", "Ref White", "SDR Bright.", "MaxCLL"]
        weights = [3, 1, 1, 1, 1]
        for i, (h, w) in enumerate(zip(headers, weights)):
            header_frame.grid_columnconfigure(i, weight=w)
            ctk.CTkLabel(header_frame, text=h,
                         font=ctk.CTkFont(size=12, weight="bold")).grid(
                row=0, column=i, padx=8, pady=4, sticky="w")

        # Profile rows
        for profile_def in PROFILE_DEFS:
            params = get_profile_params(profile_def, max_tml, tv_model=tv_model)
            row_frame = ctk.CTkFrame(self._table_frame, fg_color="gray20")
            row_frame.pack(fill="x", pady=1)
            for i in range(5):
                row_frame.grid_columnconfigure(i, weight=weights[i])

            gamma_str = f"{params['gamma']}" if params['gamma'] else "sRGB"
            values = [
                params["name"], gamma_str,
                f"{params['ref_white']} nits", f"{params['sdr_brightness']}%",
                str(max_tml),
            ]
            for i, v in enumerate(values):
                ctk.CTkLabel(row_frame, text=v,
                             font=ctk.CTkFont(size=11)).grid(
                    row=0, column=i, padx=8, pady=4, sticky="w")

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _log_msg(self, msg: str):
        self._log.configure(state="normal")
        self._log.insert("end", msg + "\n")
        self._log.see("end")
        self._log.configure(state="disabled")

    def _clear_log(self):
        self._log.configure(state="normal")
        self._log.delete("1.0", "end")
        self._log.configure(state="disabled")

    def _on_generate(self):
        self._clear_log()
        self._gen_btn.configure(state="disabled", text="Generating...")

        def do_generate():
            try:
                max_tml = self._get_tml()
                output_dir = self._output_var.get()
                tv_name = self._tv_label.cget("text")

                # Build short model name like "LG G4"
                brand = self._brand_var.get()
                model_key = self._parse_model_key() or ""
                tv_model = f"{brand} {model_key}" if model_key else ""

                self._log_msg(f"Generating profiles for {tv_name}...")
                self._log_msg(f"Max TML: {max_tml} nits")
                self._log_msg(f"Output: {output_dir}")
                self._log_msg("")

                profiles = generate_profiles(max_tml, output_dir,
                                             tv_model=tv_model)
                self._profiles_generated = profiles

                for p in profiles:
                    self._log_msg(f"  Created: {p['icc_filename']}")

                self._log_msg(f"\n{len(profiles)} ICC profiles saved to:")
                self._log_msg(f"  {output_dir}")
                has_display = bool(self._display_id_var.get().strip())
                self._log_msg(f"\nWhat to do next:")
                if not has_display:
                    self._log_msg(
                        f"  1. Click 'Detect' under Target Display "
                        f"and select your TV")
                    self._log_msg(
                        f"  2. Click 'Install to Windows' (may need admin)")
                else:
                    self._log_msg(
                        f"  1. Click 'Install to Windows' (may need admin)")
                self._log_msg(f"  Then click 'Setup Guide' for TV & game settings")

                self._update_install_button()
                self._export_btn.configure(state="normal")
                self._step2_hint.configure(text_color="gray80")

            except Exception as e:
                self._log_msg(f"ERROR: {e}")
            finally:
                self._gen_btn.configure(state="normal",
                                        text="1. Generate ICC Profiles")

        threading.Thread(target=do_generate, daemon=True).start()

    def _on_export(self):
        if not self._profiles_generated:
            self._log_msg("Generate profiles first!")
            return
        try:
            import shutil

            # Generate to output dir
            output_dir = self._output_var.get()
            path = generate_nvpresets(
                profiles=self._profiles_generated,
                display_name=self._display_name_var.get(),
                display_id=self._display_id_var.get(),
                refresh_rate=float(self._refresh_var.get()),
                output_dir=output_dir,
            )
            self._log_msg(f"\nExported: {path}")

            # Try to install directly to ColorControl directory
            cc_dir = os.path.join(
                os.environ.get("APPDATA", ""),
                "Maassoft", "ColorControl")
            cc_presets = os.path.join(cc_dir, "NvPresets.json")

            if os.path.isdir(cc_dir):
                # Back up existing presets
                if os.path.exists(cc_presets):
                    backup = cc_presets + ".backup"
                    shutil.copy2(cc_presets, backup)
                    self._log_msg(f"Backed up existing: NvPresets.json.backup")

                # Copy new presets
                shutil.copy2(path, cc_presets)
                self._log_msg(f"Installed to ColorControl config directory.")
                self._log_msg(
                    "Restart ColorControl to see the new presets "
                    "in the Nvidia controller tab.")
            else:
                self._log_msg(
                    "ColorControl not found. Copy NvPresets.json "
                    f"manually from: {output_dir}")
        except Exception as e:
            self._log_msg(f"Export error: {e}")

    def _on_install(self):
        if not self._profiles_generated:
            self._log_msg("Generate profiles first!")
            return

        device_id = self._display_id_var.get().strip()
        if not device_id:
            self._log_msg(
                "\nSelect a display first: click 'Detect' under "
                "'Target Display' on the left.")
            return

        paths = [p["icc_path"] for p in self._profiles_generated]

        # The Native HDR profile is the primary one to associate with the display
        native = next(
            (p["icc_filename"] for p in self._profiles_generated
             if p["id"] == "native_hdr"), "")

        self._log_msg(f"\nInstalling {len(paths)} profiles...")
        self._log_msg(f"Target display: {self._display_name_var.get()} ({device_id})")

        results = install_profiles(paths, device_id=device_id,
                                   primary_profile=native)

        installed = sum(1 for r in results if r["installed"])
        associated = sum(1 for r in results if r["associated"])

        for r in results:
            status = "OK" if r["installed"] else "FAILED"
            extra = ""
            if r["is_primary"] and r["associated"]:
                extra = " (associated with display)"
            elif r["is_primary"] and not r["associated"] and device_id:
                extra = " (association failed)"
            if r["error"] and not r["installed"]:
                extra = f" - {r['error']}"
            self._log_msg(f"  [{status}] {r['filename']}{extra}")

        if installed == len(results):
            self._log_msg(f"\nAll {installed} profiles installed!")
            if associated:
                self._log_msg(
                    "Native HDR profile is set as your display's "
                    "color profile.")

            # Check if ColorControl is installed and prompt
            cc_dir = os.path.join(
                os.environ.get("APPDATA", ""),
                "Maassoft", "ColorControl")
            if os.path.isdir(cc_dir):
                self._log_msg(
                    "\nColorControl detected! Click 'Export NvPresets' "
                    "to add these profiles as switchable presets in "
                    "ColorControl's Nvidia controller.")
            else:
                self._log_msg(
                    "\nSwitch profiles via Windows Color Management "
                    "(colorcpl) or install ColorControl by maasoft "
                    "for quick-switching and game auto-apply.")
        elif installed == 0:
            self._log_msg(
                "\nCould not install (access denied). "
                "Right-click the app and 'Run as Administrator'.")
        else:
            self._log_msg(
                f"\n{installed}/{len(results)} installed. "
                "Run as Administrator to install the rest.")

    def _show_setup_guide(self):
        max_tml = self._get_tml()
        pw = self._pw_var.get()
        tv_model = self._get_tv_model()
        brand = self._brand_var.get()

        # PS5 clicks from bottom for HDR calibration
        ps5_clicks = {800: 14, 1000: 15, 1500: 18, 2000: 20}
        clicks = ps5_clicks.get(max_tml, 14)

        guide = ctk.CTkToplevel(self)
        guide.title("Setup Guide")
        guide.geometry("720x700")
        guide.attributes("-topmost", True)
        guide.after(200, lambda: guide.attributes("-topmost", False))

        text = ctk.CTkTextbox(guide, font=ctk.CTkFont(family="Consolas", size=12),
                              wrap="word")
        text.pack(fill="both", expand=True, padx=10, pady=10)

        content = f"""SETUP GUIDE - {tv_model or 'Your TV'} ({max_tml} nits)
{'=' * 60}

STEP 1: GENERATE & INSTALL ICC PROFILES
----------------------------------------
a) Click "Generate ICC Profiles" to create your profiles.

b) Select your display: Under "ColorControl Export", click
   "Detect" and pick your TV from the dropdown. This tells
   the installer which display to associate profiles with.

c) Click "Install to Windows" (requires Administrator).
   This copies profiles to the system color directory AND
   associates the Native HDR profile with your display.

   This REPLACES the "Windows HDR Calibration" app - you
   do NOT need to run it separately. The Native HDR profile
   contains the same MinCLL/MaxCLL data ({max_tml} nits).

   If you can't run as admin, manually copy files from your
   output folder to:
   C:\\Windows\\System32\\spool\\drivers\\color\\
   Then open Color Management (colorcpl) to associate them.


STEP 2: WINDOWS DISPLAY SETTINGS
----------------------------------------
  Settings > System > Display > HDR

  - Turn HDR ON (leave it on permanently)
  - SDR content brightness: Leave at 0%
    (the ICC profiles handle brightness per-profile)


STEP 4: TV PICTURE SETTINGS
----------------------------------------
Set your TV to Game Mode for your PC's HDMI input.

"""
        if brand == "LG":
            content += """  LG TV Settings:
  - Picture Mode: Game Optimizer
  - HDMI Ultra HD Deep Color: ON for your PC's HDMI port
  - Instant Game Response: ON

  HDR Dynamic Tone Mapping (Settings > Picture):
    ON:   TV brightens the image - best for lit rooms
    HGiG: Raw accuracy, no TV processing - best for
          dark rooms (will look dim in a lit room)
    OFF:  Not recommended (forces 4000 nit curve)
    PS5/Xbox: HGiG recommended

  To disable ASBL (auto-dimming of static content):
  Use ColorControl > Config > Disable TPC + Disable GSR
"""
        elif brand == "Sony":
            content += """  Sony TV Settings:
  - Picture Mode: Game
  - Enhanced HDMI signal format: Enhanced for your input

  HDR Tone Mapping:
    On/Auto: TV brightens the image - best for lit rooms
    Off:     Raw accuracy - best for dark rooms
    PS5/Xbox: HGiG if available
"""
        elif brand == "Samsung":
            content += """  Samsung TV Settings:
  - Picture Mode: Game
  - Input Signal Plus: ON for your PC's HDMI port

  HDR Tone Mapping / Game HDR:
    On/Auto: TV brightens the image - best for lit rooms
    Off:     Raw accuracy - best for dark rooms
    PS5/Xbox: HGiG if available
"""

        content += f"""

STEP 5: IN-GAME HDR SETTINGS
----------------------------------------
For native HDR games, set these in each game's HDR menu:

  Min brightness / Black level:   0
  Max brightness / Peak white:    {max_tml} nits
  Paper white / Reference white:  {pw} nits

HGiG-compliant games auto-detect your display capabilities
from the ICC profile.


STEP 6: CONSOLE HDR CALIBRATION (Optional)
----------------------------------------
  Xbox: Settings > TV & display > Calibrate HDR
    Screen 1: Set to 0
    Screen 2: Set to {max_tml}
    Screen 3: Set to {max_tml}

  PS5: Settings > Screen & Video > HDR > Adjust HDR
    Screen 1: {clicks} clicks from the bottom
    Screen 2: {clicks} clicks from the bottom
    Screen 3: All the way to the bottom (0)


STEP 7: USING YOUR PROFILES
----------------------------------------
Which profile to use and when:

  Native HDR - sRGB + 80 nits
    Use for: Native HDR games, HDR video, sRGB SDR games
    SDR brightness: 0%

  Virtual SDR - 2.2 + 120 nits
    Use for: Most SDR games (mastered to gamma 2.2)
    SDR brightness: 10%

  Virtual SDR - 2.4 + 100 nits
    Use for: SDR video, games mastered to gamma 2.4/BT.1886
    SDR brightness: 5%

  Auto HDR - 2.2 + {pw} nits
    Use for: Auto HDR games originally mastered to gamma 2.2
    SDR brightness: {self._get_auto_hdr_sdr()}%

  Auto HDR - 2.4 + {pw} nits
    Use for: Auto HDR games originally mastered to gamma 2.4
    SDR brightness: {self._get_auto_hdr_sdr()}%

  Auto HDR - sRGB + {pw} nits
    Use for: Auto HDR with no gamma correction, sRGB games
    SDR brightness: {self._get_auto_hdr_sdr()}%


COLORCONTROL USERS
----------------------------------------
If you use ColorControl by maasoft:

  1. Click "Export NvPresets.json" in the app
  2. Copy it to: %APPDATA%\\Maassoft\\ColorControl\\
     (back up your existing NvPresets.json first!)
  3. Restart ColorControl
  4. Your profiles appear in the Nvidia controller tab
  5. Set each profile to "Show in Quick Access"
  6. Use your quick access shortcut to switch profiles
  7. In the Game Launcher, assign profiles to games so
     they auto-apply when you launch each game

WITHOUT COLORCONTROL
----------------------------------------
  - Use Windows Color Management (Control Panel) to
    assign profiles to your display
  - Manually adjust SDR content brightness in
    Settings > Display > HDR for each profile
  - Or use another ICC profile switcher utility
"""

        text.insert("1.0", content)
        text.configure(state="disabled")

    def _get_auto_hdr_sdr(self) -> int:
        from src.tv_database import get_auto_hdr_sdr_brightness
        return get_auto_hdr_sdr_brightness(self._get_tml())

    def _show_game_import(self):
        win = ctk.CTkToplevel(self)
        win.title("Import Games to ColorControl")
        win.geometry("780x560")
        win.attributes("-topmost", True)
        win.after(200, lambda: win.attributes("-topmost", False))

        # Top bar: profile selectors
        top = ctk.CTkFrame(win)
        top.pack(fill="x", padx=10, pady=(10, 4))

        # Get available preset names from generated profiles
        preset_names = [p["name"] for p in self._profiles_generated] if self._profiles_generated else [
            "Native HDR - sRGB + 80 nits"]
        native = preset_names[0]

        ctk.CTkLabel(top, text="Launch profile:",
                     font=ctk.CTkFont(size=12)).pack(side="left", padx=(8, 4))
        launch_var = ctk.StringVar(value=native)
        ctk.CTkOptionMenu(top, variable=launch_var,
                          values=preset_names, width=250, height=28).pack(
            side="left", padx=(0, 12))

        ctk.CTkLabel(top, text="On close:",
                     font=ctk.CTkFont(size=12)).pack(side="left", padx=(0, 4))
        close_var = ctk.StringVar(value=native)
        ctk.CTkOptionMenu(top, variable=close_var,
                          values=preset_names, width=250, height=28).pack(
            side="left")

        # Scan status
        status_label = ctk.CTkLabel(
            win, text="Scanning Steam and Epic libraries...",
            font=ctk.CTkFont(size=11), text_color="gray60")
        status_label.pack(padx=10, pady=(2, 2), anchor="w")

        # Game list (scrollable with checkboxes)
        list_frame = ctk.CTkScrollableFrame(win)
        list_frame.pack(fill="both", expand=True, padx=10, pady=(0, 6))

        # Bottom buttons
        bottom = ctk.CTkFrame(win, fg_color="transparent")
        bottom.pack(fill="x", padx=10, pady=(0, 10))

        select_all_var = ctk.BooleanVar(value=True)
        check_vars = []

        def toggle_all():
            val = select_all_var.get()
            for cv in check_vars:
                cv.set(val)

        ctk.CTkCheckBox(bottom, text="Select All", variable=select_all_var,
                        command=toggle_all, font=ctk.CTkFont(size=12)).pack(
            side="left", padx=8)

        import_btn = ctk.CTkButton(
            bottom, text="Import to ColorControl",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=34, state="disabled",
        )
        import_btn.pack(side="right", padx=8)

        result_label = ctk.CTkLabel(
            bottom, text="", font=ctk.CTkFont(size=11), text_color="gray60")
        result_label.pack(side="right", padx=8)

        def do_scan():
            games = scan_all()
            status_label.configure(
                text=f"Found {len(games)} games from Steam and Epic")

            for g in games:
                var = ctk.BooleanVar(value=True)
                check_vars.append(var)

                row = ctk.CTkFrame(list_frame, fg_color="transparent")
                row.pack(fill="x", pady=1)

                ctk.CTkCheckBox(row, text="", variable=var,
                                width=24).pack(side="left", padx=(4, 0))
                ctk.CTkLabel(
                    row, text=f"[{g['source']}]",
                    font=ctk.CTkFont(size=11), text_color="gray55",
                    width=50).pack(side="left", padx=(4, 4))
                ctk.CTkLabel(
                    row, text=g["name"],
                    font=ctk.CTkFont(size=12)).pack(
                    side="left", padx=(0, 8))
                ctk.CTkLabel(
                    row, text=os.path.basename(g["exe_path"]),
                    font=ctk.CTkFont(size=10), text_color="gray50").pack(
                    side="left")

            def do_import():
                selected = [g for g, cv in zip(games, check_vars) if cv.get()]
                if not selected:
                    result_label.configure(text="No games selected")
                    return

                try:
                    path, added, existing = export_game_presets(
                        selected,
                        preset_name=launch_var.get(),
                        finalize_preset=close_var.get(),
                    )
                    result_label.configure(
                        text=f"Added {added} new games "
                             f"({existing} existing kept). "
                             f"Restart ColorControl!",
                        text_color="green")
                except Exception as e:
                    result_label.configure(
                        text=f"Error: {e}", text_color="red")

            import_btn.configure(command=do_import, state="normal")

        win.after(100, lambda: threading.Thread(
            target=do_scan, daemon=True).start())

    def _detect_displays(self):
        self._detected_displays = detect_windows_displays()
        if not self._detected_displays:
            self._display_picker_var.set("(no displays found)")
            self._display_picker.configure(values=["(no displays found)"])
            return
        names = [d["display_name"] for d in self._detected_displays]
        self._display_picker.configure(values=names)
        # Don't auto-select — let the user pick
        if len(self._detected_displays) == 1:
            self._display_picker_var.set(names[0])
            self._on_display_picked(names[0])
        else:
            self._display_picker_var.set("-- Select your TV --")

    def _on_display_picked(self, value: str):
        for d in self._detected_displays:
            if d["display_name"] == value:
                self._display_name_var.set(d["display_name"])
                self._display_id_var.set(d["device_id"])
                self._update_install_button()
                break

    def _update_install_button(self):
        """Enable Install button only when profiles exist AND display is selected."""
        has_profiles = bool(self._profiles_generated)
        has_display = bool(self._display_id_var.get().strip())
        if has_profiles and has_display:
            self._install_btn.configure(state="normal")
        else:
            self._install_btn.configure(state="disabled")

    def _open_output_folder(self):
        path = self._output_var.get()
        os.makedirs(path, exist_ok=True)
        subprocess.Popen(["explorer", os.path.normpath(path)])

    def _browse_output(self):
        path = ctk.filedialog.askdirectory(
            title="Select Output Directory",
            initialdir=self._output_var.get(),
        )
        if path:
            self._output_var.set(path)


def run():
    app = OLEDCalibratorApp()
    app.mainloop()
