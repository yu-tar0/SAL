from __future__ import annotations

import html
import json
from pathlib import Path

from build_loader_brand_toggle_artifact import (
    BRAND_LABELS,
    BRAND_ORDER,
    METRICS,
    ROOT,
    TODAY,
    THEME_METADATA,
    ModelRow,
    format_display_value,
    load_rows,
    parse_measure,
    render_switchable_text,
    series_sort_key,
)


ARTIFACT_ID = "2026-07-02-comparison-avant-bobcat-shared-bars"
ARTIFACT_DIR = ROOT / "artifacts" / ARTIFACT_ID
MARKDOWN_PATH = ARTIFACT_DIR / f"{ARTIFACT_ID}.md"
HTML_PATH = ARTIFACT_DIR / f"{ARTIFACT_ID}.web.html"

RANGE_CHART_PLOT_WIDTH = 1040
RANGE_CHART_UNIT_MARGIN = 60
RANGE_CHART_SVG_WIDTH = RANGE_CHART_PLOT_WIDTH + RANGE_CHART_UNIT_MARGIN

BRAND_STYLES = {
    "Avant Tecno": {"label": "AVANT", "fill": "#000000", "stroke": "#ffffff"},
    "Bobcat": {"label": "Bobcat", "fill": "#E69F00", "stroke": "#ffffff"},
    "Case": {"label": "Case", "fill": "#009E73", "stroke": "#ffffff"},
    "Gianni Ferrari": {"label": "Gianni Ferrari", "fill": "#D55E00", "stroke": "#ffffff"},
    "Tobroco-Giant / Giant": {"label": "Giant", "fill": "#9467BD", "stroke": "#ffffff"},
    "MultiOne": {"label": "MultiOne", "fill": "#0072B2", "stroke": "#ffffff"},
    "New Holland": {"label": "New Holland", "fill": "#56B4E9", "stroke": "#ffffff"},
    "Yanmar": {"label": "Yanmar", "fill": "#D62728", "stroke": "#ffffff"},
}

HISTOGRAM_STEPS = {
    "horsepower": 1,
    "lift_capacity": 100,
    "lift_height": 100,
    "telescopic_length": 100,
    "aux_flow": 1,
    "aux_pressure": 20,
    "max_breakout_force": 10,
    "max_tow_force": 10,
    "max_torque": 10,
    "max_speed": 1,
    "operating_weight": 100,
    "turning_radius_inner": 100,
    "turning_radius_outer": 100,
    "width": 200,
    "length": 100,
    "height": 200,
    "battery_capacity": 1,
}

HISTOGRAM_EXCLUDED_METRIC_IDS = {"telescopic_length"}


def brand_id(row: ModelRow) -> str:
    return BRAND_LABELS.get(row.manufacturer_name, row.manufacturer_name).lower().replace(" ", "-")


def brand_label(row: ModelRow) -> str:
    return BRAND_LABELS.get(row.manufacturer_name, row.manufacturer_name)


def horsepower_value(row: ModelRow) -> float | None:
    return parse_measure(row.horsepower, "hp")


def sort_brand_rows(rows: list[ModelRow]) -> list[ModelRow]:
    brand_order = {name: index for index, name in enumerate(BRAND_ORDER)}
    return sorted(
        rows,
        key=lambda row: (
            brand_order.get(row.manufacturer_name, 999),
            series_sort_key(row.series),
            row.sal_model,
        ),
    )


def build_markdown(rows: list[ModelRow], summaries: list[ModelRow]) -> str:
    comparison_rows = [row for row in rows if not row.is_series_summary]
    total_count = len(comparison_rows)
    avant_count = sum(1 for row in comparison_rows if row.manufacturer_name == "Avant Tecno")
    bobcat_count = sum(1 for row in comparison_rows if row.manufacturer_name == "Bobcat")

    max_lift = max(comparison_rows, key=lambda row: parse_measure(row.lift_capacity_kg, "kg") or -1)
    max_speed = max(comparison_rows, key=lambda row: parse_measure(row.max_speed_kmh, "km/h") or -1)
    max_lift_us = render_switchable_text(max_lift.lift_capacity_kg, "weight").split('data-us="', 1)[1].split('"', 1)[0] if max_lift.lift_capacity_kg else "-"
    max_speed_us = render_switchable_text(max_speed.max_speed_kmh, "speed").split('data-us="', 1)[1].split('"', 1)[0] if max_speed.max_speed_kmh else "-"

    lines = [
        "---",
        "title: マルチブランド ローダー比較 同一数値バー版",
        f"created: {TODAY}",
        f"updated: {TODAY}",
        "type: artifact",
        "status: current-db",
        "input:",
        "  - db/knowledge.duckdb",
        "  - table: loader_specification_import_rows",
        "outputs:",
        f"  - artifacts/{ARTIFACT_ID}/{MARKDOWN_PATH.name}",
        f"  - artifacts/{ARTIFACT_ID}/{HTML_PATH.name}",
        "purpose: 複数ブランドの個別型式を同じ数値バー上に重ねて比較できる Web HTML を作る",
        "---",
        "",
        "# マルチブランド ローダー比較 同一数値バー版",
        "",
        "共通 curated テーブル `loader_specification_import_rows` を入力元に、複数ブランドの個別型式を同一レンジバー上へ重ねて比較できる Web Artifact を作成した。ブランド色でマーカーを分け、表示オンオフで見比べられる。",
        "",
        "## 要約",
        "",
        f"- 比較対象の個別型式は合計 {total_count} 行。登録済みブランドを同一数値バー上で比較できる。",
        f"- 最大リフト容量は {brand_label(max_lift)} の {max_lift.sal_model} で、値は {max_lift.lift_capacity_kg}。",
        f"- 最高速度は {brand_label(max_speed)} の {max_speed.sal_model} で、値は {max_speed.max_speed_kmh}。",
        "- HTML では同一数値バー上に複数ブランドの型式を重ね、ブランドごとの表示オンオフと SI / US 切替を共通で使える。",
        "",
        "## Provenance",
        "",
        "- DuckDB: `db/knowledge.duckdb`",
        "- 参照テーブル: `loader_specification_import_rows`",
        "- 生成スクリプト: `scripts/build_loader_brand_overlay_artifact.py`",
        f"- 生成物: `{MARKDOWN_PATH.name}` / `{HTML_PATH.name}`",
    ]

    if summaries:
        lines.extend(
            [
                "",
                "## シリーズ要約行",
                "",
                "| ブランド | シリーズ行 | リフト容量 | リフト高 | 最高速度 | バッテリー容量 | 充電時間 |",
                "| --- | --- | --- | --- | --- | --- | --- |",
            ]
        )
        for row in summaries:
            lines.append(
                "| "
                + " | ".join(
                    [
                        brand_label(row),
                        row.sal_model or "-",
                        row.lift_capacity_kg or "-",
                        row.lift_height_mm or "-",
                        row.max_speed_kmh or "-",
                        row.battery_capacity or "-",
                        row.charge_time or "-",
                    ]
                )
                + " |"
            )

    lines.extend(
        [
            "",
            "## 未解決点",
            "",
            "- ブランドごとに埋まっている列の密度は異なる。",
            "- Bobcat の一部は容量列に複数条件の値が混在しており、比較上は記載文字列をそのまま残している。",
            "- 電動モデルやシリーズ要約は現状 AVANT 側に偏っている。",
        ]
    )
    return "\n".join(lines) + "\n"


def render_combined_range_svg(
    rows: list[ModelRow],
    metric_key: str,
    metric_unit: str,
    family: str | None,
    us_unit: str,
    extract_mode: str,
) -> str:
    values: list[tuple[ModelRow, float]] = []
    for row in rows:
        value = parse_measure(getattr(row, metric_key), metric_unit, extract_mode)
        if value is None:
            continue
        values.append((row, value))

    if not values:
        return '<div class="empty-chart">比較可能な値なし</div>'

    values.sort(key=lambda item: (item[1], brand_label(item[0]), item[0].sal_model))

    minimum = min(value for _, value in values)
    maximum = max(value for _, value in values)
    if minimum == maximum:
        maximum = minimum + 1

    chart_width = RANGE_CHART_PLOT_WIDTH
    svg_width = RANGE_CHART_SVG_WIDTH
    chart_height = 28 + len(values) * 24 + 48
    axis_y = 18 + len(values) * 24
    left_pad = 34
    right_pad = 24
    usable_width = chart_width - left_pad - right_pad

    def x_pos(value: float) -> float:
        return left_pad + (value - minimum) / (maximum - minimum) * usable_width

    tick_values = [minimum + (maximum - minimum) * step / 4 for step in range(5)]
    svg_parts = [
        f'<svg class="range-svg" viewBox="0 0 {svg_width} {chart_height}" role="img" aria-label="{html.escape(metric_key)} combined range chart">',
        f'<line x1="{left_pad}" y1="{axis_y}" x2="{chart_width - right_pad}" y2="{axis_y}" class="axis-line js-range-axis-line" />',
    ]

    for tick in tick_values:
        x = x_pos(tick)
        metric_label = format_display_value(tick, family, "metric", metric_unit, us_unit)
        us_label = format_display_value(tick, family, "us", metric_unit, us_unit)
        svg_parts.append(f'<line x1="{x:.1f}" y1="10" x2="{x:.1f}" y2="{axis_y}" class="axis-guide js-range-axis-guide" />')
        svg_parts.append(
            f'<text x="{x:.1f}" y="{axis_y + 18}" class="axis-label js-value-switch js-range-axis-label" '
            f'text-anchor="middle" data-metric="{html.escape(metric_label)}" '
            f'data-us="{html.escape(us_label)}">{html.escape(metric_label)}</text>'
        )

    svg_parts.append(
        f'<text x="{chart_width - right_pad + 8}" y="{axis_y + 4}" class="axis-unit js-unit-label js-range-axis-unit" '
        f'text-anchor="start" data-metric-unit="{html.escape(metric_unit)}" '
        f'data-us-unit="{html.escape(us_unit)}">{html.escape(metric_unit)}</text>'
    )

    label_nodes = []
    for index, (row, value) in enumerate(values):
        y = 18 + index * 24
        x = x_pos(value)
        style = BRAND_STYLES.get(row.manufacturer_name, {"label": brand_label(row), "fill": "#374151", "stroke": "#ffffff"})
        row_brand_id = brand_id(row)
        row_horsepower = horsepower_value(row)
        horsepower_attr = "" if row_horsepower is None else f' data-horsepower="{row_horsepower:.1f}"'
        svg_parts.append(
            f'<g class="js-brand-filter-target js-range-point" data-brand-id="{html.escape(row_brand_id)}" '
            f'data-point-x="{x:.1f}"{horsepower_attr}>'
        )
        svg_parts.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="7" fill="{style["fill"]}" stroke="{style["stroke"]}" stroke-width="2" />'
        )
        svg_parts.append("</g>")

        model_label = row.sal_model or row.label
        label_prefix = f"{brand_label(row)} / {model_label}"
        if row.is_electric:
            label_prefix = f"{label_prefix} / 電動"
        metric_marker = f"{label_prefix} / {format_display_value(value, family, 'metric', metric_unit, us_unit)}"
        us_marker = f"{label_prefix} / {format_display_value(value, family, 'us', metric_unit, us_unit)}"
        label_class = "range-point-label is-left" if x > chart_width * 0.72 else "range-point-label is-right"
        label_left = x / svg_width * 100
        label_top = y / chart_height * 100
        label_nodes.append(
            f'<div class="{label_class} js-brand-filter-target js-range-point-label" data-brand-id="{html.escape(row_brand_id)}" '
            f'data-label-side="{"left" if x > chart_width * 0.72 else "right"}" '
            f'data-point-x-percent="{label_left:.3f}"{horsepower_attr} style="left:{label_left:.3f}%; top:{label_top:.3f}%">'
            f'<span class="range-point-label-dot" style="background:{style["fill"]}; border-color:{style["stroke"]};"></span>'
            f'<span class="marker-label js-value-switch" data-metric="{html.escape(metric_marker)}" data-us="{html.escape(us_marker)}">{html.escape(metric_marker)}</span>'
            '</div>'
        )

    svg_parts.append("</svg>")

    return (
        f'<div class="range-chart-svg js-range-chart" style="height:{chart_height}px;" data-chart-width="{svg_width}" data-row-step="24" data-top-offset="18" data-bottom-pad="48" data-axis-label-offset="18">'
        f'{"".join(svg_parts)}'
        f'<div class="range-point-label-layer">{"".join(label_nodes)}</div>'
        '</div>'
    )


def render_row_attrs(row: ModelRow) -> str:
    horsepower = horsepower_value(row)
    horsepower_attr = "" if horsepower is None else f' data-horsepower="{horsepower:.1f}"'
    return f'class="js-brand-filter-target js-filter-target" data-brand-id="{html.escape(brand_id(row))}"{horsepower_attr}'


def render_combined_table(rows: list[ModelRow]) -> str:
    if not rows:
        return '<div class="empty-state">該当データなし</div>'

    body_rows = []
    for row in rows:
        body_rows.append(
            "<tr "
            + render_row_attrs(row)
            + ">"
            + "".join(
                [
                    f"<td>{html.escape(brand_label(row))}</td>",
                    f"<td>{html.escape(row.series or '-')}</td>",
                    f"<td>{html.escape(row.sal_model or '-')}</td>",
                    f"<td>{html.escape(row.powertrain_type or '-')}</td>",
                    f"<td>{render_switchable_text(row.lift_capacity_kg, 'weight')}</td>",
                    f"<td>{render_switchable_text(row.lift_height_mm, 'length')}</td>",
                    f"<td>{render_switchable_text(row.max_speed_kmh, 'speed')}</td>",
                    f"<td>{render_switchable_text(row.width_mm, 'length')}</td>",
                    f"<td>{render_switchable_text(row.operating_weight_kg, 'weight')}</td>",
                    f"<td>{html.escape(row.battery_capacity or '-')}</td>",
                ]
            )
            + "</tr>"
        )

    return (
        '<table class="data-table"><thead><tr>'
        '<th>ブランド</th><th>シリーズ</th><th>型式</th><th>動力</th><th>リフト容量</th><th>リフト高</th><th>最高速度</th><th>全幅</th><th>運転質量</th><th>バッテリー容量</th>'
        '</tr></thead><tbody>'
        + "".join(body_rows)
        + "</tbody></table>"
    )


def render_summary_table(rows: list[ModelRow]) -> str:
    if not rows:
        return '<div class="empty-state">シリーズ要約行なし</div>'

    body_rows = []
    for row in rows:
        body_rows.append(
            "<tr "
            + render_row_attrs(row)
            + ">"
            + "".join(
                [
                    f"<td>{html.escape(brand_label(row))}</td>",
                    f"<td>{html.escape(row.sal_model or '-')}</td>",
                    f"<td>{render_switchable_text(row.lift_capacity_kg, 'weight')}</td>",
                    f"<td>{render_switchable_text(row.lift_height_mm, 'length')}</td>",
                    f"<td>{render_switchable_text(row.max_speed_kmh, 'speed')}</td>",
                    f"<td>{html.escape(row.battery_capacity or '-')}</td>",
                    f"<td>{html.escape(row.charge_time or '-')}</td>",
                ]
            )
            + "</tr>"
        )

    return (
        '<table class="data-table"><thead><tr>'
        '<th>ブランド</th><th>シリーズ行</th><th>リフト容量</th><th>リフト高</th><th>最高速度</th><th>バッテリー容量</th><th>充電時間</th>'
        '</tr></thead><tbody>'
        + "".join(body_rows)
        + "</tbody></table>"
    )


def build_html(rows: list[ModelRow], summaries: list[ModelRow]) -> str:
    comparison_rows = [row for row in rows if not row.is_series_summary]
    comparison_rows = sort_brand_rows(comparison_rows)
    summaries = sort_brand_rows(summaries)
    brand_palette = [
        {
            "manufacturer": name,
            "brandId": BRAND_LABELS[name].lower().replace(" ", "-"),
            "label": BRAND_STYLES[name]["label"],
            "fill": BRAND_STYLES[name]["fill"],
            "stroke": BRAND_STYLES[name]["stroke"],
        }
        for name in BRAND_ORDER
        if name in BRAND_STYLES and any(row.manufacturer_name == name for row in rows)
    ]
    brand_css_vars = "\n".join(
        f'            --brand-{item["brandId"]}-fill: {item["fill"]};\n'
        f'            --brand-{item["brandId"]}-stroke: {item["stroke"]};'
        for item in brand_palette
    )

    metric_selector_items = "".join(
        f'<label class="metric-option"><input type="checkbox" class="metric-toggle-input" data-target-metric="{html.escape(metric["id"])}" checked> <span>{html.escape(metric["label"])} <small>({html.escape(metric["metric_unit"])} / {html.escape(metric["us_unit"])})</small></span></label>'
        for metric in METRICS
    )
    horsepower_values = [horsepower_value(row) for row in comparison_rows if horsepower_value(row) is not None]
    horsepower_min = int(min(horsepower_values)) if horsepower_values else 0
    horsepower_max = int(max(horsepower_values)) if horsepower_values else 0
    brand_filter_items = "".join(
        f'<label class="brand-filter-option"><input type="checkbox" class="brand-filter-input" data-brand-id="{BRAND_LABELS[name].lower().replace(" ", "-")}" checked> <span>{html.escape(BRAND_LABELS[name])}</span></label>'
        for name in BRAND_ORDER
        if any(row.manufacturer_name == name for row in rows)
    )

    legend_items = "".join(
        f'<div class="legend-item"><span class="swatch" style="background:var(--brand-{item["brandId"]}-fill); border:2px solid var(--brand-{item["brandId"]}-stroke);"></span><span>{html.escape(item["label"])} マーカー</span></div>'
        for item in brand_palette
    )

    metrics_html = []
    for metric in METRICS:
        metrics_html.append(
            (
                f'<div class="metric-card metric-row" data-metric-id="{html.escape(metric["id"])}">'
                '<div class="metric-card-head">'
                f'<span class="metric-card-title metric-name">{html.escape(metric["label"])}</span>'
                f'<button type="button" class="download-button js-download-chart" data-download-target="{html.escape(metric["id"])}">画像保存</button>'
                '</div>'
                f'<span class="metric-card-subtitle">{html.escape(metric["metric_unit"])} / {html.escape(metric["us_unit"])} で表示。型式ごとの位置を横棒で比較できる。</span>'
                f'<div class="chart-panel">{render_combined_range_svg(comparison_rows, metric["key"], metric["parse_unit"], metric["family"], metric["us_unit"], metric["extract_mode"])}</div>'
                '</div>'
            )
        )

    kpi_rows = [
        {
            "brandId": brand_id(row),
            "brandLabel": brand_label(row),
            "model": row.sal_model,
            "isElectric": row.is_electric,
            "horsepower": horsepower_value(row),
        }
        for row in comparison_rows
    ]

    histogram_metrics = [metric for metric in METRICS if metric["id"] not in HISTOGRAM_EXCLUDED_METRIC_IDS]

    histogram_rows = [
        {
            "brandId": brand_id(row),
            "brandLabel": brand_label(row),
            "model": row.sal_model,
            "isElectric": row.is_electric,
            "metricValues": {
                metric["id"]: parse_measure(getattr(row, metric["key"]), metric["parse_unit"], metric["extract_mode"])
                for metric in histogram_metrics
            },
        }
        for row in comparison_rows
    ]

    metric_configs = {
        metric["id"]: {
            "id": metric["id"],
            "label": metric["label"],
            "metric_unit": metric["metric_unit"],
            "us_unit": metric["us_unit"],
            "histogram_step": HISTOGRAM_STEPS.get(metric["id"], 1),
        }
        for metric in histogram_metrics
    }

    histogram_cards_html = []
    for metric in histogram_metrics:
        histogram_cards_html.append(
            (
                f'<div class="kpi kpi-histogram" data-metric-id="{html.escape(metric["id"])}">'
                '<div class="histogram-head">'
                f'<span class="kpi-label">{html.escape(metric["label"])}分布</span>'
                f'<button type="button" class="download-button js-download-histogram" data-download-target="{html.escape(metric["id"])}">ヒストグラム画像保存</button>'
                '</div>'
                f'<span>表示中の比較対象を{html.escape(metric["label"])}で確認</span>'
                f'<div class="histogram-wrap js-histogram-wrap"></div>'
                f'<div class="histogram-legend js-histogram-legend"></div>'
                f'<div class="histogram-caption js-histogram-caption">現在表示中の型式を、{html.escape(metric["label"])}で集計する。横軸は仕様値、縦軸は型式数。</div>'
                '</div>'
            )
        )

    theme_json = json.dumps(THEME_METADATA, ensure_ascii=False, indent=8)
    kpi_rows_json = json.dumps(kpi_rows, ensure_ascii=False)
    histogram_rows_json = json.dumps(histogram_rows, ensure_ascii=False)
    metric_configs_json = json.dumps(metric_configs, ensure_ascii=False)
    brand_palette_json = json.dumps(brand_palette, ensure_ascii=False)
    return f'''<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>マルチブランド ローダー比較 同一数値バー版</title>
    <!-- Artifact Theme: blackrock-v1-color -->
    <script type="application/json" id="artifact-theme-metadata">{theme_json}
    </script>
    <style>
        :root {{
            --page-bg: #F5F6F8;
            --paper-bg: #FFFFFF;
            --ink: #171717;
            --muted: #171717;
            --accent: #000000;
            --line: #DADCE0;
            --soft: #F3F4F6;
            --warn: #8A5A00;
            --warn-bg: #FFF4D8;
            --font-main: "Yu Gothic", "Meiryo", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
{brand_css_vars}
        }}
        * {{ box-sizing: border-box; }}
        body {{
            margin: 0;
            background:
                radial-gradient(circle at top left, #ffffff 0, #eef1f4 28%, var(--page-bg) 60%),
                linear-gradient(180deg, #eef1f4 0, var(--page-bg) 100%);
            color: var(--ink);
            font-family: var(--font-main);
        }}
        .topbar {{
            position: sticky;
            top: 0;
            z-index: 20;
            display: flex;
            gap: 18px;
            align-items: center;
            justify-content: center;
            flex-wrap: wrap;
            padding: 14px 18px;
            background: rgba(255, 255, 255, 0.94);
            border-bottom: 1px solid var(--line);
            backdrop-filter: blur(8px);
        }}
        .unit-toggle, .brand-filter {{ display: inline-flex; gap: 6px; align-items: center; flex-wrap: wrap; }}
        .download-actions {{ display: inline-flex; gap: 8px; align-items: center; flex-wrap: wrap; }}
        .filter-toolbar {{ display: grid; grid-template-columns: 1fr; gap: 14px; margin-top: 18px; padding: 14px 16px; border: 1px solid var(--line); background: #ffffff; }}
        .horsepower-filter {{ display: grid; grid-template-columns: 220px 1fr auto; gap: 14px; align-items: center; }}
        .horsepower-filter-label {{ font-size: 13px; font-weight: 700; }}
        .horsepower-filter-inputs {{ display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 10px; }}
        .horsepower-filter-field {{ display: grid; gap: 4px; }}
        .horsepower-filter-field span {{ font-size: 12px; color: var(--ink); }}
        .horsepower-filter-field input {{ width: 100%; border: 1px solid var(--line); padding: 8px 10px; font: inherit; }}
        .horsepower-filter-range {{ font-size: 13px; font-weight: 700; white-space: nowrap; }}
        .unit-toggle button {{ border: 1px solid var(--line); background: #ffffff; color: var(--ink); padding: 8px 12px; font: inherit; cursor: pointer; }}
        .unit-toggle button.active {{ background: #222222; border-color: #222222; color: #ffffff; }}
        .download-button {{ border: 1px solid var(--line); background: #ffffff; color: var(--ink); padding: 7px 11px; font: inherit; font-size: 12px; font-weight: 700; cursor: pointer; }}
        .download-button:hover {{ background: #f4f4f4; }}
        .brand-filter-option {{ display: inline-flex; align-items: center; gap: 6px; padding: 6px 10px; border: 1px solid var(--line); background: #ffffff; }}
        .topbar a {{ color: var(--ink); text-decoration: none; font-weight: 700; }}
        main {{ max-width: 1440px; margin: 28px auto 60px; padding: 0 20px; }}
        .hero {{ padding: 36px 40px 28px; border: 1px solid var(--line); background: linear-gradient(180deg, #ffffff 0, #f9fafb 100%); box-shadow: 0 18px 48px rgba(23, 23, 23, 0.08); }}
        h1, h2, h3, p {{ margin: 0; }}
        h1 {{ font-size: 44px; line-height: 1.08; letter-spacing: 0.01em; }}
        .subtitle {{ margin-top: 16px; max-width: 1100px; color: var(--ink); font-size: 18px; line-height: 1.7; }}
        .meta {{ margin-top: 18px; color: var(--ink); font-size: 14px; }}
        .control-grid {{ display: grid; grid-template-columns: 320px 1fr; gap: 16px; margin-top: 22px; }}
        .card {{ border: 1px solid var(--line); background: #ffffff; }}
        .card-head {{ padding: 14px 16px; background: #222222; color: #ffffff; font-size: 15px; font-weight: 700; letter-spacing: 0.04em; }}
        .legend-item {{ display: flex; align-items: center; gap: 14px; padding: 14px 16px; border-top: 1px dotted var(--line); font-size: 14px; font-weight: 700; }}
        .legend-item:first-of-type {{ border-top: 0; }}
        .swatch {{ width: 16px; height: 16px; display: inline-block; flex: 0 0 auto; border-radius: 999px; }}
        .metric-selector {{ padding: 16px 18px; border: 1px solid var(--line); background: #ffffff; }}
        .metric-selector-title {{ font-size: 14px; font-weight: 700; letter-spacing: 0.03em; }}
        .metric-selector-grid {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px 16px; margin-top: 12px; }}
        .metric-option {{ display: flex; gap: 8px; align-items: flex-start; font-size: 13px; color: var(--ink); }}
        .metric-option small {{ color: var(--ink); }}
        .visible-brand-summary {{ margin-top: 22px; padding: 14px 16px; border: 1px solid var(--line); background: #ffffff; }}
        .visible-brand-summary strong {{ display: block; font-size: 13px; letter-spacing: 0.04em; }}
        .visible-brand-list {{ display: flex; gap: 8px; flex-wrap: wrap; margin-top: 10px; }}
        .visible-brand-chip {{ display: inline-flex; align-items: center; padding: 6px 10px; border: 1px solid var(--line); background: #f7f8fa; font-size: 13px; font-weight: 700; }}
        .kpi-grid {{ display: grid; grid-template-columns: minmax(280px, 420px); gap: 16px; margin-top: 16px; }}
        .kpi {{ padding: 18px 20px; border: 1px solid var(--line); background: rgba(255, 255, 255, 0.96); min-height: 180px; }}
        .kpi-histogram {{ min-height: 0; }}
        .histogram-card-list {{ display: grid; gap: 16px; margin-top: 22px; }}
        .kpi-label {{ display: block; font-size: 12px; font-weight: 700; letter-spacing: 0.08em; color: var(--ink); text-transform: uppercase; }}
        .kpi strong {{ display: block; margin-top: 10px; font-size: 30px; line-height: 1.05; }}
        .kpi span {{ display: block; margin-top: 10px; color: var(--ink); font-size: 14px; }}
        .kpi-meta {{ margin-top: 12px; font-size: 13px; color: var(--ink); line-height: 1.5; }}
        .kpi-scope {{ margin-top: 12px; padding: 10px 12px; border-left: 4px solid var(--accent); background: #f7f8fa; color: var(--ink); font-size: 13px; line-height: 1.6; }}
        .histogram-wrap {{ margin-top: 14px; border: 1px solid var(--line); background: #ffffff; padding: 12px; }}
        .histogram-head {{ display: flex; align-items: center; justify-content: space-between; gap: 12px; }}
        .histogram-head .download-button {{ flex: 0 0 auto; }}
        .histogram-svg {{ width: 100%; height: auto; display: block; }}
        .histogram-axis {{ stroke: #777; stroke-width: 2; }}
        .histogram-tick {{ stroke: #c9cfd6; stroke-width: 1; stroke-dasharray: 2 4; }}
        .histogram-bar {{ cursor: help; }}
        .histogram-tooltip {{ position: fixed; left: 0; top: 0; z-index: 40; max-width: 360px; padding: 10px 12px; border: 1px solid rgba(23, 23, 23, 0.14); background: rgba(255, 255, 255, 0.98); color: var(--ink); box-shadow: 0 12px 28px rgba(23, 23, 23, 0.18); font-size: 12px; line-height: 1.5; pointer-events: none; opacity: 0; transition: opacity 100ms ease; white-space: pre-line; }}
        .histogram-tooltip.is-visible {{ opacity: 1; }}
        .histogram-label {{ fill: #171717; font-size: 9px; font-weight: 700; }}
        .histogram-count {{ fill: #171717; font-size: 9px; font-weight: 700; }}
        .histogram-caption {{ margin-top: 10px; font-size: 13px; color: var(--ink); line-height: 1.5; }}
        .histogram-legend {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(128px, 1fr)); gap: 8px; margin-top: 10px; }}
        .histogram-legend-item {{ display: inline-flex; align-items: center; gap: 8px; padding: 8px 10px; border: 1px solid var(--line); background: #f7f8fa; font-size: 12px; font-weight: 700; color: var(--ink); line-height: 1.2; transition: opacity 120ms ease, filter 120ms ease; }}
        .histogram-legend-item.is-muted {{ opacity: 0.45; filter: grayscale(1); }}
        .histogram-legend-item .swatch {{ width: 14px; height: 14px; }}
        .section {{ margin-top: 22px; padding: 22px; border: 1px solid var(--line); background: var(--paper-bg); box-shadow: 0 10px 28px rgba(23, 23, 23, 0.05); }}
        .section-title {{ display: flex; align-items: baseline; justify-content: space-between; gap: 18px; padding-bottom: 14px; border-bottom: 4px solid var(--accent); }}
        .section-title h2 {{ font-size: 34px; line-height: 1.1; }}
        .section-title p {{ color: var(--ink); font-size: 15px; }}
        .data-table {{ width: 100%; border-collapse: collapse; }}
        .data-table th, .data-table td {{ border: 1px solid var(--line); padding: 12px 10px; vertical-align: top; text-align: left; }}
        .data-table thead th {{ background: #222222; color: #ffffff; font-size: 15px; }}
        .metric-card-list {{ display: grid; gap: 16px; margin-top: 4px; }}
        .metric-card {{ padding: 18px 20px; border: 1px solid var(--line); background: rgba(255, 255, 255, 0.96); }}
        .metric-card-head {{ display: flex; align-items: center; justify-content: space-between; gap: 12px; }}
        .metric-card-title {{ font-size: 20px; font-weight: 700; color: var(--ink); line-height: 1.2; }}
        .metric-card-subtitle {{ display: block; margin-top: 6px; font-size: 14px; color: var(--ink); }}
        .chart-panel {{ margin-top: 14px; border: 1px solid var(--line); background: #ffffff; padding: 12px; min-width: 1180px; overflow-x: auto; }}
        .metric-unit {{ color: var(--ink); font-size: 13px; }}
        .range-chart-svg {{ position: relative; width: {RANGE_CHART_SVG_WIDTH}px; min-width: {RANGE_CHART_SVG_WIDTH}px; background: #ffffff; overflow: visible; }}
        .range-svg {{ width: {RANGE_CHART_SVG_WIDTH}px; height: auto; display: block; background: #ffffff; }}
        .axis-line {{ stroke: #777; stroke-width: 2; }}
        .axis-guide {{ stroke: #c9cfd6; stroke-width: 1; stroke-dasharray: 2 4; }}
        .axis-label {{ fill: var(--muted); font-size: 13px; font-weight: 700; }}
        .axis-unit {{ fill: var(--ink); font-size: 14px; font-weight: 700; }}
        .marker-label {{ fill: var(--ink); font-size: 11px; font-weight: 700; }}
        .range-point-label-layer {{ position: absolute; inset: 0; pointer-events: none; }}
        .range-point-label {{ position: absolute; display: inline-flex; align-items: center; gap: 6px; max-width: 220px; padding: 1px 4px; background: rgba(255, 255, 255, 0.92); border: 1px solid rgba(201, 207, 214, 0.9); border-radius: 4px; line-height: 1.15; white-space: nowrap; }}
        .range-point-label.is-right {{ transform: translate(12px, -50%); }}
        .range-point-label.is-left {{ transform: translate(calc(-100% - 12px), -50%); }}
        .range-point-label-dot {{ width: 10px; height: 10px; flex: 0 0 auto; border-radius: 999px; border: 2px solid #ffffff; }}
        .note-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 18px; }}
        .note {{ padding: 18px 20px; border: 1px solid var(--line); background: linear-gradient(180deg, #ffffff 0, #f7f7f7 100%); }}
        .note h3 {{ font-size: 20px; margin-bottom: 10px; }}
        .note ul {{ margin: 0; padding-left: 18px; color: var(--muted); line-height: 1.7; }}
        .provenance {{ margin-top: 18px; padding: 16px 18px; border-left: 6px solid var(--accent); background: var(--soft); color: var(--muted); line-height: 1.7; }}
        .empty-chart, .empty-state {{ padding: 16px; color: var(--muted); background: #ffffff; border: 1px dashed var(--line); }}
        @media (max-width: 1200px) {{
            .control-grid {{ grid-template-columns: 1fr; }}
            .kpi-grid {{ grid-template-columns: 1fr; }}
            .horsepower-filter {{ grid-template-columns: 1fr; }}
            .chart-panel {{ min-width: 0; }}
            .range-chart-svg {{ width: {RANGE_CHART_SVG_WIDTH}px; min-width: {RANGE_CHART_SVG_WIDTH}px; }}
            .metric-selector-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
        }}
        @media (max-width: 760px) {{
            .topbar {{ position: static; }}
            main {{ padding: 0 10px; margin: 12px auto 30px; }}
            .hero, .section {{ padding: 18px 14px; }}
            h1 {{ font-size: 34px; }}
            .section-title {{ display: block; }}
            .section-title h2 {{ font-size: 28px; }}
            .note-grid {{ grid-template-columns: 1fr; }}
            .metric-selector-grid {{ grid-template-columns: 1fr; }}
        }}
    </style>
</head>
<body>
    <nav class="topbar">
        <strong>マルチブランド 同一バー比較</strong>
        <div class="brand-filter" aria-label="brand filter">{brand_filter_items}</div>
        <div class="unit-toggle" aria-label="unit toggle">
            <button type="button" class="active" data-unit-system="metric">SI</button>
            <button type="button" data-unit-system="us">US</button>
        </div>
        <div class="download-actions" aria-label="download actions">
            <button type="button" class="download-button js-download-visible-charts">表示中グラフを一括画像保存</button>
        </div>
        <a href="{MARKDOWN_PATH.name}">MD正本</a>
    </nav>
    <main>
        <section class="hero">
            <h1>マルチブランド 同一数値バー比較</h1>
            <p class="subtitle">複数ブランドの個別型式を同じ数値バー上へ重ねて比較するページ。ブランドごとに表示オンオフできるので、同時表示で差を見ることも、任意のブランドだけに絞ることもできる。</p>
            <p class="meta">{TODAY} | Web閲覧用 | Source Markdown: {MARKDOWN_PATH.name}</p>
            <div class="filter-toolbar">
                <div class="horsepower-filter">
                    <div class="horsepower-filter-label">エンジン出力フィルタ</div>
                    <div class="horsepower-filter-inputs">
                        <label class="horsepower-filter-field"><span>最小 hp</span><input type="number" class="js-horsepower-min" min="{horsepower_min}" max="{horsepower_max}" value="{horsepower_min}" step="1"></label>
                        <label class="horsepower-filter-field"><span>最大 hp</span><input type="number" class="js-horsepower-max" min="{horsepower_min}" max="{horsepower_max}" value="{horsepower_max}" step="1"></label>
                    </div>
                    <div class="horsepower-filter-range js-horsepower-range-text">現在の範囲: {horsepower_min} - {horsepower_max} hp</div>
                </div>
            </div>
            <div class="visible-brand-summary">
                <strong>現在表示中のメーカー</strong>
                <div class="visible-brand-list js-visible-brand-list"></div>
            </div>
            <div class="kpi-grid">
                <div class="kpi">
                    <span class="kpi-label">現在の比較対象</span>
                    <strong class="js-kpi-count-value">{len(comparison_rows)}台</strong>
                    <span class="js-kpi-count-caption">表示中の個別型式</span>
                    <div class="kpi-meta js-kpi-count-meta">全 {len(BRAND_ORDER)} ブランド中、表示中ブランドを集計</div>
                </div>
            </div>
            <p class="kpi-scope js-kpi-scope">統計は常に現在表示中のメーカーだけを母集団として再計算する。非表示のメーカーは件数にも含めない。</p>
            <div class="histogram-card-list">{''.join(histogram_cards_html)}</div>
            <div class="control-grid">
                <aside class="card">
                    <div class="card-head">ブランド凡例</div>
                    {legend_items}
                </aside>
                <div class="metric-selector">
                    <div class="metric-selector-title">表示する数値バー</div>
                    <div class="metric-selector-grid">{metric_selector_items}</div>
                </div>
            </div>
        </section>

        <section class="section">
            <div class="section-title">
                <h2>同一数値バー比較</h2>
                <p>両ブランドの型式を同じレンジ上に重ねて表示。上部チェックでブランドごとの表示オンオフができる。</p>
            </div>
            <div class="metric-card-list">{''.join(metrics_html)}</div>
        </section>

        <section class="section">
            <div class="section-title">
                <h2>個別型式一覧</h2>
                <p>数値バーに載せた型式をブランド列つきで一覧化。</p>
            </div>
            {render_combined_table(comparison_rows)}
        </section>

        <section class="section">
            <div class="section-title">
                <h2>シリーズ要約行</h2>
                <p>個別型式とは別に、シリーズ要約行があるものだけを保持。</p>
            </div>
            {render_summary_table(summaries)}
            <div class="note-grid">
                <div class="note">
                    <h3>このページの意図</h3>
                    <ul>
                        <li>複数ブランドを同じバー上で見て、仕様差の大きさを一目で確認する。</li>
                        <li>ブランドフィルタで片側を消し、密集した項目だけ個別に確認する。</li>
                        <li>元データは共通 curated テーブルなので、今後ほかメーカーも同じ構造で追加できる。</li>
                    </ul>
                </div>
                <div class="note">
                    <h3>注意点</h3>
                    <ul>
                        <li>Bobcat の一部容量値は ROC 条件違いを含む記述で、数値位置は抽出された最大値ベース。</li>
                        <li>電動モデルとシリーズ要約は現状 AVANT 側に偏っている。</li>
                        <li>オプション / 標準 / なし の機能比較列はまだ未構造化。</li>
                    </ul>
                </div>
            </div>
            <div class="provenance">
                Provenance: <code>db/knowledge.duckdb</code> の <code>loader_specification_import_rows</code> を入力元にした。レンジ図の位置は取得文字列から数値部分を抜き出し、速度レンジは上限値、<code>3.1 m</code> のような値は mm に換算して計算している。ブランドフィルタは比較バーと一覧表の両方に効く。
            </div>
        </section>
    </main>
    <div class="histogram-tooltip js-histogram-tooltip" aria-hidden="true"></div>
    <script>
        (function () {{
            var currentUnitSystem = 'metric';
            var kpiRows = {kpi_rows_json};
            var histogramRows = {histogram_rows_json};
            var metricConfigs = {metric_configs_json};
            var brandPalette = {brand_palette_json};

            function horsepowerFilterRange() {{
                var minInput = document.querySelector('.js-horsepower-min');
                var maxInput = document.querySelector('.js-horsepower-max');
                var minValue = minInput ? Number(minInput.value || 0) : Number.NEGATIVE_INFINITY;
                var maxValue = maxInput ? Number(maxInput.value || 0) : Number.POSITIVE_INFINITY;
                if (minValue > maxValue) {{
                    return {{ min: maxValue, max: minValue }};
                }}
                return {{ min: minValue, max: maxValue }};
            }}

            function updateHorsepowerRangeText() {{
                var range = horsepowerFilterRange();
                var node = document.querySelector('.js-horsepower-range-text');
                if (node) {{
                    node.textContent = '現在の範囲: ' + range.min + ' - ' + range.max + ' hp';
                }}
            }}

            function bindHistogramTooltips() {{
                var tooltip = document.querySelector('.js-histogram-tooltip');
                if (!tooltip) {{
                    return;
                }}

                function hideTooltip() {{
                    tooltip.classList.remove('is-visible');
                    tooltip.setAttribute('aria-hidden', 'true');
                }}

                function moveTooltip(event) {{
                    var offsetX = 14;
                    var offsetY = 16;
                    var maxLeft = Math.max(12, window.innerWidth - tooltip.offsetWidth - 12);
                    var maxTop = Math.max(12, window.innerHeight - tooltip.offsetHeight - 12);
                    var left = Math.min(event.clientX + offsetX, maxLeft);
                    var top = Math.min(event.clientY + offsetY, maxTop);
                    tooltip.style.left = left + 'px';
                    tooltip.style.top = top + 'px';
                }}

                document.addEventListener('mouseover', function (event) {{
                    var bar = event.target.closest('.histogram-bar');
                    if (!bar) {{
                        return;
                    }}
                    var message = bar.getAttribute('data-tooltip');
                    if (!message) {{
                        return;
                    }}
                    tooltip.textContent = message;
                    tooltip.classList.add('is-visible');
                    tooltip.setAttribute('aria-hidden', 'false');
                    moveTooltip(event);
                }});

                document.addEventListener('mousemove', function (event) {{
                    if (!tooltip.classList.contains('is-visible')) {{
                        return;
                    }}
                    moveTooltip(event);
                }});

                document.addEventListener('mouseout', function (event) {{
                    var bar = event.target.closest('.histogram-bar');
                    if (!bar) {{
                        return;
                    }}
                    var nextTarget = event.relatedTarget;
                    if (nextTarget && nextTarget.closest && nextTarget.closest('.histogram-bar') === bar) {{
                        return;
                    }}
                    hideTooltip();
                }});

                document.addEventListener('scroll', hideTooltip, true);
                window.addEventListener('blur', hideTooltip);
            }}

            function applyUnitSystem(system) {{
                currentUnitSystem = system;
                document.querySelectorAll('.js-value-switch').forEach(function (node) {{
                    var nextValue = node.getAttribute(system === 'us' ? 'data-us' : 'data-metric');
                    if (nextValue !== null) {{
                        node.textContent = nextValue;
                    }}
                }});

                document.querySelectorAll('.js-unit-label').forEach(function (node) {{
                    var nextUnit = node.getAttribute(system === 'us' ? 'data-us-unit' : 'data-metric-unit');
                    if (nextUnit !== null) {{
                        node.textContent = nextUnit;
                    }}
                }});

                document.querySelectorAll('[data-unit-system]').forEach(function (button) {{
                    var active = button.getAttribute('data-unit-system') === system;
                    button.classList.toggle('active', active);
                    button.setAttribute('aria-pressed', active ? 'true' : 'false');
                }});
            }}

            function applyMetricVisibility() {{
                document.querySelectorAll('.metric-toggle-input').forEach(function (input) {{
                    var metricId = input.getAttribute('data-target-metric');
                    document.querySelectorAll('.metric-row[data-metric-id="' + metricId + '"]').forEach(function (row) {{
                        row.style.display = input.checked ? '' : 'none';
                    }});
                }});
            }}

            function applyBrandVisibility() {{
                var range = horsepowerFilterRange();
                document.querySelectorAll('.brand-filter-input').forEach(function (input) {{
                    var currentBrandId = input.getAttribute('data-brand-id');
                    document.querySelectorAll('.js-brand-filter-target[data-brand-id="' + currentBrandId + '"]').forEach(function (node) {{
                        var horsepowerAttr = node.getAttribute('data-horsepower');
                        var horsepower = horsepowerAttr === null ? null : Number(horsepowerAttr);
                        var inHorsepowerRange = horsepower === null ? true : horsepower >= range.min && horsepower <= range.max;
                        node.style.display = input.checked && inHorsepowerRange ? '' : 'none';
                    }});
                }});

                updateHorsepowerRangeText();
                relayoutRangeCharts();
                updateVisibleKpis();
            }}

            function visibleBrandIds() {{
                return Array.prototype.map.call(
                    Array.prototype.filter.call(document.querySelectorAll('.brand-filter-input'), function (input) {{
                        return input.checked;
                    }}),
                    function (input) {{
                        return input.getAttribute('data-brand-id');
                    }}
                );
            }}

            function visibleBrandLabels() {{
                return Array.prototype.map.call(
                    Array.prototype.filter.call(document.querySelectorAll('.brand-filter-input'), function (input) {{
                        return input.checked;
                    }}),
                    function (input) {{
                        var label = input.parentElement ? input.parentElement.querySelector('span') : null;
                        return label ? label.textContent.trim() : input.getAttribute('data-brand-id');
                    }}
                );
            }}

            function renderMetricHistogram(node, rows, metricConfig, legendNode, metaNode) {{
                if (!node || !metricConfig) {{
                    return;
                }}

                function hasHistogramValue(value) {{
                    return value !== null && value !== undefined && !Number.isNaN(value) && Number(value) !== 0;
                }}

                var metricRows = rows.filter(function (row) {{
                    var value = row.metricValues[metricConfig.id];
                    return hasHistogramValue(value);
                }});
                var excludedRows = rows.filter(function (row) {{
                    var value = row.metricValues[metricConfig.id];
                    return !hasHistogramValue(value);
                }});
                var excludedElectricCount = excludedRows.filter(function (row) {{
                    return row.isElectric;
                }}).length;
                var zeroExcludedCount = excludedRows.filter(function (row) {{
                    var value = row.metricValues[metricConfig.id];
                    return value !== null && value !== undefined && !Number.isNaN(value) && Number(value) === 0;
                }}).length;

                if (!metricRows.length) {{
                    node.innerHTML = '<div class="empty-state">表示条件に一致する' + escapeXml(metricConfig.label) + 'データなし</div>';
                    if (metaNode) {{
                        metaNode.textContent = '表示中の型式に ' + metricConfig.label + ' 値がないため分布を描けない。' + (zeroExcludedCount > 0 ? ' 0 値 ' + zeroExcludedCount + ' 台はデータなしとして除外した。' : '') + (excludedElectricCount > 0 ? ' 電動 ' + excludedElectricCount + ' 台はこの分布に含めていない。' : '');
                    }}
                    if (legendNode) {{
                        var activeBrandIdsForEmpty = visibleBrandIds();
                        legendNode.innerHTML = brandPalette
                            .filter(function (brand) {{ return activeBrandIdsForEmpty.indexOf(brand.brandId) >= 0; }})
                            .map(function (brand) {{
                                return '<span class="histogram-legend-item is-muted"><span class="swatch" style="background:var(--brand-' + brand.brandId + '-fill); border:2px solid var(--brand-' + brand.brandId + '-stroke);"></span><span>' + escapeXml(brand.label) + '</span></span>';
                            }}).join('');
                    }}
                    return;
                }}

                var metricValues = metricRows.map(function (row) {{ return row.metricValues[metricConfig.id]; }});
                var range = {{ min: Math.min.apply(null, metricValues), max: Math.max.apply(null, metricValues) }};
                var step = metricConfig.histogram_step || 1;
                var start = Math.floor(range.min / step) * step;
                var end = Math.ceil(range.max / step) * step;
                if (end <= start) {{
                    end = start + step;
                }}

                var binCount = Math.max(1, Math.round((end - start) / step));
                var counts = new Array(binCount).fill(0);
                var brandCounts = new Array(binCount).fill(null).map(function () {{ return {{}}; }});
                var brandRows = new Array(binCount).fill(null).map(function () {{ return {{}}; }});
                metricRows.forEach(function (row) {{
                    var value = row.metricValues[metricConfig.id];
                    var index = Math.floor((value - start) / step);
                    if (index < 0) {{
                        index = 0;
                    }}
                    if (index >= binCount) {{
                        index = binCount - 1;
                    }}
                    counts[index] += 1;
                    brandCounts[index][row.brandId] = (brandCounts[index][row.brandId] || 0) + 1;
                    if (!brandRows[index][row.brandId]) {{
                        brandRows[index][row.brandId] = [];
                    }}
                    brandRows[index][row.brandId].push({{
                        brandLabel: row.brandLabel,
                        model: row.model,
                        value: value
                    }});
                }});

                var histogramBrandIds = metricRows.reduce(function (ids, row) {{
                    if (ids.indexOf(row.brandId) < 0) {{
                        ids.push(row.brandId);
                    }}
                    return ids;
                }}, []);
                var activeBrandIds = visibleBrandIds();
                var visibleBrands = brandPalette
                    .filter(function (brand) {{ return activeBrandIds.indexOf(brand.brandId) >= 0; }})
                    .map(function (brand) {{
                        return {{
                            brandId: brand.brandId,
                            brandLabel: brand.label,
                            brandColor: brand.fill,
                            brandStroke: brand.stroke,
                            isMuted: histogramBrandIds.indexOf(brand.brandId) < 0
                        }};
                    }});

                if (legendNode) {{
                    legendNode.innerHTML = visibleBrands.map(function (brand) {{
                        return '<span class="histogram-legend-item' + (brand.isMuted ? ' is-muted' : '') + '"><span class="swatch" style="background:var(--brand-' + brand.brandId + '-fill); border:2px solid var(--brand-' + brand.brandId + '-stroke);"></span><span>' + escapeXml(brand.brandLabel) + '</span></span>';
                    }}).join('');
                }}

                var width = 860;
                var height = 220;
                var marginLeft = 46;
                var marginRight = 18;
                var marginTop = 18;
                var marginBottom = 60;
                var plotWidth = width - marginLeft - marginRight;
                var plotHeight = height - marginTop - marginBottom;
                var maxCount = Math.max.apply(null, counts);
                var barGap = binCount > 40 ? 1 : binCount > 24 ? 2 : 6;
                var barWidth = Math.max(3, (plotWidth - barGap * (binCount - 1)) / binCount);
                var totalBarsWidth = barWidth * binCount + barGap * (binCount - 1);
                var startX = marginLeft + Math.max(0, (plotWidth - totalBarsWidth) / 2);
                var bars = counts.map(function (count, index) {{
                    var x = startX + index * (barWidth + barGap);
                    var binStart = start + index * step;
                    var showLabel = count > 0;
                    var stackedHeight = 0;
                    var segments = visibleBrands.map(function (brand) {{
                        var brandCount = brandCounts[index][brand.brandId] || 0;
                        if (brandCount <= 0) {{
                            return '';
                        }}

                        var brandItems = (brandRows[index][brand.brandId] || []).slice().sort(function (left, right) {{
                            if (left.value !== right.value) {{
                                return right.value - left.value;
                            }}
                            return String(left.model || '').localeCompare(String(right.model || ''));
                        }});
                        var tooltipLines = [
                            brand.brandLabel + ' | ' + metricConfig.label + ' | ' + brandCount + '台'
                        ].concat(brandItems.map(function (item) {{
                            return item.brandLabel + ' / ' + (item.model || '-') + ' / ' + formatTooltipValue(item.value, metricConfig.metric_unit);
                        }}));
                        var tooltipText = tooltipLines.join('\\n');

                        var segmentHeight = maxCount <= 0 ? 0 : (brandCount / maxCount) * (plotHeight - 8);
                        var y = marginTop + plotHeight - stackedHeight - segmentHeight;
                        stackedHeight += segmentHeight;
                        return '<rect x="' + x.toFixed(1) + '" y="' + y.toFixed(1) + '" width="' + barWidth.toFixed(1) + '" height="' + Math.max(segmentHeight, 0).toFixed(1) + '" class="histogram-bar" data-tooltip="' + escapeXml(tooltipText) + '" style="fill:' + brand.brandColor + '; stroke:' + brand.brandStroke + '; stroke-width:0.6;" />';
                    }}).join('');
                    var labelY = marginTop + plotHeight - stackedHeight;
                    var tickLabelX = (x + barWidth / 2).toFixed(1);
                    var tickLabelY = (marginTop + plotHeight + 12).toFixed(1);
                    return ''
                        + '<line x1="' + (x + barWidth / 2).toFixed(1) + '" y1="' + marginTop + '" x2="' + (x + barWidth / 2).toFixed(1) + '" y2="' + (marginTop + plotHeight) + '" class="histogram-tick" />'
                        + segments
                        + (count > 0 ? '<text x="' + (x + barWidth / 2).toFixed(1) + '" y="' + (labelY - 6).toFixed(1) + '" text-anchor="middle" class="histogram-count">' + count + '</text>' : '')
                        + (showLabel ? '<text x="' + tickLabelX + '" y="' + tickLabelY + '" text-anchor="end" transform="rotate(-45 ' + tickLabelX + ' ' + tickLabelY + ')" class="histogram-label">' + binStart + '</text>' : '');
                }}).join('');

                node.innerHTML = ''
                    + '<svg class="histogram-svg" viewBox="0 0 ' + width + ' ' + height + '" aria-hidden="true">'
                    + '<line x1="' + marginLeft + '" y1="' + (marginTop + plotHeight) + '" x2="' + (width - marginRight) + '" y2="' + (marginTop + plotHeight) + '" class="histogram-axis" />'
                    + '<line x1="' + marginLeft + '" y1="' + marginTop + '" x2="' + marginLeft + '" y2="' + (marginTop + plotHeight) + '" class="histogram-axis" />'
                    + bars
                    + '<text x="' + (width - marginRight) + '" y="' + (height - 8) + '" text-anchor="end" class="histogram-label">' + escapeXml(metricConfig.metric_unit) + '</text>'
                    + '<text x="' + marginLeft + '" y="' + (marginTop - 4) + '" text-anchor="start" class="histogram-label">型式数</text>'
                    + '</svg>';

                if (metaNode) {{
                    metaNode.textContent = '表示中 ' + metricRows.length + ' 台の ' + metricConfig.label + ' を ' + step + ' ' + metricConfig.metric_unit + ' 刻みで集計。棒はメーカー色で積み上げ、横軸は ' + metricConfig.metric_unit + '、縦軸は型式数。' + (excludedRows.length > 0 ? ' なお、表示中 ' + rows.length + ' 台のうち ' + metricConfig.label + ' 値を持たない ' + excludedRows.length + ' 台はこの分布から除外している。' : '') + (zeroExcludedCount > 0 ? ' このうち 0 値 ' + zeroExcludedCount + ' 台はデータなしとして扱った。' : '') + (excludedElectricCount > 0 ? ' 電動 ' + excludedElectricCount + ' 台は数値化できないため未集計。' : '');
                }}
            }}

            function updateVisibleKpis() {{
                var activeBrandIds = visibleBrandIds();
                var activeBrandLabels = visibleBrandLabels();
                var horsepowerRange = horsepowerFilterRange();
                var visibleRows = kpiRows.filter(function (row) {{
                    var horsepowerOk = row.horsepower === null || row.horsepower === undefined ? true : row.horsepower >= horsepowerRange.min && row.horsepower <= horsepowerRange.max;
                    return activeBrandIds.indexOf(row.brandId) >= 0 && horsepowerOk;
                }});
                var visibleHistogramRows = histogramRows.filter(function (row) {{
                    var horsepowerValue = row.metricValues.horsepower === null || row.metricValues.horsepower === undefined ? null : Number(row.metricValues.horsepower);
                    var horsepowerOk = horsepowerValue === null || Number.isNaN(horsepowerValue) ? true : horsepowerValue >= horsepowerRange.min && horsepowerValue <= horsepowerRange.max;
                    return activeBrandIds.indexOf(row.brandId) >= 0 && horsepowerOk;
                }});

                var countValue = document.querySelector('.js-kpi-count-value');
                var countCaption = document.querySelector('.js-kpi-count-caption');
                var countMeta = document.querySelector('.js-kpi-count-meta');
                var scopeNode = document.querySelector('.js-kpi-scope');
                var visibleBrandList = document.querySelector('.js-visible-brand-list');

                function renderAllHistograms(rows) {{
                    Object.keys(metricConfigs).forEach(function (metricId) {{
                        var metricConfig = metricConfigs[metricId];
                        var card = document.querySelector('.kpi-histogram[data-metric-id="' + metricId + '"]');
                        if (!card) {{
                            return;
                        }}
                        renderMetricHistogram(
                            card.querySelector('.js-histogram-wrap'),
                            rows,
                            metricConfig,
                            card.querySelector('.js-histogram-legend'),
                            card.querySelector('.js-histogram-caption')
                        );
                    }});
                }}

                if (!visibleRows.length) {{
                    if (countValue) countValue.textContent = '0台';
                    if (countCaption) countCaption.textContent = '表示中の個別型式';
                    if (countMeta) countMeta.textContent = 'ブランド選択またはエンジン出力フィルタに一致する型式がない';
                    if (scopeNode) scopeNode.textContent = '統計の母集団は、現在表示中のメーカーかつエンジン出力 ' + horsepowerRange.min + ' - ' + horsepowerRange.max + ' hp に一致する型式のみ。';
                    if (visibleBrandList) visibleBrandList.innerHTML = '<span class="visible-brand-chip">表示中メーカーなし</span>';
                    renderAllHistograms([]);
                    return;
                }}

                if (countValue) countValue.textContent = visibleRows.length + '台';
                if (countCaption) countCaption.textContent = '表示中の個別型式';
                if (countMeta) countMeta.textContent = activeBrandLabels.length + 'ブランド、エンジン出力 ' + horsepowerRange.min + ' - ' + horsepowerRange.max + ' hp を集計対象に含めている';
                if (scopeNode) {{
                    scopeNode.textContent = '統計の母集団は現在表示中のメーカーのみ。さらにエンジン出力 ' + horsepowerRange.min + ' - ' + horsepowerRange.max + ' hp に一致する型式だけを集計している。集計対象ブランド: ' + activeBrandLabels.join(', ');
                }}
                if (visibleBrandList) {{
                    visibleBrandList.innerHTML = activeBrandLabels.map(function (label) {{
                        return '<span class="visible-brand-chip">' + escapeXml(label) + '</span>';
                    }}).join('');
                }}
                renderAllHistograms(visibleHistogramRows);
                applyUnitSystem(currentUnitSystem);
            }}

            function formatTooltipValue(value, unit) {{
                if (value === null || value === undefined || Number.isNaN(value)) {{
                    return '-';
                }}
                var normalized = Math.abs(value - Math.round(value)) < 1e-9 ? String(Math.round(value)) : String(Math.round(value * 10) / 10);
                return normalized + ' ' + unit;
            }}

            function relayoutRangeCharts() {{
                document.querySelectorAll('.js-range-chart').forEach(function (chart) {{
                    var rowStep = Number(chart.getAttribute('data-row-step') || '24');
                    var topOffset = Number(chart.getAttribute('data-top-offset') || '18');
                    var bottomPad = Number(chart.getAttribute('data-bottom-pad') || '48');
                    var axisLabelOffset = Number(chart.getAttribute('data-axis-label-offset') || '18');
                    var svg = chart.querySelector('.range-svg');
                    if (!svg) {{
                        return;
                    }}

                    var visiblePoints = Array.prototype.filter.call(
                        chart.querySelectorAll('.js-range-point'),
                        function (node) {{
                            return node.style.display !== 'none';
                        }}
                    );
                    var visibleLabels = Array.prototype.filter.call(
                        chart.querySelectorAll('.js-range-point-label'),
                        function (node) {{
                            return node.style.display !== 'none';
                        }}
                    );

                    var visibleCount = visiblePoints.length;
                    var axisY = topOffset + visibleCount * rowStep;
                    var chartHeight = 28 + visibleCount * rowStep + bottomPad;
                    chart.style.height = chartHeight + 'px';
                    svg.setAttribute('viewBox', '0 0 ' + (chart.getAttribute('data-chart-width') || '{RANGE_CHART_SVG_WIDTH}') + ' ' + chartHeight);

                    var axisLine = chart.querySelector('.js-range-axis-line');
                    if (axisLine) {{
                        axisLine.setAttribute('y1', axisY);
                        axisLine.setAttribute('y2', axisY);
                    }}

                    chart.querySelectorAll('.js-range-axis-guide').forEach(function (guide) {{
                        guide.setAttribute('y2', axisY);
                    }});

                    chart.querySelectorAll('.js-range-axis-label').forEach(function (label) {{
                        label.setAttribute('y', axisY + axisLabelOffset);
                    }});

                    chart.querySelectorAll('.js-range-axis-unit').forEach(function (label) {{
                        label.setAttribute('y', axisY + 4);
                    }});

                    visiblePoints.forEach(function (point, index) {{
                        var nextY = topOffset + index * rowStep;
                        var circle = point.querySelector('circle');
                        if (circle) {{
                            circle.setAttribute('cy', nextY.toFixed(1));
                        }}
                    }});

                    visibleLabels.forEach(function (label, index) {{
                        var nextY = topOffset + index * rowStep;
                        label.style.top = (nextY / chartHeight * 100) + '%';
                    }});
                }});
            }}

            function slugifyText(value) {{
                return (value || 'chart')
                    .toLowerCase()
                    .replace(/[^a-z0-9\u3040-\u30ff\u3400-\u9fff-]+/g, '-')
                    .replace(/^-+|-+$/g, '') || 'chart';
            }}

            function escapeXml(value) {{
                return String(value)
                    .replace(/&/g, '&amp;')
                    .replace(/</g, '&lt;')
                    .replace(/>/g, '&gt;')
                    .replace(/"/g, '&quot;')
                    .replace(/'/g, '&apos;');
            }}

            function buildExportSvg(metricRow) {{
                if (!metricRow || metricRow.style.display === 'none') {{
                    return null;
                }}

                var chart = metricRow.querySelector('.js-range-chart');
                var sourceSvg = chart ? chart.querySelector('.range-svg') : null;
                if (!chart || !sourceSvg) {{
                    return null;
                }}

                var visiblePoints = Array.prototype.filter.call(
                    chart.querySelectorAll('.js-range-point'),
                    function (node) {{
                        return node.style.display !== 'none';
                    }}
                );
                if (!visiblePoints.length) {{
                    return null;
                }}

                var chartWidth = Number(chart.getAttribute('data-chart-width') || '{RANGE_CHART_SVG_WIDTH}');
                var chartHeight = Number((chart.style.height || '').replace('px', '')) || Number((sourceSvg.getAttribute('viewBox') || '0 0 {RANGE_CHART_SVG_WIDTH} 300').split(/\s+/)[3]);
                var leftMargin = 260;
                var rightMargin = 260;
                var chartAreaWidth = chartWidth + leftMargin + rightMargin;
                var chartAreaHeight = chartHeight;
                var svgInner = sourceSvg.innerHTML;
                var labelFragments = [];

                var axisStyleParts = [];
                var axisLineSample = sourceSvg.querySelector('.axis-line');
                if (axisLineSample) {{
                    var axisLineStyle = getComputedStyle(axisLineSample);
                    axisStyleParts.push('.axis-line{{stroke:' + axisLineStyle.stroke + ';stroke-width:' + axisLineStyle.strokeWidth + ';}}');
                }}
                var axisGuideSample = sourceSvg.querySelector('.axis-guide');
                if (axisGuideSample) {{
                    var axisGuideStyle = getComputedStyle(axisGuideSample);
                    axisStyleParts.push('.axis-guide{{stroke:' + axisGuideStyle.stroke + ';stroke-width:' + axisGuideStyle.strokeWidth + ';stroke-dasharray:' + axisGuideStyle.strokeDasharray + ';}}');
                }}
                var axisLabelSample = sourceSvg.querySelector('.axis-label');
                if (axisLabelSample) {{
                    var axisLabelStyle = getComputedStyle(axisLabelSample);
                    axisStyleParts.push('.axis-label{{fill:' + axisLabelStyle.fill + ';font-size:' + axisLabelStyle.fontSize + ';font-weight:' + axisLabelStyle.fontWeight + ';font-family:' + axisLabelStyle.fontFamily + ';}}');
                }}
                var axisUnitSample = sourceSvg.querySelector('.axis-unit');
                if (axisUnitSample) {{
                    var axisUnitStyle = getComputedStyle(axisUnitSample);
                    axisStyleParts.push('.axis-unit{{fill:' + axisUnitStyle.fill + ';font-size:' + axisUnitStyle.fontSize + ';font-weight:' + axisUnitStyle.fontWeight + ';font-family:' + axisUnitStyle.fontFamily + ';}}');
                }}
                var axisStyleBlock = axisStyleParts.length ? ('<style>' + axisStyleParts.join('') + '</style>') : '';

                Array.prototype.forEach.call(chart.querySelectorAll('.js-range-point-label'), function (label) {{
                    if (label.style.display === 'none') {{
                        return;
                    }}

                    var textNode = label.querySelector('.marker-label');
                    if (!textNode) {{
                        return;
                    }}

                    var text = textNode.textContent || '';
                    var xPercent = Number(label.getAttribute('data-point-x-percent') || '0');
                    var yPercent = Number((label.style.top || '0').replace('%', ''));
                    var side = label.getAttribute('data-label-side') || 'right';
                    var pointX = leftMargin + chartWidth * xPercent / 100;
                    var pointY = chartAreaHeight * yPercent / 100;
                    var estimatedWidth = Math.max(48, text.length * 7 + 14);
                    var rectHeight = 20;
                    var rectX = side === 'left' ? pointX - estimatedWidth - 18 : pointX + 10;
                    var textX = side === 'left' ? rectX + estimatedWidth - 4 : rectX + 4;
                    var textAnchor = side === 'left' ? 'end' : 'start';

                    labelFragments.push(
                        '<g>' +
                        '<rect x="' + rectX.toFixed(1) + '" y="' + (pointY - 11).toFixed(1) + '" rx="4" ry="4" width="' + estimatedWidth.toFixed(1) + '" height="' + rectHeight + '" fill="rgba(255,255,255,0.92)" stroke="rgba(201,207,214,0.9)" />' +
                        '<text x="' + textX.toFixed(1) + '" y="' + (pointY + 3).toFixed(1) + '" font-family="Yu Gothic, Meiryo, Segoe UI, sans-serif" font-size="11" font-weight="700" fill="#171717" text-anchor="' + textAnchor + '">' + escapeXml(text) + '</text>' +
                        '</g>'
                    );
                }});

                var titleNode = metricRow.querySelector('.metric-card-title.metric-name');
                var titleText = titleNode ? titleNode.textContent.trim() : (metricRow.getAttribute('data-metric-id') || 'chart');
                var subtitleNode = metricRow.querySelector('.metric-card-subtitle');
                var subtitleText = subtitleNode ? subtitleNode.textContent.replace(/\s+/g, ' ').trim() : '';

                var brandLabelById = {{}};
                Array.prototype.forEach.call(document.querySelectorAll('.brand-filter-input'), function (input) {{
                    var labelSpan = input.parentElement ? input.parentElement.querySelector('span') : null;
                    brandLabelById[input.getAttribute('data-brand-id')] = labelSpan ? labelSpan.textContent.trim() : input.getAttribute('data-brand-id');
                }});

                var legendItems = [];
                var seenBrandIds = {{}};
                Array.prototype.forEach.call(document.querySelectorAll('.brand-filter-input'), function (input) {{
                    var brandId = input.getAttribute('data-brand-id');
                    if (seenBrandIds[brandId]) {{
                        return;
                    }}
                    var samplePoint = null;
                    for (var i = 0; i < visiblePoints.length; i += 1) {{
                        if (visiblePoints[i].getAttribute('data-brand-id') === brandId) {{
                            samplePoint = visiblePoints[i];
                            break;
                        }}
                    }}
                    if (!samplePoint) {{
                        return;
                    }}
                    var circle = samplePoint.querySelector('circle');
                    legendItems.push({{
                        color: circle ? circle.getAttribute('fill') : '#374151',
                        stroke: circle ? circle.getAttribute('stroke') : '#ffffff',
                        label: brandLabelById[brandId] || brandId
                    }});
                    seenBrandIds[brandId] = true;
                }});

                var outerMargin = 20;
                var contentWidth = chartAreaWidth;
                var legendFont = 'bold 12px "Yu Gothic", Meiryo, sans-serif';
                var titleHeight = 26;
                var subtitleHeight = subtitleText ? 24 : 0;
                var chartBoxTop = outerMargin + titleHeight + subtitleHeight + 10;

                var legendChipPaddingX = 10;
                var legendChipHeight = 32;
                var legendSwatchSize = 14;
                var legendChipGap = 10;
                var legendRowGap = 8;
                var legendRows = [];
                if (legendItems.length) {{
                    var chipWidths = legendItems.map(function (item) {{
                        return legendSwatchSize + 8 + measureTextWidth(item.label, legendFont) + legendChipPaddingX * 2;
                    }});
                    var currentRow = [];
                    var currentWidth = 0;
                    legendItems.forEach(function (item, index) {{
                        var chipWidth = chipWidths[index];
                        var addWidth = currentRow.length ? chipWidth + legendChipGap : chipWidth;
                        if (currentRow.length > 0 && currentWidth + addWidth > contentWidth) {{
                            legendRows.push(currentRow);
                            currentRow = [];
                            currentWidth = 0;
                            addWidth = chipWidth;
                        }}
                        currentRow.push({{ item: item, width: chipWidth }});
                        currentWidth += addWidth;
                    }});
                    if (currentRow.length) {{
                        legendRows.push(currentRow);
                    }}
                }}

                var legendTop = chartBoxTop + chartAreaHeight + 24;
                var legendRowHeight = legendChipHeight + legendRowGap;
                var legendHeight = legendRows.length ? legendRows.length * legendRowHeight + 8 : 0;
                var totalWidth = outerMargin * 2 + contentWidth;
                var totalHeight = legendTop + legendHeight + outerMargin;
                var centerX = totalWidth / 2;

                var parts = [];
                parts.push('<svg xmlns="http://www.w3.org/2000/svg" width="' + totalWidth + '" height="' + totalHeight + '" viewBox="0 0 ' + totalWidth + ' ' + totalHeight + '">');
                parts.push('<rect width="100%" height="100%" fill="#ffffff" />');
                parts.push(axisStyleBlock);
                parts.push('<rect x="0.5" y="0.5" width="' + (totalWidth - 1) + '" height="' + (totalHeight - 1) + '" fill="none" stroke="#DADCE0" stroke-width="1" />');
                parts.push('<text x="' + centerX + '" y="' + (outerMargin + 18) + '" text-anchor="middle" font-family="Yu Gothic, Meiryo, sans-serif" font-size="20" font-weight="700" fill="#171717">' + escapeXml(titleText) + '</text>');
                if (subtitleText) {{
                    parts.push('<text x="' + centerX + '" y="' + (outerMargin + titleHeight + 14) + '" text-anchor="middle" font-family="Yu Gothic, Meiryo, sans-serif" font-size="14" fill="#171717">' + escapeXml(subtitleText) + '</text>');
                }}
                parts.push('<g transform="translate(' + outerMargin + ',' + chartBoxTop + ')">');
                parts.push('<g transform="translate(' + leftMargin + ',0)">' + svgInner + '</g>');
                parts.push(labelFragments.join(''));
                parts.push('</g>');

                legendRows.forEach(function (row, rowIndex) {{
                    var rowY = legendTop + rowIndex * legendRowHeight;
                    var rowWidth = row.reduce(function (sum, entry) {{ return sum + entry.width; }}, 0) + legendChipGap * (row.length - 1);
                    var rowStartX = outerMargin + Math.max(0, (contentWidth - rowWidth) / 2);
                    var chipX = rowStartX;
                    row.forEach(function (entry) {{
                        parts.push('<rect x="' + chipX + '" y="' + rowY + '" width="' + entry.width + '" height="' + legendChipHeight + '" fill="#f7f8fa" stroke="#DADCE0" stroke-width="1" />');
                        parts.push('<circle cx="' + (chipX + legendChipPaddingX + legendSwatchSize / 2) + '" cy="' + (rowY + legendChipHeight / 2) + '" r="' + (legendSwatchSize / 2) + '" fill="' + entry.item.color + '" stroke="' + entry.item.stroke + '" stroke-width="2" />');
                        parts.push('<text x="' + (chipX + legendChipPaddingX + legendSwatchSize + 8) + '" y="' + (rowY + legendChipHeight / 2 + 4) + '" font-family="Yu Gothic, Meiryo, sans-serif" font-size="12" font-weight="700" fill="#171717">' + escapeXml(entry.item.label) + '</text>');
                        chipX += entry.width + legendChipGap;
                    }});
                }});

                parts.push('</svg>');
                return parts.join('');
            }}

            function measureTextWidth(text, font) {{
                if (!measureTextWidth._canvas) {{
                    measureTextWidth._canvas = document.createElement('canvas');
                }}
                var ctx = measureTextWidth._canvas.getContext('2d');
                ctx.font = font;
                return ctx.measureText(text || '').width;
            }}

            function wrapTextByWidth(text, font, maxWidth) {{
                var lines = [];
                var current = '';
                for (var i = 0; i < text.length; i += 1) {{
                    var candidate = current + text[i];
                    if (current.length > 0 && measureTextWidth(candidate, font) > maxWidth) {{
                        lines.push(current);
                        current = text[i];
                    }} else {{
                        current = candidate;
                    }}
                }}
                if (current.length > 0) {{
                    lines.push(current);
                }}
                return lines;
            }}

            function buildHistogramExportSvg(metricId) {{
                var card = document.querySelector('.kpi-histogram[data-metric-id="' + metricId + '"]');
                if (!card) {{
                    return null;
                }}

                var sourceSvg = card.querySelector('.histogram-svg');
                if (!sourceSvg) {{
                    return null;
                }}

                var viewBoxParts = (sourceSvg.getAttribute('viewBox') || '0 0 860 220').split(/\s+/);
                var chartWidth = Number(viewBoxParts[2]) || 860;
                var chartHeight = Number(viewBoxParts[3]) || 220;
                var chartScale = 1.5;

                var metricConfig = metricConfigs[metricId];
                var titleNode = card.querySelector('.kpi-label');
                var titleText = titleNode ? titleNode.textContent.trim() : ((metricConfig ? metricConfig.label : metricId) + '分布');
                var subtitleNode = card.querySelector(':scope > span');
                var subtitleText = subtitleNode ? subtitleNode.textContent.trim() : '';
                var captionNode = card.querySelector('.js-histogram-caption');
                var captionText = captionNode ? captionNode.textContent.trim() : '';

                var legendItems = Array.prototype.map.call(card.querySelectorAll('.histogram-legend-item'), function (item) {{
                    var swatch = item.querySelector('.swatch');
                    var labelNode = item.querySelector('span:last-child');
                    var swatchStyle = swatch ? getComputedStyle(swatch) : null;
                    return {{
                        color: swatchStyle ? swatchStyle.backgroundColor : '#374151',
                        stroke: swatchStyle ? swatchStyle.borderTopColor : '#ffffff',
                        label: labelNode ? labelNode.textContent.trim() : ''
                    }};
                }});

                var outerMargin = 20;
                var chartInset = 12;
                var contentWidth = chartWidth * chartScale + chartInset * 2;
                var totalWidth = outerMargin * 2 + contentWidth;
                var subtitleFont = '14px "Yu Gothic", Meiryo, sans-serif';
                var captionFont = '13px "Yu Gothic", Meiryo, sans-serif';
                var legendFont = 'bold 12px "Yu Gothic", Meiryo, sans-serif';

                var titleHeight = 26;
                var subtitleHeight = subtitleText ? 24 : 0;
                var chartBoxTop = outerMargin + titleHeight + subtitleHeight + 10;
                var chartBoxHeight = chartHeight * chartScale + chartInset * 2;

                var legendChipPaddingX = 10;
                var legendChipHeight = 32;
                var legendSwatchSize = 14;
                var legendChipGap = 10;
                var legendRowGap = 8;
                var legendRows = [];
                if (legendItems.length) {{
                    var chipWidths = legendItems.map(function (item) {{
                        return legendSwatchSize + 8 + measureTextWidth(item.label, legendFont) + legendChipPaddingX * 2;
                    }});
                    var currentRow = [];
                    var currentWidth = 0;
                    legendItems.forEach(function (item, index) {{
                        var chipWidth = chipWidths[index];
                        var addWidth = currentRow.length ? chipWidth + legendChipGap : chipWidth;
                        if (currentRow.length > 0 && currentWidth + addWidth > contentWidth) {{
                            legendRows.push(currentRow);
                            currentRow = [];
                            currentWidth = 0;
                            addWidth = chipWidth;
                        }}
                        currentRow.push({{ item: item, width: chipWidth }});
                        currentWidth += addWidth;
                    }});
                    if (currentRow.length) {{
                        legendRows.push(currentRow);
                    }}
                }}
                var legendTop = chartBoxTop + chartBoxHeight + 24;
                var legendRowHeight = legendChipHeight + legendRowGap;
                var legendHeight = legendRows.length ? legendRows.length * legendRowHeight + 8 : 0;

                var captionLines = captionText ? wrapTextByWidth(captionText, captionFont, contentWidth) : [];
                var captionLineHeight = 20;
                var captionTop = legendTop + legendHeight + (legendRows.length ? 16 : 0);
                var captionHeight = captionLines.length * captionLineHeight;

                var totalHeight = captionTop + captionHeight + outerMargin;
                var centerX = totalWidth / 2;

                var styleBlock = ''
                    + '<style>'
                    + '.histogram-axis {{ stroke: #777; stroke-width: 2; }}'
                    + '.histogram-tick {{ stroke: #c9cfd6; stroke-width: 1; stroke-dasharray: 2 4; }}'
                    + '.histogram-label {{ fill: #171717; font-size: 9px; font-weight: 700; font-family: "Yu Gothic", Meiryo, sans-serif; }}'
                    + '.histogram-count {{ fill: #171717; font-size: 9px; font-weight: 700; font-family: "Yu Gothic", Meiryo, sans-serif; }}'
                    + '</style>';

                var parts = [];
                parts.push('<svg xmlns="http://www.w3.org/2000/svg" width="' + totalWidth + '" height="' + totalHeight + '" viewBox="0 0 ' + totalWidth + ' ' + totalHeight + '">');
                parts.push('<rect width="100%" height="100%" fill="#ffffff" />');
                parts.push(styleBlock);
                parts.push('<rect x="0.5" y="0.5" width="' + (totalWidth - 1) + '" height="' + (totalHeight - 1) + '" fill="none" stroke="#DADCE0" stroke-width="1" />');
                parts.push('<text x="' + centerX + '" y="' + (outerMargin + 18) + '" text-anchor="middle" font-family="Yu Gothic, Meiryo, sans-serif" font-size="20" font-weight="700" fill="#171717">' + escapeXml(titleText) + '</text>');
                if (subtitleText) {{
                    parts.push('<text x="' + centerX + '" y="' + (outerMargin + titleHeight + 14) + '" text-anchor="middle" font-family="Yu Gothic, Meiryo, sans-serif" font-size="14" fill="#171717">' + escapeXml(subtitleText) + '</text>');
                }}
                parts.push('<rect x="' + outerMargin + '" y="' + chartBoxTop + '" width="' + contentWidth + '" height="' + chartBoxHeight + '" fill="#ffffff" stroke="#DADCE0" stroke-width="1" />');
                parts.push('<g transform="translate(' + (outerMargin + chartInset) + ',' + (chartBoxTop + chartInset) + ') scale(' + chartScale + ')">' + sourceSvg.innerHTML + '</g>');

                legendRows.forEach(function (row, rowIndex) {{
                    var rowY = legendTop + rowIndex * legendRowHeight;
                    var rowWidth = row.reduce(function (sum, entry) {{ return sum + entry.width; }}, 0) + legendChipGap * (row.length - 1);
                    var rowStartX = outerMargin + Math.max(0, (contentWidth - rowWidth) / 2);
                    var chipX = rowStartX;
                    row.forEach(function (entry) {{
                        parts.push('<rect x="' + chipX + '" y="' + rowY + '" width="' + entry.width + '" height="' + legendChipHeight + '" fill="#f7f8fa" stroke="#DADCE0" stroke-width="1" />');
                        parts.push('<circle cx="' + (chipX + legendChipPaddingX + legendSwatchSize / 2) + '" cy="' + (rowY + legendChipHeight / 2) + '" r="' + (legendSwatchSize / 2) + '" fill="' + entry.item.color + '" stroke="' + entry.item.stroke + '" stroke-width="2" />');
                        parts.push('<text x="' + (chipX + legendChipPaddingX + legendSwatchSize + 8) + '" y="' + (rowY + legendChipHeight / 2 + 4) + '" font-family="Yu Gothic, Meiryo, sans-serif" font-size="12" font-weight="700" fill="#171717">' + escapeXml(entry.item.label) + '</text>');
                        chipX += entry.width + legendChipGap;
                    }});
                }});

                captionLines.forEach(function (line, index) {{
                    parts.push('<text x="' + outerMargin + '" y="' + (captionTop + index * captionLineHeight + 14) + '" font-family="Yu Gothic, Meiryo, sans-serif" font-size="13" fill="#171717">' + escapeXml(line) + '</text>');
                }});

                parts.push('</svg>');
                return parts.join('');
            }}

            function downloadSvgText(fileName, svgText) {{
                var blob = new Blob([svgText], {{ type: 'image/svg+xml;charset=utf-8' }});
                var url = URL.createObjectURL(blob);
                var link = document.createElement('a');
                link.href = url;
                link.download = fileName;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                window.setTimeout(function () {{
                    URL.revokeObjectURL(url);
                }}, 1000);
            }}

            function downloadDataUrl(fileName, dataUrl) {{
                var link = document.createElement('a');
                link.href = dataUrl;
                link.download = fileName;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            }}

            function rasterizeElementAsPng(element, fileName, onFallback) {{
                if (!element) {{
                    onFallback();
                    return;
                }}

                var rect = element.getBoundingClientRect();
                var width = Math.ceil(rect.width);
                var height = Math.ceil(rect.height);
                if (!width || !height) {{
                    onFallback();
                    return;
                }}

                var styleNode = document.querySelector('style');
                var styleText = styleNode ? styleNode.textContent : '';
                var padding = 16;
                var totalWidth = width + padding * 2;
                var totalHeight = height + padding * 2;

                var svgMarkup = ''
                    + '<svg xmlns="http://www.w3.org/2000/svg" width="' + totalWidth + '" height="' + totalHeight + '">'
                    + '<rect width="100%" height="100%" fill="#ffffff" />'
                    + '<foreignObject x="' + padding + '" y="' + padding + '" width="' + width + '" height="' + height + '">'
                    + '<div xmlns="http://www.w3.org/1999/xhtml">'
                    + '<style>' + styleText + '</style>'
                    + element.outerHTML
                    + '</div>'
                    + '</foreignObject>'
                    + '</svg>';

                var svgBlob = new Blob([svgMarkup], {{ type: 'image/svg+xml;charset=utf-8' }});
                var url = URL.createObjectURL(svgBlob);
                var img = new Image();

                img.onload = function () {{
                    try {{
                        var dpr = window.devicePixelRatio || 1;
                        var canvas = document.createElement('canvas');
                        canvas.width = totalWidth * dpr;
                        canvas.height = totalHeight * dpr;
                        var ctx = canvas.getContext('2d');
                        ctx.scale(dpr, dpr);
                        ctx.fillStyle = '#ffffff';
                        ctx.fillRect(0, 0, totalWidth, totalHeight);
                        ctx.drawImage(img, 0, 0, totalWidth, totalHeight);
                        var pngUrl = canvas.toDataURL('image/png');
                        downloadDataUrl(fileName, pngUrl);
                    }} catch (err) {{
                        onFallback();
                    }} finally {{
                        URL.revokeObjectURL(url);
                    }}
                }};

                img.onerror = function () {{
                    URL.revokeObjectURL(url);
                    onFallback();
                }};

                img.src = url;
            }}

            function exportHistogramCardAsPng(metricId, onFallback) {{
                var metricConfig = metricConfigs[metricId];
                var label = metricConfig ? metricConfig.label : metricId;
                rasterizeElementAsPng(document.querySelector('.kpi-histogram[data-metric-id="' + metricId + '"]'), 'loader-histogram-' + slugifyText(label) + '.png', onFallback);
            }}

            function exportMetricChartAsPng(metricRow, onFallback) {{
                if (!metricRow || metricRow.style.display === 'none') {{
                    onFallback();
                    return;
                }}

                var chartContainer = metricRow.querySelector('.range-chart-svg');
                var metricNameNode = metricRow.querySelector('.metric-name');
                var metricName = metricNameNode ? metricNameNode.textContent.trim() : (metricRow.getAttribute('data-metric-id') || 'chart');
                rasterizeElementAsPng(chartContainer, 'loader-chart-' + slugifyText(metricName) + '.png', onFallback);
            }}

            function downloadMetricChart(metricRow) {{
                if (!metricRow || metricRow.style.display === 'none') {{
                    return false;
                }}

                exportMetricChartAsPng(metricRow, function () {{
                    var svgText = buildExportSvg(metricRow);
                    if (!svgText) {{
                        return;
                    }}

                    var metricNameNode = metricRow.querySelector('.metric-name');
                    var metricName = metricNameNode ? metricNameNode.textContent.trim() : (metricRow.getAttribute('data-metric-id') || 'chart');
                    downloadSvgText('loader-chart-' + slugifyText(metricName) + '.svg', svgText);
                }});
                return true;
            }}

            function downloadVisibleCharts() {{
                var visibleRows = Array.prototype.filter.call(
                    document.querySelectorAll('.metric-row'),
                    function (row) {{
                        return row.style.display !== 'none';
                    }}
                );

                visibleRows.forEach(function (row, index) {{
                    window.setTimeout(function () {{
                        downloadMetricChart(row);
                    }}, index * 180);
                }});
            }}

            document.querySelectorAll('[data-unit-system]').forEach(function (button) {{
                button.addEventListener('click', function () {{
                    applyUnitSystem(button.getAttribute('data-unit-system'));
                }});
            }});

            document.querySelectorAll('.metric-toggle-input').forEach(function (input) {{
                input.addEventListener('change', applyMetricVisibility);
            }});

            document.querySelectorAll('.brand-filter-input').forEach(function (input) {{
                input.addEventListener('change', applyBrandVisibility);
            }});

            document.querySelectorAll('.js-horsepower-min, .js-horsepower-max').forEach(function (input) {{
                input.addEventListener('input', applyBrandVisibility);
                input.addEventListener('change', applyBrandVisibility);
            }});

            document.querySelectorAll('.js-download-chart').forEach(function (button) {{
                button.addEventListener('click', function () {{
                    var metricId = button.getAttribute('data-download-target');
                    var metricRow = document.querySelector('.metric-row[data-metric-id="' + metricId + '"]');
                    downloadMetricChart(metricRow);
                }});
            }});

            document.querySelectorAll('.js-download-histogram').forEach(function (button) {{
                button.addEventListener('click', function () {{
                    var metricId = button.getAttribute('data-download-target');
                    var metricConfig = metricConfigs[metricId];
                    exportHistogramCardAsPng(metricId, function () {{
                        var svgText = buildHistogramExportSvg(metricId);
                        if (svgText) {{
                            downloadSvgText('loader-histogram-' + slugifyText(metricConfig ? metricConfig.label : metricId) + '.svg', svgText);
                        }}
                    }});
                }});
            }});

            var bulkDownloadButton = document.querySelector('.js-download-visible-charts');
            if (bulkDownloadButton) {{
                bulkDownloadButton.addEventListener('click', downloadVisibleCharts);
            }}

            bindHistogramTooltips();
            applyUnitSystem('metric');
            applyMetricVisibility();
            applyBrandVisibility();
        }})();
    </script>
</body>
</html>
'''


def main() -> None:
    rows = load_rows()
    summaries = [row for row in rows if row.is_series_summary]
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    MARKDOWN_PATH.write_text(build_markdown(rows, summaries), encoding="utf-8")
    HTML_PATH.write_text(build_html(rows, summaries), encoding="utf-8")
    print(f"wrote_markdown={MARKDOWN_PATH}")
    print(f"wrote_html={HTML_PATH}")


if __name__ == "__main__":
    main()