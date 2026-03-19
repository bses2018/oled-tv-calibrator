"""Generate the app icon programmatically."""

import os
import math


def generate_icon(path: str, size: int = 256):
    """Create an OLED-themed app icon: a rounded screen with color bands."""
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    margin = size // 16
    r = size // 8  # corner radius

    # Outer bezel - dark metallic frame
    draw.rounded_rectangle(
        [margin, margin, size - margin, size - margin],
        radius=r, fill=(40, 40, 45), outline=(70, 70, 80), width=2)

    # Inner screen area
    screen_m = margin + size // 12
    draw.rounded_rectangle(
        [screen_m, screen_m, size - screen_m, size - screen_m],
        radius=r // 2, fill=(5, 5, 10))

    # Color calibration bars (like a test pattern)
    bar_top = screen_m + size // 10
    bar_bottom = size - screen_m - size // 4
    bar_left = screen_m + size // 20
    bar_right = size - screen_m - size // 20
    bar_w = (bar_right - bar_left) // 7

    colors = [
        (220, 40, 40),    # red
        (40, 180, 40),    # green
        (40, 80, 220),    # blue
        (220, 200, 40),   # yellow
        (40, 200, 200),   # cyan
        (180, 40, 200),   # magenta
        (240, 240, 240),  # white
    ]

    for i, color in enumerate(colors):
        x1 = bar_left + i * bar_w
        x2 = x1 + bar_w - 2
        draw.rectangle([x1, bar_top, x2, bar_bottom], fill=color)

    # HDR brightness gradient bar at bottom
    grad_top = bar_bottom + size // 20
    grad_bottom = size - screen_m - size // 16
    grad_left = bar_left
    grad_right = bar_right
    steps = grad_right - grad_left
    for x in range(steps):
        t = x / max(steps - 1, 1)
        # PQ-like curve: slow start, bright end
        v = int(255 * (t ** 0.45))
        draw.line([(grad_left + x, grad_top),
                   (grad_left + x, grad_bottom)],
                  fill=(v, v, v))

    # "HDR" text overlay
    text = "HDR"
    try:
        font_size = size // 5
        font = ImageFont.truetype("arial.ttf", font_size)
    except (OSError, IOError):
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tx = (size - tw) // 2
    ty = bar_top + (bar_bottom - bar_top - th) // 2 - size // 30

    # Text shadow
    draw.text((tx + 2, ty + 2), text, fill=(0, 0, 0, 180), font=font)
    # Text
    draw.text((tx, ty), text, fill=(255, 255, 255, 230), font=font)

    # Save as ICO with multiple sizes
    icon_sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    img.save(path, format="ICO", sizes=icon_sizes)
    return path


def get_icon_path() -> str:
    """Get or generate the app icon path."""
    icon_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    icon_path = os.path.join(icon_dir, "oled_calibrator.ico")

    if not os.path.exists(icon_path):
        try:
            generate_icon(icon_path)
        except Exception:
            return ""

    return icon_path
