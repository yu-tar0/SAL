#!/usr/bin/env python3
"""Render a simple HTML preview for an image-color-theme JSON file."""
import argparse
import json


TEMPLATE = """<!DOCTYPE html>
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("theme")
    parser.add_argument("--out", default="preview.html")
    args = parser.parse_args()

    with open(args.theme, encoding="utf-8") as f:
        data = json.load(f)
    colors = data["colors"]
    swatches = ""
    for key, value in colors.items():
        swatches += (
            f'<div><div class="chip" style="background:{value}"></div>'
            f'<div class="label">{key}<br>{value}</div></div>'
        )
    html = TEMPLATE.format(
        name=data.get("name", "Theme"),
        description=data.get("description", ""),
        swatches=swatches,
        **colors,
    )
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"wrote: {args.out}")


if __name__ == "__main__":
    main()
