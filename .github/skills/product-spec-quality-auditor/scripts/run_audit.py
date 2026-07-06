# -*- coding: utf-8 -*-
"""SQL 監査を read_only で順番に実行し、結果を audit_outputs/ に保存する。

使い方:
    python .github/skills/product-spec-quality-auditor/scripts/run_audit.py
    python .github/skills/product-spec-quality-auditor/scripts/run_audit.py --db db/knowledge.duckdb --out-dir audit_outputs

動作:
    - knowledge.duckdb へ必ず read_only=True で接続する（書き込み API は一切使わない）。
    - sql/*.sql をファイル名順に読み、「-- AUDIT: <名前>」単位で分割して実行する。
    - 各クエリの結果を audit_outputs/raw/<名前>.csv（UTF-8 BOM 付き）に保存する。
    - 全結果をまとめた audit_outputs/sql_audit_results.md も出力する（長い結果は先頭50行に切る）。
    - 実行メタ情報（成功/失敗/オブジェクト不足）を audit_outputs/raw/_run_meta.json に保存する。
      オブジェクト不足はエラーではなく「不足」として監査レポートに載る。
    - SELECT 系（SELECT / WITH / SUMMARIZE / DESCRIBE / PRAGMA / FROM）以外の文はブロックし、
      実行せずに blocked として記録する（監査専用の防御）。
"""
import argparse
import csv
import json
import re
import sys
from pathlib import Path

import duckdb

REPO_ROOT = Path(__file__).resolve().parents[4]
SQL_DIR = Path(__file__).resolve().parents[1] / "sql"

READONLY_KEYWORDS = ("select", "with", "summarize", "describe", "pragma", "from")
MD_ROW_LIMIT = 50


def split_audits(sql_text: str) -> "list[tuple[str, str]]":
    """'-- AUDIT: name' 区切りで [(name, query), ...] を返す。"""
    audits: list[tuple[str, str]] = []
    current, buf = None, []
    for line in sql_text.splitlines():
        m = re.match(r"^--\s*AUDIT:\s*(\w+)", line)
        if m:
            if current and "\n".join(buf).strip():
                audits.append((current, "\n".join(buf)))
            current, buf = m.group(1), []
        elif current is not None:
            buf.append(line)
    if current and "\n".join(buf).strip():
        audits.append((current, "\n".join(buf)))
    return audits


def first_keyword(query: str) -> str:
    stripped = re.sub(r"--[^\n]*", "", query)
    m = re.search(r"[A-Za-z]+", stripped)
    return m.group(0).lower() if m else ""


def classify_error(msg: str) -> str:
    lowered = msg.lower()
    if "does not exist" in lowered or "not found" in lowered:
        return "missing_object"
    return "error"


def to_markdown_table(cols, rows, limit=MD_ROW_LIMIT):
    def cell(v):
        s = "" if v is None else str(v)
        return s.replace("|", "\\|").replace("\n", " ")

    lines = ["| " + " | ".join(cols) + " |",
             "|" + "---|" * len(cols)]
    for row in rows[:limit]:
        lines.append("| " + " | ".join(cell(v) for v in row) + " |")
    if len(rows) > limit:
        lines.append(f"\n（全 {len(rows)} 行のうち先頭 {limit} 行のみ表示。全量は raw/ の CSV を参照）")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description="SQL 品質監査を read_only で実行する")
    ap.add_argument("--db", default=str(REPO_ROOT / "db" / "knowledge.duckdb"))
    ap.add_argument("--out-dir", default=str(REPO_ROOT / "audit_outputs"))
    args = ap.parse_args()

    sys.stdout.reconfigure(encoding="utf-8")
    out_dir = Path(args.out_dir)
    raw_dir = out_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    if not Path(args.db).exists():
        print(f"NG: DB が見つかりません: {args.db}")
        sys.exit(1)

    # 読み取り専用接続。監査中に DB を変更しないための必須条件。
    con = duckdb.connect(args.db, read_only=True)

    meta = []
    md_sections = []
    try:
        for sql_file in sorted(SQL_DIR.glob("*.sql")):
            print(f"== {sql_file.name}")
            md_sections.append(f"\n## {sql_file.name}\n")
            for name, query in split_audits(sql_file.read_text(encoding="utf-8")):
                entry = {"file": sql_file.name, "name": name}
                kw = first_keyword(query)
                if kw not in READONLY_KEYWORDS:
                    entry.update(status="blocked_non_readonly",
                                 error=f"先頭キーワード '{kw}' は監査で許可されていない")
                    meta.append(entry)
                    print(f"  BLOCKED {name}: 非 read-only 文のため実行しない")
                    continue
                try:
                    cur = con.execute(query)
                    cols = [d[0] for d in cur.description]
                    rows = cur.fetchall()
                except duckdb.Error as e:
                    status = classify_error(str(e))
                    entry.update(status=status, error=str(e).splitlines()[0])
                    meta.append(entry)
                    label = "MISSING" if status == "missing_object" else "ERROR"
                    print(f"  {label} {name}: {entry['error']}")
                    md_sections.append(f"### {name}\n\n**{label}**: `{entry['error']}`\n")
                    continue

                csv_path = raw_dir / f"{name}.csv"
                with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
                    w = csv.writer(f)
                    w.writerow(cols)
                    w.writerows(rows)
                entry.update(status="ok", rows=len(rows), csv=csv_path.name)
                meta.append(entry)
                print(f"  OK {name} ({len(rows)} rows)")
                md_sections.append(f"### {name}\n\n{to_markdown_table(cols, rows)}\n")
    finally:
        con.close()

    (raw_dir / "_run_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    md_path = out_dir / "sql_audit_results.md"
    header = ("# SQL 監査結果（生データ）\n\n"
              f"- DB: `{args.db}`（read_only で接続）\n"
              f"- 実行ブロック数: {len(meta)} / OK: {sum(1 for m in meta if m['status'] == 'ok')}"
              f" / 不足: {sum(1 for m in meta if m['status'] == 'missing_object')}"
              f" / エラー: {sum(1 for m in meta if m['status'] == 'error')}\n")
    md_path.write_text(header + "\n".join(md_sections), encoding="utf-8")

    print(f"done. raw CSV: {raw_dir.as_posix()} / markdown: {md_path.as_posix()}")
    print("次: python .github/skills/product-spec-quality-auditor/scripts/generate_audit_report.py")


if __name__ == "__main__":
    main()
