"""OLED TV Calibrator - HDR Profile Generator

Automatically generates ICC color profiles and ColorControl presets
for OLED TVs based on the selected TV model and peak brightness.
"""

import sys
import os

# Ensure the project root is on the path
sys.path.insert(0, os.path.dirname(__file__))

from src.gui.app import run

if __name__ == "__main__":
    run()
