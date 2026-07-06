# -*- coding: utf-8 -*-
"""承認済みの人間判断から normalizer_change_plan.md と reaudit_targets.csv を作る。

使い方:
    python .github/skills/product-spec-remediation-planner/scripts/build_normalizer_change_plan.py
        [--out-dir remediation_outputs]

前提:
    scripts/import_review_decisions.py の実行済み（_decisions.json があること）。

出力（remediation_outputs/ 配下）:
    - normalizer_change_plan.md  product-spec-normalizer に渡す修正実行計画（12節構成）
    - reaudit_targets.csv        再監査目標（指標の現在値と目標値、再確認すべき項目）

動作:
    - DB には接続しない。normalizer のファイルにも触れない。
    - 承認済み（approved）の判断だけを「実行してよい修正」に載せ、
      reject / 保留 / 不整合は「実行してはいけない修正」として明示する。
    - 既存テーブルの直接変更は指示せず、v2 テーブル・ビューの新設として書く。
"""
import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

from analyze_audit_outputs import DEFAULT_OUT_DIR, load_analysis, write_csv
from build_remediation_plan import REAUDIT_TARGETS, fmt, md_escape, table

# human_decision → (修正種別, 対象normalizerファイル, 優先度)
DECISION_TO_CHANGE = {
    "split_canonical": ("canonical分割", "sql/04_create_initial_canonical_specs.sql + sql/05（spec_mapping_v2）", "P1"),
    "create_new_canonical": ("canonical追加", "sql/04_create_initial_canonical_specs.sql", "P2"),
    "map_to_existing": ("mapping修正（synonym追加）", "sql/05_build_spec_mapping.sql / spec_synonyms", "P2"),
    "approve": ("AI推奨の適用（重複排除・確定等）", "sql/06_build_normalized_specs.sql（normalized_specs_v2）", "P2"),
    "exclude_from_comparison": ("比較対象外化", "sql/05（対象外印）+ sql/07（ビューから除外）", "P3"),
    "add_conversion_rule": ("単位変換ルール追加", "unit_conversions / sql/06_build_normalized_specs.sql", "P2"),
    "change_canonical_unit": ("canonical_unit変更", "sql/04 + sql/06（v2で再正規化）", "P2"),
    "fix_raw_unit_extraction": ("抽出ロジック修正", "sql/03_build_raw_specs.sql", "P2"),
    "do_not_convert": ("変換禁止（blocklist）", "sql/06（変換スキップ+テキスト保持を明示）", "P3"),
}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = ap.parse_args(argv)
    out_dir = args.out_dir

    dpath = out_dir / "_decisions.json"
    if not dpath.exists():
        print("エラー: _decisions.json が無い。先に import_review_decisions.py を実行する。",
              file=sys.stderr)
        return 1
    with dpath.open(encoding="utf-8") as f:
        d = json.load(f)
    analysis = load_analysis(out_dir) or {}
    metrics = analysis.get("current_metrics", {})
    counts = d["counts"]
    approved = d["approved"]
    remaining = d["remaining"]

    lines = []
    a = lines.append
    a("# product-spec-normalizer 修正実行計画")
    a("")
    a(f"生成: {d['generated_at']} / 入力: {d['source']}")
    a("")
    a("## 1. 人間レビュー反映結果")
    a("")
    reviewed = sum(counts.get(k, 0) for k in
                   ("approved", "rejected", "needs_source_check", "not_applied",
                    "inconsistent_decision", "missing_required_field"))
    a(f"- レビュー済み件数：{reviewed}")
    a(f"- 修正対象件数：{counts.get('approved', 0)}")
    a(f"- 保留件数：{counts.get('deferred', 0) + counts.get('pending', 0) + counts.get('not_applied', 0)}")
    a(f"- 差し戻し件数：{counts.get('needs_source_check', 0)}（needs_source_check）"
      f" + reject {counts.get('rejected', 0)}")
    a(f"- 不整合件数：{counts.get('inconsistent_decision', 0)}"
      f"（ほか必須欠落 {counts.get('missing_required_field', 0)}、"
      f"不備行は reviewed_decision_errors.csv 参照）")
    a("")
    a("## 2. 実行してよい修正")
    a("")
    a("人間が status=reviewed / apply_flag=true で承認した修正のみ。根拠 review_id 必須。")
    a("")
    rows = []
    for r in sorted(approved, key=lambda r: (
            DECISION_TO_CHANGE.get(r["human_decision"], ("", "", "P9"))[2], r["review_id"])):
        kind, _file, prio = DECISION_TO_CHANGE.get(r["human_decision"], ("その他", "", "P3"))
        target = (r.get("final_canonical_item") or r.get("canonical_item")
                  or r.get("raw_item_name") or "")
        content = r.get("reviewer_note") or r.get("ai_recommendation") or r["human_decision"]
        rows.append([prio, kind, target, content, r["review_id"]])
    a(table(["優先度", "修正種別", "対象", "内容", "根拠review_id"], rows))
    a("")
    a("## 3. 実行してはいけない修正")
    a("")
    reasons = defaultdict(list)
    for r in remaining:
        cls = r.get("classification", "")
        label = {"rejected": "人間が reject（修正しない）",
                 "needs_source_check": "元資料の確認待ち（差し戻し）",
                 "deferred": "人間が保留（deferred / keep_manual_review）",
                 "pending": "未レビュー（判断が入っていない）",
                 "not_applied": "apply_flag=false（反映不可の明示）",
                 "inconsistent_decision": "シート間で判断が矛盾",
                 "missing_required_field": "必須項目（canonical/unit）欠落"}.get(cls, cls)
        reasons[label].append(r["review_id"])
    a(table(["理由", "件数", "対応"],
            [[label, len(ids),
              "manual_review_remaining.csv 参照。normalizer 修正には含めない"
              + ("。再レビュー後に mode 2 を再実行" if "未レビュー" in label or "保留" in label
                 else "")]
             for label, ids in sorted(reasons.items(), key=lambda kv: -len(kv[1]))]))
    a("")
    a("**この表の項目は、いかなる理由でも今回の normalizer 修正に含めない。**"
      "人間判断とAI推奨が矛盾する場合も人間判断を優先する。")
    a("")
    a("## 4. canonical_item追加・分割")
    a("")
    rows = []
    for r in approved:
        if r["human_decision"] == "split_canonical":
            rows.append(["分割", r.get("current_canonical_item") or r.get("canonical_item"),
                         r["final_canonical_item"],
                         r.get("reviewer_note") or "意味の異なる項目の分離", r["review_id"]])
        elif r["human_decision"] == "create_new_canonical":
            rows.append(["追加", "", r["final_canonical_item"],
                         r.get("reviewer_note") or f"未マッピング項目 {r.get('raw_item_name','')} の受け皿",
                         r["review_id"]])
    a(table(["種別", "current_canonical_item", "new_canonical_item", "理由", "review_id"], rows))
    a("")
    a("## 5. mapping修正")
    a("")
    rows = []
    for r in approved:
        if r["human_decision"] == "map_to_existing":
            rows.append([r.get("raw_item_name", ""), r.get("canonical_item") or "(未マッピング)",
                         r["final_canonical_item"], "synonym追加で v2 に反映", r["review_id"]])
        elif r["human_decision"] == "split_canonical" and r.get("target_raw_items"):
            rows.append([r.get("target_raw_items", ""),
                         r.get("current_canonical_item") or r.get("canonical_item"),
                         r["final_canonical_item"], "分割先へ振り替え", r["review_id"]])
    a(table(["raw_item_name", "current_canonical_item", "new_canonical_item", "対応", "review_id"],
            rows))
    a("")
    a("## 6. 単位変換ルール")
    a("")
    a(table(["canonical_item", "original_unit", "target_unit", "conversion_rule", "review_id"],
            [[r.get("canonical_item", ""), r.get("original_unit", ""),
              r.get("final_unit") or r.get("target_unit", ""),
              r.get("conversion_rule") or "（人間指定: reviewer_note 参照）", r["review_id"]]
             for r in approved
             if r["human_decision"] in ("add_conversion_rule", "change_canonical_unit")]))
    a("")
    a("## 7. 変換禁止・比較対象外")
    a("")
    rows = [[f"{r.get('canonical_item','')} ({r.get('original_unit','')}→{r.get('target_unit','')})",
             r.get("reviewer_note") or "一意換算不能のため変換禁止（テキスト保持）", r["review_id"]]
            for r in approved if r["human_decision"] == "do_not_convert"]
    rows += [[r.get("raw_item_name", ""),
              r.get("reviewer_note") or "比較対象外（raw_specs には残す）", r["review_id"]]
             for r in approved if r["human_decision"] == "exclude_from_comparison"]
    a(table(["対象", "理由", "review_id"], rows))
    a("")
    a("## 8. normalizer修正対象ファイル")
    a("")
    used = {}
    for r in approved:
        kind, file, prio = DECISION_TO_CHANGE.get(r["human_decision"], (None, None, None))
        if file:
            used.setdefault(file, [set(), prio])[0].add(kind)
            used[file][1] = min(used[file][1], prio)
    a(table(["ファイル", "修正内容", "優先度"],
            [[file, " / ".join(sorted(kinds)), prio]
             for file, (kinds, prio) in sorted(used.items(), key=lambda kv: kv[1][1])]))
    a("")
    a("## 9. v2テーブル・ビュー作成方針")
    a("")
    a("既存テーブル（spec_mapping / normalized_specs / 比較ビュー）は直接変更しない。")
    a("")
    a("1. `canonical_specs` への項目追加・分割定義（第4節）を反映した定義を用意する")
    a("2. `spec_mapping_v2` を新規作成：synonym追加・振り替え（第5節）・除外印（第7節）を反映")
    a("3. `normalized_specs_v2` を新規作成：変換ルール追加（第6節）・変換禁止（第7節）・"
      "重複排除（第2節の deduplicate）を反映")
    a("4. `product_comparison_core_view_v2` / `product_comparison_full_view_v2` を作成")
    a("5. v1 と v2 の差分（行数・値の変化）を確認し、意図した変更のみであることを検証する")
    a("6. 再監査（第10節）合格後に、参照側を v2 へ切り替える（v1 は監査証跡として残す）")
    a("")
    a("## 10. 再監査手順")
    a("")
    a("```powershell")
    a("# v2 オブジェクト作成後、監査を再実行（read_only）")
    a("python .github/skills/product-spec-quality-auditor/scripts/run_audit.py")
    a("python .github/skills/product-spec-quality-auditor/scripts/generate_audit_report.py")
    a("python .github/skills/product-spec-quality-auditor/scripts/export_audit_findings.py")
    a("```")
    a("")
    a("再監査は v2 オブジェクトを対象に行い、reaudit_targets.csv の項目を重点確認する。")
    a("")
    a("## 11. 再監査目標")
    a("")
    target_rows = [[label, fmt(metrics.get(key)), target]
                   for label, key, target in REAUDIT_TARGETS]
    a(table(["指標", "現在値", "目標値"], target_rows))
    a("")
    a("## 12. 残課題")
    a("")
    a(f"- 修正対象外 {len(remaining)} 件（manual_review_remaining.csv）。"
      "内訳は第3節のとおり。needs_source_check は元Excel確認後に再レビューする")
    a(f"- 不備行 {d['n_errors']} 件（reviewed_decision_errors.csv）。記入を修正して "
      "import_review_decisions.py を再実行する")
    a("- v2 切り替え後、v1 参照が残っていないかの確認（normalizer 側の作業）")
    a("")

    (out_dir / "normalizer_change_plan.md").write_text("\n".join(lines), encoding="utf-8")

    # 再監査目標CSV: 指標行 + 修正対象になった canonical_item の重点確認行
    reaudit_rows = [{"target_type": "metric", "target": label,
                     "current_value": fmt(metrics.get(key)), "goal": target, "review_id": ""}
                    for label, key, target in REAUDIT_TARGETS]
    seen = set()
    for r in approved:
        item = r.get("final_canonical_item") or r.get("canonical_item")
        if item and item not in seen:
            seen.add(item)
            reaudit_rows.append({
                "target_type": "canonical_item", "target": item,
                "current_value": "", "goal": "修正が意図どおり反映され、値競合・単位不一致が解消していること",
                "review_id": r["review_id"]})
    write_csv(out_dir / "reaudit_targets.csv",
              ["target_type", "target", "current_value", "goal", "review_id"], reaudit_rows)

    print(f"written: {out_dir / 'normalizer_change_plan.md'}")
    print(f"written: {out_dir / 'reaudit_targets.csv'} ({len(reaudit_rows)}行)")
    print(f"実行してよい修正: {len(approved)}件 / 実行してはいけない・保留: {len(remaining)}件")
    return 0


if __name__ == "__main__":
    sys.exit(main())
