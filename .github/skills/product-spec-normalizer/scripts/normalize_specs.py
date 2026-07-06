# -*- coding: utf-8 -*-
"""product-spec-normalizer のパイプラインを実行する（DuckDB は Python 経由のみ）。

使い方:
    python .github/skills/product-spec-normalizer/scripts/normalize_specs.py            # 02-07 を実行
    python .github/skills/product-spec-normalizer/scripts/normalize_specs.py --steps 05 06 07
    python .github/skills/product-spec-normalizer/scripts/normalize_specs.py --drop     # 標準化オブジェクトを全削除して終了

動作:
    - sql/02〜07 を番号順に実行する（01 は read_only 調査用、08 は export_review_files.py が使う）。
    - 既存の raw テーブルには一切触れない。作成・削除するのは STANDARD_OBJECTS のみ。
    - 実行後、db/schema.sql を DB の実テーブルから再生成して同期する
      （db/scripts/load_excel_raw_to_duckdb.py と同じ方式）。
    - 実行サマリー（各テーブルの行数）を表示する。
"""
import argparse
import datetime as dt
import sys
from pathlib import Path

import duckdb

REPO_ROOT = Path(__file__).resolve().parents[4]
SQL_DIR = Path(__file__).resolve().parents[1] / "sql"
DEFAULT_STEPS = ["02", "03", "04", "05", "06", "07"]

# このスキルが所有する標準化オブジェクト。--drop はこれ以外に触れない。
STANDARD_TABLES = [
    "normalized_specs", "spec_mapping", "raw_specs", "products",
    "canonical_specs", "spec_synonyms", "spec_patterns", "unit_conversions",
    "normalization_issues",
]
STANDARD_VIEWS = [
    "product_comparison_view", "product_comparison_core_view",
    "product_comparison_full_view", "best_normalized_specs",
]
STANDARD_SEQUENCES = ["raw_spec_seq", "normalized_spec_seq", "normalization_issue_seq"]
STANDARD_MACROS = ["psn_product_id", "psn_item_key", "psn_unit_key"]


def dump_schema(con, schema_path: Path) -> None:
    """db/schema.sql を DB の実テーブル・ビューから再生成する（既存ローダーと同じ形式）。"""
    rows = con.execute(
        "SELECT sql FROM duckdb_tables() WHERE NOT internal ORDER BY table_name").fetchall()
    views = con.execute(
        "SELECT sql FROM duckdb_views() WHERE NOT internal ORDER BY view_name").fetchall()
    lines = [
        "-- db/schema.sql",
        "-- db/scripts/load_excel_raw_to_duckdb.py が knowledge.duckdb の実テーブルから自動生成。",
        f"-- 最終更新: {dt.date.today().isoformat()}",
        "",
    ]
    for (sql,) in rows + views:
        lines.append(sql.rstrip().rstrip(";") + ";")
        lines.append("")
    schema_path.write_text("\n".join(lines), encoding="utf-8")


def run_sql_file(con, path: Path) -> None:
    print(f"-- {path.name}")
    con.execute(path.read_text(encoding="utf-8"))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--db", default=str(REPO_ROOT / "db" / "knowledge.duckdb"))
    ap.add_argument("--steps", nargs="*", default=DEFAULT_STEPS,
                    help="実行するステップ番号（例: 05 06 07）。既定は 02-07")
    ap.add_argument("--drop", action="store_true",
                    help="標準化オブジェクトをすべて削除して終了する（既存 raw テーブルは触らない）")
    ap.add_argument("--no-schema-sync", action="store_true",
                    help="db/schema.sql の再生成をスキップする")
    args = ap.parse_args()

    sys.stdout.reconfigure(encoding="utf-8")
    con = duckdb.connect(args.db)
    try:
        if args.drop:
            for v in STANDARD_VIEWS:
                con.execute(f"DROP VIEW IF EXISTS {v}")
            for t in STANDARD_TABLES:
                con.execute(f"DROP TABLE IF EXISTS {t}")
            for s in STANDARD_SEQUENCES:
                con.execute(f"DROP SEQUENCE IF EXISTS {s}")
            for m in STANDARD_MACROS:
                con.execute(f"DROP MACRO IF EXISTS {m}")
            print("dropped all product-spec-normalizer objects.")
        else:
            files = sorted(SQL_DIR.glob("*.sql"))
            for step in args.steps:
                matches = [f for f in files if f.name.startswith(step + "_")]
                if not matches:
                    sys.exit(f"step not found: {step}")
                for f in matches:
                    run_sql_file(con, f)

            print("\n== summary ==")
            for t in ["products", "raw_specs", "canonical_specs", "spec_synonyms",
                      "spec_patterns", "unit_conversions", "spec_mapping",
                      "normalized_specs", "normalization_issues"]:
                try:
                    n = con.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
                    print(f"{t:24s} {n:6d} rows")
                except duckdb.CatalogException:
                    print(f"{t:24s} (not created)")

        if not args.no_schema_sync:
            dump_schema(con, REPO_ROOT / "db" / "schema.sql")
            print("schema synced: db/schema.sql")
    finally:
        con.close()


if __name__ == "__main__":
    main()
