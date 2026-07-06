# -*- coding: utf-8 -*-
"""レビュー用ファイル（マッピング・品質チェック・比較表）を CSV に書き出す。

使い方:
    python .github/skills/product-spec-normalizer/scripts/export_review_files.py
    python .github/skills/product-spec-normalizer/scripts/export_review_files.py --out-dir db/review

動作:
    - sql/08_quality_checks.sql を「-- CHECK: <名前>」で分割し、各クエリを <名前>.csv に出力する。
    - 併せて spec_mapping 全量 / normalization_issues / 比較ビュー2種も CSV 化する。
    - CSV は Excel でそのまま開けるよう UTF-8 BOM 付きで書き出す。
    - DB へは read_only で接続する（書き込みしない）。
"""
import argparse
import csv
import re
import sys
from pathlib import Path

import duckdb

REPO_ROOT = Path(__file__).resolve().parents[4]
QC_SQL = Path(__file__).resolve().parents[1] / "sql" / "08_quality_checks.sql"

EXTRA_QUERIES = {
    "spec_mapping_all": "SELECT * FROM spec_mapping ORDER BY company, source_table, raw_item_name",
    "normalization_issues_open": "SELECT * FROM normalization_issues WHERE status='open' ORDER BY issue_type, company",
    "product_comparison_core": "SELECT * FROM product_comparison_core_view ORDER BY company, product_name",
    "product_comparison_full": "SELECT * FROM product_comparison_full_view ORDER BY company, product_name",
    "best_normalized_specs": "SELECT * FROM best_normalized_specs ORDER BY product_id, canonical_item",
}


def split_checks(sql_text: str) -> dict[str, str]:
    """'-- CHECK: name' 区切りで {name: query} を返す。"""
    checks: dict[str, str] = {}
    current, buf = None, []
    for line in sql_text.splitlines():
        m = re.match(r"^--\s*CHECK:\s*(\w+)", line)
        if m:
            if current and "".join(buf).strip():
                checks[current] = "\n".join(buf)
            current, buf = m.group(1), []
        elif current is not None:
            buf.append(line)
    if current and "".join(buf).strip():
        checks[current] = "\n".join(buf)
    return checks


def export(con, name: str, query: str, out_dir: Path) -> None:
    try:
        cur = con.execute(query)
    except duckdb.Error as e:
        print(f"  SKIP {name}: {e}")
        return
    cols = [d[0] for d in cur.description]
    rows = cur.fetchall()
    path = out_dir / f"{name}.csv"
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(cols)
        w.writerows(rows)
    print(f"  {path.as_posix()} ({len(rows)} rows)")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--db", default=str(REPO_ROOT / "db" / "knowledge.duckdb"))
    ap.add_argument("--out-dir", default=str(REPO_ROOT / "db" / "review"))
    args = ap.parse_args()

    sys.stdout.reconfigure(encoding="utf-8")
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect(args.db, read_only=True)
    try:
        print("quality checks:")
        for name, query in split_checks(QC_SQL.read_text(encoding="utf-8")).items():
            export(con, name, query, out_dir)
        print("extras:")
        for name, query in EXTRA_QUERIES.items():
            export(con, name, query, out_dir)
    finally:
        con.close()
    print(f"done. review files in {out_dir.as_posix()}")


if __name__ == "__main__":
    main()
