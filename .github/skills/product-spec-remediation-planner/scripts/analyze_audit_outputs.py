# -*- coding: utf-8 -*-
"""audit_outputs/ の監査CSVを読み込み、問題を分類・優先度付けして集計する。

使い方:
    python .github/skills/product-spec-remediation-planner/scripts/analyze_audit_outputs.py
        [--audit-dir audit_outputs] [--out-dir remediation_outputs]

出力（remediation_outputs/ 配下）:
    - _analysis.json          全指摘（review_id付き）と分類・集計の中間データ。後続スクリプトの入力
    - _run_meta.json          入力ファイルの有無・fallback・実行時刻
    - remediation_summary.csv issue_type×分類ごとの件数・優先度・人間レビュー要否

動作:
    - DB には接続しない。normalizer のファイルにも触れない。audit_outputs/ は読み取りのみ。
    - 存在しない入力ファイルがあっても止めず、不足として記録する。
    - risky_group_merges.csv が無い場合は suspicious_mappings.csv を代替として読む。
    - 分類はすべて規則ベースの「候補」であり、confidence < 0.8 は人間レビュー必須として扱う。
"""
import argparse
import csv
import json
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

# Windows コンソール（cp932）での文字化けを防ぐ
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_AUDIT_DIR = REPO_ROOT / "audit_outputs"
DEFAULT_OUT_DIR = REPO_ROOT / "remediation_outputs"

ANALYSIS_JSON = "_analysis.json"
RUN_META_JSON = "_run_meta.json"

# 期待する監査結果ファイル
EXPECTED_INPUTS = [
    "quality_audit_report.md",
    "audit_summary.csv",
    "suspicious_mappings.csv",
    "risky_group_merges.csv",
    "unmapped_raw_items.csv",
    "unit_mismatches.csv",
    "duplicate_canonical_items.csv",
    "low_confidence_mappings.csv",
    "comparison_missing_rates.csv",
    "company_coverage.csv",
    "human_review_required.csv",
    "canonical_coverage.csv",
    "final_score_inputs.csv",
]

# 人間レビューの固定語彙
DECISION_VOCAB = [
    "approve", "reject", "split_canonical", "map_to_existing",
    "create_new_canonical", "exclude_from_comparison", "add_conversion_rule",
    "change_canonical_unit", "fix_raw_unit_extraction", "do_not_convert",
    "needs_source_check", "keep_manual_review",
]
STATUS_VOCAB = ["pending", "reviewed", "deferred"]

# final_canonical_item / final_unit が必須になる human_decision
DECISIONS_REQUIRE_CANONICAL = {"map_to_existing", "create_new_canonical", "split_canonical"}
DECISIONS_REQUIRE_UNIT = {"add_conversion_rule", "change_canonical_unit"}

# 意味混同群 → canonical 分割の接尾辞候補（canonical_split_guide.md 参照）
CONDITION_BUCKETS = [
    ("max", r"\bmax\.?\b|最大|\bpeak\b|ピーク", "_max"),
    ("rated", r"\brated\b|定格", "_rated"),
    ("cab", r"\bcab\b|キャブ", "_cab"),
    ("canopy", r"\bcanopy\b|キャノピー", "_canopy"),
    ("shipping", r"梱包|shipping|transport|輸送", "_shipping"),
    ("counterweight", r"counterweight|カウンタ", "_with_counterweight"),
    ("optional", r"\boption(al)?\b|オプション", "_optional"),
    ("standby", r"\bstandby\b|待機", "_standby"),
    ("storage", r"\bstorage\b|保管", "_storage"),
    ("hinge", r"\bhinge\b|ヒンジ", "_to_hinge_pin"),
]

# 既知の単位変換候補: (original_unit小文字, canonical_unit) -> (rule, confidence, 注記)
KNOWN_UNIT_RULES = {
    ("km/hr.", "km/h"): ("alias", 0.9, "表記ゆれ"),
    ("km/hr", "km/h"): ("alias", 0.9, "表記ゆれ"),
    ("kmh", "km/h"): ("alias", 0.9, "表記ゆれ"),
    ("mph", "km/h"): ("multiply:1.60934", 0.85, "確定換算"),
    ("hp", "kW"): ("multiply:0.7457", 0.6, "機械馬力(hp)前提。PS(0.7355)の可能性があれば人間確認"),
    ("ps", "kW"): ("multiply:0.7355", 0.7, "メートル馬力前提"),
    ("l", "cc"): ("multiply:1000", 0.9, "確定換算"),
    ("in3", "cc"): ("multiply:16.387", 0.85, "確定換算"),
    ("lb", "kg"): ("multiply:0.45359", 0.85, "確定換算"),
    ("lbs", "kg"): ("multiply:0.45359", 0.85, "確定換算"),
    ("psi", "MPa"): ("multiply:0.0068948", 0.8, "確定換算"),
    ("bar", "MPa"): ("multiply:0.1", 0.9, "確定換算"),
}

TIRE_PATTERN = re.compile(r"\d+\s*[xX×]\s*\d+(\.\d+)?")
SINGLE_LETTER_SUFFIX = re.compile(r"/\s*[A-Z]\s*$")
RANGE_OR_MULTI = re.compile(r"[〜~／/]|(\d)\s*-\s*(\d)|@|\brpm\b", re.IGNORECASE)

# 未マッピング項目 → 既存canonical候補のキーワード規則
MAP_TO_EXISTING_RULES = [
    (r"flow\s*rate|流量", "aux_hydraulic_flow", 0.6),
    (r"pressure|圧力", "aux_hydraulic_pressure", 0.5),
    (r"travel\s*speed|走行速度", "max_travel_speed", 0.6),
    (r"turning\s*radius|回転半径|旋回半径", "turning_radius", 0.55),
    (r"ground\s*clearance|最低地上高", "ground_clearance", 0.6),
    (r"wheel\s*base|ホイールベース|軸距", "wheelbase", 0.6),
]

# 新規canonical候補のキーワード規則: (pattern, canonical案, 表示名, category, unit, value_type)
NEW_CANONICAL_RULES = [
    (r"engine\s*oil", "engine_oil_capacity", "エンジンオイル容量", "service", "L", "numeric"),
    (r"coolant", "engine_coolant_capacity", "冷却水容量", "service", "L", "numeric"),
    (r"fuel\s*(tank|capacity)|燃料タンク", "fuel_tank_capacity", "燃料タンク容量", "service", "L", "numeric"),
    (r"hydraulic\s*(tank|reservoir|oil)|作動油", "hydraulic_tank_capacity", "作動油タンク容量", "service", "L", "numeric"),
    (r"low\s*range", "travel_speed_low_range", "走行速度（低速レンジ）", "performance", "km/h", "numeric"),
]

EXCLUDE_RULES = [
    (TIRE_PATTERN, "タイヤサイズ等のバリエーション列挙で、1製品1値の比較軸にならない", 0.7),
    (re.compile(r"備考|remarks?|\bnotes?\b|warranty|保証|\bcolou?r\b|(^|_)色", re.IGNORECASE),
     "自由記述・保証・色など比較に使えない項目", 0.75),
    (re.compile(r"^(シリーズ|series)$", re.IGNORECASE), "製品シリーズ名で比較軸にならない", 0.7),
]


# ---------------------------------------------------------------- I/O helpers

def read_csv_dicts(path: Path):
    """CSV を dict のリストで返す。無ければ None。"""
    if not path.exists():
        return None
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, header, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(header)
        for row in rows:
            if isinstance(row, dict):
                w.writerow([row.get(h, "") for h in header])
            else:
                w.writerow(row)


def load_analysis(out_dir: Path):
    path = out_dir / ANALYSIS_JSON
    if not path.exists():
        return None
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def ensure_analysis(audit_dir: Path, out_dir: Path):
    """_analysis.json を読み込む。無ければこのモジュールの分析を実行して作る。"""
    analysis = load_analysis(out_dir)
    if analysis is None:
        analysis = run_analysis(audit_dir, out_dir)
    return analysis


def to_float(text):
    try:
        return float(str(text).replace(",", "").strip())
    except (TypeError, ValueError):
        return None


def contains(pattern, text):
    return bool(re.search(pattern, text or "", re.IGNORECASE))


def load_canonical_names(audit_dir: Path):
    """監査の raw/canonical_definitions.csv から canonical_specs の実名一覧を読む。

    planner は DB を見ないため、これが候補名検証の唯一の情報源。無ければ None
    （候補名は未検証としてconfidenceを下げ、その旨を記録する）。
    """
    rows = read_csv_dicts(audit_dir / "raw" / "canonical_definitions.csv")
    if rows is None:
        return None
    return {(r.get("canonical_item") or "").strip()
            for r in rows if (r.get("canonical_item") or "").strip()}


def near_canonical_matches(candidate, canonical_names, limit=3):
    """トークン重なりで実在canonicalの近い名前を探す（hydraulic_tank_capacity →
    hydraulic_system_capacity のような取り違え検出用）。"""
    tokens = set(candidate.lower().split("_"))
    scored = []
    for name in canonical_names:
        overlap = len(tokens & set(name.lower().split("_")))
        if overlap >= 2 or (overlap >= 1 and (candidate in name or name in candidate)):
            scored.append((overlap, name))
    return [n for _, n in sorted(scored, key=lambda t: (-t[0], t[1]))[:limit]]


def validate_against_canonical(cls, decision, canonical, why, conf, unc, canonical_names):
    """unmapped の分類候補を canonical_specs 実名と突き合わせて補正する。"""
    if canonical_names is None:
        if canonical:
            unc = (unc + "。" if unc else "") + \
                "canonical_definitions.csv が無く候補名は未検証（実名との突き合わせが必要）"
            conf = min(conf, 0.6)
        return cls, decision, canonical, why, conf, unc
    if not canonical:
        return cls, decision, canonical, why, conf, unc
    if cls == "map_to_existing" and canonical not in canonical_names:
        near = near_canonical_matches(canonical, canonical_names)
        if near:
            return ("manual_review_required", "keep_manual_review", " | ".join(near),
                    f"推定候補 {canonical} は canonical_specs に実在しない。近い実在項目: {', '.join(near)}",
                    0.5, "実在する近似項目のどれに寄せるか（または新設か）の判断が必要")
        return ("manual_review_required", "keep_manual_review", "",
                f"推定候補 {canonical} は canonical_specs に実在しない",
                0.45, "実在候補が見つからず、新設か除外かの判断が必要")
    if cls == "create_new_canonical":
        if canonical in canonical_names:
            return ("map_to_existing", "map_to_existing", canonical,
                    f"候補 {canonical} は canonical_specs に既に実在するためマッピング追加で足りる",
                    0.75, "")
        near = near_canonical_matches(canonical, canonical_names)
        if near:
            return ("manual_review_required", "keep_manual_review",
                    f"{canonical}（新設案） | " + " | ".join(near),
                    f"新設案 {canonical} は既存の {near[0]} と重複の疑いがある",
                    0.5, f"既存 {', '.join(near)} との意味の違いを確認してから新設可否を決める")
    return cls, decision, canonical, why, conf, unc


# ---------------------------------------------------------------- 現在指標

def parse_current_metrics(audit_dir: Path, tables):
    """audit_summary.csv と各CSVから再監査目標の「現在値」を作る。"""
    metrics = {
        "total_score": None, "spec_mapping_score": None, "normalized_specs_score": None,
        "unmapped_pct": None, "unmapped_rows": None,
        "unit_mismatch_rows": None, "numeric_parse_failed_rows": None, "value_conflicts": None,
    }
    summary = tables.get("audit_summary.csv")
    if summary:
        for row in summary:
            cat = (row.get("category") or "").strip()
            problems = row.get("main_problems") or ""
            if cat == "TOTAL":
                metrics["total_score"] = to_float(row.get("score"))
            elif cat == "spec_mapping品質":
                metrics["spec_mapping_score"] = to_float(row.get("score"))
                m = re.search(r"未マッピング率が\s*([\d.]+)%（(\d+)/(\d+)）", problems)
                if m:
                    metrics["unmapped_pct"] = float(m.group(1))
                    metrics["unmapped_rows"] = int(m.group(2))
            elif cat == "normalized_specs品質":
                metrics["normalized_specs_score"] = to_float(row.get("score"))
                m = re.search(r"不一致の行が\s*(\d+)\s*行", problems)
                if m:
                    metrics["unit_mismatch_rows"] = int(m.group(1))
                m = re.search(r"数値化できていない行が\s*(\d+)\s*行", problems)
                if m:
                    metrics["numeric_parse_failed_rows"] = int(m.group(1))
                m = re.search(r"異なる値が\s*(\d+)\s*組", problems)
                if m:
                    metrics["value_conflicts"] = int(m.group(1))
    # フォールバック（レポート文言が変わっても CSV 実数から埋める）
    if metrics["unit_mismatch_rows"] is None and tables.get("unit_mismatches.csv") is not None:
        metrics["unit_mismatch_rows"] = len(tables["unit_mismatches.csv"])
    if metrics["value_conflicts"] is None and tables.get("duplicate_canonical_items.csv") is not None:
        metrics["value_conflicts"] = sum(
            1 for r in tables["duplicate_canonical_items.csv"]
            if (to_float(r.get("n_distinct_values")) or 0) > 1)
    if metrics["unmapped_rows"] is None and tables.get("unmapped_raw_items.csv") is not None:
        metrics["unmapped_rows"] = sum(
            int(to_float(r.get("n_rows")) or 0) for r in tables["unmapped_raw_items.csv"])
    return metrics


# ---------------------------------------------------------------- 各分類器

def make_finding(review_id, issue_type, priority, classification, question,
                 recommendation, decision, options, confidence, affected_count,
                 sample_values, source_examples, reason, uncertainty, **extras):
    f = {
        "review_id": review_id,
        "issue_type": issue_type,
        "priority": priority,
        "classification": classification,
        "question": question,
        "ai_recommendation": recommendation,
        "recommended_decision": decision,
        "decision_options": options,
        "confidence": round(confidence, 2),
        "affected_count": affected_count,
        "sample_values": sample_values,
        "source_examples": source_examples,
        "reason": reason,
        "ai_uncertainty": uncertainty,
        "needs_human": confidence < 0.8 or priority == "P1",
    }
    f.update(extras)
    return f


def analyze_risky_groups(rows, source_name, canonical_names=frozenset()):
    """risky_group_merges（または suspicious_mappings）を群単位に集約し、分割案を作る。

    監査側の定義（sql/10 の risky_group_merges）に合わせ、同一 (rule_name, canonical_item) に
    複数の異なる raw_item_name が寄っている群だけを「統合リスク」として扱う。
    raw_item_name が1種類だけの群は統合ではないため対象外とし、件数のみ記録する。
    """
    findings, splits = [], []
    groups = defaultdict(list)
    for r in rows:
        key = (r.get("rule_name") or r.get("group") or "unknown",
               r.get("canonical_item") or "")
        groups[key].append(r)
    skipped_single_raw = 0
    idx, sidx = 0, 0
    for (rule, canonical), members in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        if len({m.get("raw_item_name") or "" for m in members}) < 2:
            skipped_single_raw += 1
            continue
        idx += 1
        rid = f"RGM-{idx:04d}"
        names = sorted({m.get("raw_item_name") or "" for m in members})
        concern = members[0].get("concern") or rule
        # raw項目名を条件バケットに振り分けて分割案を作る
        buckets = defaultdict(list)
        base = []
        canonical_words = set((canonical or "").lower().split("_"))
        for name in names:
            hit = None
            for bname, pat, suffix in CONDITION_BUCKETS:
                # canonical 名が既に条件語を含む場合（max_reach 等）はその条件で分割しない
                if bname in canonical_words or suffix.strip("_") in canonical_words:
                    continue
                if contains(pat, name):
                    hit = (bname, suffix)
                    break
            if hit:
                buckets[hit].append(name)
            else:
                base.append(name)
        split_targets = {k: v for k, v in buckets.items()}
        proposal = ""
        if split_targets and (base or len(split_targets) > 1):
            parts = [f"{canonical}{suffix}({len(ns)}件)" for (b, suffix), ns in sorted(split_targets.items())]
            proposal = f"{canonical} を分割: 基本={canonical}, 追加=" + ", ".join(parts)
        findings.append(make_finding(
            rid, "risky_group_merge", "P1", rule,
            f"canonical_item「{canonical}」に意味の異なる項目が混ざっていないか（{concern}）",
            proposal or f"raw項目名を確認し、条件違いがあれば {canonical} を分割する",
            "split_canonical" if proposal else "keep_manual_review",
            ["approve", "reject", "split_canonical", "needs_source_check", "keep_manual_review"],
            0.7 if proposal else 0.5,
            len(members),
            " | ".join(names[:6]),
            " | ".join(f"{m.get('company','')}:{m.get('product_name') or m.get('product','')}"
                       for m in members[:4]),
            f"監査({source_name})が「{concern}」として検出",
            "" if proposal else "raw項目名から条件語を特定できず、分割の要否を機械判定できない",
            canonical_item=canonical, rule_name=rule,
        ))
        if proposal:
            for (bname, suffix), ns in sorted(split_targets.items()):
                sidx += 1
                new_item = canonical + suffix
                exists = new_item in canonical_names
                splits.append(make_finding(
                    f"SPL-{sidx:04d}", "canonical_split_proposal", "P1", rule,
                    f"「{canonical}」から「{new_item}」を分割してよいか",
                    (f"既存の {new_item} へマッピングを振り替える（項目は実在する）" if exists
                     else f"{new_item} を新設し、条件語（{bname}）を含む raw 項目を移す"),
                    "split_canonical",
                    ["approve", "reject", "split_canonical", "needs_source_check"],
                    0.75 if exists else 0.7, len(ns),
                    " | ".join(ns[:6]), "",
                    f"raw項目名に条件語（{bname}）を含むため、無条件の {canonical} と同列比較できない",
                    "" if exists else "接尾辞の命名は既存canonical規約に合わせて人間が最終決定する",
                    current_canonical_item=canonical, new_canonical_item=new_item,
                    target_raw_items=" | ".join(ns), parent_review_id=rid,
                ))
    return findings, splits, skipped_single_raw


def classify_unmapped_row(name, notes):
    """unmapped_raw_items の1行を5分類する。(分類, 推奨decision, 候補canonical, 理由, conf, 迷い)"""
    if SINGLE_LETTER_SUFFIX.search(name or ""):
        return ("source_extraction_issue", "needs_source_check", "",
                "一文字接尾辞はヘッダ分解の失敗を示す（元表の列見出しが崩れている疑い）",
                0.8, "元Excelを見て正しい列名を確認する必要がある")
    for pat, why, conf in EXCLUDE_RULES:
        if pat.search(name or ""):
            return ("exclude_from_comparison", "exclude_from_comparison", "", why, conf, "")
    for pat, canonical, display, category, unit, vtype in NEW_CANONICAL_RULES:
        if contains(pat, name):
            return ("create_new_canonical", "create_new_canonical", canonical,
                    f"比較価値があるが対応するcanonicalが無い（候補: {canonical} / {display} / {unit}）",
                    0.7, "canonical_unit と value_type は既存規約と突き合わせて確認")
    for pat, canonical, conf in MAP_TO_EXISTING_RULES:
        if contains(pat, name):
            if contains(r"option|オプション", name):
                return ("manual_review_required", "keep_manual_review", canonical,
                        f"{canonical} に近いがオプション条件付き", 0.45,
                        "オプション条件付きのため、既存項目に寄せるとオプション/標準の混同になる恐れ")
            if canonical.startswith("aux_") and contains(r"driving|working", name):
                return ("manual_review_required", "keep_manual_review", canonical,
                        f"{canonical} は補助(aux)回路の項目だが、raw名は駆動/作業油圧を指しており別回路の疑い",
                        0.45, "drive_hydraulic_system / work_hydraulic_system 等の別項目が正しい可能性")
            return ("map_to_existing", "map_to_existing", canonical,
                    f"既存 canonical「{canonical}」と同義とみなせる語を含む", conf,
                    "canonical定義（単位・value_type）との整合は人間確認")
    if contains(r"option|オプション", name):
        return ("manual_review_required", "keep_manual_review", "",
                "オプション項目。新設(_optional)か除外かの判断が必要", 0.45,
                "オプション項目を比較軸に含める方針が未確定")
    return ("manual_review_required", "keep_manual_review", "",
            "既存の規則で分類できない", 0.4, "候補canonicalを特定できず、元表の文脈が必要")


def analyze_unmapped(rows, canonical_names=None):
    findings = []
    ordered = sorted(rows, key=lambda r: -(to_float(r.get("n_rows")) or 0))
    for i, r in enumerate(ordered, 1):
        name = r.get("raw_item_name") or ""
        cls, decision, canonical, why, conf, unc = classify_unmapped_row(name, r.get("notes_example"))
        cls, decision, canonical, why, conf, unc = validate_against_canonical(
            cls, decision, canonical, why, conf, unc, canonical_names)
        n_rows = int(to_float(r.get("n_rows")) or 0)
        priority = "P2" if cls == "source_extraction_issue" else "P3"
        findings.append(make_finding(
            f"UNM-{i:04d}", "unmapped_raw_item", priority, cls,
            f"未マッピング項目「{name}」をどう扱うか",
            {"map_to_existing": f"{canonical} にマッピング（synonym追加）",
             "create_new_canonical": f"新規canonical「{canonical}」を作成",
             "exclude_from_comparison": "比較対象外にする",
             "source_extraction_issue": "取り込み側（raw_specs構築）の修正が先",
             "manual_review_required": "人間が分類する"}[cls],
            decision,
            ["map_to_existing", "create_new_canonical", "exclude_from_comparison",
             "needs_source_check", "keep_manual_review", "reject"],
            conf, n_rows,
            (r.get("notes_example") or "")[:80],
            f"{r.get('company','')}: {name}（{r.get('products','')}製品）",
            why, unc,
            raw_item_name=name, company=r.get("company", ""),
            proposed_canonical=canonical,
        ))
    return findings


def classify_unit_row(r):
    """unit_mismatches の1行を6分類する。(分類, decision, rule, conf, 理由, 迷い)"""
    canonical_unit = (r.get("canonical_unit") or "").strip()
    original_unit = (r.get("original_unit") or "").strip()
    original_value = (r.get("original_value") or "").strip()
    notes = r.get("notes") or ""
    key = (original_unit.lower(), canonical_unit)
    if key in KNOWN_UNIT_RULES:
        rule, conf, note = KNOWN_UNIT_RULES[key]
        return ("missing_conversion_rule", "add_conversion_rule", rule, conf,
                f"{original_unit} → {canonical_unit} は既知の換算（{note}）",
                "" if conf >= 0.8 else note)
    if original_unit and original_unit.lower() == canonical_unit.lower():
        return ("value_contains_condition", "keep_manual_review", "", 0.65,
                "単位は一致しており、変換でなく値の数値化失敗（条件・レンジ・複数値）が原因",
                "代表値を採るか、テキスト保持のままにするかは比較方針次第")
    # 複合単位の判定: 「Ah / 48V」のような空白付きスラッシュ・@・複数スラッシュのみ。
    # km/h・L/min のような通常の比率単位は複合扱いしない
    if "@" in original_unit or " / " in original_unit or original_unit.count("/") > 1:
        return ("not_convertible", "do_not_convert", "", 0.75,
                f"複合単位「{original_unit}」は追加情報なしに {canonical_unit} へ一意換算できない",
                "値に必要情報（例: 電圧）が含まれる場合の複合パースを行うかは設計判断")
    if "(" in original_unit:
        return ("wrong_raw_unit_extraction", "fix_raw_unit_extraction", "", 0.7,
                f"単位「{original_unit}」が複合表記の誤分解に見える（値と単位の切り出し不備）",
                "元セルの表記を確認して抽出規則を直す必要がある")
    if "[numeric_parse_failed]" in notes or RANGE_OR_MULTI.search(original_value):
        return ("value_contains_condition", "keep_manual_review", "", 0.65,
                "値に条件・レンジ・複数値が含まれ、単純な数値化・換算ができない",
                "代表値を採るか、テキスト保持のままにするかは比較方針次第")
    if "[unit_no_rule]" in notes:
        return ("missing_conversion_rule", "keep_manual_review", "", 0.5,
                f"{original_unit} → {canonical_unit} の変換ルールが無い（既知テーブルにも無し）",
                "換算式が一意に書けるか要確認。書けなければ do_not_convert にすべき")
    if not original_unit and not original_value.replace(".", "").isdigit():
        return ("wrong_raw_unit_extraction", "needs_source_check", "", 0.5,
                "元単位が抽出されておらず、値がそのまま数値でない", "元表を見ないと原因を特定できない")
    return ("manual_review_required", "keep_manual_review", "", 0.4,
            "既存の規則で原因を特定できない", "unit と値の組から原因を機械判定できない")


def analyze_unit_mismatches(rows):
    findings = []
    # 同一 (canonical_item, original_unit, canonical_unit, 原因) は1判断に集約する
    groups = defaultdict(list)
    for r in rows:
        cls = classify_unit_row(r)
        key = (r.get("canonical_item") or "", (r.get("original_unit") or "").strip(),
               r.get("canonical_unit") or "", cls[0], cls[2])
        groups[key].append((r, cls))
    for i, (key, members) in enumerate(
            sorted(groups.items(), key=lambda kv: -len(kv[1])), 1):
        canonical, orig_unit, canon_unit, cls_name, rule = key
        r0, (cls, decision, rule, conf, why, unc) = members[0][0], members[0][1]
        findings.append(make_finding(
            f"UNI-{i:04d}", "unit_mismatch", "P2", cls,
            f"「{canonical}」の {orig_unit or '(単位なし)'} → {canon_unit} 不一致をどう解消するか",
            {"missing_conversion_rule": f"変換ルール追加: {rule or '（式は人間が確定）'}",
             "wrong_canonical_unit": "canonical_unit の変更を検討",
             "wrong_raw_unit_extraction": "抽出ロジックの修正（値/単位の切り出し）",
             "not_convertible": "変換禁止（blocklist）にしてテキスト保持を正式化",
             "value_contains_condition": "条件付き値。数値化方針を人間が決める",
             "manual_review_required": "人間が原因を特定する"}[cls],
            decision,
            ["add_conversion_rule", "change_canonical_unit", "fix_raw_unit_extraction",
             "do_not_convert", "needs_source_check", "keep_manual_review", "reject"],
            conf, len(members),
            " | ".join((m[0].get("original_value") or "")[:40] for m in members[:4]),
            " | ".join(f"{m[0].get('company','')}:{m[0].get('product_name','')}" for m in members[:4]),
            why, unc,
            canonical_item=canonical, original_unit=orig_unit,
            target_unit=canon_unit, conversion_rule=rule,
        ))
    return findings


def classify_duplicate_row(r):
    """duplicate_canonical_items の1行を7分類する。"""
    canonical = r.get("canonical_item") or ""
    values_raw = [v.strip() for v in (r.get("values_seen") or "").split("|")]
    n_distinct = int(to_float(r.get("n_distinct_values")) or 0)
    nums = [to_float(v) for v in values_raw]
    if n_distinct <= 1:
        return ("duplicate_source_rows", "approve", 0.9,
                "全行が同一値。元表の重複取り込みであり、重複排除で解決できる", "")
    if any(n is None for n in nums):
        return ("manual_review_required", "needs_source_check", 0.6,
                "値に非数値（規格文字列等）が混入しており、抽出不備の疑いがある",
                "どの行が正しい値か元表を見ないと判定できない")
    spread = (max(nums) - min(nums)) / max(abs(max(nums)), 1e-9)
    if spread < 0.02:
        return ("duplicate_source_rows", "approve", 0.75,
                "値の差が2%未満で、丸め・換算経路の違いによる実質同一値とみられる",
                "どちらの精度を採用するかは要確認")
    if RANGE_OR_MULTI.search(r.get("values_seen") or ""):
        return ("range_or_multi_value", "keep_manual_review", 0.55,
                "レンジ・複数値表記が別行に分かれた疑い", "代表値の選び方が未定")
    if contains(r"power|torque|出力|トルク", canonical):
        return ("rated_vs_peak_value", "keep_manual_review", 0.5,
                "出力系で値が2系統に分かれており、定格/最大の混在が疑われる",
                "どちらが定格かは元表の脚注を見ないと確定できない")
    if contains(r"load|capacity|荷重|容量", canonical):
        return ("standard_vs_max_value", "keep_manual_review", 0.5,
                "荷重・容量系で値が分かれており、標準/最大の混在が疑われる",
                "測定条件（アタッチメント等）の違いの可能性もある")
    if contains(r"weight|重量|質量", canonical):
        return ("body_vs_packaging", "keep_manual_review", 0.5,
                "重量系で値が分かれており、本体/梱包・キャブ有無の混在が疑われる",
                "構成（キャブ/キャノピー等）の情報が raw 項目名側に必要")
    return ("manual_review_required", "keep_manual_review", 0.4,
            "値が食い違う原因を機械判定できない", "元表・raw項目名の突き合わせが必要")


def analyze_duplicates(rows):
    findings = []
    # 同一 canonical_item × 分類で集約（1行1判断、同じ問題は寄せる）
    classified = [(r, classify_duplicate_row(r)) for r in rows]
    groups = defaultdict(list)
    for r, cls in classified:
        groups[(r.get("canonical_item") or "", cls[0])].append((r, cls))
    for i, ((canonical, cls_name), members) in enumerate(
            sorted(groups.items(), key=lambda kv: -len(kv[1])), 1):
        r0, (cls, decision, conf, why, unc) = members[0]
        conflict = cls != "duplicate_source_rows"
        findings.append(make_finding(
            f"DUP-{i:04d}", "duplicate_canonical_item",
            "P1" if conflict else "P2", cls,
            f"「{canonical}」の同一製品内重複（{cls}）をどう解消するか",
            {"duplicate_source_rows": "重複排除（1製品1行に統合）を normalizer に指示",
             "standard_vs_max_value": f"標準/最大の分離。必要なら {canonical} を分割",
             "rated_vs_peak_value": f"定格/最大の分離。必要なら {canonical} を分割",
             "body_vs_packaging": f"本体/梱包・構成別の分離。必要なら {canonical} を分割",
             "option_vs_standard": "オプション/標準の分離",
             "range_or_multi_value": "レンジ・複数値の取り扱い規則を決める",
             "manual_review_required": "元表を確認して原因を特定する"}[cls],
            decision,
            ["approve", "reject", "split_canonical", "needs_source_check", "keep_manual_review"],
            conf, len(members),
            " | ".join((m[0].get("values_seen") or "")[:50] for m in members[:3]),
            " | ".join(f"{m[0].get('company','')}:{m[0].get('product_id','')}" for m in members[:4]),
            why, unc,
            canonical_item=canonical,
        ))
    return findings


def analyze_low_confidence(rows):
    findings = []
    # raw_item_name × canonical_item で集約
    groups = defaultdict(list)
    multi_canonical = defaultdict(set)
    for r in rows:
        groups[(r.get("raw_item_name") or "", r.get("canonical_item") or "")].append(r)
        multi_canonical[(r.get("company"), r.get("raw_item_name"))].add(r.get("canonical_item"))
    for i, ((raw_name, canonical), members) in enumerate(
            sorted(groups.items(), key=lambda kv: -len(kv[1])), 1):
        r0 = members[0]
        conf0 = to_float(r0.get("confidence")) or 0.0
        if len(multi_canonical[(r0.get("company"), raw_name)]) > 1:
            bucket, decision = "canonical設計見直し候補", "keep_manual_review"
            why = "同一raw項目が複数canonicalに割り当てられており、設計側の見直しが必要"
        elif contains(r"テキスト保持|変換規則が無い|変換ルールなし", r0.get("notes") or ""):
            bucket, decision = "人間レビュー候補", "keep_manual_review"
            why = "単位変換不能によりテキスト保持。unit_mismatch 側の判断（変換/禁止）と連動"
        elif (r0.get("mapping_method") == "inferred") and conf0 <= 0.65:
            bucket, decision = "人間レビュー候補", "keep_manual_review"
            why = "推測（inferred）マッピングで confidence が低く、意味の確認が必要"
        else:
            bucket, decision = "人間レビュー候補", "approve"
            why = "confidence がやや低いが根拠が明確なら承認可"
        findings.append(make_finding(
            f"LCM-{i:04d}", "low_confidence_mapping", "P3", bucket,
            f"低confidenceマッピング「{raw_name}」→「{canonical}」を確定してよいか",
            f"{bucket}として扱う（{why}）",
            decision,
            ["approve", "reject", "map_to_existing", "exclude_from_comparison",
             "needs_source_check", "keep_manual_review"],
            min(conf0 + 0.1, 0.7), len(members),
            (r0.get("notes") or "")[:80],
            " | ".join(f"{m.get('company','')}:{m.get('product_name','')}" for m in members[:4]),
            why, "低confidenceの確定は人間承認が必須（勝手に確定しない）",
            raw_item_name=raw_name, canonical_item=canonical,
        ))
    return findings


def derive_exclusions(unmapped_findings, lcm_findings):
    """UNM/LCM から除外候補（EXC-）を派生させる。"""
    out = []
    i = 0
    for f in unmapped_findings + lcm_findings:
        if f["classification"] in ("exclude_from_comparison", "除外候補"):
            i += 1
            out.append(make_finding(
                f"EXC-{i:04d}", "exclusion_candidate", "P3", f["classification"],
                f"「{f.get('raw_item_name','')}」を比較対象外にしてよいか",
                "比較対象外（raw_specsには残す）", "exclude_from_comparison",
                ["exclude_from_comparison", "reject", "map_to_existing", "keep_manual_review"],
                f["confidence"], f["affected_count"],
                f["sample_values"], f["source_examples"],
                f["reason"], "重要スペックなら除外でなく新規canonicalを検討",
                raw_item_name=f.get("raw_item_name", ""), parent_review_id=f["review_id"],
            ))
    return out


# ---------------------------------------------------------------- main

def run_analysis(audit_dir: Path, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    missing, fallbacks = [], []
    tables = {}
    for name in EXPECTED_INPUTS:
        path = audit_dir / name
        if name.endswith(".csv"):
            data = read_csv_dicts(path)
            if data is None:
                missing.append(name)
            tables[name] = data
        elif not path.exists():
            missing.append(name)

    # risky_group_merges が無ければ suspicious_mappings を代替
    risky_rows = tables.get("risky_group_merges.csv")
    risky_source = "risky_group_merges.csv"
    if risky_rows is None:
        risky_rows = tables.get("suspicious_mappings.csv") or []
        risky_source = "suspicious_mappings.csv (fallback)"
        if "risky_group_merges.csv" in missing:
            fallbacks.append("risky_group_merges.csv → suspicious_mappings.csv を代替使用")

    canonical_names = load_canonical_names(audit_dir)
    if canonical_names is None:
        fallbacks.append("raw/canonical_definitions.csv 無し → canonical候補名は未検証")

    rgm, spl, rgm_single_raw = analyze_risky_groups(
        risky_rows, risky_source, canonical_names or frozenset())
    unm = analyze_unmapped(tables.get("unmapped_raw_items.csv") or [], canonical_names)
    uni = analyze_unit_mismatches(tables.get("unit_mismatches.csv") or [])
    dup = analyze_duplicates(tables.get("duplicate_canonical_items.csv") or [])
    lcm = analyze_low_confidence(tables.get("low_confidence_mappings.csv") or [])
    exc = derive_exclusions(unm, lcm)
    findings = rgm + spl + unm + uni + dup + lcm + exc

    metrics = parse_current_metrics(audit_dir, tables)

    summary_rows = []
    counter = defaultdict(lambda: {"count": 0, "affected": 0, "human": 0, "priority": "P4"})
    for f in findings:
        key = (f["issue_type"], f["classification"])
        c = counter[key]
        c["count"] += 1
        c["affected"] += f["affected_count"]
        c["human"] += 1 if f["needs_human"] else 0
        c["priority"] = min(c["priority"], f["priority"])
    for (issue_type, cls), c in sorted(counter.items(),
                                       key=lambda kv: (kv[1]["priority"], -kv[1]["affected"])):
        summary_rows.append({
            "issue_type": issue_type, "classification": cls, "priority": c["priority"],
            "findings": c["count"], "affected_rows": c["affected"],
            "needs_human_review": c["human"],
        })
    write_csv(out_dir / "remediation_summary.csv",
              ["issue_type", "classification", "priority", "findings",
               "affected_rows", "needs_human_review"], summary_rows)

    analysis = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "audit_dir": str(audit_dir),
        "missing_inputs": missing,
        "fallbacks": fallbacks,
        "risky_source": risky_source,
        "rgm_single_raw_skipped": rgm_single_raw,
        "canonical_names_available": canonical_names is not None,
        "n_canonical_names": len(canonical_names) if canonical_names else 0,
        "current_metrics": metrics,
        "findings": findings,
        "summary": summary_rows,
    }
    with (out_dir / ANALYSIS_JSON).open("w", encoding="utf-8") as f:
        json.dump(analysis, f, ensure_ascii=False, indent=1)
    with (out_dir / RUN_META_JSON).open("w", encoding="utf-8") as f:
        json.dump({"generated_at": analysis["generated_at"], "missing_inputs": missing,
                   "fallbacks": fallbacks, "n_findings": len(findings)},
                  f, ensure_ascii=False, indent=1)
    return analysis


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--audit-dir", type=Path, default=DEFAULT_AUDIT_DIR)
    ap.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = ap.parse_args(argv)
    analysis = run_analysis(args.audit_dir, args.out_dir)
    n_p1 = sum(1 for f in analysis["findings"] if f["priority"] == "P1")
    print(f"findings: {len(analysis['findings'])} (P1: {n_p1})")
    if analysis["missing_inputs"]:
        print("missing inputs:", ", ".join(analysis["missing_inputs"]))
    for fb in analysis["fallbacks"]:
        print("fallback:", fb)
    print(f"written: {args.out_dir / ANALYSIS_JSON}")
    print(f"written: {args.out_dir / 'remediation_summary.csv'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
