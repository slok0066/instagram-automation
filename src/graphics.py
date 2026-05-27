# graphics.py
"""
Pillow graphics engine for polished vertical quiz videos.
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
        return (58, 139, 213, 255)
    if "java" in lang:
        return (231, 111, 45, 255)
    if "c++" in lang or "cpp" in lang:
        return (51, 127, 210, 255)
    return (0, 229, 255, 255)


def _draw_readability_scrim(draw):
    for y in range(0, CANVAS_H, 4):
        top_strength = max(0, 150 - int(y * 0.22))
        bottom_strength = max(0, int((y - 980) * 0.16))
        alpha = min(185, max(62, top_strength, bottom_strength))
        draw.rectangle([(0, y), (CANVAS_W, y + 4)], fill=(4, 6, 12, alpha))


def _draw_panel(draw, rect, radius=28, fill=(12, 16, 26, 222), outline=(255, 255, 255, 34), width=1):
    x1, y1, x2, y2 = rect
    _rounded(draw, (x1 + 8, y1 + 14, x2 + 8, y2 + 14), radius, (0, 0, 0, 86))
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
        height = 60 + len(lines) * line_h + 22
        if height <= max_height:
            return font, lines, height, line_h
    font = load_font(font_path, min_size)
    line_h = _line_height(draw, font) + 8
    max_lines = max(4, int((max_height - 82) / line_h))
    lines = _prepare_code_lines(code, font, max_width, draw, max_lines)
    height = min(max_height, 60 + len(lines) * line_h + 22)
    return font, lines, height, line_h


def _draw_header(draw, question_data, font_path, lang_color):
    question_id = int(question_data.get("id", 1))
    language = question_data.get("language", "Coding")

    font_meta = load_font(font_path, 25)
    font_title = load_font(font_path, 72)
    font_subtitle = load_font(font_path, 28)

    pill = (MARGIN_X, 72, MARGIN_X + 220, 124)
    _rounded(draw, pill, 18, lang_color)
    _center_text(draw, pill, f"PART {question_id:03d}", font_meta, (255, 255, 255, 255))

    draw.text((MARGIN_X, 150), f"{language} Quiz", font=font_title, fill=(255, 255, 255, 255))
    draw.text((MARGIN_X, 224), "Read the code. Pick the output.", font=font_subtitle, fill=(196, 203, 218, 235))


def _draw_code_box(draw, rect, code_lines, font, line_h, lang_color):
    x1, y1, x2, y2 = rect
    _rounded(draw, rect, 22, (7, 10, 18, 244), (255, 255, 255, 34), 1)
    _rounded(draw, (x1, y1, x2, y1 + 52), 22, (18, 23, 35, 255))
    draw.rectangle((x1, y1 + 30, x2, y1 + 52), fill=(18, 23, 35, 255))

    dot_y = y1 + 26
    for index, color in enumerate([(255, 95, 86, 255), (255, 189, 46, 255), (39, 201, 63, 255)]):
        cx = x1 + 28 + index * 24
        draw.ellipse((cx - 6, dot_y - 6, cx + 6, dot_y + 6), fill=color)

    label_font = load_font(os.path.join("assets", "fonts", "font.ttf"), 21)
    draw.text((x2 - 154, y1 + 13), "SNIPPET", font=label_font, fill=(137, 148, 170, 220))
    draw.rectangle((x1, y1 + 52, x2, y1 + 56), fill=lang_color)

    code_x = x1 + 28
    code_y = y1 + 76
    for line in code_lines:
        draw.text((code_x, code_y), line, font=font, fill=(235, 239, 248, 255))
        code_y += line_h


def _draw_options(draw, options, font_path, lang_color, option_y):
    option_letters = ["A", "B", "C", "D"]
    option_x1 = MARGIN_X
    option_x2 = CANVAS_W - MARGIN_X
    option_h = 134
    option_gap = 28
    text_left = option_x1 + 124
    text_right = option_x2 - 32

    for i, option in enumerate(options[:4]):
        y1 = option_y + i * (option_h + option_gap)
        y2 = y1 + option_h
        fill = (13, 17, 28, 232)
        outline = (255, 255, 255, 42)
        _draw_panel(draw, (option_x1, y1, option_x2, y2), radius=24, fill=fill, outline=outline)

        letter_rect = (option_x1 + 28, y1 + 34, option_x1 + 86, y1 + 92)
        _rounded(draw, letter_rect, 17, lang_color, None, 1)
        letter_font = load_font(font_path, 34)
        _center_text(draw, letter_rect, option_letters[i], letter_font, (255, 255, 255, 255))

        max_width = text_right - text_left
        option_font, lines = _fit_wrapped_font(option, font_path, draw, max_width, 33, 24, 2)
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
    lang_color = _language_color(language)
    _draw_header(draw, question_data, font_path, lang_color)

    panel_x1 = MARGIN_X
    panel_x2 = CANVAS_W - MARGIN_X
    panel_y1 = 310
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
    _draw_panel(draw, (panel_x1, panel_y1, panel_x2, panel_y2), radius=30)

    accent_rect = (panel_x1, panel_y1, panel_x1 + 10, panel_y2)
    draw.rectangle(accent_rect, fill=lang_color)

    y = panel_y1 + 48
    for line in q_lines:
        draw.text((inner_x1, y), line, font=q_font, fill=(255, 255, 255, 255))
        y += q_line_h

    y += 22
    _draw_code_box(draw, (inner_x1, y, inner_x2, y + code_h), code_lines, code_font, code_line_h, lang_color)

    option_start_y = max(panel_y2 + 54, 940)
    option_start_y = min(option_start_y, 1134)
    _draw_options(draw, question_data.get("options", []), font_path, lang_color, option_start_y)

    footer_font = load_font(font_path, 25)
    footer = "Comment A, B, C, or D"
    width, _, _ = _text_size(draw, footer, footer_font)
    draw.text(((CANVAS_W - width) / 2, 1814), footer, font=footer_font, fill=(205, 212, 228, 230))

    # 11. Draw Watermark Cover Icon to hide Gemini logo (centered over x=935, y=1773)
    cover_path = os.path.join("assets", "watermark_cover.png")
    if os.path.exists(cover_path):
        try:
            cover_img = Image.open(cover_path).convert("RGBA")
            cover_size = 140  # Rescaled to safely cover the watermark with a larger neat border
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
