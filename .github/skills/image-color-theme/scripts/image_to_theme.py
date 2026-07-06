#!/usr/bin/env python3
"""Generate a 9-color HTML Artifact theme from an image."""
import argparse
import colorsys
import json
import re
import sys
from collections import Counter
from datetime import date

try:
    from PIL import Image
except ImportError:
    sys.exit("Pillow is required: pip install pillow")


PREVIEW_TEMPLATE = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<title>{name} preview</title>
<style>
:root {{
  --page-bg: {page_bg};
  --paper-bg: {paper_bg};
  --ink: {ink};
  --muted: {muted};
  --accent: {accent};
  --line: {line};
  --soft: {soft};
  --warn: {warn};
  --warn-bg: {warn_bg};
}}
body {{
  margin: 0;
  background: var(--page-bg);
  color: var(--ink);
  padding: 32px;
  font-family: system-ui, "Noto Sans JP", sans-serif;
  line-height: 1.7;
}}
.paper {{
  background: var(--paper-bg);
  max-width: 760px;
  margin: 0 auto;
  padding: 40px 48px;
  border: 1px solid var(--line);
  border-radius: 8px;
}}
h1 {{
  font-size: 30px;
  margin: 0 0 6px;
  padding-bottom: 12px;
  border-bottom: 4px solid var(--accent);
}}
h2 {{ color: var(--accent); font-size: 20px; margin: 28px 0 8px; }}
p, li {{ color: var(--muted); }}
a {{ color: var(--accent); }}
.soft {{ background: var(--soft); border-left: 6px solid var(--accent); padding: 14px 18px; margin: 16px 0; }}
.warn {{ background: var(--warn-bg); border-left: 6px solid var(--warn); padding: 14px 18px; margin: 16px 0; }}
table {{ width: 100%; border-collapse: collapse; margin: 18px 0; }}
th {{ background: var(--accent); color: var(--paper-bg); text-align: left; padding: 9px 12px; }}
td {{ border-bottom: 1px solid var(--line); padding: 9px 12px; }}
.swatches {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(110px, 1fr)); gap: 10px; margin-top: 20px; }}
.chip {{ height: 42px; border: 1px solid var(--line); border-radius: 6px; }}
.label {{ color: var(--muted); font-size: 12px; margin-top: 4px; }}
</style>
</head>
<body>
<main class="paper">
<h1>{name}</h1>
<p>{description}</p>
<h2>本文サンプル</h2>
<p>本文は ink と muted を使い、<a href="#">リンクや強調</a>には accent を使います。</p>
<div class="soft">通常の強調ボックスです。</div>
<div class="warn">注意喚起のボックスです。</div>
<table><tr><th>項目</th><th>値</th></tr><tr><td>Alpha</td><td>123</td></tr><tr><td>Beta</td><td>456</td></tr></table>
<div class="swatches">{swatches}</div>
</main>
</body>
</html>
"""


def rgb_to_hex(r, g, b):
    return "#{:02X}{:02X}{:02X}".format(int(round(r)), int(round(g)), int(round(b)))


def hex_to_rgb(value):
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def hls_hex(h, l, s):
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    return rgb_to_hex(r * 255, g * 255, b * 255)


def hls_of(rgb):
    r, g, b = [x / 255 for x in rgb]
    return colorsys.rgb_to_hls(r, g, b)


def rel_luminance(rgb):
    def channel(c):
        c = c / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = [channel(x) for x in rgb]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(rgb1, rgb2):
    l1, l2 = rel_luminance(rgb1), rel_luminance(rgb2)
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)


def extract_palette(path, count=8):
    image = Image.open(path).convert("RGB")
    image.thumbnail((900, 900))
    quantized = image.convert("P", palette=Image.ADAPTIVE, colors=count).convert("RGB")
    counter = Counter(quantized.getdata())
    total = sum(counter.values())
    palette = []
    for rgb, pixel_count in counter.most_common():
        h, l, s = hls_of(rgb)
        palette.append(
            {
                "rgb": rgb,
                "hex": rgb_to_hex(*rgb),
                "share": pixel_count / total,
                "hue": h,
                "light": l,
                "sat": s,
            }
        )
    return palette


def pick_accent(palette):
    chromatic = [c for c in palette if c["sat"] > 0.15 and 0.10 < c["light"] < 0.90]
    if chromatic:
        return max(chromatic, key=lambda c: c["share"] * (0.3 + c["sat"]))
    neutral_marks = [c for c in palette if c["light"] < 0.88]
    pool = neutral_marks if neutral_marks else palette
    return max(pool, key=lambda c: c["share"] * (1.0 - c["light"]))


def has_near_white(palette, threshold=0.92):
    whites = [c for c in palette if c["light"] >= threshold and c["share"] > 0.005]
    return max(whites, key=lambda c: c["share"]) if whites else None


def build_colors(palette, accessible=False):
    accent = pick_accent(palette)
    h = accent["hue"]
    accent_hex = accent["hex"]

    white = has_near_white(palette)
    if white is None or white["light"] >= 0.95:
        paper_bg = "#FFFFFF"
    else:
        paper_bg = white["hex"]
    paper_rgb = hex_to_rgb(paper_bg)

    if accent["sat"] <= 0.15:
        return (
            {
                "page_bg": "#F5F6F8",
                "paper_bg": paper_bg,
                "ink": "#171717",
                "muted": "#5F6368",
                "accent": accent_hex,
                "line": "#DADCE0",
                "soft": "#F3F4F6",
                "warn": "#8A5A00",
                "warn_bg": "#FFF4D8",
            },
            accent,
        )

    if accessible:
        l, s = accent["light"], accent["sat"]
        while contrast(hex_to_rgb(hls_hex(h, l, s)), paper_rgb) < 4.5 and l > 0.05:
            l -= 0.02
        accent_hex = hls_hex(h, l, s)

    ink_l, ink_s = 0.16, 0.30
    while contrast(hex_to_rgb(hls_hex(h, ink_l, ink_s)), paper_rgb) < 7.0 and ink_l > 0.02:
        ink_l -= 0.01

    return (
        {
            "page_bg": hls_hex(h, 0.970, 0.18),
            "paper_bg": paper_bg,
            "ink": hls_hex(h, ink_l, ink_s),
            "muted": hls_hex(h, 0.430, 0.14),
            "accent": accent_hex,
            "line": hls_hex(h, 0.870, 0.22),
            "soft": hls_hex(h, 0.945, 0.42),
            "warn": "#8A5A00",
            "warn_bg": "#FFF4D8",
        },
        accent,
    )


def slugify(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "theme"


def render_preview(theme):
    colors = theme["colors"]
    swatches = ""
    for key, value in colors.items():
        swatches += (
            f'<div><div class="chip" style="background:{value}"></div>'
            f'<div class="label">{key}<br>{value}</div></div>'
        )
    return PREVIEW_TEMPLATE.format(
        name=theme.get("name", "Theme"),
        description=theme.get("description", ""),
        swatches=swatches,
        **colors,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("image")
    parser.add_argument("--name", default="Untitled Theme")
    parser.add_argument("--id", default=None)
    parser.add_argument("--description", default=None)
    parser.add_argument("--accessible", action="store_true")
    parser.add_argument("--out", default=None)
    parser.add_argument("--preview-out", default=None)
    args = parser.parse_args()

    theme_id = args.id or f"{slugify(args.name)}-v1"
    description = args.description or f"{args.name} theme generated faithfully from image colors."
    today = date.today().isoformat()

    palette = extract_palette(args.image)
    colors, accent = build_colors(palette, accessible=args.accessible)
    result = {
        "id": theme_id,
        "name": args.name,
        "version": 1,
        "status": "active",
        "created": today,
        "updated": today,
        "description": description,
        "colors": colors,
    }

    output = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(output + "\n")
        print(f"wrote: {args.out}")
    else:
        print(output)

    if args.preview_out:
        with open(args.preview_out, "w", encoding="utf-8") as f:
            f.write(render_preview(result))
        print(f"wrote: {args.preview_out}")

    paper_rgb = hex_to_rgb(colors["paper_bg"])
    print("\n--- Extracted palette ---", file=sys.stderr)
    for color in palette[:6]:
        print(
            f"  {color['hex']} share={color['share'] * 100:5.1f}% sat={color['sat']:.2f}",
            file=sys.stderr,
        )
    print("--- Notes ---", file=sys.stderr)
    print(f"  accent source: {accent['hex']} share={accent['share'] * 100:.1f}%", file=sys.stderr)
    print(f"  accent contrast/paper: {contrast(hex_to_rgb(colors['accent']), paper_rgb):.2f}", file=sys.stderr)
    print(f"  ink contrast/paper:    {contrast(hex_to_rgb(colors['ink']), paper_rgb):.2f}", file=sys.stderr)


if __name__ == "__main__":
    main()
