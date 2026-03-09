#!/usr/bin/env python3
"""
Generate PWA icons and favicon for RechnungsKern.
Creates:
  - public/icon-192.png  (192x192)
  - public/icon-512.png  (512x512)
  - public/icons/icon-192.png  (192x192, maskable copy)
  - public/icons/icon-512.png  (512x512, maskable copy)
  - public/favicon.ico   (multi-size ICO: 16x16, 32x32, 48x48)

Requirements: pip install Pillow
"""

import os
import sys
import shutil

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("ERROR: Pillow is required. Install with: pip install Pillow")
    sys.exit(1)

# Brand colors
TEAL = (13, 148, 136)       # #0d9488
WHITE = (255, 255, 255)
DARK_BG = (15, 23, 42)      # #0f172a (matches manifest background_color)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PUBLIC_DIR = os.path.join(SCRIPT_DIR, '..', 'public')
ICONS_DIR = os.path.join(PUBLIC_DIR, 'icons')

os.makedirs(ICONS_DIR, exist_ok=True)


def find_font(size: int):
    """Try to find a bold sans-serif font, fall back to default."""
    font_paths = [
        # macOS
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/SFNSDisplay.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Supplemental/Helvetica Neue.ttc",
        "/Library/Fonts/Arial Bold.ttf",
        # Linux
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
        # Windows
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/calibrib.ttf",
    ]
    for path in font_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except (OSError, IOError):
                continue
    # Fallback to default
    try:
        return ImageFont.truetype("arial.ttf", size)
    except (OSError, IOError):
        return ImageFont.load_default()


def create_icon(size: int) -> Image.Image:
    """Create a single icon at the given size."""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Draw rounded rectangle background
    margin = int(size * 0.04)
    radius = int(size * 0.18)
    draw.rounded_rectangle(
        [margin, margin, size - margin, size - margin],
        radius=radius,
        fill=TEAL,
    )

    # Draw "RK" text (skip on very small sizes where font rendering fails)
    font_size = max(int(size * 0.38), 8)
    if size >= 32:
        font = find_font(font_size)
        text = "RK"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (size - text_width) / 2 - bbox[0]
        y = (size - text_height) / 2 - bbox[1]
        draw.text((x, y), text, fill=WHITE, font=font)
    else:
        # For tiny sizes, just draw a simple "R" or leave as solid color
        try:
            font = find_font(font_size)
            text = "R"
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x = (size - text_width) / 2 - bbox[0]
            y = (size - text_height) / 2 - bbox[1]
            draw.text((x, y), text, fill=WHITE, font=font)
        except Exception:
            pass  # Just use the solid colored square for very small sizes

    return img


def create_favicon(sizes=None) -> None:
    """Create multi-size favicon.ico."""
    if sizes is None:
        sizes = [16, 32, 48]
    images = []
    for s in sizes:
        icon = create_icon(s)
        # Convert to RGB with white background for ICO
        bg = Image.new('RGB', (s, s), DARK_BG)
        bg.paste(icon, mask=icon.split()[3] if icon.mode == 'RGBA' else None)
        images.append(bg)

    favicon_path = os.path.join(PUBLIC_DIR, 'favicon.ico')
    images[0].save(
        favicon_path,
        format='ICO',
        sizes=[(s, s) for s in sizes],
        append_images=images[1:],
    )
    print(f"  Created: {favicon_path}")


def main():
    print("Generating RechnungsKern PWA icons...")

    # Generate main icons
    for size in [192, 512]:
        icon = create_icon(size)

        # Save to public root
        root_path = os.path.join(PUBLIC_DIR, f'icon-{size}.png')
        icon.save(root_path, 'PNG', optimize=True)
        print(f"  Created: {root_path}")

        # Save maskable copy to /icons/ subdirectory
        maskable_path = os.path.join(ICONS_DIR, f'icon-{size}.png')
        shutil.copy2(root_path, maskable_path)
        print(f"  Created: {maskable_path}")

    # Generate favicon
    create_favicon([16, 32, 48])

    print("\nDone! All icons generated successfully.")
    print("\nFiles created:")
    print("  public/icon-192.png      - PWA icon 192x192")
    print("  public/icon-512.png      - PWA icon 512x512")
    print("  public/icons/icon-192.png - Maskable icon 192x192")
    print("  public/icons/icon-512.png - Maskable icon 512x512")
    print("  public/favicon.ico       - Favicon (16/32/48)")


if __name__ == '__main__':
    main()
