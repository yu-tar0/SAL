# -*- coding: utf-8 -*-
"""SQL 監査結果を読み込み、スコアリング基準に沿って点数化し、品質監査レポートを生成する。

使い方:
    python .github/skills/product-spec-quality-auditor/scripts/generate_audit_report.py
    python .github/skills/product-spec-quality-auditor/scripts/generate_audit_report.py --out-dir audit_outputs

前提:
    先に scripts/run_audit.py を実行し、audit_outputs/raw/ に CSV と _run_meta.json があること。

動作:
    - audit_outputs/raw/score_inputs_*.csv から数値指標を読み込む。
    - docs/score_rubric.md の基準どおりに 100 点満点で機械的スコアを算出する。
    - 問題を 重大 / 中程度 / 軽微 に分類する。
    - audit_outputs/quality_audit_report.md と audit_outputs/audit_summary.csv を出力する。
    - DB には一切接続しない（CSV のみを読む）。ファイルの追加以外の変更はしない。

重要:
    ここで出るスコアは「機械的に測れる指標」に基づくベースライン。
    マッピングの意味的な妥当性（重量種別・定格/最大の混同など）は suspicious_mappings.csv を
    人間またはエージェントがレビューし、必要ならレポートの点数・判定を下方修正すること。
"""
import argparse
import csv
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]

CATEGORIES = [
    ("データ保全", 15),
    ("テーブル設計", 10),
    ("raw_specs品質", 10),
    ("canonical_specs品質", 10),
    ("spec_mapping品質", 20),
    ("normalized_specs品質", 15),
    ("comparison_view品質", 10),
    ("issue管理", 5),
    ("運用しやすさ", 5),
]


# ---------------------------------------------------------------- 入出力補助

def load_raw_csv(raw_dir: Path, name: str):
    """raw/<name>.csv を [dict, ...] で返す。無ければ None。"""
    path = raw_dir / f"{name}.csv"
    if not path.exists():
        return None
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def load_metrics(raw_dir: Path) -> dict:
    metrics = {}
    for path in sorted(raw_dir.glob("score_inputs_*.csv")):
        with path.open(encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                try:
                    metrics[row["metric"]] = float(row["value"])
                except (KeyError, TypeError, ValueError):
                    pass
    return metrics


def parse_pct(value) -> float:
    """null_percentage は版によって '25.0%' 文字列のことがあるため防御的に解析する。"""
    if value is None:
        return 0.0
    try:
        return float(str(value).replace("%", "").strip())
    except ValueError:
        return 0.0


# ---------------------------------------------------------------- スコアリング

class Finding:
    def __init__(self, severity, category, problem, impact, evidence, target):
        self.severity = severity  # critical / moderate / minor
        self.category = category
        self.problem = problem
        self.impact = impact
        self.evidence = evidence
        self.target = target


class Scorer:
    def __init__(self, metrics, meta, raw_dir):
        self.m = metrics
        self.meta = meta
        self.raw_dir = raw_dir
        self.findings: list[Finding] = []
        self.goods: list[str] = []
        self.scores: dict[str, tuple[int, int, str]] = {}  # name -> (score, max, note)

    def get(self, name, default=None):
        return self.m.get(name, default)

    def add(self, severity, category, problem, impact, evidence, target):
        self.findings.append(Finding(severity, category, problem, impact, evidence, target))

    def unavailable(self, category, max_pts, reason):
        self.add("critical", category, f"監査に必要な指標が取得できない（{reason}）",
                 "このカテゴリは品質を保証できない", "score_inputs の実行失敗（_run_meta.json 参照）",
                 reason)
        self.scores[category] = (0, max_pts, "評価不能（対象オブジェクト不足）")

    # --- 各カテゴリ ---

    def score_preservation(self):
        cat, mx = "データ保全", 15
        raw_total = self.get("raw_rows_total")
        norm_total = self.get("normalized_present_rows")
        if raw_total is None or self.get("normalized_not_traceable") is None:
            return self.unavailable(cat, mx, "raw_specs / normalized_specs が読めない")
        pts = mx
        unc = self.get("uncovered_source_tables", 0)
        if unc > 0:
            d = 4 if unc > 3 else 2
            pts -= d
            self.add("moderate", cat, f"raw_specs に取り込まれていない元テーブルが {unc:.0f} 件ある",
                     "元データの一部が標準化対象から漏れている",
                     "uncovered_source_tables.csv", "raw_specs")
        miss_src = self.get("raw_missing_source", 0)
        if miss_src > 0:
            pts -= 3
            self.add("critical", cat, f"raw_specs の source 情報欠落が {miss_src:.0f} 行ある",
                     "元テーブル・元行へ遡れない", "raw_specs_source_gaps.csv", "raw_specs")
        nt = self.get("normalized_not_traceable", 0)
        denom = norm_total or self.get("normalized_present_rows", 0) or 1
        nt_ratio = 100.0 * nt / max(denom, 1)
        if nt > 0:
            if nt_ratio > 5:
                pts -= 8
                sev = "critical"
            elif nt_ratio > 1:
                pts -= 5
                sev = "critical"
            else:
                pts -= 2
                sev = "moderate"
            self.add(sev, cat,
                     f"normalized から raw へ戻れない行が {nt:.0f} 行（{nt_ratio:.1f}%）ある",
                     "値の根拠を原本で確認できない",
                     "normalized_not_traceable_examples.csv", "normalized_specs")
        else:
            self.goods.append("normalized_specs の全行が raw_specs（元テーブル・元行・元列）へ追跡できる")
        miss_orig = self.get("normalized_missing_original", 0)
        if miss_orig > 0:
            pts -= 2
            self.add("moderate", cat, f"present なのに original_value が無い行が {miss_orig:.0f} 行ある",
                     "元値との対応が追えない", "normalized_specs_source_gaps.csv", "normalized_specs")
        if miss_src == 0 and unc == 0:
            self.goods.append("raw_specs の source 情報（元テーブル・元行・元列）に欠落がない")
        self.scores[cat] = (int(round(max(pts, 0))), mx, "")

    def score_table_design(self):
        cat, mx = "テーブル設計", 10
        pts = mx
        presence = load_raw_csv(self.raw_dir, "expected_objects_presence") or []
        missing = [r["object_name"] for r in presence if r.get("presence") == "MISSING"]
        core = {"products", "raw_specs", "canonical_specs", "spec_mapping",
                "normalized_specs", "normalization_issues",
                "product_comparison_core_view", "product_comparison_full_view"}
        core_missing = [x for x in missing if x in core]
        if core_missing:
            pts -= min(8, 2 * len(core_missing))
            self.add("critical", cat,
                     "必須オブジェクトが存在しない: " + ", ".join(core_missing),
                     "標準化パイプラインが完結していない",
                     "expected_objects_presence.csv", ", ".join(core_missing))
        aux_missing = [x for x in missing if x not in core]
        if aux_missing:
            pts -= 1
            self.add("minor", cat,
                     "補助オブジェクトが存在しない: " + ", ".join(aux_missing),
                     "辞書・変換ルールの再現性が下がる",
                     "expected_objects_presence.csv", ", ".join(aux_missing))
        for name, metric in [("products", "products_total"), ("raw_specs", "raw_rows_total"),
                             ("canonical_specs", "canonical_items_total"),
                             ("spec_mapping", "mapping_rows_total")]:
            v = self.get(metric)
            if v is not None and v == 0:
                pts -= 2
                self.add("critical", cat, f"{name} が 0 行", "パイプラインが実質未実行",
                         f"row_count_{name}.csv", name)
        if not missing:
            self.goods.append("期待される標準化テーブル・ビューがすべて存在する")
        self.scores[cat] = (int(round(max(pts, 0))), mx, "")

    def score_raw(self):
        cat, mx = "raw_specs品質", 10
        if self.get("raw_rows_total") is None:
            return self.unavailable(cat, mx, "raw_specs が読めない")
        pts = mx
        pw = self.get("products_without_raw", 0)
        if pw > 0:
            pts -= min(4, 2 * pw)
            self.add("critical", cat, f"raw_specs に 1 行も無い製品が {pw:.0f} 件ある",
                     "その製品は比較表にほぼ欠損で並ぶ", "products_raw_spec_counts.csv", "products / raw_specs")
        orphan = self.get("raw_products_not_in_master", 0)
        if orphan > 0:
            pts -= 2
            self.add("moderate", cat, f"products マスタに無い product_id が raw_specs に {orphan:.0f} 件ある",
                     "製品との紐づけが壊れている", "raw_products_not_in_master.csv", "raw_specs")
        dup = self.get("raw_duplicate_groups", 0)
        if dup > 0:
            pts -= 2
            self.add("moderate", cat, f"raw_specs に重複行グループが {dup:.0f} 件ある",
                     "二重取り込みの疑い。集計・正規化が二重になる", "raw_duplicate_rows.csv", "raw_specs")
        sep = self.get("raw_unit_not_separated", 0)
        total = max(self.get("raw_rows_total", 1), 1)
        if sep > 0:
            if 100.0 * sep / total > 1:
                pts -= 2
                sev = "moderate"
            else:
                pts -= 1
                sev = "minor"
            self.add(sev, cat, f"値と単位が分離されていない疑いの行が {sep:.0f} 行ある",
                     "単位変換・数値比較ができない", "raw_value_unit_not_separated.csv", "raw_specs")
        else:
            self.goods.append("raw_specs で値と単位の分離漏れは検出されなかった")
        if pw == 0:
            self.goods.append("products の全製品に raw_specs の仕様行がある")
        self.scores[cat] = (int(round(max(pts, 0))), mx, "")

    def score_canonical(self):
        cat, mx = "canonical_specs品質", 10
        total = self.get("canonical_items_total")
        if total is None:
            return self.unavailable(cat, mx, "canonical_specs が読めない")
        pts = mx
        gaps = self.get("canonical_field_gaps", 0)
        if gaps > 0:
            pts -= 2
            self.add("moderate", cat, f"category / priority / value_type が未定義の項目が {gaps:.0f} 件ある",
                     "比較軸としての扱いが不定になる", "canonical_field_gaps.csv", "canonical_specs")
        dup = self.get("canonical_dup_display_names", 0)
        if dup > 0:
            pts -= 1
            self.add("minor", cat, f"表示名が重複する canonical 項目が {dup:.0f} 組ある",
                     "同じ意味の二重定義の疑い", "canonical_duplicate_display_names.csv", "canonical_specs")
        unused = self.get("canonical_unused", 0)
        if total and 100.0 * unused / total > 30:
            pts -= 2
            self.add("minor", cat, f"未使用の canonical 項目が {unused:.0f}/{total:.0f} 件ある",
                     "定義過剰。比較軸の設計を見直す余地", "canonical_unused_items.csv", "canonical_specs")
        cov = self.get("priority1_avg_coverage_pct")
        if cov is not None:
            if cov < 30:
                pts -= 4
                self.add("critical", cat, f"priority=1 項目の平均製品カバー率が {cov:.0f}% しかない",
                         "最重要比較項目が比較表として機能しない",
                         "canonical_product_coverage.csv", "canonical_specs / normalized_specs")
            elif cov < 50:
                pts -= 3
                self.add("moderate", cat, f"priority=1 項目の平均製品カバー率が {cov:.0f}% と低い",
                         "主要比較項目に欠損が多い", "canonical_product_coverage.csv", "canonical_specs")
            else:
                self.goods.append(f"priority=1 の主要比較項目は平均 {cov:.0f}% の製品をカバーしている")
        self.scores[cat] = (int(round(max(pts, 0))), mx, "")

    def score_mapping(self):
        cat, mx = "spec_mapping品質", 20
        total = self.get("mapping_rows_total")
        if total is None or total == 0:
            return self.unavailable(cat, mx, "spec_mapping が読めない、または 0 行")
        pts = mx
        unmapped = self.get("mapping_unmapped", 0)
        rate = 100.0 * unmapped / total
        if rate > 30:
            pts -= 10
            self.add("critical", cat, f"未マッピング率が {rate:.1f}%（{unmapped:.0f}/{total:.0f}）",
                     "比較表の大半が欠損になる", "unmapped_raw_items.csv", "spec_mapping")
        elif rate > 15:
            pts -= 6
            self.add("moderate", cat, f"未マッピング率が {rate:.1f}%（{unmapped:.0f}/{total:.0f}）",
                     "辞書追加のレビューが必要", "unmapped_raw_items.csv", "spec_mapping")
        elif rate > 5:
            pts -= 3
            self.add("moderate", cat, f"未マッピング率が {rate:.1f}%",
                     "残項目の要否判断が必要", "unmapped_raw_items.csv", "spec_mapping")
        else:
            self.goods.append(f"未マッピング率が {rate:.1f}% と低い")
        mapped = max(total - unmapped, 1)
        lt070 = self.get("mapping_conf_lt_070", 0)
        lt050 = self.get("mapping_conf_lt_050", 0)
        r070 = 100.0 * lt070 / mapped
        if r070 > 10:
            pts -= 4
            self.add("moderate", cat, f"confidence<0.7 のマッピングが {lt070:.0f} 件（マッピング済の {r070:.1f}%）",
                     "推定ベースの対応が多くレビュー必須", "low_confidence_mappings.csv", "spec_mapping")
        elif r070 > 5:
            pts -= 2
            self.add("minor", cat, f"confidence<0.7 のマッピングが {lt070:.0f} 件",
                     "レビュー対象", "low_confidence_mappings.csv", "spec_mapping")
        if lt050 > 0:
            pts -= 2
            self.add("moderate", cat, f"confidence<0.5 の低確度マッピングが {lt050:.0f} 件ある",
                     "誤マッピングの可能性が高い", "low_confidence_mappings.csv", "spec_mapping")
        multi = self.get("mapping_multi_canonical_groups", 0)
        if multi > 0:
            pts -= 4
            self.add("critical", cat,
                     f"同一会社で同じ raw_item_name が複数の canonical_item に割り当てられた組が {multi:.0f} 件ある",
                     "意味の混同・比較値の取り違えに直結する",
                     "raw_item_multi_canonical_same_company.csv", "spec_mapping")
        risky = self.get("risky_group_merges", 0)
        if risky > 0:
            pts -= 5
            self.add("critical", cat,
                     f"意味が違う可能性のある項目群（重量種別・定格/最大など）を同一 canonical_item に統合している疑いが {risky:.0f} 組ある",
                     "誤った横比較（例: 本体重量と梱包重量の比較）を生む",
                     "risky_group_merges.csv / suspicious_mappings.csv", "spec_mapping")
        else:
            self.goods.append("重点確認語群（重量/定格/消費電力/寸法/規格/オプション/温度）での複数項目統合は検出されなかった")
        over = self.get("mapping_overrated_confidence", 0)
        if over > 0:
            pts -= 2
            self.add("moderate", cat, f"confidence が過大評価の疑いのあるマッピングが {over:.0f} 件ある",
                     "レビュー対象が『問題なし』に見えてしまう",
                     "confidence_overrated_candidates.csv", "spec_mapping")
        self.scores[cat] = (int(round(max(pts, 0))), mx, "")

    def score_normalized(self):
        cat, mx = "normalized_specs品質", 15
        total = self.get("normalized_present_rows")
        if total is None:
            return self.unavailable(cat, mx, "normalized_specs が読めない")
        pts = mx
        total = max(total, 1)
        um = self.get("unit_mismatch_rows", 0)
        if um > 0:
            if 100.0 * um / total > 2:
                pts -= 6
                sev = "critical"
            else:
                pts -= 3
                sev = "moderate"
            self.add(sev, cat, f"normalized_unit が canonical_unit と不一致の行が {um:.0f} 行ある",
                     "単位の違う値が同じ列で比較される", "unit_mismatches.csv", "normalized_specs")
        else:
            self.goods.append("normalized_unit と canonical_unit の不一致は 0 件")
        pf = self.get("numeric_parse_failures", 0)
        if pf > 0:
            if 100.0 * pf / total > 5:
                pts -= 4
                sev = "moderate"
            else:
                pts -= 2
                sev = "minor"
            self.add(sev, cat, f"numeric 扱いなのに数値化できていない行が {pf:.0f} 行ある",
                     "数値比較から漏れる", "numeric_parse_failures.csv", "normalized_specs")
        dup = self.get("duplicate_conflicting_pairs", 0)
        if dup > 0:
            pts -= 3
            self.add("moderate", cat,
                     f"同一 product_id×canonical_item に異なる値が {dup:.0f} 組ある",
                     "採用値の根拠確認が必要", "duplicate_canonical_items.csv", "normalized_specs")
        lc = self.get("normalized_conf_lt_070", 0)
        if 100.0 * lc / total > 20:
            pts -= 3
            self.add("moderate", cat, f"confidence<0.7 の正規化行が {lc:.0f} 行（{100.0 * lc / total:.0f}%）ある",
                     "正規化結果全体の信頼度が低い", "low_confidence_normalized.csv", "normalized_specs")
        nm = self.get("notes_missing_low_conf", 0)
        if nm > 0:
            pts -= 2
            self.add("minor", cat, f"推定を含む（confidence<0.8）のに notes が無い行が {nm:.0f} 行ある",
                     "判断理由が追跡できない", "notes_missing_low_confidence.csv", "normalized_specs")
        zn = self.get("normalized_zero_or_negative", 0)
        if zn > 0:
            pts -= 2
            self.add("moderate", cat, f"物理量なのに 0 以下の値が {zn:.0f} 行ある",
                     "変換・パースのミスの疑い", "normalized_zero_or_negative.csv", "normalized_specs")
        self.scores[cat] = (int(round(max(pts, 0))), mx, "")

    def score_comparison(self):
        cat, mx = "comparison_view品質", 10
        core = self.get("core_rows")
        if core is None:
            return self.unavailable(cat, mx, "product_comparison_core_view が読めない")
        pts = mx
        dup = self.get("core_dup_products", 0)
        if dup > 0:
            pts -= 4
            self.add("critical", cat, f"比較ビューで同一製品が重複している（{dup:.0f} 製品）",
                     "1行1製品になっていない", "comparison_core_duplicates.csv",
                     "product_comparison_core_view")
        else:
            self.goods.append("比較ビューは 1 行 1 製品になっており重複がない")
        prod = self.get("products_total")
        if prod is not None and core != prod:
            pts -= 2
            self.add("moderate", cat,
                     f"比較ビューの行数（{core:.0f}）が products の製品数（{prod:.0f}）と一致しない",
                     "製品の落ち・重複がある", "comparison_core_counts.csv",
                     "product_comparison_core_view")
        hi = self.get("core_columns_missing_ge80", 0)
        if hi > 0:
            pts -= min(4, int(hi))
            self.add("moderate", cat, f"欠損率 80% 以上の列が core ビューに {hi:.0f} 列ある",
                     "比較項目として機能していない列がある",
                     "comparison_core_missing_rates.csv", "product_comparison_core_view")
        self.scores[cat] = (int(round(max(pts, 0))), mx, "")

    def score_issues(self):
        cat, mx = "issue管理", 5
        total = self.get("issues_total")
        if total is None:
            return self.unavailable(cat, mx, "normalization_issues が読めない")
        pts = mx
        lt070 = self.get("mapping_conf_lt_070", 0)
        unmapped = self.get("mapping_unmapped", 0)
        if total == 0 and (lt070 > 0 or unmapped > 0):
            pts = 0
            self.add("critical", cat, "要レビュー項目があるのに normalization_issues が空",
                     "人間レビューの入口が無い", "issues_by_type.csv", "normalization_issues")
        lni = self.get("low_conf_not_issued", 0)
        if lni > 0:
            pts -= 2
            self.add("moderate", cat, f"confidence<0.7 なのに issue 未記録のマッピングが {lni:.0f} 件ある",
                     "レビュー漏れが起きる", "low_confidence_not_issued.csv", "normalization_issues")
        uni = self.get("unmapped_not_issued", 0)
        if uni > 0:
            pts -= 2
            self.add("moderate", cat, f"未マッピングなのに issue 未記録の項目が {uni:.0f} 件ある",
                     "辞書追加の検討対象から漏れる", "unmapped_not_issued.csv", "normalization_issues")
        mref = self.get("issues_missing_reference", 0)
        if mref > 0:
            pts -= 1
            self.add("minor", cat, f"対象を追えない issue が {mref:.0f} 件ある",
                     "レビューできる粒度になっていない", "issues_missing_reference.csv",
                     "normalization_issues")
        if lni == 0 and uni == 0 and total > 0:
            self.goods.append("低confidence・未マッピング項目が normalization_issues に漏れなく記録されている")
        self.scores[cat] = (int(round(max(pts, 0))), mx, "")

    def score_operability(self):
        cat, mx = "運用しやすさ", 5
        pts = mx
        errors = [x for x in self.meta if x.get("status") == "error"]
        if errors:
            pts -= min(3, len(errors))
            names = ", ".join(x["name"] for x in errors[:5])
            self.add("moderate", cat, f"監査 SQL が {len(errors)} 本エラーになった（{names}）",
                     "スキーマが想定から変わっており追加データに弱い可能性",
                     "raw/_run_meta.json", "監査SQL / スキーマ")
        docs = REPO_ROOT / ".github" / "skills" / "product-spec-normalizer" / "docs"
        if not docs.exists():
            pts -= 1
            self.add("minor", cat, "product-spec-normalizer の運用ドキュメントが見つからない",
                     "再実行手順・レビュー手順が属人化する", str(docs), "docs")
        blocked = [x for x in self.meta if x.get("status") == "blocked_non_readonly"]
        if blocked:
            pts -= 1
            self.add("moderate", cat, f"監査 SQL に非 read-only 文が {len(blocked)} 本混入していた（実行はブロック済み）",
                     "監査専用の原則に反する", "raw/_run_meta.json", "監査SQL")
        if not errors:
            self.goods.append("監査 SQL がスキーマ変更なしで全件実行できた（構造が安定している）")
        self.scores[cat] = (int(round(max(pts, 0))), mx, "")

    def run(self):
        self.score_preservation()
        self.score_table_design()
        self.score_raw()
        self.score_canonical()
        self.score_mapping()
        self.score_normalized()
        self.score_comparison()
        self.score_issues()
        self.score_operability()


# ---------------------------------------------------------------- レポート生成

def judge_total(total: int) -> str:
    if total >= 90:
        return "実務利用可能"
    if total >= 75:
        return "軽微な修正後に利用可能"
    if total >= 60:
        return "レビュー前提で限定利用"
    if total >= 40:
        return "設計または実装の見直しが必要"
    return "作り直し推奨"


def judge_category(score: int, mx: int) -> str:
    r = score / mx if mx else 0
    if r >= 0.9:
        return "良好"
    if r >= 0.7:
        return "概ね良好"
    if r >= 0.5:
        return "要改善"
    return "要見直し"


def md_escape(s) -> str:
    return ("" if s is None else str(s)).replace("|", "\\|").replace("\n", " ")


def findings_table(findings, priority_prefix) -> str:
    if not findings:
        return "該当なし。\n"
    lines = ["| 優先度 | 問題 | 影響 | 根拠 | 対象 |", "|---|---|---|---|---|"]
    for i, f in enumerate(findings, 1):
        lines.append(f"| {priority_prefix}{i} | {md_escape(f.problem)} | {md_escape(f.impact)} "
                     f"| {md_escape(f.evidence)} | {md_escape(f.target)} |")
    return "\n".join(lines) + "\n"


def numeric_checks_table(m: dict) -> str:
    def fmt(v):
        return "N/A（取得不可）" if v is None else f"{v:,.0f}"

    def check(name, value, ok, caution=None):
        if value is None:
            return (name, fmt(value), "評価不能")
        if ok(value):
            return (name, fmt(value), "OK")
        if caution and caution(value):
            return (name, fmt(value), "注意")
        return (name, fmt(value), "NG")

    total_map = m.get("mapping_rows_total") or 0
    unmapped = m.get("mapping_unmapped")
    unmapped_pct = (100.0 * unmapped / total_map) if (unmapped is not None and total_map) else None
    rows = [
        ("product数", fmt(m.get("products_total")), "-"),
        ("raw_specs件数", fmt(m.get("raw_rows_total")), "-"),
        ("canonical_specs件数", fmt(m.get("canonical_items_total")), "-"),
        ("spec_mapping件数", fmt(m.get("mapping_rows_total")), "-"),
        ("normalized_specs件数（present）", fmt(m.get("normalized_present_rows")), "-"),
        ("normalization_issues件数", fmt(m.get("issues_total")), "-"),
        check("未マッピング件数", unmapped, lambda v: total_map and 100.0 * v / total_map <= 5,
              lambda v: total_map and 100.0 * v / total_map <= 15),
        ("未マッピング率(%)", "N/A" if unmapped_pct is None else f"{unmapped_pct:.1f}", "-"),
        check("confidence<0.7 のmapping件数", m.get("mapping_conf_lt_070"),
              lambda v: v == 0, lambda v: v <= 20),
        check("confidence<0.5 のmapping件数", m.get("mapping_conf_lt_050"), lambda v: v == 0),
        check("同一product×canonical の値競合", m.get("duplicate_conflicting_pairs"), lambda v: v == 0),
        check("normalized_unit と canonical_unit の不一致", m.get("unit_mismatch_rows"), lambda v: v == 0),
        check("numeric なのに数値化できていない件数", m.get("numeric_parse_failures"),
              lambda v: v == 0, lambda v: v <= 10),
        check("比較ビューの製品重複", m.get("core_dup_products"), lambda v: v == 0),
        check("欠損率80%以上の比較列数", m.get("core_columns_missing_ge80"),
              lambda v: v == 0, lambda v: v <= 2),
        check("source情報が欠落している raw 行", m.get("raw_missing_source"), lambda v: v == 0),
        check("raw へ遡れない normalized 行", m.get("normalized_not_traceable"), lambda v: v == 0),
        check("manual_required 件数", m.get("mapping_manual_required"),
              lambda v: v == 0, lambda v: True),
        check("重点語群の複数項目統合（混同疑い）", m.get("risky_group_merges"), lambda v: v == 0),
        check("issue未記録の低confidence項目", m.get("low_conf_not_issued"), lambda v: v == 0),
    ]
    lines = ["| チェック項目 | 結果 | 判定 |", "|---|---:|---|"]
    for name, val, judge in rows:
        lines.append(f"| {name} | {val} | {judge} |")
    return "\n".join(lines) + "\n"


def suspicious_table(raw_dir: Path, limit=20) -> str:
    rows = load_raw_csv(raw_dir, "risky_semantic_mappings")
    if rows is None:
        return "（risky_semantic_mappings が取得できなかった。spec_mapping の不足を参照）\n"
    if not rows:
        return "該当なし（重点確認語群に一致する非 exact マッピングは検出されなかった）。\n"
    lines = ["| company | product_name | raw_item_name | canonical_item | confidence | 懸念 |",
             "|---|---|---|---|---:|---|"]
    for r in rows[:limit]:
        lines.append("| " + " | ".join(md_escape(r.get(k, "")) for k in
                     ("company", "product_name", "raw_item_name", "canonical_item",
                      "confidence")) + f" | {md_escape(r.get('concern', ''))} |")
    if len(rows) > limit:
        lines.append(f"\n（全 {len(rows)} 件。全量は suspicious_mappings.csv を参照）")
    return "\n".join(lines) + "\n"


def missing_rate_table(raw_dir: Path, threshold=50.0) -> str:
    rows = load_raw_csv(raw_dir, "comparison_core_missing_rates")
    if rows is None:
        return "（comparison ビューの欠損率が取得できなかった）\n"
    out = []
    for r in rows:
        rate = parse_pct(r.get("null_percentage"))
        if rate >= threshold:
            total = int(float(r.get("total_rows") or 0))
            populated = round(total * (1 - rate / 100.0))
            out.append((r.get("column_name", ""), rate, populated, total))
    if not out:
        return f"欠損率 {threshold:.0f}% 以上の列はない。\n"
    lines = ["| column | missing_rate | populated_count | total_products |",
             "|---|---:|---:|---:|"]
    for col, rate, pop, total in out:
        lines.append(f"| {md_escape(col)} | {rate:.1f}% | {pop} | {total} |")
    return "\n".join(lines) + "\n"


def build_report(scorer: Scorer, m: dict, raw_dir: Path) -> str:
    total = sum(s for s, _, _ in scorer.scores.values())
    verdict = judge_total(total)
    criticals = [f for f in scorer.findings if f.severity == "critical"]
    moderates = [f for f in scorer.findings if f.severity == "moderate"]
    minors = [f for f in scorer.findings if f.severity == "minor"]

    reasons = "; ".join(f.problem for f in criticals[:3]) if criticals else \
        "機械的チェックでは重大な問題は検出されなかった（意味的レビューは第8節・第10節で確認）"

    summary_lines = ["| 評価項目 | 点数 | 判定 | 主な問題 |", "|---|---:|---|---|"]
    for name, mx in CATEGORIES:
        score, _, note = scorer.scores.get(name, (0, mx, "未評価"))
        probs = [f.problem for f in scorer.findings if f.category == name]
        main = note or (probs[0] if probs else "特になし")
        summary_lines.append(f"| {name} | {score}/{mx} | {judge_category(score, mx)} | {md_escape(main)} |")

    goods = "\n".join(f"- {g}" for g in scorer.goods) if scorer.goods else "- （特筆すべき良い点は検出されなかった）"

    review_items = []
    if m.get("risky_group_merges", 0) > 0:
        review_items.append("`suspicious_mappings.csv` の重点語群統合（重量種別・定格/最大など）が本当に同じ意味か")
    if m.get("mapping_conf_lt_070", 0) > 0:
        review_items.append("`low_confidence_mappings.csv` の confidence<0.7 マッピングの妥当性")
    if m.get("mapping_unmapped", 0) > 0:
        review_items.append("`unmapped_raw_items.csv` の未マッピング項目を辞書追加するか比較対象外にするかの判断")
    if m.get("duplicate_conflicting_pairs", 0) > 0:
        review_items.append("`duplicate_canonical_items.csv` の同一製品×項目で値が食い違う組の採用値")
    if m.get("unit_mismatch_rows", 0) > 0:
        review_items.append("`unit_mismatches.csv` の単位不整合行の変換ルール")
    if m.get("issues_open", 0) > 0:
        review_items.append(f"normalization_issues の open {m.get('issues_open'):.0f} 件（audit_outputs/raw/open_issues_list.csv）")
    review_items.append("`comparison_missing_rates.csv` の高欠損列を比較軸として残すかの判断")
    review = "\n".join(f"- {x}" for x in review_items)

    fix_lines = ["> 注意: 修正はこの Skill では行わない。以下は product-spec-normalizer 側で対応する際の提案。", ""]
    seen = set()
    for f in criticals + moderates:
        key = (f.category, f.problem[:30])
        if key in seen:
            continue
        seen.add(key)
        fix_lines.append(f"- **{f.category}**: {f.problem} → 根拠 `{f.evidence}` を確認し、"
                         "normalizer の辞書（spec_synonyms / spec_patterns / unit_conversions）"
                         "または sql/03〜07 の該当ステップを修正して部分再実行する。")
    if len(fix_lines) == 2:
        fix_lines.append("- 機械的チェックで修正が必要な問題は検出されなかった。第10節のレビューを完了させること。")

    report = f"""# 品質監査レポート

- 対象 DB: `db/knowledge.duckdb`（read_only で監査。DB は変更していない）
- 監査 Skill: `product-spec-quality-auditor`
- 注記: 本レポートの点数は機械的指標に基づくベースライン。第8節・第10節の意味的レビューの結果、
  spec_mapping / normalized_specs の点数はさらに下がりうる（上がることはない）。

## 1. 総合評価

- 総合点：{total} / 100
- 判定：{verdict}
- 主な理由：{reasons}

## 2. 評価サマリー

{chr(10).join(summary_lines)}

## 3. 良い点

{goods}

## 4. 重大な問題

{findings_table(criticals, "P")}

## 5. 中程度の問題

{findings_table(moderates, "M")}

## 6. 軽微な問題

{findings_table(minors, "L")}

## 7. 数値チェック結果

{numeric_checks_table(m)}

## 8. 怪しいマッピング例

{suspicious_table(raw_dir)}

## 9. 欠損率が高い比較項目

{missing_rate_table(raw_dir)}

## 10. 今すぐ人間が確認すべき項目

{review}

## 11. 修正方針

{chr(10).join(fix_lines)}

## 12. 判定

総合 {total} 点、「{verdict}」。
重大 {len(criticals)} 件 / 中程度 {len(moderates)} 件 / 軽微 {len(minors)} 件。
第10節のレビューが完了し、重大な問題が解消（または誤検出と確認）されるまで、
比較ビューの数値を対外資料にそのまま使わないこと。
"""
    return report


def main() -> None:
    ap = argparse.ArgumentParser(description="監査結果を点数化しレポートを生成する")
    ap.add_argument("--out-dir", default=str(REPO_ROOT / "audit_outputs"))
    args = ap.parse_args()

    sys.stdout.reconfigure(encoding="utf-8")
    out_dir = Path(args.out_dir)
    raw_dir = out_dir / "raw"
    meta_path = raw_dir / "_run_meta.json"
    if not meta_path.exists():
        print("NG: audit_outputs/raw/_run_meta.json がない。先に run_audit.py を実行すること。")
        sys.exit(1)

    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    metrics = load_metrics(raw_dir)

    scorer = Scorer(metrics, meta, raw_dir)
    scorer.run()

    report = build_report(scorer, metrics, raw_dir)
    report_path = out_dir / "quality_audit_report.md"
    report_path.write_text(report, encoding="utf-8")

    summary_path = out_dir / "audit_summary.csv"
    with summary_path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["category", "score", "max", "judgment", "main_problems"])
        for name, mx in CATEGORIES:
            score, _, note = scorer.scores.get(name, (0, mx, "未評価"))
            probs = "; ".join(f.problem for f in scorer.findings if f.category == name)
            w.writerow([name, score, mx, judge_category(score, mx), note or probs or "特になし"])
        total = sum(s for s, _, _ in scorer.scores.values())
        w.writerow(["TOTAL", total, 100, judge_total(total), ""])

    total = sum(s for s, _, _ in scorer.scores.values())
    print(f"総合点: {total}/100（{judge_total(total)}）")
    print(f"report: {report_path.as_posix()}")
    print(f"summary: {summary_path.as_posix()}")
    print("次: python .github/skills/product-spec-quality-auditor/scripts/export_audit_findings.py")


if __name__ == "__main__":
    main()
