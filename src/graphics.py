# graphics.py
"""
Pillow graphics engine for ultra-polished vertical quiz videos.
"""

import os
from PIL import Image, ImageDraw

import config
from utils import load_font, wrap_text


CANVAS_W = 1080
CANVAS_H = 1920
MARGIN_X = 64


def _text_size(draw, text, font):
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0], bbox[3] - bbox[1], bbox[1]
    except Exception:
        width, height = draw.textsize(text, font=font)
        return width, height, 0


def _line_height(draw, font):
    _, height, _ = _text_size(draw, "Ag", font)
    return max(height, getattr(font, "size", 24))


def _rounded(draw, rect, radius, fill, outline=None, width=1):
    if hasattr(draw, "rounded_rectangle"):
        draw.rounded_rectangle(rect, radius=radius, fill=fill, outline=outline, width=width)
    else:
        draw.rectangle(rect, fill=fill, outline=outline, width=width)


def _center_text(draw, rect, text, font, fill):
    x1, y1, x2, y2 = rect
    width, height, offset_y = _text_size(draw, text, font)
    x = x1 + (x2 - x1 - width) / 2
    y = y1 + (y2 - y1 - height) / 2 - offset_y
    draw.text((x, y), text, font=font, fill=fill)


def _language_color(language):
    lang = language.lower()
    if "python" in lang:
        return (0, 210, 255, 255), (45, 150, 235, 255)       # Electric Cyan & Python Blue
    if "java" in lang:
        return (255, 128, 40, 255), (235, 90, 30, 255)       # Vibrant Flame Orange
    if "c++" in lang or "cpp" in lang:
        return (110, 145, 255, 255), (55, 120, 240, 255)    # Neon Indigo Blue
    return (0, 230, 255, 255), (0, 170, 225, 255)


def _get_filename_for_lang(language):
    lang = language.lower()
    if "python" in lang:
        return "main.py"
    if "java" in lang:
        return "Main.java"
    if "c++" in lang or "cpp" in lang:
        return "main.cpp"
    return "solution.code"


def _draw_readability_scrim(draw):
    for y in range(0, CANVAS_H, 4):
        top_strength = max(0, 160 - int(y * 0.24))
        bottom_strength = max(0, int((y - 960) * 0.18))
        alpha = min(195, max(68, top_strength, bottom_strength))
        draw.rectangle([(0, y), (CANVAS_W, y + 4)], fill=(3, 5, 10, alpha))


def _draw_panel(draw, rect, radius=28, fill=(13, 18, 30, 238), outline=(255, 255, 255, 45), width=2):
    x1, y1, x2, y2 = rect
    # Drop shadow
    _rounded(draw, (x1 + 6, y1 + 12, x2 + 6, y2 + 12), radius, (0, 0, 0, 95))
    # Main panel card
    _rounded(draw, rect, radius, fill, outline, width)


def _fit_wrapped_font(text, font_path, draw, max_width, start_size, min_size, max_lines):
    for size in range(start_size, min_size - 1, -1):
        font = load_font(font_path, size)
        lines = wrap_text(text, font, max_width, draw)
        if len(lines) <= max_lines:
            return font, lines
    font = load_font(font_path, min_size)
    lines = wrap_text(text, font, max_width, draw)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        if lines:
            lines[-1] = lines[-1].rstrip(". ") + "..."
    return font, lines


def _wrap_code_line(line, font, max_width, draw):
    if not line:
        return [""]

    indent = line[: len(line) - len(line.lstrip(" "))]
    words = line.split(" ")
    lines = []
    current = ""

    def fits(value):
        return _text_size(draw, value, font)[0] <= max_width

    for word in words:
        candidate = word if not current else f"{current} {word}"
        if fits(candidate):
            current = candidate
            continue

        if current:
            lines.append(current)
            current = indent + "  " + word if lines else word
            if fits(current):
                continue

        chunk = ""
        prefix = indent + "  " if lines else ""
        for ch in word:
            candidate = prefix + chunk + ch
            if fits(candidate):
                chunk += ch
            else:
                if chunk:
                    lines.append(prefix + chunk)
                chunk = ch
                prefix = indent + "  "
        current = prefix + chunk if chunk else ""

    if current:
        lines.append(current)
    return lines


def _prepare_code_lines(code, font, max_width, draw, max_lines):
    rendered = []
    for raw_line in code.split("\n"):
        rendered.extend(_wrap_code_line(raw_line.replace("\t", "    "), font, max_width, draw))
    if len(rendered) > max_lines:
        rendered = rendered[: max_lines - 1] + ["..."]
    return rendered


def _fit_code(font_path, code, draw, max_width, max_height, start_size=38, min_size=28):
    for size in range(start_size, min_size - 1, -1):
        font = load_font(font_path, size)
        line_h = _line_height(draw, font) + 10
        max_lines = max(4, int((max_height - 82) / line_h))
        lines = _prepare_code_lines(code, font, max_width, draw, max_lines)
        height = 64 + len(lines) * line_h + 24
        if height <= max_height:
            return font, lines, height, line_h
    font = load_font(font_path, min_size)
    line_h = _line_height(draw, font) + 8
    max_lines = max(4, int((max_height - 82) / line_h))
    lines = _prepare_code_lines(code, font, max_width, draw, max_lines)
    height = min(max_height, 64 + len(lines) * line_h + 24)
    return font, lines, height, line_h


def _draw_header(draw, question_data, font_path, primary_color, secondary_color):
    question_id = int(question_data.get("id", 1))
    language = question_data.get("language", "Coding")

    font_meta = load_font(font_path, 25)
    font_title = load_font(font_path, 72)
    font_subtitle = load_font(font_path, 28)

    # PART Pill Capsule with border glow
    pill = (MARGIN_X, 72, MARGIN_X + 220, 126)
    _rounded(draw, pill, 20, secondary_color, outline=primary_color, width=2)
    _center_text(draw, pill, f"PART {question_id:03d}", font_meta, (255, 255, 255, 255))

    # Language Quiz Title
    draw.text((MARGIN_X, 152), f"{language} Quiz", font=font_title, fill=(255, 255, 255, 255))
    draw.text((MARGIN_X, 228), "⚡ Read the code. Pick the output.", font=font_subtitle, fill=(200, 210, 230, 240))


def _draw_code_box(draw, rect, code_lines, font, line_h, primary_color, filename):
    x1, y1, x2, y2 = rect
    # IDE Outer Window container
    _rounded(draw, rect, 24, (6, 9, 17, 250), (255, 255, 255, 40), 1)
    
    # IDE Header Bar
    header_h = 56
    _rounded(draw, (x1, y1, x2, y1 + header_h), 24, (16, 21, 33, 255))
    draw.rectangle((x1, y1 + 32, x2, y1 + header_h), fill=(16, 21, 33, 255))

    # macOS Window Dots (Red, Yellow, Green)
    dot_y = y1 + 28
    for index, color in enumerate([(255, 95, 86, 255), (255, 189, 46, 255), (39, 201, 63, 255)]):
        cx = x1 + 28 + index * 24
        draw.ellipse((cx - 6, dot_y - 6, cx + 6, dot_y + 6), fill=color)

    # Code File Tab Name (e.g. main.py)
    tab_font = load_font(os.path.join("assets", "fonts", "font.ttf"), 22)
    tab_rect = (x1 + 115, y1 + 10, x1 + 260, y1 + 46)
    _rounded(draw, tab_rect, 10, (26, 33, 50, 255), outline=primary_color, width=1)
    _center_text(draw, tab_rect, filename, tab_font, (220, 230, 250, 255))

    # Accent Neon separator line
    draw.rectangle((x1, y1 + header_h, x2, y1 + header_h + 3), fill=primary_color)

    # Code Lines
    code_x = x1 + 32
    code_y = y1 + header_h + 24
    for line in code_lines:
        draw.text((code_x, code_y), line, font=font, fill=(240, 244, 255, 255))
        code_y += line_h


def _draw_options(draw, options, font_path, primary_color, secondary_color, option_y):
    option_letters = ["A", "B", "C", "D"]
    option_x1 = MARGIN_X
    option_x2 = CANVAS_W - MARGIN_X
    option_h = 136
    option_gap = 26
    text_left = option_x1 + 128
    text_right = option_x2 - 32

    for i, option in enumerate(options[:4]):
        y1 = option_y + i * (option_h + option_gap)
        y2 = y1 + option_h
        fill = (14, 19, 32, 238)
        outline = (255, 255, 255, 48)
        _draw_panel(draw, (option_x1, y1, option_x2, y2), radius=26, fill=fill, outline=outline, width=1)

        # Option Letter Badge (A, B, C, D)
        letter_rect = (option_x1 + 26, y1 + 32, option_x1 + 92, y1 + 98)
        _rounded(draw, letter_rect, 18, secondary_color, outline=primary_color, width=2)
        letter_font = load_font(font_path, 36)
        _center_text(draw, letter_rect, option_letters[i], letter_font, (255, 255, 255, 255))

        # Option Text
        max_width = text_right - text_left
        option_font, lines = _fit_wrapped_font(option, font_path, draw, max_width, 34, 24, 2)
        line_h = _line_height(draw, option_font) + 8
        block_h = len(lines) * line_h - 8
        text_y = y1 + (option_h - block_h) / 2
        for line in lines:
            draw.text((text_left, text_y), line, font=option_font, fill=(248, 250, 255, 255))
            text_y += line_h


def generate_graphics(question_data, output_img_path, transparent_bg=False):
    """
    Render a 1080x1920 quiz frame with a measured card layout for reels.
    """
    font_path = os.path.join("assets", "fonts", "font.ttf")

    if transparent_bg:
        base_img = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    else:
        bg_path = os.path.join("assets", "background.png")
        if os.path.exists(bg_path):
            base_img = Image.open(bg_path).convert("RGBA")
            if base_img.size != (CANVAS_W, CANVAS_H):
                base_img = base_img.resize((CANVAS_W, CANVAS_H), Image.Resampling.LANCZOS)
        else:
            base_img = Image.new("RGBA", (CANVAS_W, CANVAS_H), (7, 10, 18, 255))

    overlay = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    _draw_readability_scrim(draw)

    language = question_data.get("language", "Coding")
    primary_color, secondary_color = _language_color(language)
    _draw_header(draw, question_data, font_path, primary_color, secondary_color)

    panel_x1 = MARGIN_X
    panel_x2 = CANVAS_W - MARGIN_X
    panel_y1 = 312
    panel_y2 = 1068
    inner_x1 = panel_x1 + 42
    inner_x2 = panel_x2 - 42
    inner_w = inner_x2 - inner_x1

    question = question_data.get("question", "")
    q_font, q_lines = _fit_wrapped_font(question, font_path, draw, inner_w, 42, 32, 3)
    q_line_h = _line_height(draw, q_font) + 12

    code = question_data.get("code", "")
    code_font, code_lines, code_h, code_line_h = _fit_code(
        font_path,
        code,
        draw,
        inner_w - 56,
        max_height=520,
    )

    q_block_h = len(q_lines) * q_line_h - 12
    content_h = 54 + q_block_h + 34 + code_h + 44
    panel_y2 = min(1068, panel_y1 + content_h)
    
    # Main Question Card Panel with glowing accent border
    _draw_panel(draw, (panel_x1, panel_y1, panel_x2, panel_y2), radius=30, outline=(255, 255, 255, 55), width=2)

    # Accent Neon Bar on left
    accent_rect = (panel_x1, panel_y1, panel_x1 + 10, panel_y2)
    draw.rectangle(accent_rect, fill=primary_color)

    y = panel_y1 + 48
    for line in q_lines:
        draw.text((inner_x1, y), line, font=q_font, fill=(255, 255, 255, 255))
        y += q_line_h

    y += 22
    filename = _get_filename_for_lang(language)
    _draw_code_box(draw, (inner_x1, y, inner_x2, y + code_h), code_lines, code_font, code_line_h, primary_color, filename)

    option_start_y = max(panel_y2 + 50, 940)
    option_start_y = min(option_start_y, 1134)
    _draw_options(draw, question_data.get("options", []), font_path, primary_color, secondary_color, option_start_y)

    # Floating CTA Pill Banner at bottom
    cta_rect = (MARGIN_X + 110, 1800, CANVAS_W - MARGIN_X - 110, 1860)
    _rounded(draw, cta_rect, 20, (14, 20, 34, 240), outline=primary_color, width=2)
    footer_font = load_font(font_path, 25)
    _center_text(draw, cta_rect, "💬 COMMENT YOUR ANSWER (A, B, C, D)", footer_font, (255, 255, 255, 255))

    # Watermark Cover Icon to hide Gemini logo (centered over x=935, y=1773)
    cover_path = os.path.join("assets", "watermark_cover.png")
    if os.path.exists(cover_path):
        try:
            cover_img = Image.open(cover_path).convert("RGBA")
            cover_size = 140
            cover_img = cover_img.resize((cover_size, cover_size), Image.Resampling.LANCZOS)
            x_pos = 935 - (cover_size // 2)
            y_pos = 1773 - (cover_size // 2)
            overlay.paste(cover_img, (x_pos, y_pos), cover_img)
            print("[+] Successfully overlayed watermark cover at bottom-right corner.")
        except Exception as e:
            print(f"[!] Warning: Failed to paste watermark cover: {e}")

    final_img = Image.alpha_composite(base_img, overlay)
    if not transparent_bg:
        final_img = final_img.convert("RGB")
    final_img.save(output_img_path, "PNG")
