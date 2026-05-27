# utils.py
"""
Utility functions for text wrapping, font downloading, and credential masking.
"""

import os
import requests
from PIL import ImageFont

def mask_token(token):
    """Masks secret API tokens so they are safe to print in logs."""
    if not token or len(token) <= 8:
        return "***"
    return token[:4] + "..." + token[-4:]


def check_and_download_font():
    """
    Checks if a custom font exists.
    If not, it automatically downloads a premium Google Font to ensure beautiful typography.
    """
    font_path = os.path.join("assets", "fonts", "font.ttf")
    if not os.path.exists(font_path):
        print("[!] Font not found in assets/fonts/font.ttf.")
        try:
            print("[*] Attempting to download premium 'Roboto-Bold.ttf' from Google Fonts repository...")
            url = "https://raw.githubusercontent.com/googlefonts/roboto/main/src/hinted/Roboto-Bold.ttf"
            response = requests.get(url, timeout=15)
            if response.status_code == 200:
                os.makedirs(os.path.dirname(font_path), exist_ok=True)
                with open(font_path, "wb") as f:
                    f.write(response.content)
                print("[+] Successfully downloaded premium font to assets/fonts/font.ttf!")
            else:
                print(f"[-] Failed to download font (HTTP status code {response.status_code}). Using system fallback.")
        except Exception as e:
            print(f"[-] Could not download font due to error: {e}")
            print("[*] Falling back to default system/PIL font.")


def load_font(font_path, font_size):
    """Loads a TTF font, falling back to PIL default font if not available."""
    if not os.path.exists(font_path):
        return ImageFont.load_default()
    try:
        return ImageFont.truetype(font_path, font_size)
    except Exception as e:
        print(f"[-] Error loading custom font at size {font_size}: {e}. Falling back to default.")
        return ImageFont.load_default()


def wrap_text(text, font, max_width, draw):
    """
    A robust paragraph-aware word-wrapping utility.
    Splits text by space and wraps it to fit within a given maximum pixel width.
    """
    paragraphs = text.split("\n")
    lines = []
    for paragraph in paragraphs:
        if not paragraph.strip():
            lines.append("")
            continue
        words = paragraph.split(" ")
        current_line = []
        for word in words:
            current_line.append(word)
            line_str = " ".join(current_line)
            try:
                if hasattr(draw, "textbbox"):
                    bbox = draw.textbbox((0, 0), line_str, font=font)
                    width = bbox[2] - bbox[0]
                else:
                    # Deprecated fallback for older PIL versions
                    width, _ = draw.textsize(line_str, font=font)
            except Exception:
                # Character count approximation fallback
                width = len(line_str) * (font.size * 0.6 if hasattr(font, "size") else 12)
                
            if width > max_width:
                if len(current_line) > 1:
                    current_line.pop()
                    lines.append(" ".join(current_line))
                    current_line = [word]
                else:
                    # If a single word exceeds bounds, force draw it on its own line
                    lines.append(" ".join(current_line))
                    current_line = []
        if current_line:
            lines.append(" ".join(current_line))
    return lines
