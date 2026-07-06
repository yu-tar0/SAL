from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass
from pathlib import Path

import duckdb


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "db" / "knowledge.duckdb"
ARTIFACT_ID = "2026-07-02-comparison-avant-loader-specs-current-db"
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

SERIES_COLORS = {
    "200 series": "#1D4ED8",
    "400 series": "#0F766E",
    "500 series": "#E85D04",
    "600 series": "#7C3AED",
    "700 series": "#B91C1C",
    "800 series": "#6B4F2A",
    "e500 series": "#2F7D32",
    "e700 series": "#0B5D1E",
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
    def label(self) -> str:
        return re.sub(r"^(?:AVANT|Avant)\s+", "", self.sal_model).strip()

    @property
    def is_series_summary(self) -> bool:
        return self.label.lower().endswith("series")

    @property
    def is_electric(self) -> bool:
        return self.powertrain_type.lower().startswith("electric")

    @property
    def series_color(self) -> str:
        return SERIES_COLORS.get(self.series, "#374151")


def clean_text(value: object) -> str:
    if value is None:
        return ""
    return " ".join(str(value).split())


def parse_measure(text: str, target_unit: str, extract_mode: str = "range_max") -> float | None:
    normalized = clean_text(text).replace(",", "")
    if not normalized:
        return None

    numbers = [float(value) for value in re.findall(r"\d+(?:\.\d+)?", normalized)]
    if not numbers:
        return None

    lower = normalized.lower()
    if target_unit == "mm":
        if "mm" in lower:
            pass
        if re.search(r"(^|[^a-z])m($|[^a-z])", lower):
            numbers = [value * 1000 for value in numbers]

    if extract_mode == "first":
        return numbers[0]
    if extract_mode == "second":
        return numbers[1] if len(numbers) > 1 else None
    if any(sep in normalized for sep in ["-", "–", "to"]) and len(numbers) > 1:
        return numbers[-1]
    return numbers[0]


def format_number(value: float, unit: str) -> str:
    if unit in {"hp", "kg", "mm"}:
        return f"{int(round(value))}"
    if value.is_integer():
        return str(int(value))
    return f"{value:.1f}"


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


def format_display_value(value: float, family: str | None, system: str, metric_unit: str, us_unit: str) -> str:
    unit = metric_unit if system == "metric" else us_unit
    converted = convert_metric_value(value, family, system)
    if unit in {"mm", "kg", "hp", "kgf", "kWh"}:
        return str(int(round(converted)))
    rounded = round(converted, 1)
    if float(rounded).is_integer():
        return str(int(rounded))
    return f"{rounded:.1f}"


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


def md_cell(value: str) -> str:
    if not value:
        return "-"
    return value.replace("|", "\\|")


def html_cell(value: str) -> str:
    if not value:
        return "-"
    return html.escape(value)


def load_rows() -> list[ModelRow]:
    sql = """
    SELECT
      COALESCE("シリーズ", '') AS series,
      COALESCE("SAL型式", '') AS sal_model,
      COALESCE("動力区分", '') AS powertrain_type,
      COALESCE("馬力", '') AS horsepower,
      COALESCE("リフト容量 (kg)", '') AS lift_capacity_kg,
      COALESCE("リフト高 (mm)", '') AS lift_height_mm,
    COALESCE("テレスコ長 (mm)", '') AS telescopic_length_mm,
    COALESCE("補助油圧 流量 / 圧力 (L/min / MPa)", '') AS aux_hydraulic_flow_pressure_l_min_mpa,
    COALESCE("最大ブレークアウト力 (kgf)", '') AS max_breakout_force_kgf,
    COALESCE("最大牽引力 (kgf)", '') AS max_tow_force_kgf,
    COALESCE("最大トルク (N·m @ rpm)", '') AS max_torque_nm_rpm,
      COALESCE("最高速度 (km/h)", '') AS max_speed_kmh,
      COALESCE("運転質量 (kg)", '') AS operating_weight_kg,
    COALESCE("旋回半径 内側 / 外側 (mm)", '') AS turning_radius_inner_outer_mm,
      COALESCE("全幅 (mm)", '') AS width_mm,
    COALESCE("全長 (mm)", '') AS length_mm,
    COALESCE("全高 (mm)", '') AS height_mm,
      COALESCE("トランスミッション", '') AS transmission,
      COALESCE("燃料", '') AS fuel,
      COALESCE("バッテリー容量", '') AS battery_capacity,
      COALESCE("充電時間", '') AS charge_time,
      COALESCE("PDFページ", '') AS pdf_page,
      COALESCE("カタログページURL", '') AS catalog_page_url,
      COALESCE("油圧システムメモ", '') AS hydraulic_system_notes
    FROM avant_loader_specs_raw
    WHERE COALESCE(TRIM("SAL型式"), '') <> ''
    ORDER BY "シリーズ", "SAL型式"
    """

    with duckdb.connect(str(DB_PATH), read_only=True) as con:
        records = con.execute(sql).fetchall()

    return [ModelRow(*[clean_text(value) for value in record]) for record in records]


def series_sort_key(name: str) -> tuple[int, str]:
    match = re.search(r"(\d+)", name)
    if match:
        return (int(match.group(1)), name)
    return (9999, name)


def build_markdown(rows: list[ModelRow]) -> str:
    combustion = [row for row in rows if not row.is_electric and not row.is_series_summary]
    electric = [row for row in rows if row.is_electric and not row.is_series_summary]
    summaries = [row for row in rows if row.is_series_summary]

    max_lift = max(combustion, key=lambda row: parse_measure(row.lift_capacity_kg, "kg") or -1)
    max_speed = max(combustion, key=lambda row: parse_measure(row.max_speed_kmh, "km/h") or -1)
    min_width = min(combustion, key=lambda row: parse_measure(row.width_mm, "mm") or 10**9)

    lines: list[str] = [
        "---",
        "title: AVANT SAL比較表 現行DuckDB版",
        f"created: {TODAY}",
        f"updated: {TODAY}",
        "type: artifact",
        "status: current-db",
        "input:",
        "  - db/knowledge.duckdb",
        "  - table: avant_loader_specs_raw",
        "outputs:",
        f"  - artifacts/{ARTIFACT_ID}/{MARKDOWN_PATH.name}",
        f"  - artifacts/{ARTIFACT_ID}/{HTML_PATH.name}",
        "purpose: 現行 knowledge.duckdb の AVANT raw 仕様を、比較しやすい Markdown 正本と Web HTML に整理する",
        "---",
        "",
        "# AVANT SAL比較表 現行DuckDB版",
        "",
        "現行の `db/knowledge.duckdb` に入っている `avant_loader_specs_raw` を直接参照し、添付試作の見せ方を踏まえて再構成した比較 Artifact です。旧 `loader_specifications_current` ではなく、現在の raw テーブルにある値をそのまま基準にしています。",
        "",
        "## 要約",
        "",
        f"- 現行 DuckDB には、AVANT の個別機種 {len(combustion)} 台の燃焼系モデル、{len(electric)} 台の電動個別モデル、{len(summaries)} 行のシリーズ要約が入っています。",
        f"- 燃焼系の最大リフト容量は {max_lift.sal_model} の {max_lift.lift_capacity_kg}、最高速度は {max_speed.sal_model} の {max_speed.max_speed_kmh} です。",
        f"- 最小幅は {min_width.sal_model} の {min_width.width_mm} で、コンパクト側の基準点として見やすくなっています。",
        "- HTML では、燃焼系個別モデルの主要数値をレンジ表示し、電動モデルとシリーズ要約は別表に分けています。",
        "",
        "## 比較対象の区分",
        "",
        "- 燃焼系個別モデル: 200 / 400 / 500 / 600 / 700 / 800 series の個別型式",
        "- 電動個別モデル: e513 / e527 / e727",
        "- シリーズ要約: e500 series / e700 series のシリーズ行",
        "",
        "## 燃焼系個別モデル一覧",
        "",
        "| シリーズ | 型式 | 動力 | 馬力 | リフト容量 | リフト高 | 最高速度 | 全幅 | 運転質量 | トランスミッション |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]

    for row in combustion:
        lines.append(
            "| "
            + " | ".join(
                [
                    md_cell(row.series),
                    md_cell(row.sal_model),
                    md_cell(row.powertrain_type),
                    md_cell(row.horsepower),
                    md_cell(row.lift_capacity_kg),
                    md_cell(row.lift_height_mm),
                    md_cell(row.max_speed_kmh),
                    md_cell(row.width_mm),
                    md_cell(row.operating_weight_kg),
                    md_cell(row.transmission),
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## 電動モデル比較",
            "",
            "| シリーズ | 型式 | 動力 | リフト容量 | リフト高 | 最高速度 | 運転質量 | バッテリー容量 | 充電時間 |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )

    for row in electric:
        lines.append(
            "| "
            + " | ".join(
                [
                    md_cell(row.series),
                    md_cell(row.sal_model),
                    md_cell(row.powertrain_type),
                    md_cell(row.lift_capacity_kg),
                    md_cell(row.lift_height_mm),
                    md_cell(row.max_speed_kmh),
                    md_cell(row.operating_weight_kg),
                    md_cell(row.battery_capacity),
                    md_cell(row.charge_time),
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## シリーズ要約行",
            "",
            "| シリーズ行 | リフト容量 | リフト高 | 最高速度 | バッテリー容量 | 充電時間 | 備考 |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )

    for row in summaries:
        lines.append(
            "| "
            + " | ".join(
                [
                    md_cell(row.sal_model),
                    md_cell(row.lift_capacity_kg),
                    md_cell(row.lift_height_mm),
                    md_cell(row.max_speed_kmh),
                    md_cell(row.battery_capacity),
                    md_cell(row.charge_time),
                    md_cell(row.hydraulic_system_notes),
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## 分類比較",
            "",
            "| 型式 | シリーズ | 動力区分 | 燃料 | トランスミッション | 備考 |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )

    for row in [item for item in rows if not item.is_series_summary]:
        lines.append(
            "| "
            + " | ".join(
                [
                    md_cell(row.sal_model),
                    md_cell(row.series),
                    md_cell(row.powertrain_type),
                    md_cell(row.fuel),
                    md_cell(row.transmission),
                    md_cell(row.hydraulic_system_notes),
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## 読み方",
            "",
            "- HTML のレンジ図は、各項目の最小値から最大値までの間に個別型式を置いたものです。",
            "- 速度のような `0-10 km/h` 形式は、比較用に上限値を採用しています。",
            "- `3.1 m` のように mm 列へ m 表記が入っている値は、HTML 生成時に mm へ換算して位置合わせしています。",
            "",
            "## Provenance",
            "",
            "- DuckDB: `db/knowledge.duckdb`",
            "- 参照テーブル: `avant_loader_specs_raw`",
            "- 生成スクリプト: `scripts/build_avant_loader_comparison_artifact.py`",
            f"- 生成物: `{MARKDOWN_PATH.name}` / `{HTML_PATH.name}`",
            "- 旧試作との違い: `loader_specifications_current` ではなく、現行DBに存在する raw テーブルを直接参照",
            "",
            "## 未解決点",
            "",
            "- 燃焼系と電動系で幅や油圧補機の記述粒度が揃っていない行があります。",
            "- オプション / 標準 / なし を横並びにする機能比較列は、現行DBにはまだ構造化されていません。",
            "- 電動モデルの一部は重量や充電時間の書き方に差があるため、厳密な比較用には追加の正規化が必要です。",
        ]
    )

    return "\n".join(lines) + "\n"


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


def render_table(headers: list[str], rows: list[list[str]], families: list[str | None] | None = None) -> str:
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
    return f"<table class=\"data-table\"><thead><tr>{head}</tr></thead><tbody>{''.join(body_rows)}</tbody></table>"


def build_html(rows: list[ModelRow]) -> str:
    combustion = [row for row in rows if not row.is_electric and not row.is_series_summary]
    electric = [row for row in rows if row.is_electric and not row.is_series_summary]
    summaries = [row for row in rows if row.is_series_summary]
    comparison_rows = [row for row in rows if not row.is_series_summary]

    metrics_html = []
    for metric in METRICS:
        metrics_html.append(
            f"<tr class=\"metric-row\" data-metric-id=\"{html.escape(metric['id'])}\">"
            f"<th><div class=\"metric-name\">{html.escape(metric['label'])}</div><div class=\"metric-unit js-unit-label\" data-metric-unit=\"{html.escape(metric['metric_unit'])}\" data-us-unit=\"{html.escape(metric['us_unit'])}\">{html.escape(metric['metric_unit'])}</div></th>"
            f"<td class=\"range-cell\">{render_range_svg(comparison_rows, metric['key'], metric['parse_unit'], metric['family'], metric['us_unit'], metric['extract_mode'])}</td>"
            f"<td><span class=\"js-unit-label\" data-metric-unit=\"{html.escape(metric['metric_unit'])}\" data-us-unit=\"{html.escape(metric['us_unit'])}\">{html.escape(metric['metric_unit'])}</span></td>"
            "</tr>"
        )

    series_names = sorted({row.series for row in comparison_rows}, key=series_sort_key)
    legend_items = "".join(
        f'<div class="legend-item"><span class="swatch" style="background:{SERIES_COLORS.get(name, "#374151")};"></span><span>{html.escape(name)}</span></div>'
        for name in series_names
    )
    metric_selector_items = "".join(
        f'<label class="metric-option"><input type="checkbox" class="metric-toggle-input" data-target-metric="{html.escape(metric["id"])}" checked> <span>{html.escape(metric["label"])} <small>({html.escape(metric["metric_unit"])} / {html.escape(metric["us_unit"])})</small></span></label>'
        for metric in METRICS
    )

    combustion_table = render_table(
        ["シリーズ", "型式", "動力", "馬力", "リフト容量", "リフト高", "最高速度", "全幅", "運転質量"],
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
            ]
            for row in combustion
        ],
        [None, None, None, None, "weight", "length", "speed", "length", "weight"],
    )
    electric_table = render_table(
        ["シリーズ", "型式", "動力", "リフト容量", "リフト高", "最高速度", "運転質量", "バッテリー容量", "充電時間"],
        [
            [
                row.series,
                row.sal_model,
                row.powertrain_type,
                row.lift_capacity_kg,
                row.lift_height_mm,
                row.max_speed_kmh,
                row.operating_weight_kg,
                row.battery_capacity,
                row.charge_time,
            ]
            for row in electric
        ],
        [None, None, None, "weight", "length", "speed", "weight", None, None],
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
            for row in rows
            if not row.is_series_summary
        ],
    )

    max_lift = max(combustion, key=lambda row: parse_measure(row.lift_capacity_kg, "kg") or -1)
    max_speed = max(combustion, key=lambda row: parse_measure(row.max_speed_kmh, "km/h") or -1)
    min_width = min(combustion, key=lambda row: parse_measure(row.width_mm, "mm") or 10**9)

    theme_json = json.dumps(THEME_METADATA, ensure_ascii=False, indent=8)
    return f"""<!DOCTYPE html>
<html lang=\"ja\">
<head>
    <meta charset=\"UTF-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
    <title>AVANT SAL比較表 現行DuckDB版</title>
    <!-- Artifact Theme: blackrock-v1-color -->
    <script type=\"application/json\" id=\"artifact-theme-metadata\">{theme_json}
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
            padding: 14px 18px;
            background: rgba(255, 255, 255, 0.94);
            border-bottom: 1px solid var(--line);
            backdrop-filter: blur(8px);
        }}
        .unit-toggle {{
            display: inline-flex;
            gap: 6px;
            align-items: center;
        }}
        .unit-toggle button {{
            border: 1px solid var(--line);
            background: #ffffff;
            color: var(--ink);
            padding: 8px 12px;
            font: inherit;
            cursor: pointer;
        }}
        .unit-toggle button.active {{
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
        .hero {{
            padding: 42px 44px 32px;
            border: 1px solid var(--line);
            background: linear-gradient(180deg, #ffffff 0, #f9fafb 100%);
            box-shadow: 0 18px 48px rgba(23, 23, 23, 0.08);
        }}
        h1, h2, h3, p {{ margin: 0; }}
        h1 {{ font-size: 48px; line-height: 1.08; letter-spacing: 0.01em; }}
        .subtitle {{ margin-top: 16px; max-width: 980px; color: var(--muted); font-size: 18px; line-height: 1.7; }}
        .meta {{ margin-top: 20px; color: var(--muted); font-size: 14px; }}
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
        .metric-selector {{
            margin-top: 18px;
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
        .empty-chart {{ padding: 16px; color: var(--muted); }}
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
            .topbar {{ position: static; flex-wrap: wrap; }}
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
    <nav class=\"topbar\">
        <strong>AVANT SAL比較表 現行DuckDB版</strong>
        <div class=\"unit-toggle\" aria-label=\"unit toggle\">
            <button type=\"button\" class=\"active\" data-unit-system=\"metric\">SI</button>
            <button type=\"button\" data-unit-system=\"us\">US</button>
        </div>
        <a href=\"{MARKDOWN_PATH.name}\">MD正本</a>
    </nav>
    <main>
        <section class=\"hero\">
            <h1>AVANT SAL 比較一覧</h1>
            <p class=\"subtitle\">現行の <code>knowledge.duckdb</code> にある <code>avant_loader_specs_raw</code> を直接参照し、添付試作のレイアウトをベースに整理した Web Artifact です。燃焼系個別モデルはレンジ比較、電動個別モデルとシリーズ要約は別表に分けています。</p>
            <p class=\"meta\">{TODAY} | Web閲覧用 | Source Markdown: {MARKDOWN_PATH.name}</p>
            <div class=\"kpi-grid\">
                <div class=\"kpi\"><strong>{len(combustion)}台</strong><span>燃焼系の個別モデル</span></div>
                <div class=\"kpi\"><strong>{html.escape(max_lift.sal_model)}</strong><span>最大リフト容量 {render_switchable_text(max_lift.lift_capacity_kg, 'weight')}</span></div>
                <div class=\"kpi\"><strong>{html.escape(max_speed.sal_model)}</strong><span>最高速度 {render_switchable_text(max_speed.max_speed_kmh, 'speed')} / 最小幅 {render_switchable_text(min_width.width_mm, 'length')}</span></div>
            </div>
        </section>

        <section class=\"section\">
            <div class=\"section-title\">
                <h2>仕様レンジと型式の位置</h2>
                <p>個別型式のうち、その項目に値があるモデルだけ表示。下の選択で表示項目を切り替え。</p>
            </div>
            <div class="metric-selector">
                <div class="metric-selector-title">表示する数値バー</div>
                <div class="metric-selector-grid">
                    {metric_selector_items}
                </div>
            </div>
            <div class=\"layout\">
                <aside class=\"card\">
                    <div class=\"card-head\">シリーズ凡例</div>
                    {legend_items}
                </aside>
                <div class=\"card\">
                    <table class=\"comparison-table\">
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

        <section class=\"section\">
            <div class=\"section-title\">
                <h2>燃焼系個別モデル一覧</h2>
                <p>200 から 800 series までの個別型式を現行 DB の表記でそのまま整理。</p>
            </div>
            {combustion_table}
        </section>

        <section class=\"section\">
            <div class=\"section-title\">
                <h2>電動モデルとシリーズ要約</h2>
                <p>電動の個別型式とシリーズ行は、比較軸が異なるため別表に分離。</p>
            </div>
            {electric_table}
            <div style=\"height:16px;\"></div>
            {summary_table}
        </section>

        <section class=\"section\">
            <div class=\"section-title\">
                <h2>分類比較</h2>
                <p>動力区分、燃料、トランスミッション、油圧メモを横並びで確認。</p>
            </div>
            {classification_table}

            <div class=\"note-grid\">
                <div class=\"note\">
                    <h3>今回変えた点</h3>
                    <ul>
                        <li>旧 <code>loader_specifications_current</code> 依存をやめ、現行 DB にある <code>avant_loader_specs_raw</code> を直接使用。</li>
                        <li>700 / 800 series も個別機種として拾えるため、燃焼系の比較対象を 15 台まで拡張。</li>
                        <li>電動系は個別モデルとシリーズ要約を分け、充電時間やバッテリー容量を落とさず保持。</li>
                    </ul>
                </div>
                <div class=\"note\">
                    <h3>まだ足りないもの</h3>
                    <ul>
                        <li>オプション / 標準 / なし を比較できる機能フラグ列。</li>
                        <li>電動系を含めた幅や油圧系の正規化済み比較列。</li>
                        <li>シリーズ行と個別行を同列比較するときの整形ルール。</li>
                    </ul>
                </div>
            </div>

            <div class=\"provenance\">
                Provenance: <code>db/knowledge.duckdb</code> の <code>avant_loader_specs_raw</code> を入力元にした。数値レンジは取得文字列から数値部分を抜き出し、速度レンジは上限値、<code>3.1 m</code> のような値は mm に換算して位置を計算している。上部ボタンで SI と US customary を切り替えられる。ブラウザ閲覧はこの <code>web.html</code> を入口とする。
            </div>
        </section>
    </main>
    <script>
        (function () {{
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

            document.querySelectorAll('[data-unit-system]').forEach(function (button) {{
                button.addEventListener('click', function () {{
                    applyUnitSystem(button.getAttribute('data-unit-system'));
                }});
            }});

            document.querySelectorAll('.metric-toggle-input').forEach(function (input) {{
                input.addEventListener('change', applyMetricVisibility);
            }});

            applyUnitSystem('metric');
            applyMetricVisibility();
        }})();
    </script>
</body>
</html>
"""


def main() -> None:
    rows = load_rows()
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    MARKDOWN_PATH.write_text(build_markdown(rows), encoding="utf-8")
    HTML_PATH.write_text(build_html(rows), encoding="utf-8")
    print(f"wrote_markdown={MARKDOWN_PATH}")
    print(f"wrote_html={HTML_PATH}")


if __name__ == "__main__":
    main()