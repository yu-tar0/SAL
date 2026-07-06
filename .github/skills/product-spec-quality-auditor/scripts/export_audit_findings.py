# -*- coding: utf-8 -*-
"""人間レビュー用の指摘 CSV を audit_outputs/ 直下に書き出す。

使い方:
    python .github/skills/product-spec-quality-auditor/scripts/export_audit_findings.py

前提:
    先に scripts/run_audit.py を実行し、audit_outputs/raw/ に CSV があること。

出力（audit_outputs/ 直下）:
    - suspicious_mappings.csv        怪しいマッピング（重点語群の混同疑い候補）
    - low_confidence_mappings.csv    confidence<0.7 のマッピング
    - unmapped_raw_items.csv         未マッピングの raw 項目
    - duplicate_canonical_items.csv  同一製品×canonical_item の重複
    - unit_mismatches.csv            normalized_unit と canonical_unit の不一致
    - comparison_missing_rates.csv   比較ビューの列別欠損率（core + full）
    - company_coverage.csv           会社別カバレッジ
    - human_review_required.csv      上記を横断した「人間レビューが必要な項目」の統合リスト

動作:
    - DB には接続しない。audit_outputs/raw/ の CSV を読むだけ。
    - ファイルの追加以外の変更はしない。
"""
import argparse
import csv
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]

# raw/ のクエリ結果 → 最終成果物へのコピー対応
DIRECT_EXPORTS = {
    "risky_semantic_mappings": "suspicious_mappings.csv",
    "low_confidence_mappings": "low_confidence_mappings.csv",
    "unmapped_raw_items": "unmapped_raw_items.csv",
    "duplicate_canonical_items": "duplicate_canonical_items.csv",
    "unit_mismatches": "unit_mismatches.csv",
    "company_summary": "company_coverage.csv",
}

REVIEW_COLUMNS = ["reason", "company", "product", "item", "canonical_item", "confidence", "detail"]

# human_review_required.csv に取り込む raw CSV と列の対応
REVIEW_SOURCES = [
    ("risky_semantic_mappings", "怪しいマッピング（意味混同の疑い）",
     {"company": "company", "product": "product_name", "item": "raw_item_name",
      "canonical_item": "canonical_item", "confidence": "confidence", "detail": "concern"}),
    ("low_confidence_mappings", "低confidenceマッピング（<0.7）",
     {"company": "company", "product": "product_id", "item": "raw_item_name",
      "canonical_item": "canonical_item", "confidence": "confidence", "detail": "notes"}),
    ("unmapped_raw_items", "未マッピング項目（辞書追加か対象外かの判断）",
     {"company": "company", "item": "raw_item_name", "detail": "notes_example"}),
    ("duplicate_canonical_items", "同一製品×項目の重複（採用値の確認）",
     {"company": "company", "product": "product_id", "canonical_item": "canonical_item",
      "detail": "values_seen"}),
    ("unit_mismatches", "単位不整合（変換ルールの確認）",
     {"company": "company", "product": "product_id", "canonical_item": "canonical_item",
      "confidence": "confidence", "detail": "original_value"}),
    ("open_issues_list", "normalization_issues の open 項目",
     {"company": "company", "product": "product_id", "item": "raw_item_name",
      "detail": "detail"}),
    ("raw_item_multi_canonical_same_company", "同一raw項目の複数canonical割当（混同の疑い）",
     {"company": "company", "item": "raw_item_name", "canonical_item": "canonical_items"}),
]


def read_raw(raw_dir: Path, name: str):
    path = raw_dir / f"{name}.csv"
    if not path.exists():
        return None, None
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        rows = list(reader)
    if not rows:
        return [], []
    return rows[0], rows[1:]


def write_csv(path: Path, header, rows):
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print(f"  {path.as_posix()} ({len(rows)} rows)")


def parse_pct(value) -> float:
    try:
        return float(str(value).replace("%", "").strip())
    except (TypeError, ValueError):
        return 0.0


def export_missing_rates(raw_dir: Path, out_dir: Path) -> None:
    """core / full ビューの欠損率を view 列付きで1本に統合する。"""
    out_rows = []
    for view, name in [("product_comparison_core_view", "comparison_core_missing_rates"),
                       ("product_comparison_full_view", "comparison_full_missing_rates")]:
        header, rows = read_raw(raw_dir, name)
        if header is None:
            continue
        idx = {c: i for i, c in enumerate(header)}
        for r in rows:
            rate = parse_pct(r[idx["null_percentage"]]) if "null_percentage" in idx else 0.0
            total = int(float(r[idx["total_rows"]] or 0)) if "total_rows" in idx else 0
            populated = round(total * (1 - rate / 100.0))
            out_rows.append([view, r[idx.get("column_name", 0)],
                             r[idx["column_type"]] if "column_type" in idx else "",
                             f"{rate:.1f}", populated, total])
    out_rows.sort(key=lambda x: -float(x[3]))
    write_csv(out_dir / "comparison_missing_rates.csv",
              ["view", "column", "column_type", "missing_rate_pct", "populated_count", "total_products"],
              out_rows)


def export_human_review(raw_dir: Path, out_dir: Path) -> None:
    out_rows = []
    for name, reason, colmap in REVIEW_SOURCES:
        header, rows = read_raw(raw_dir, name)
        if header is None:
            continue
        idx = {c: i for i, c in enumerate(header)}
        for r in rows:
            def pick(target):
                src = colmap.get(target)
                if src is None or src not in idx:
                    return ""
                return r[idx[src]]
            out_rows.append([reason, pick("company"), pick("product"), pick("item"),
                             pick("canonical_item"), pick("confidence"), pick("detail")])
    write_csv(out_dir / "human_review_required.csv", REVIEW_COLUMNS, out_rows)


def main() -> None:
    ap = argparse.ArgumentParser(description="人間レビュー用の指摘 CSV を出力する")
    ap.add_argument("--out-dir", default=str(REPO_ROOT / "audit_outputs"))
    args = ap.parse_args()

    sys.stdout.reconfigure(encoding="utf-8")
    out_dir = Path(args.out_dir)
    raw_dir = out_dir / "raw"
    if not raw_dir.exists():
        print("NG: audit_outputs/raw/ がない。先に run_audit.py を実行すること。")
        sys.exit(1)

    print("findings:")
    for src, dst in DIRECT_EXPORTS.items():
        header, rows = read_raw(raw_dir, src)
        if header is None:
            print(f"  SKIP {dst}: 元となる {src}.csv がない（対象オブジェクト不足の可能性）")
            continue
        write_csv(out_dir / dst, header, rows)

    export_missing_rates(raw_dir, out_dir)
    export_human_review(raw_dir, out_dir)
    print(f"done. findings in {out_dir.as_posix()}")


if __name__ == "__main__":
    main()
