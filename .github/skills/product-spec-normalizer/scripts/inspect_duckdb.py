# -*- coding: utf-8 -*-
"""knowledge.duckdb の既存テーブルを read_only で調査し、Markdown レポートを出力する。

使い方:
    python .github/skills/product-spec-normalizer/scripts/inspect_duckdb.py
    python .github/skills/product-spec-normalizer/scripts/inspect_duckdb.py --out db/review/profile_report.md
    python .github/skills/product-spec-normalizer/scripts/inspect_duckdb.py --items   # 縦持ちテーブルの項目名一覧も出す

出力内容:
    - テーブル一覧・行数・元 Excel パス
    - 列シグネチャによるテーブルのグループ化（縦持ち/横持ちの型を判断する材料）
    - 各シグネチャの代表テーブルのサンプル行
    - 仕様項目・単位に相当する列の候補
    - (--items) 縦持ちテーブルの distinct 仕様項目
"""
import argparse
import sys
from collections import defaultdict
from pathlib import Path

import duckdb

REPO_ROOT = Path(__file__).resolve().parents[4]
META_COLS = ("raw_path", "sheet_name", "row_no")

ROLE_HINTS = {
    "company": ("メーカー", "メーカー名"),
    "model": ("型式", "SAL型式", "Model"),
    "item": ("仕様項目", "項目"),
    "value": ("仕様値", "数値", "内容", "US値", "メートル値", "仕様_US値", "メートル数値", "US数値"),
    "category": ("仕様カテゴリ", "大分類", "中分類", "区分", "セクション", "大項目", "分類"),
}


def q(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--db", default=str(REPO_ROOT / "db" / "knowledge.duckdb"))
    ap.add_argument("--out", default=None, help="Markdown の出力先（省略時は標準出力）")
    ap.add_argument("--items", action="store_true", help="縦持ちテーブルの仕様項目一覧も出力する")
    ap.add_argument("--sample-rows", type=int, default=3)
    args = ap.parse_args()

    con = duckdb.connect(args.db, read_only=True)
    lines: list[str] = ["# knowledge.duckdb プロファイル", ""]

    tables = [t for (t,) in con.execute(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_type='BASE TABLE' ORDER BY table_name").fetchall()]

    # 1. テーブル一覧
    lines += [f"## テーブル一覧 ({len(tables)} tables)", "",
              "| table | rows | raw_path |", "|---|---:|---|"]
    for t in tables:
        n = con.execute(f"SELECT count(*) FROM {q(t)}").fetchone()[0]
        rp = con.execute(
            "SELECT any_value(raw_path) FROM excel_imports WHERE table_name = ?", [t]).fetchone()[0]
        lines.append(f"| {t} | {n} | {rp or ''} |")
    lines.append("")

    # 2. 列シグネチャでグループ化 + サンプル
    sig = defaultdict(list)
    for t in tables:
        cols = tuple(c[0] for c in con.execute(f"SELECT * FROM {q(t)} LIMIT 0").description
                     if c[0] not in META_COLS)
        sig[cols].append(t)

    lines += ["## 列シグネチャ別グループ", ""]
    for cols, ts in sorted(sig.items(), key=lambda kv: -len(kv[1])):
        rep = ts[0]
        roles = []
        for role, hints in ROLE_HINTS.items():
            hit = [c for c in cols if c in hints]
            if hit:
                roles.append(f"{role}={'/'.join(hit)}")
        lines += [f"### {len(ts)} tables: 代表 `{rep}`", "",
                  f"- columns: {', '.join(cols)}",
                  f"- 役割候補: {'; '.join(roles) or '(該当なし)'}",
                  f"- tables: {', '.join(ts)}", "", "サンプル行:", "", "```"]
        for row in con.execute(f"SELECT * FROM {q(rep)} LIMIT {args.sample_rows}").fetchall():
            lines.append(" | ".join("" if v is None else str(v)[:40] for v in row))
        lines += ["```", ""]

    # 3. 縦持ちテーブルの仕様項目一覧（任意）
    if args.items:
        lines += ["## 縦持ちテーブルの仕様項目（distinct）", ""]
        for t in tables:
            cols = [c[0] for c in con.execute(f"SELECT * FROM {q(t)} LIMIT 0").description]
            item_col = next((c for c in ("仕様項目", "項目") if c in cols), None)
            if not item_col:
                continue
            rows = con.execute(
                f"SELECT {q(item_col)}, count(*) FROM {q(t)} GROUP BY 1 ORDER BY 1").fetchall()
            lines.append(f"### {t} ({item_col})")
            lines += [f"- {r[0]} ({r[1]})" for r in rows if r[0] is not None]
            lines.append("")

    report = "\n".join(lines)
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(report, encoding="utf-8")
        print(f"written: {out}")
    else:
        sys.stdout.reconfigure(encoding="utf-8")
        print(report)


if __name__ == "__main__":
    main()
