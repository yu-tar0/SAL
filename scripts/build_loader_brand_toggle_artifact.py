from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass
from pathlib import Path

import duckdb


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "db" / "knowledge.duckdb"
ARTIFACT_ID = "2026-07-02-comparison-avant-bobcat-toggle"
ARTIFACT_DIR = ROOT / "artifacts" / ARTIFACT_ID
MARKDOWN_PATH = ARTIFACT_DIR / f"{ARTIFACT_ID}.md"
HTML_PATH = ARTIFACT_DIR / f"{ARTIFACT_ID}.web.html"
TODAY = "2026-07-02"

THEME_METADATA = {
    "theme_id": "blackrock-v1-color",
    "theme_name": "BlackRock",
    "theme_version": 1,
    "applied_on": TODAY,
    "source_theme_file": ".github/skills/html-artifact/assets/themes.json",
    "colors": {
        "page_bg": "#F5F6F8",
        "paper_bg": "#FFFFFF",
        "ink": "#171717",
        "muted": "#5F6368",
        "accent": "#000000",
        "line": "#DADCE0",
        "soft": "#F3F4F6",
        "warn": "#8A5A00",
        "warn_bg": "#FFF4D8",
    },
}

BRAND_ORDER = [
    "Avant Tecno",
    "Bobcat",
    "Case",
    "Gianni Ferrari",
    "Tobroco-Giant / Giant",
    "MultiOne",
    "New Holland",
    "Yanmar",
]
BRAND_LABELS = {
    "Avant Tecno": "AVANT",
    "Bobcat": "Bobcat",
    "Case": "Case",
    "Gianni Ferrari": "Gianni Ferrari",
    "Tobroco-Giant / Giant": "Giant",
    "MultiOne": "MultiOne",
    "New Holland": "New Holland",
    "Yanmar": "Yanmar",
}
SERIES_COLORS = {
    "200 series": "#1D4ED8",
    "400 series": "#0F766E",
    "500 series": "#E85D04",
    "600 series": "#7C3AED",
    "700 series": "#B91C1C",
    "800 series": "#6B4F2A",
    "e500 series": "#2F7D32",
    "e700 series": "#0B5D1E",
    "Small Articulated Loaders": "#0F4C81",
}
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
METRICS = [
    {"id": "horsepower", "key": "horsepower", "label": "エンジン出力", "metric_unit": "hp", "parse_unit": "hp", "family": None, "us_unit": "hp", "extract_mode": "range_max"},
    {"id": "lift_capacity", "key": "lift_capacity_kg", "label": "リフト容量", "metric_unit": "kg", "parse_unit": "kg", "family": "weight", "us_unit": "lb", "extract_mode": "range_max"},
    {"id": "lift_height", "key": "lift_height_mm", "label": "リフト高", "metric_unit": "mm", "parse_unit": "mm", "family": "length", "us_unit": "in", "extract_mode": "range_max"},
    {"id": "telescopic_length", "key": "telescopic_length_mm", "label": "テレスコ長", "metric_unit": "mm", "parse_unit": "mm", "family": "length", "us_unit": "in", "extract_mode": "range_max"},
    {"id": "aux_flow", "key": "aux_hydraulic_flow_pressure_l_min_mpa", "label": "補助油圧流量", "metric_unit": "L/min", "parse_unit": "L/min", "family": "flow", "us_unit": "gpm", "extract_mode": "first"},
    {"id": "aux_pressure", "key": "aux_hydraulic_flow_pressure_l_min_mpa", "label": "補助油圧圧力", "metric_unit": "MPa", "parse_unit": "MPa", "family": "pressure", "us_unit": "PSI", "extract_mode": "second"},
    {"id": "max_breakout_force", "key": "max_breakout_force_kgf", "label": "最大ブレークアウト力", "metric_unit": "kgf", "parse_unit": "kgf", "family": "force", "us_unit": "lbf", "extract_mode": "range_max"},
    {"id": "max_tow_force", "key": "max_tow_force_kgf", "label": "最大牽引力", "metric_unit": "kgf", "parse_unit": "kgf", "family": "force", "us_unit": "lbf", "extract_mode": "range_max"},
    {"id": "max_torque", "key": "max_torque_nm_rpm", "label": "最大トルク", "metric_unit": "N·m", "parse_unit": "N·m", "family": "torque", "us_unit": "lb-ft", "extract_mode": "first"},
    {"id": "max_speed", "key": "max_speed_kmh", "label": "最高速度", "metric_unit": "km/h", "parse_unit": "km/h", "family": "speed", "us_unit": "mph", "extract_mode": "range_max"},
    {"id": "operating_weight", "key": "operating_weight_kg", "label": "運転質量", "metric_unit": "kg", "parse_unit": "kg", "family": "weight", "us_unit": "lb", "extract_mode": "range_max"},
    {"id": "turning_radius_inner", "key": "turning_radius_inner_outer_mm", "label": "旋回半径 内側", "metric_unit": "mm", "parse_unit": "mm", "family": "length", "us_unit": "in", "extract_mode": "first"},
    {"id": "turning_radius_outer", "key": "turning_radius_inner_outer_mm", "label": "旋回半径 外側", "metric_unit": "mm", "parse_unit": "mm", "family": "length", "us_unit": "in", "extract_mode": "second"},
    {"id": "width", "key": "width_mm", "label": "全幅", "metric_unit": "mm", "parse_unit": "mm", "family": "length", "us_unit": "in", "extract_mode": "first"},
    {"id": "length", "key": "length_mm", "label": "全長", "metric_unit": "mm", "parse_unit": "mm", "family": "length", "us_unit": "in", "extract_mode": "range_max"},
    {"id": "height", "key": "height_mm", "label": "全高", "metric_unit": "mm", "parse_unit": "mm", "family": "length", "us_unit": "in", "extract_mode": "range_max"},
    {"id": "battery_capacity", "key": "battery_capacity", "label": "バッテリー容量", "metric_unit": "kWh", "parse_unit": "kWh", "family": None, "us_unit": "kWh", "extract_mode": "range_max"},
]


@dataclass
class ModelRow:
    manufacturer_name: str
    series: str
    sal_model: str
    powertrain_type: str
    horsepower: str
    lift_capacity_kg: str
    lift_height_mm: str
    telescopic_length_mm: str
    aux_hydraulic_flow_pressure_l_min_mpa: str
    max_breakout_force_kgf: str
    max_tow_force_kgf: str
    max_torque_nm_rpm: str
    max_speed_kmh: str
    operating_weight_kg: str
    turning_radius_inner_outer_mm: str
    width_mm: str
    length_mm: str
    height_mm: str
    transmission: str
    fuel: str
    battery_capacity: str
    charge_time: str
    pdf_page: str
    catalog_page_url: str
    hydraulic_system_notes: str

    @property
    def brand_label(self) -> str:
        return BRAND_LABELS.get(self.manufacturer_name, self.manufacturer_name)

    @property
    def brand_id(self) -> str:
        return slugify(self.brand_label)

    @property
    def label(self) -> str:
        return re.sub(r"^(?:AVANT|Avant|Bobcat)\s+", "", self.sal_model).strip()

    @property
    def is_series_summary(self) -> bool:
        return self.label.lower().endswith("series")

    @property
    def is_electric(self) -> bool:
        return self.powertrain_type.lower().startswith("electric")

    @property
    def series_color(self) -> str:
        return SERIES_COLORS.get(self.series, "#374151")


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def clean_text(value: object) -> str:
    if value is None:
        return ""
    return " ".join(str(value).split())


def md_cell(value: str) -> str:
    if not value:
        return "-"
    return value.replace("|", "\\|")


def html_cell(value: str) -> str:
    if not value:
        return "-"
    return html.escape(value)


def parse_measure(text: str, target_unit: str, extract_mode: str = "range_max") -> float | None:
    normalized = clean_text(text).replace(",", "")
    if not normalized:
        return None

    numbers = [float(value) for value in re.findall(r"\d+(?:\.\d+)?", normalized)]
    if not numbers:
        return None

    lower = normalized.lower()
    if target_unit == "mm":
        if re.search(r"(^|[^a-z])m($|[^a-z])", lower):
            numbers = [value * 1000 for value in numbers]

    if extract_mode == "first":
        return numbers[0]
    if extract_mode == "second":
        return numbers[1] if len(numbers) > 1 else None
    if any(sep in normalized for sep in ["-", "–", "to"]) and len(numbers) > 1:
        return numbers[-1]
    return numbers[0]


def format_display_value(value: float, family: str | None, system: str, metric_unit: str, us_unit: str) -> str:
    unit = metric_unit if system == "metric" else us_unit
    converted = convert_metric_value(value, family, system)
    if unit in {"mm", "kg", "hp", "kgf", "kWh"}:
        return str(int(round(converted)))
    rounded = round(converted, 1)
    if float(rounded).is_integer():
        return str(int(rounded))
    return f"{rounded:.1f}"


def convert_metric_value(value: float, family: str | None, system: str) -> float:
    if system == "metric" or family is None:
        return value
    if family == "length":
        return value / 25.4
    if family == "weight":
        return value * 2.2046226218
    if family == "speed":
        return value * 0.6213711922
    if family == "flow":
        return value / 3.785411784
    if family == "pressure":
        return value * 145.03773773
    if family == "force":
        return value * 2.2046226218
    if family == "torque":
        return value * 0.7375621493
    return value


def convert_metric_text_to_us(text: str, family: str | None) -> str:
    normalized = clean_text(text)
    if not normalized or normalized == "-" or family is None:
        return normalized or "-"

    if family == "length":
        if "mm" in normalized.lower():
            converted = re.sub(
                r"\d+(?:,\d{3})*(?:\.\d+)?",
                lambda match: format_display_value(float(match.group(0).replace(',', '')), family, "us", "mm", "in"),
                normalized,
            )
            return re.sub(r"mm", "in", converted, flags=re.IGNORECASE)
        if re.search(r"(^|[^a-z])m($|[^a-z])", normalized.lower()):
            converted = re.sub(
                r"\d+(?:,\d{3})*(?:\.\d+)?",
                lambda match: format_display_value(float(match.group(0).replace(',', '')) * 1000, family, "us", "mm", "in"),
                normalized,
            )
            return re.sub(r"(^|[^a-z])m($|[^a-z])", lambda match: f"{match.group(1)}in{match.group(2)}", converted, flags=re.IGNORECASE)

    if family == "weight":
        converted = re.sub(
            r"\d+(?:,\d{3})*(?:\.\d+)?",
            lambda match: format_display_value(float(match.group(0).replace(',', '')), family, "us", "kg", "lb"),
            normalized,
        )
        return re.sub(r"kg", "lb", converted, flags=re.IGNORECASE)

    if family == "speed":
        converted = re.sub(
            r"\d+(?:,\d{3})*(?:\.\d+)?",
            lambda match: format_display_value(float(match.group(0).replace(',', '')), family, "us", "km/h", "mph"),
            normalized,
        )
        return re.sub(r"km/h", "mph", converted, flags=re.IGNORECASE)

    if family == "flow":
        converted = re.sub(
            r"\d+(?:,\d{3})*(?:\.\d+)?",
            lambda match: format_display_value(float(match.group(0).replace(',', '')), family, "us", "L/min", "gpm"),
            normalized,
        )
        return re.sub(r"L/min", "gpm", converted, flags=re.IGNORECASE)

    if family == "pressure":
        converted = re.sub(
            r"\d+(?:,\d{3})*(?:\.\d+)?",
            lambda match: format_display_value(float(match.group(0).replace(',', '')), family, "us", "MPa", "PSI"),
            normalized,
        )
        return re.sub(r"MPa", "PSI", converted, flags=re.IGNORECASE)

    if family == "force":
        converted = re.sub(
            r"\d+(?:,\d{3})*(?:\.\d+)?",
            lambda match: format_display_value(float(match.group(0).replace(',', '')), family, "us", "kgf", "lbf"),
            normalized,
        )
        return re.sub(r"kgf", "lbf", converted, flags=re.IGNORECASE)

    if family == "torque":
        converted = re.sub(
            r"\d+(?:,\d{3})*(?:\.\d+)?",
            lambda match: format_display_value(float(match.group(0).replace(',', '')), family, "us", "N·m", "lb-ft"),
            normalized,
        )
        return re.sub(r"N·m", "lb-ft", converted, flags=re.IGNORECASE)

    return normalized


def render_switchable_text(metric_text: str, family: str | None) -> str:
    metric_value = metric_text if metric_text else "-"
    us_value = convert_metric_text_to_us(metric_value, family)
    return (
        f'<span class="js-value-switch" data-metric="{html.escape(metric_value)}" '
        f'data-us="{html.escape(us_value)}">{html.escape(metric_value)}</span>'
    )


def series_sort_key(name: str) -> tuple[int, str]:
    match = re.search(r"(\d+)", name)
    if match:
        return (int(match.group(1)), name)
    return (9999, name)


def render_table(headers: list[str], rows: list[list[str]], families: list[str | None] | None = None) -> str:
    if not rows:
        return '<div class="empty-state">該当データなし</div>'

    head = "".join(f"<th>{html.escape(header)}</th>" for header in headers)
    body_rows = []
    for row in rows:
        cells = []
        for index, cell in enumerate(row):
            family = families[index] if families is not None else None
            if family is None:
                cells.append(f"<td>{html_cell(cell)}</td>")
            else:
                cells.append(f"<td>{render_switchable_text(cell, family)}</td>")
        body_rows.append("<tr>" + "".join(cells) + "</tr>")
    return f'<table class="data-table"><thead><tr>{head}</tr></thead><tbody>{"".join(body_rows)}</tbody></table>'


def render_range_svg(
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

    minimum = min(value for _, value in values)
    maximum = max(value for _, value in values)
    if minimum == maximum:
        maximum = minimum + 1

    chart_width = 780
    chart_height = 28 + len(values) * 24 + 48
    axis_y = 18 + len(values) * 24
    left_pad = 34
    max_label_chars = max(
        len(f"{row.label}/{format_display_value(value, family, 'metric', metric_unit, us_unit)}")
        for row, value in values
    )
    right_pad = max(24, 24 + max_label_chars * 8)
    usable_width = chart_width - left_pad - right_pad

    def x_pos(value: float) -> float:
        return left_pad + (value - minimum) / (maximum - minimum) * usable_width

    tick_values = [minimum + (maximum - minimum) * step / 4 for step in range(5)]
    svg_parts = [
        f'<svg class="range-svg" viewBox="0 0 {chart_width} {chart_height}" role="img" aria-label="{html.escape(metric_key)} range chart">',
        f'<line x1="{left_pad}" y1="{axis_y}" x2="{chart_width - right_pad}" y2="{axis_y}" class="axis-line" />',
    ]

    for tick in tick_values:
        x = x_pos(tick)
        metric_label = format_display_value(tick, family, "metric", metric_unit, us_unit)
        us_label = format_display_value(tick, family, "us", metric_unit, us_unit)
        svg_parts.append(f'<line x1="{x:.1f}" y1="10" x2="{x:.1f}" y2="{axis_y}" class="axis-guide" />')
        svg_parts.append(
            f'<text x="{x:.1f}" y="{axis_y + 18}" class="axis-label js-value-switch" '
            f'text-anchor="middle" data-metric="{html.escape(metric_label)}" '
            f'data-us="{html.escape(us_label)}">{html.escape(metric_label)}</text>'
        )

    for index, (row, value) in enumerate(values):
        y = 18 + index * 24
        x = x_pos(value)
        metric_marker = f"{row.label}/{format_display_value(value, family, 'metric', metric_unit, us_unit)}"
        us_marker = f"{row.label}/{format_display_value(value, family, 'us', metric_unit, us_unit)}"
        svg_parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="7" fill="{row.series_color}" stroke="#ffffff" stroke-width="2" />')
        svg_parts.append(
            f'<text x="{x + 12:.1f}" y="{y + 4:.1f}" class="marker-label js-value-switch" '
            f'data-metric="{html.escape(metric_marker)}" data-us="{html.escape(us_marker)}">{html.escape(metric_marker)}</text>'
        )

    svg_parts.append("</svg>")
    return "".join(svg_parts)


def load_rows() -> list[ModelRow]:
    manufacturer_names = ", ".join(f"'{name}'" for name in BRAND_ORDER)
    sql = """
    SELECT
      COALESCE(manufacturer_name, '') AS manufacturer_name,
      COALESCE(series, '') AS series,
      COALESCE(sal_model, '') AS sal_model,
      COALESCE(powertrain_type, '') AS powertrain_type,
      COALESCE(horsepower, '') AS horsepower,
      COALESCE(lift_capacity_kg, '') AS lift_capacity_kg,
      COALESCE(lift_height_mm, '') AS lift_height_mm,
      COALESCE(telescopic_length_mm, '') AS telescopic_length_mm,
      COALESCE(aux_hydraulic_flow_pressure_l_min_mpa, '') AS aux_hydraulic_flow_pressure_l_min_mpa,
      COALESCE(max_breakout_force_kgf, '') AS max_breakout_force_kgf,
      COALESCE(max_tow_force_kgf, '') AS max_tow_force_kgf,
      COALESCE(max_torque_nm_rpm, '') AS max_torque_nm_rpm,
      COALESCE(max_speed_kmh, '') AS max_speed_kmh,
      COALESCE(operating_weight_kg, '') AS operating_weight_kg,
      COALESCE(turning_radius_inner_outer_mm, '') AS turning_radius_inner_outer_mm,
      COALESCE(width_mm, '') AS width_mm,
      COALESCE(length_mm, '') AS length_mm,
      COALESCE(height_mm, '') AS height_mm,
      COALESCE(transmission, '') AS transmission,
      COALESCE(fuel, '') AS fuel,
      COALESCE(battery_capacity, '') AS battery_capacity,
      COALESCE(charge_time, '') AS charge_time,
      COALESCE(pdf_page, '') AS pdf_page,
      COALESCE(catalog_page_url, '') AS catalog_page_url,
      COALESCE(hydraulic_system_notes, '') AS hydraulic_system_notes
    FROM loader_specification_import_rows
    WHERE COALESCE(TRIM(sal_model), '') <> ''
            AND manufacturer_name IN (""" + manufacturer_names + """)
    ORDER BY manufacturer_name, series, sal_model
    """

    with duckdb.connect(str(DB_PATH), read_only=True) as con:
        records = con.execute(sql).fetchall()
    return [ModelRow(*[clean_text(value) for value in record]) for record in records]


def group_rows_by_brand(rows: list[ModelRow]) -> list[tuple[str, str, list[ModelRow]]]:
    groups: list[tuple[str, str, list[ModelRow]]] = []
    for manufacturer_name in BRAND_ORDER:
        brand_rows = [row for row in rows if row.manufacturer_name == manufacturer_name]
        if not brand_rows:
            continue
        groups.append((slugify(BRAND_LABELS.get(manufacturer_name, manufacturer_name)), BRAND_LABELS.get(manufacturer_name, manufacturer_name), brand_rows))
    return groups


def brand_summary_text(brand_label: str, rows: list[ModelRow]) -> list[str]:
    comparison_rows = [row for row in rows if not row.is_series_summary]
    electric_count = sum(1 for row in comparison_rows if row.is_electric)
    series_names = sorted({row.series for row in comparison_rows}, key=series_sort_key)
    notes = [f"{brand_label} の個別型式 {len(comparison_rows)} 行を共通 schema で比較できるようにした。"]
    if electric_count:
        notes.append(f"電動モデル {electric_count} 行も同じページ内で切り替えて確認できる。")
    else:
        notes.append("現時点では電動モデル行はなく、すべて燃焼系またはエンジン系として載っている。")
    notes.append(f"シリーズは {', '.join(series_names)} を含む。")
    return notes


def build_markdown(groups: list[tuple[str, str, list[ModelRow]]]) -> str:
    total_rows = sum(len([row for row in rows if not row.is_series_summary]) for _, _, rows in groups)
    lines = [
        "---",
        "title: マルチブランド ローダー比較 切替ビュー",
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
        "purpose: 共通 curated テーブルから複数ブランドを選択式で切り替え表示できる Web HTML を作る",
        "---",
        "",
        "# マルチブランド ローダー比較 切替ビュー",
        "",
        "共通 curated テーブル `loader_specification_import_rows` を入力元に、複数ブランドの表示をボタンで切り替えられる Web Artifact を作成した。既存の AVANT 単独 HTML のレイアウトを踏襲しつつ、ブランド単位で比較レンジ、型式一覧、分類比較をまとめている。",
        "",
        "## 要約",
        "",
        f"- 対象の個別型式は合計 {total_rows} 行。",
    ]

    for _, brand_label, rows in groups:
        lines.append(f"- {brand_label}: " + " ".join(brand_summary_text(brand_label, rows)))

    lines.extend(
        [
            "",
            "## Provenance",
            "",
            "- DuckDB: `db/knowledge.duckdb`",
            "- 参照テーブル: `loader_specification_import_rows`",
            "- 生成スクリプト: `scripts/build_loader_brand_toggle_artifact.py`",
            f"- 生成物: `{MARKDOWN_PATH.name}` / `{HTML_PATH.name}`",
            "",
            "## 未解決点",
            "",
            "- ブランド間で保有列は揃っていても、実際に埋まっている項目数は異なる。",
            "- 電動モデルやシリーズ要約は現状 AVANT 側に偏っている。",
            "- 機能フラグやオプション差分はまだ構造化していない。",
        ]
    )
    return "\n".join(lines) + "\n"


def render_brand_panel(brand_id: str, brand_label: str, rows: list[ModelRow], is_active: bool) -> str:
    comparison_rows = [row for row in rows if not row.is_series_summary]
    summaries = [row for row in rows if row.is_series_summary]
    electric = [row for row in comparison_rows if row.is_electric]

    metrics_html = []
    for metric in METRICS:
        metrics_html.append(
            (
                f'<tr class="metric-row" data-metric-id="{html.escape(metric["id"])}">'
                f'<th><div class="metric-name">{html.escape(metric["label"])}'
                '</div>'
                f'<div class="metric-unit js-unit-label" data-metric-unit="{html.escape(metric["metric_unit"])}" data-us-unit="{html.escape(metric["us_unit"])}">{html.escape(metric["metric_unit"])}'
                '</div></th>'
                f'<td class="range-cell">{render_range_svg(comparison_rows, metric["key"], metric["parse_unit"], metric["family"], metric["us_unit"], metric["extract_mode"])}'
                '</td>'
                f'<td><span class="js-unit-label" data-metric-unit="{html.escape(metric["metric_unit"])}" data-us-unit="{html.escape(metric["us_unit"])}">{html.escape(metric["metric_unit"])}'
                '</span></td>'
                '</tr>'
            )
        )

    series_names = sorted({row.series for row in comparison_rows}, key=series_sort_key)
    legend_items = "".join(
        f'<div class="legend-item"><span class="swatch" style="background:{SERIES_COLORS.get(name, "#374151")};"></span><span>{html.escape(name)}</span></div>'
        for name in series_names
    )

    model_table = render_table(
        ["シリーズ", "型式", "動力", "馬力", "リフト容量", "リフト高", "最高速度", "全幅", "運転質量", "バッテリー容量", "充電時間"],
        [
            [
                row.series,
                row.sal_model,
                row.powertrain_type,
                row.horsepower,
                row.lift_capacity_kg,
                row.lift_height_mm,
                row.max_speed_kmh,
                row.width_mm,
                row.operating_weight_kg,
                row.battery_capacity,
                row.charge_time,
            ]
            for row in comparison_rows
        ],
        [None, None, None, None, "weight", "length", "speed", "length", "weight", None, None],
    )
    summary_table = render_table(
        ["シリーズ行", "リフト容量", "リフト高", "最高速度", "バッテリー容量", "充電時間", "備考"],
        [
            [
                row.sal_model,
                row.lift_capacity_kg,
                row.lift_height_mm,
                row.max_speed_kmh,
                row.battery_capacity,
                row.charge_time,
                row.hydraulic_system_notes,
            ]
            for row in summaries
        ],
        [None, "weight", "length", "speed", None, None, None],
    )
    classification_table = render_table(
        ["型式", "シリーズ", "動力区分", "燃料", "トランスミッション", "備考"],
        [
            [
                row.sal_model,
                row.series,
                row.powertrain_type,
                row.fuel,
                row.transmission,
                row.hydraulic_system_notes,
            ]
            for row in comparison_rows
        ],
    )

    max_lift = max(comparison_rows, key=lambda row: parse_measure(row.lift_capacity_kg, "kg") or -1)
    max_speed = max(comparison_rows, key=lambda row: parse_measure(row.max_speed_kmh, "km/h") or -1)
    min_width = min(comparison_rows, key=lambda row: parse_measure(row.width_mm, "mm") or 10**9)
    series_count = len(series_names)
    powertrain_count = len({row.powertrain_type for row in comparison_rows if row.powertrain_type})
    powertrain_labels = ", ".join(sorted({row.powertrain_type for row in comparison_rows if row.powertrain_type})) or "-"

    subtitle = (
        f"共通 curated テーブル <code>loader_specification_import_rows</code> から {html.escape(brand_label)} を抽出した比較ビュー。"
        "上のブランド選択は表示対象だけを切り替え、単位切替とメトリクス表示設定はそのまま維持する。"
    )
    summary_intro = "シリーズ要約行を保持しているため、個別型式とは別に確認する。" if summaries else "このブランドにはシリーズ要約行はまだない。"
    electric_note = f"電動モデル {len(electric)} 行を含む。" if electric else "電動モデル行は未収録。"
    hidden_attrs = "" if is_active else ' aria-hidden="true" style="display:none;"'

    return f'''
        <section class="brand-panel" data-brand-panel="{html.escape(brand_id)}"{hidden_attrs}>
            <section class="hero">
                <h1>{html.escape(brand_label)} Loader 比較一覧</h1>
                <p class="subtitle">{subtitle}</p>
                <p class="meta">{TODAY} | Web閲覧用 | Source Markdown: {MARKDOWN_PATH.name}</p>
                <div class="kpi-grid">
                    <div class="kpi"><strong>{len(comparison_rows)}台</strong><span>個別型式数 / {series_count} series</span></div>
                    <div class="kpi"><strong>{html.escape(max_lift.sal_model)}</strong><span>最大リフト容量 {render_switchable_text(max_lift.lift_capacity_kg, 'weight')}</span></div>
                    <div class="kpi"><strong>{html.escape(max_speed.sal_model)}</strong><span>最高速度 {render_switchable_text(max_speed.max_speed_kmh, 'speed')} / 最小幅 {render_switchable_text(min_width.width_mm, 'length')}</span></div>
                </div>
            </section>

            <section class="section">
                <div class="section-title">
                    <h2>仕様レンジと型式の位置</h2>
                    <p>個別型式のうち、その項目に値があるモデルだけ表示。選択中ブランドに対してレンジ図を切り替える。</p>
                </div>
                <div class="layout">
                    <aside class="card">
                        <div class="card-head">シリーズ凡例</div>
                        {legend_items}
                    </aside>
                    <div class="card">
                        <table class="comparison-table">
                            <thead>
                                <tr>
                                    <th>仕様項目</th>
                                    <th>仕様レンジと各型式の位置</th>
                                    <th>単位</th>
                                </tr>
                            </thead>
                            <tbody>
                                {''.join(metrics_html)}
                            </tbody>
                        </table>
                    </div>
                </div>
            </section>

            <section class="section">
                <div class="section-title">
                    <h2>個別型式一覧</h2>
                    <p>{html.escape(electric_note)}</p>
                </div>
                {model_table}
            </section>

            <section class="section">
                <div class="section-title">
                    <h2>シリーズ要約</h2>
                    <p>{html.escape(summary_intro)}</p>
                </div>
                {summary_table}
            </section>

            <section class="section">
                <div class="section-title">
                    <h2>分類比較</h2>
                    <p>動力区分、燃料、トランスミッション、油圧メモを横並びで確認。</p>
                </div>
                {classification_table}
                <div class="note-grid">
                    <div class="note">
                        <h3>このブランドの見どころ</h3>
                        <ul>
                            <li>動力区分は {html.escape(powertrain_labels)}。</li>
                            <li>同じ画面で SI / US とメトリクス表示の有無を切り替えられる。</li>
                            <li>元データは共通 schema に正規化済みなので、別ブランドとも同じ列で比較できる。</li>
                        </ul>
                    </div>
                    <div class="note">
                        <h3>まだ足りないもの</h3>
                        <ul>
                            <li>オプション / 標準 / なし を比較できる機能フラグ列。</li>
                            <li>メーカー横断で完全に揃った油圧・電動系の正規化列。</li>
                            <li>シリーズ要約行と個別行を混在比較するときの追加ルール。</li>
                        </ul>
                    </div>
                </div>
                <div class="provenance">
                    Provenance: <code>db/knowledge.duckdb</code> の <code>loader_specification_import_rows</code> を入力元にした。ブランド切替はページ内の表示だけを切り替え、単位ボタンとメトリクス選択はそのまま共有する。レンジ図の数値は取得文字列から数値部分を抜き出し、速度レンジは上限値、<code>3.1 m</code> のような値は mm に換算して位置を計算している。
                </div>
            </section>
        </section>
    '''


def build_html(groups: list[tuple[str, str, list[ModelRow]]]) -> str:
    theme_json = json.dumps(THEME_METADATA, ensure_ascii=False, indent=8)
    metric_selector_items = "".join(
        f'<label class="metric-option"><input type="checkbox" class="metric-toggle-input" data-target-metric="{html.escape(metric["id"])}" checked> <span>{html.escape(metric["label"])} <small>({html.escape(metric["metric_unit"])} / {html.escape(metric["us_unit"])})</small></span></label>'
        for metric in METRICS
    )
    brand_toggle_buttons = "".join(
        f'<button type="button" class="brand-button{" active" if index == 0 else ""}" data-brand-target="{html.escape(brand_id)}" data-brand-label="{html.escape(brand_label)}" aria-pressed="{"true" if index == 0 else "false"}">{html.escape(brand_label)}</button>'
        for index, (brand_id, brand_label, _) in enumerate(groups)
    )
    brand_panels = "".join(
        render_brand_panel(brand_id, brand_label, rows, index == 0)
        for index, (brand_id, brand_label, rows) in enumerate(groups)
    )

    return f'''<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>マルチブランド ローダー比較 切替ビュー</title>
    <!-- Artifact Theme: blackrock-v1-color -->
    <script type="application/json" id="artifact-theme-metadata">{theme_json}
    </script>
    <style>
        :root {{
            --page-bg: #F5F6F8;
            --paper-bg: #FFFFFF;
            --ink: #171717;
            --muted: #5F6368;
            --accent: #000000;
            --line: #DADCE0;
            --soft: #F3F4F6;
            --warn: #8A5A00;
            --warn-bg: #FFF4D8;
            --font-main: "Yu Gothic", "Meiryo", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
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
        .brand-toggle, .unit-toggle {{
            display: inline-flex;
            gap: 6px;
            align-items: center;
            flex-wrap: wrap;
        }}
        .brand-toggle button, .unit-toggle button {{
            border: 1px solid var(--line);
            background: #ffffff;
            color: var(--ink);
            padding: 8px 12px;
            font: inherit;
            cursor: pointer;
        }}
        .brand-toggle button.active, .unit-toggle button.active {{
            background: #222222;
            border-color: #222222;
            color: #ffffff;
        }}
        .topbar a {{
            color: var(--ink);
            text-decoration: none;
            font-weight: 700;
        }}
        main {{
            max-width: 1380px;
            margin: 28px auto 60px;
            padding: 0 20px;
        }}
        .page-hero {{
            padding: 30px 34px 24px;
            border: 1px solid var(--line);
            background: linear-gradient(180deg, #ffffff 0, #f9fafb 100%);
            box-shadow: 0 18px 48px rgba(23, 23, 23, 0.08);
        }}
        .hero {{
            padding: 42px 44px 32px;
            border: 1px solid var(--line);
            background: linear-gradient(180deg, #ffffff 0, #f9fafb 100%);
            box-shadow: 0 18px 48px rgba(23, 23, 23, 0.08);
        }}
        h1, h2, h3, p {{ margin: 0; }}
        h1 {{ font-size: 48px; line-height: 1.08; letter-spacing: 0.01em; }}
        .page-hero h1 {{ font-size: 40px; }}
        .subtitle {{ margin-top: 16px; max-width: 980px; color: var(--muted); font-size: 18px; line-height: 1.7; }}
        .meta {{ margin-top: 20px; color: var(--muted); font-size: 14px; }}
        .metric-selector {{
            margin-top: 22px;
            padding: 16px 18px;
            border: 1px solid var(--line);
            background: #ffffff;
        }}
        .metric-selector-title {{ font-size: 14px; font-weight: 700; letter-spacing: 0.03em; }}
        .metric-selector-grid {{
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 10px 16px;
            margin-top: 12px;
        }}
        .metric-option {{ display: flex; gap: 8px; align-items: flex-start; font-size: 13px; color: var(--ink); }}
        .metric-option small {{ color: var(--muted); }}
        .brand-panel {{ margin-top: 22px; }}
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 16px;
            margin-top: 22px;
        }}
        .kpi {{
            padding: 18px 20px;
            border: 1px solid var(--line);
            background: rgba(255, 255, 255, 0.92);
        }}
        .kpi strong {{ display: block; font-size: 30px; line-height: 1; }}
        .kpi span {{ display: block; margin-top: 10px; color: var(--muted); font-size: 14px; }}
        .section {{
            margin-top: 22px;
            padding: 22px;
            border: 1px solid var(--line);
            background: var(--paper-bg);
            box-shadow: 0 10px 28px rgba(23, 23, 23, 0.05);
        }}
        .section-title {{
            display: flex;
            align-items: baseline;
            justify-content: space-between;
            gap: 18px;
            padding-bottom: 14px;
            border-bottom: 4px solid var(--accent);
        }}
        .section-title h2 {{ font-size: 34px; line-height: 1.1; }}
        .section-title p {{ color: var(--muted); font-size: 15px; }}
        .layout {{
            display: grid;
            grid-template-columns: 280px 1fr;
            gap: 16px;
            margin-top: 18px;
        }}
        .card {{ border: 1px solid var(--line); background: #ffffff; }}
        .card-head {{ padding: 14px 16px; background: #222222; color: #ffffff; font-size: 15px; font-weight: 700; letter-spacing: 0.04em; }}
        .legend-item {{ display: flex; align-items: center; gap: 14px; padding: 14px 16px; border-top: 1px dotted var(--line); font-size: 14px; font-weight: 700; }}
        .legend-item:first-of-type {{ border-top: 0; }}
        .swatch {{ width: 16px; height: 16px; display: inline-block; flex: 0 0 auto; border-radius: 999px; }}
        .comparison-table, .data-table {{ width: 100%; border-collapse: collapse; }}
        .comparison-table th, .comparison-table td, .data-table th, .data-table td {{ border: 1px solid var(--line); padding: 12px 10px; vertical-align: top; text-align: left; }}
        .comparison-table thead th, .data-table thead th {{ background: #222222; color: #ffffff; font-size: 15px; }}
        .comparison-table tbody th {{ width: 180px; background: #fafafa; text-align: left; font-size: 16px; }}
        .metric-name {{ font-weight: 700; line-height: 1.25; }}
        .metric-unit {{ color: var(--muted); font-size: 13px; }}
        .range-cell {{ min-width: 820px; padding: 0; }}
        .range-svg {{ width: 100%; height: auto; display: block; background: #ffffff; }}
        .axis-line {{ stroke: #777; stroke-width: 2; }}
        .axis-guide {{ stroke: #c9cfd6; stroke-width: 1; stroke-dasharray: 2 4; }}
        .axis-label {{ fill: var(--muted); font-size: 11px; font-weight: 700; }}
        .marker-label {{ fill: var(--ink); font-size: 11px; font-weight: 700; }}
        .empty-chart, .empty-state {{ padding: 16px; color: var(--muted); background: #ffffff; border: 1px dashed var(--line); }}
        .note-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 18px; }}
        .note {{ padding: 18px 20px; border: 1px solid var(--line); background: linear-gradient(180deg, #ffffff 0, #f7f7f7 100%); }}
        .note h3 {{ font-size: 20px; margin-bottom: 10px; }}
        .note ul {{ margin: 0; padding-left: 18px; color: var(--muted); line-height: 1.7; }}
        .provenance {{ margin-top: 18px; padding: 16px 18px; border-left: 6px solid var(--accent); background: var(--soft); color: var(--muted); line-height: 1.7; }}
        @media (max-width: 1180px) {{
            .layout {{ grid-template-columns: 1fr; }}
            .range-cell {{ min-width: 0; }}
            .kpi-grid {{ grid-template-columns: 1fr; }}
            .metric-selector-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
        }}
        @media (max-width: 760px) {{
            .topbar {{ position: static; }}
            main {{ padding: 0 10px; margin: 12px auto 30px; }}
            .page-hero, .hero, .section {{ padding: 18px 14px; }}
            h1, .page-hero h1 {{ font-size: 34px; }}
            .section-title {{ display: block; }}
            .section-title h2 {{ font-size: 28px; }}
            .note-grid {{ grid-template-columns: 1fr; }}
            .metric-selector-grid {{ grid-template-columns: 1fr; }}
        }}
    </style>
</head>
<body>
    <nav class="topbar">
        <strong><span id="current-brand-nav">AVANT</span> 比較ページ</strong>
        <div class="brand-toggle" aria-label="brand toggle">
            {brand_toggle_buttons}
        </div>
        <div class="unit-toggle" aria-label="unit toggle">
            <button type="button" class="active" data-unit-system="metric">SI</button>
            <button type="button" data-unit-system="us">US</button>
        </div>
        <a href="{MARKDOWN_PATH.name}">MD正本</a>
    </nav>
    <main>
        <section class="page-hero">
            <h1><span id="current-brand-hero">AVANT</span> 比較ページ</h1>
            <p class="subtitle">既存の AVANT 単独 HTML を踏まえて、共通 curated テーブル <code>loader_specification_import_rows</code> から <span id="current-brand-copy">AVANT</span> を選択式で切り替えられるようにした。メトリクス表示と単位切替はページ全体で共有する。</p>
            <p class="meta">{TODAY} | Web閲覧用 | Source Markdown: {MARKDOWN_PATH.name}</p>
            <div class="metric-selector">
                <div class="metric-selector-title">表示する数値バー</div>
                <div class="metric-selector-grid">
                    {metric_selector_items}
                </div>
            </div>
        </section>
        {brand_panels}
    </main>
    <script>
        (function () {{
            function resolveBrandId(requestedBrandId) {{
                var buttons = Array.prototype.slice.call(document.querySelectorAll('[data-brand-target]'));
                if (!buttons.length) {{
                    return null;
                }}

                var matchedButton = buttons.find(function (button) {{
                    return button.getAttribute('data-brand-target') === requestedBrandId;
                }});
                return matchedButton ? matchedButton.getAttribute('data-brand-target') : buttons[0].getAttribute('data-brand-target');
            }}

            function updateBrandChrome(brandLabel) {{
                var titleText = brandLabel + ' 比較ページ';
                document.title = titleText;

                ['current-brand-nav', 'current-brand-hero', 'current-brand-copy'].forEach(function (id) {{
                    var node = document.getElementById(id);
                    if (node) {{
                        node.textContent = brandLabel;
                    }}
                }});
            }}

            function applyUnitSystem(system) {{
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

            function applyBrand(brandId, updateHash) {{
                var resolvedBrandId = resolveBrandId(brandId);
                if (!resolvedBrandId) {{
                    return;
                }}

                var activeLabel = null;
                document.querySelectorAll('[data-brand-panel]').forEach(function (panel) {{
                    var active = panel.getAttribute('data-brand-panel') === resolvedBrandId;
                    panel.style.display = active ? '' : 'none';
                    panel.setAttribute('aria-hidden', active ? 'false' : 'true');
                }});

                document.querySelectorAll('[data-brand-target]').forEach(function (button) {{
                    var active = button.getAttribute('data-brand-target') === resolvedBrandId;
                    button.classList.toggle('active', active);
                    button.setAttribute('aria-pressed', active ? 'true' : 'false');
                    if (active) {{
                        activeLabel = button.getAttribute('data-brand-label') || button.textContent.trim();
                    }}
                }});

                if (activeLabel) {{
                    updateBrandChrome(activeLabel);
                }}

                if (updateHash) {{
                    var nextHash = '#' + resolvedBrandId;
                    if (window.location.hash !== nextHash) {{
                        if (window.history && window.history.replaceState) {{
                            window.history.replaceState(null, '', nextHash);
                        }} else {{
                            window.location.hash = nextHash;
                        }}
                    }}
                }}
            }}

            document.querySelectorAll('[data-unit-system]').forEach(function (button) {{
                button.addEventListener('click', function () {{
                    applyUnitSystem(button.getAttribute('data-unit-system'));
                }});
            }});

            document.querySelectorAll('.metric-toggle-input').forEach(function (input) {{
                input.addEventListener('change', applyMetricVisibility);
            }});

            document.querySelectorAll('[data-brand-target]').forEach(function (button) {{
                button.addEventListener('click', function () {{
                    applyBrand(button.getAttribute('data-brand-target'), true);
                }});
            }});

            window.addEventListener('hashchange', function () {{
                applyBrand(window.location.hash.replace(/^#/, ''), false);
            }});

            applyUnitSystem('metric');
            applyMetricVisibility();
            applyBrand(window.location.hash.replace(/^#/, ''), true);
        }})();
    </script>
</body>
</html>
'''


def main() -> None:
    rows = load_rows()
    groups = group_rows_by_brand(rows)
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    MARKDOWN_PATH.write_text(build_markdown(groups), encoding="utf-8")
    HTML_PATH.write_text(build_html(groups), encoding="utf-8")
    print(f"wrote_markdown={MARKDOWN_PATH}")
    print(f"wrote_html={HTML_PATH}")


if __name__ == "__main__":
    main()