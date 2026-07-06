# -*- coding: utf-8 -*-
"""監査結果の分析（_analysis.json）から remediation_plan.md と修正候補CSV群を作る。

使い方:
    python .github/skills/product-spec-remediation-planner/scripts/build_remediation_plan.py
        [--audit-dir audit_outputs] [--out-dir remediation_outputs]

前提:
    scripts/analyze_audit_outputs.py の実行済み（未実行なら自動で実行する）。

出力（remediation_outputs/ 配下）:
    - remediation_plan.md                 修正計画（14節構成）
    - canonical_split_proposals.csv       canonical_item 分割案（SPL-）
    - mapping_fix_candidates.csv          既存canonicalへのマッピング修正候補
    - new_canonical_candidates.csv        新規canonical候補
    - exclusion_candidates.csv            比較対象外候補（EXC-）
    - unit_rule_candidates.csv            追加してよい単位変換ルール候補
    - conversion_blocklist_candidates.csv 変換禁止にすべき候補
    - duplicate_resolution_plan.csv       重複解消計画（DUP-）
    - manual_review_required.csv          人間レビューが必要な全項目（優先度順）

動作:
    - DB には接続しない。normalizer のファイルにも触れない。
    - すべて候補であり、確定は人間レビュー（mode 2）後に行う。
"""
import argparse
import sys
from pathlib import Path

from analyze_audit_outputs import (
    DEFAULT_AUDIT_DIR, DEFAULT_OUT_DIR, NEW_CANONICAL_RULES,
    ensure_analysis, write_csv, contains,
)

# 再監査の最低目標（remediation_policy.md / SKILL.md と一致させる）
REAUDIT_TARGETS = [
    ("未マッピング率(%)", "unmapped_pct", "10未満"),
    ("単位不一致(行)", "unit_mismatch_rows", "10未満"),
    ("数値化失敗(行)", "numeric_parse_failed_rows", "20未満"),
    ("値競合(組)", "value_conflicts", "0 または全件説明付き"),
    ("spec_mapping品質", "spec_mapping_score", "12/20以上"),
    ("normalized_specs品質", "normalized_specs_score", "9/15以上"),
    ("総合点", "total_score", "75/100以上"),
]

NORMALIZER_FILES = [
    ("sql/04_create_initial_canonical_specs.sql", "canonical_item の追加・分割定義", "P1"),
    ("sql/05_build_spec_mapping.sql / spec_synonyms", "同義語追加・振り替え（spec_mapping_v2 として再構築）", "P1"),
    ("sql/06_build_normalized_specs.sql / unit_conversions", "単位変換ルール追加・変換禁止・重複排除（normalized_specs_v2）", "P2"),
    ("sql/07_create_comparison_views.sql", "比較ビュー _v2 の作成（分割後の列・除外の反映）", "P2"),
    ("sql/03_build_raw_specs.sql", "抽出不備（値/単位分離・ヘッダ分解）の修正", "P2"),
]


def by_type(findings, issue_type, classification=None):
    out = [f for f in findings if f["issue_type"] == issue_type]
    if classification:
        out = [f for f in out if f["classification"] == classification]
    return out


def md_escape(text):
    return str(text or "").replace("|", "／").replace("\n", " ")


def table(header, rows):
    lines = ["| " + " | ".join(header) + " |",
             "|" + "|".join("---" for _ in header) + "|"]
    for r in rows:
        lines.append("| " + " | ".join(md_escape(c) for c in r) + " |")
    if not rows:
        lines.append("| （該当なし） " + "| " * (len(header) - 1) + "|")
    return "\n".join(lines)


def fmt(v, digits=1):
    if v is None:
        return "不明"
    if isinstance(v, float):
        return f"{v:.{digits}f}".rstrip("0").rstrip(".")
    return str(v)


def new_canonical_meta(candidate):
    for pat, canonical, display, category, unit, vtype in NEW_CANONICAL_RULES:
        if canonical == candidate:
            return display, category, unit, vtype
    return "", "", "", ""


def export_candidate_csvs(findings, out_dir: Path):
    spl = by_type(findings, "canonical_split_proposal")
    write_csv(out_dir / "canonical_split_proposals.csv",
              ["review_id", "current_canonical_item", "new_canonical_item", "split_reason",
               "target_raw_items", "affected_count", "confidence", "parent_review_id"],
              [{**f, "split_reason": f["reason"], "target_raw_items": f.get("target_raw_items", "")}
               for f in spl])

    mapping = by_type(findings, "unmapped_raw_item", "map_to_existing")
    write_csv(out_dir / "mapping_fix_candidates.csv",
              ["review_id", "company", "raw_item_name", "proposed_canonical", "reason",
               "affected_count", "confidence"], mapping)

    newc = by_type(findings, "unmapped_raw_item", "create_new_canonical")
    rows = []
    for f in newc:
        display, category, unit, vtype = new_canonical_meta(f.get("proposed_canonical", ""))
        rows.append({**f, "display_name_ja": display, "category": category,
                     "canonical_unit": unit, "value_type": vtype})
    write_csv(out_dir / "new_canonical_candidates.csv",
              ["review_id", "raw_item_name", "proposed_canonical", "display_name_ja",
               "category", "canonical_unit", "value_type", "reason",
               "affected_count", "confidence"], rows)

    exc = by_type(findings, "exclusion_candidate")
    write_csv(out_dir / "exclusion_candidates.csv",
              ["review_id", "raw_item_name", "reason", "affected_count", "confidence",
               "parent_review_id"], exc)

    unit_rules = by_type(findings, "unit_mismatch", "missing_conversion_rule")
    write_csv(out_dir / "unit_rule_candidates.csv",
              ["review_id", "canonical_item", "original_unit", "target_unit",
               "conversion_rule", "affected_count", "confidence", "ai_uncertainty"],
              unit_rules)

    block = [f for f in by_type(findings, "unit_mismatch")
             if f["classification"] in ("not_convertible", "value_contains_condition")]
    write_csv(out_dir / "conversion_blocklist_candidates.csv",
              ["review_id", "canonical_item", "original_unit", "target_unit",
               "classification", "reason", "affected_count", "confidence"], block)

    dup = by_type(findings, "duplicate_canonical_item")
    write_csv(out_dir / "duplicate_resolution_plan.csv",
              ["review_id", "canonical_item", "classification", "ai_recommendation",
               "sample_values", "source_examples", "affected_count", "confidence"], dup)

    manual = sorted([f for f in findings if f["needs_human"]],
                    key=lambda f: (f["priority"], -f["affected_count"]))
    write_csv(out_dir / "manual_review_required.csv",
              ["review_id", "priority", "issue_type", "classification", "question",
               "ai_recommendation", "ai_uncertainty", "sample_values", "source_examples",
               "affected_count", "confidence"], manual)
    return {"splits": spl, "mapping": mapping, "new_canonical": rows, "exclusions": exc,
            "unit_rules": unit_rules, "blocklist": block, "duplicates": dup, "manual": manual}


def build_plan_md(analysis, groups, out_dir: Path):
    findings = analysis["findings"]
    m = analysis["current_metrics"]
    manual = groups["manual"]
    n_p1 = sum(1 for f in findings if f["priority"] == "P1")
    total = m.get("total_score")

    # 最終判定（14節）: P1の量と総合点から機械的に決め、根拠を添える
    if total is not None and total < 40:
        verdict = "normalizerを部分的に作り直すべき"
    elif len(groups["splits"]) >= 5 or (total is not None and total < 50):
        verdict = "人間レビュー後にnormalizer修正を実行すべき（canonical分割が多い場合はcanonical設計の見直しも並行検討）"
    elif n_p1 > 0:
        verdict = "人間レビュー後にnormalizer修正を実行すべき"
    else:
        verdict = "この計画でnormalizer修正を実行してよい"

    lines = []
    a = lines.append
    a("# product-spec-normalizer 修正計画")
    a("")
    a(f"生成: {analysis['generated_at']} / 入力: {analysis['audit_dir']} "
      f"(risky情報源: {analysis['risky_source']})")
    a("")
    if analysis.get("canonical_names_available"):
        a(f"canonical候補名は raw/canonical_definitions.csv の実名 "
          f"{analysis.get('n_canonical_names', 0)} 項目と突き合わせて検証済み。")
    else:
        a("**注意**: raw/canonical_definitions.csv が無いため canonical 候補名は未検証。"
          "実名との突き合わせを人間レビューで必ず行うこと。")
    if analysis["missing_inputs"]:
        a("")
        a("**不足していた入力**（処理は続行、該当分析はスキップまたは代替）: "
          + ", ".join(analysis["missing_inputs"]))
    a("")
    a("## 1. 総合判断")
    a("")
    a(f"- 修正方針：P1（意味混同・値競合）を人間レビューで確定してから、"
      f"v2テーブル・ビューとして修正を反映する（既存テーブルは直接変更しない）")
    a(f"- 修正実行可否：{'人間レビュー完了までP1関連の修正は実行不可' if n_p1 else '軽微修正は実行可'}")
    a(f"- 人間レビュー要否：必要（{len(manual)}件、うちP1 {n_p1}件）")
    a(f"- 主なリスク：意味の異なる項目の同一canonical統合（{len(by_type(findings,'risky_group_merge'))}群）、"
      f"値競合（{fmt(m.get('value_conflicts'))}組）、未マッピング率 {fmt(m.get('unmapped_pct'))}%")
    a("")
    a("## 2. 優先順位")
    a("")
    prio_rows = []
    for s in analysis["summary"]:
        if s["priority"] > "P3":
            continue
        prio_rows.append([s["priority"], s["issue_type"], s["classification"],
                          "分割/振り替え/ルール追加の候補提示→人間承認後にv2で反映",
                          f"影響 {s['affected_rows']} 行"])
    a(table(["優先度", "対象", "問題", "修正方針", "期待効果"], prio_rows[:20]))
    a("")
    a("## 3. risky_group_merges 対応案")
    a("")
    a("監査側の定義（同一 canonical_item に複数の異なる raw_item_name が寄っている群のみ）に"
      "合わせて集約している。")
    if analysis.get("rgm_single_raw_skipped"):
        a(f"raw_item_name が1種類だけの群 {analysis['rgm_single_raw_skipped']} 組は"
          "「統合」に当たらないため対象外とした。")
    a("")
    a(table(["group", "現在のcanonical_item", "問題", "分割案", "人間確認要否"],
            [[f.get("rule_name", ""), f.get("canonical_item", ""), f["question"],
              f["ai_recommendation"], "必須（P1）"]
             for f in by_type(findings, "risky_group_merge")]))
    a("")
    a("## 4. unmapped_raw_items 分類")
    a("")
    a(table(["raw_item_name", "件数", "推奨対応", "canonical_item候補", "理由", "confidence"],
            [[f.get("raw_item_name", ""), f["affected_count"], f["classification"],
              f.get("proposed_canonical", ""), f["reason"], f["confidence"]]
             for f in by_type(findings, "unmapped_raw_item")]))
    a("")
    a("## 5. unit_mismatches 分類")
    a("")
    a(table(["canonical_item", "original_unit", "normalized_unit", "件数", "原因", "修正案"],
            [[f.get("canonical_item", ""), f.get("original_unit", ""),
              f.get("target_unit", ""), f["affected_count"], f["classification"],
              f["ai_recommendation"]] for f in by_type(findings, "unit_mismatch")]))
    a("")
    a("## 6. duplicate_canonical_items 対応案")
    a("")
    a(table(["product_id", "canonical_item", "値の違い", "原因候補", "修正案"],
            [[f.get("source_examples", ""), f.get("canonical_item", ""),
              f.get("sample_values", ""), f["classification"], f["ai_recommendation"]]
             for f in by_type(findings, "duplicate_canonical_item")]))
    a("")
    a("## 7. canonical_item 分割案")
    a("")
    a(table(["current_canonical_item", "new_canonical_item", "分割理由",
             "対象raw_item_name", "confidence"],
            [[f.get("current_canonical_item", ""), f.get("new_canonical_item", ""),
              f["reason"], f.get("target_raw_items", ""), f["confidence"]]
             for f in groups["splits"]]))
    a("")
    a("## 8. 新規canonical_item候補")
    a("")
    a(table(["canonical_item候補", "display_name_ja", "category", "canonical_unit",
             "value_type", "理由"],
            [[f.get("proposed_canonical", ""), f.get("display_name_ja", ""),
              f.get("category", ""), f.get("canonical_unit", ""),
              f.get("value_type", ""), f["reason"]] for f in groups["new_canonical"]]))
    a("")
    a("## 9. 比較対象外候補")
    a("")
    a(table(["raw_item_name", "件数", "除外理由", "再確認要否"],
            [[f.get("raw_item_name", ""), f["affected_count"], f["reason"],
              "要" if f["confidence"] < 0.8 else "軽"] for f in groups["exclusions"]]))
    a("")
    a("## 10. normalizer修正対象")
    a("")
    a(table(["ファイル", "修正内容", "優先度"], [list(r) for r in NORMALIZER_FILES]))
    a("")
    a("## 11. DB変更方針")
    a("")
    a("既存テーブルは直接変更しない。承認済み修正は以下の v2 オブジェクトとして新設し、")
    a("再監査で品質確認後に参照先を切り替える。")
    a("")
    a("- `spec_mapping_v2`（同義語追加・振り替え・除外印を反映）")
    a("- `normalized_specs_v2`（変換ルール追加・変換禁止・重複排除を反映）")
    a("- `product_comparison_core_view_v2` / `product_comparison_full_view_v2`")
    a("")
    a("## 12. 再監査目標")
    a("")
    a(table(["指標", "現在値", "目標値"],
            [[label, fmt(m.get(key)), target] for label, key, target in REAUDIT_TARGETS]))
    a("")
    a("最低目標: 未マッピング率10%未満 / 単位不一致10行未満 / 数値化失敗20行未満 / "
      "値競合0件または全件説明付き / spec_mapping 12/20以上 / normalized_specs 9/15以上 / "
      "総合点75/100以上")
    a("")
    a("## 13. 人間レビューが必要な項目")
    a("")
    a(table(["優先度", "review_id", "問題", "AI推奨", "影響件数"],
            [[f["priority"], f["review_id"], f["question"], f["ai_recommendation"],
              f["affected_count"]] for f in manual[:40]]))
    if len(manual) > 40:
        a("")
        a(f"（先頭40件のみ表示。全{len(manual)}件は manual_review_required.csv と "
          f"human_review_workbook.xlsx を参照）")
    a("")
    a("## 14. 次に実行すべきこと")
    a("")
    a(f"**判定: {verdict}**")
    a("")
    a("1. `export_review_workbook.py` で人間レビュー用Excelを生成（未生成の場合）")
    a("2. `human_review_workbook.xlsx` の human_decision を記入（P1優先）")
    a("3. `import_review_decisions.py` → `build_normalizer_change_plan.py` で修正計画を確定")
    a("4. `product-spec-normalizer` 側で v2 オブジェクトとして修正を実施")
    a("5. `product-spec-quality-auditor` で再監査し、第12節の目標を確認")
    a("")
    (out_dir / "remediation_plan.md").write_text("\n".join(lines), encoding="utf-8")
    return verdict


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--audit-dir", type=Path, default=DEFAULT_AUDIT_DIR)
    ap.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = ap.parse_args(argv)
    analysis = ensure_analysis(args.audit_dir, args.out_dir)
    groups = export_candidate_csvs(analysis["findings"], args.out_dir)
    verdict = build_plan_md(analysis, groups, args.out_dir)
    print(f"written: {args.out_dir / 'remediation_plan.md'}")
    print(f"判定: {verdict}")
    print(f"人間レビュー必要: {len(groups['manual'])}件 / 分割案: {len(groups['splits'])}件 / "
          f"変換ルール候補: {len(groups['unit_rules'])}件 / blocklist候補: {len(groups['blocklist'])}件")
    return 0


if __name__ == "__main__":
    sys.exit(main())
