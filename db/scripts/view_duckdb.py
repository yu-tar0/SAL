"""db/knowledge.duckdb をブラウザで確認する読み取り専用ビューア。

使い方:
    python db/scripts/view_duckdb.py
    python db/scripts/view_duckdb.py --db db/knowledge.duckdb --port 8765 --no-browser

- read_only 接続のみ。書き込みは一切できない（「確認は read_only」の運用方針をコードで強制）。
- 接続はリクエストごとに開閉するため、ビューアを起動したままでもローダーを実行できる。
- localhost のみで待ち受け、外部には公開しない。
- 依存は Python 標準ライブラリと duckdb パッケージのみ。
"""

import argparse
import json
import re
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import duckdb

REPO_ROOT = Path(__file__).resolve().parents[2]
MAX_ROWS = 500
ALLOWED_SQL = re.compile(r"^\s*(SELECT|WITH|DESCRIBE|SUMMARIZE|SHOW|EXPLAIN)\b", re.IGNORECASE)

PAGE = """<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<title>knowledge.duckdb viewer</title>
<style>
  * { box-sizing: border-box; }
  body { margin: 0; font-family: "Segoe UI", "Yu Gothic UI", sans-serif; font-size: 14px;
         color: #24292f; background: #f6f8fa; display: flex; height: 100vh; }
  #sidebar { width: 300px; min-width: 220px; background: #fff; border-right: 1px solid #d0d7de;
             overflow-y: auto; padding: 12px; flex-shrink: 0; }
  #sidebar h1 { font-size: 15px; margin: 0 0 4px; }
  #dbpath { font-size: 11px; color: #57606a; word-break: break-all; margin-bottom: 10px; }
  .tbl { padding: 6px 8px; border-radius: 6px; cursor: pointer; display: flex;
         justify-content: space-between; gap: 8px; }
  .tbl:hover { background: #f3f4f6; }
  .tbl.active { background: #ddf4ff; }
  .tbl .name { word-break: break-all; }
  .tbl .count { color: #57606a; flex-shrink: 0; }
  #main { flex: 1; display: flex; flex-direction: column; overflow: hidden; padding: 12px; gap: 10px; }
  #querybox { display: flex; gap: 8px; }
  #sql { flex: 1; height: 60px; font-family: Consolas, monospace; font-size: 13px;
         padding: 8px; border: 1px solid #d0d7de; border-radius: 6px; resize: vertical; }
  button { padding: 6px 14px; border: 1px solid #d0d7de; border-radius: 6px;
           background: #fff; cursor: pointer; }
  button:hover { background: #f3f4f6; }
  #toolbar { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
  #filter { padding: 5px 8px; border: 1px solid #d0d7de; border-radius: 6px; width: 220px; }
  #status { color: #57606a; }
  #error { color: #cf222e; white-space: pre-wrap; }
  #grid { flex: 1; overflow: auto; background: #fff; border: 1px solid #d0d7de; border-radius: 6px; }
  table { border-collapse: collapse; font-size: 13px; white-space: nowrap; }
  th, td { border-bottom: 1px solid #eaeef2; padding: 4px 10px; text-align: left;
           max-width: 480px; overflow: hidden; text-overflow: ellipsis; }
  th { position: sticky; top: 0; background: #f6f8fa; cursor: pointer; user-select: none; }
  td.null { color: #a0a7ae; font-style: italic; }
  tr:hover td { background: #f8fafc; }
</style>
</head>
<body>
<div id="sidebar">
  <h1>knowledge.duckdb</h1>
  <div id="dbpath"></div>
  <button onclick="loadTables()">再読込</button>
  <div id="tables"></div>
</div>
<div id="main">
  <div id="querybox">
    <textarea id="sql" placeholder="SELECT 文を入力（read-only 接続で実行されます）"></textarea>
    <button onclick="runQuery()">実行</button>
  </div>
  <div id="toolbar">
    <input id="filter" placeholder="表示中の行を絞り込み" oninput="renderRows()">
    <button id="prev" onclick="page(-1)" disabled>前へ</button>
    <button id="next" onclick="page(1)" disabled>次へ</button>
    <span id="status"></span>
  </div>
  <div id="error"></div>
  <div id="grid"></div>
</div>
<script>
let state = { table: null, offset: 0, limit: 100, total: 0, columns: [], rows: [], sort: null };

function esc(s) {
  return String(s).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
}

async function api(path, opts) {
  const res = await fetch(path, opts);
  return res.json();
}

async function loadTables() {
  const data = await api('/api/tables');
  document.getElementById('dbpath').textContent = data.db;
  const div = document.getElementById('tables');
  div.innerHTML = data.tables.map(t =>
    `<div class="tbl" data-name="${esc(t.name)}" onclick="selectTable(this.dataset.name)">` +
    `<span class="name">${esc(t.name)}</span><span class="count">${t.rows}行</span></div>`).join('');
  highlight();
}

function highlight() {
  document.querySelectorAll('.tbl').forEach(el =>
    el.classList.toggle('active', el.dataset.name === state.table));
}

async function selectTable(name, offset = 0) {
  state.table = name; state.offset = offset; state.sort = null;
  highlight();
  const data = await api(`/api/table?name=${encodeURIComponent(name)}&limit=${state.limit}&offset=${offset}`);
  showResult(data, `${name}: 全${data.total}行中 ${data.rows.length ? offset + 1 : 0}〜${offset + data.rows.length}行目`);
  state.total = data.total;
  document.getElementById('prev').disabled = offset <= 0;
  document.getElementById('next').disabled = offset + state.limit >= data.total;
}

function page(dir) {
  selectTable(state.table, Math.max(0, state.offset + dir * state.limit));
}

async function runQuery() {
  const sql = document.getElementById('sql').value.trim();
  if (!sql) return;
  state.table = null; highlight();
  document.getElementById('prev').disabled = true;
  document.getElementById('next').disabled = true;
  const data = await api('/api/query', { method: 'POST',
    headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ sql }) });
  showResult(data, data.error ? '' :
    `${data.rows.length}行` + (data.truncated ? `（先頭${data.rows.length}行のみ表示）` : ''));
}

function showResult(data, statusText) {
  const errEl = document.getElementById('error');
  if (data.error) {
    errEl.textContent = data.error;
    document.getElementById('status').textContent = '';
    return;
  }
  errEl.textContent = '';
  state.columns = data.columns; state.rows = data.rows;
  document.getElementById('status').textContent = statusText;
  document.getElementById('filter').value = '';
  renderRows();
}

function renderRows() {
  const q = document.getElementById('filter').value.toLowerCase();
  let rows = state.rows;
  if (q) rows = rows.filter(r => r.some(v => v !== null && String(v).toLowerCase().includes(q)));
  if (state.sort) {
    const { i, dir } = state.sort;
    rows = [...rows].sort((a, b) => {
      const x = a[i], y = b[i];
      if (x === null) return 1; if (y === null) return -1;
      if (typeof x === 'number' && typeof y === 'number') return (x - y) * dir;
      return String(x).localeCompare(String(y), 'ja') * dir;
    });
  }
  const head = state.columns.map((c, i) =>
    `<th onclick="sortBy(${i})">${esc(c)}${state.sort && state.sort.i === i ? (state.sort.dir > 0 ? ' ▲' : ' ▼') : ''}</th>`).join('');
  const body = rows.map(r => '<tr>' + r.map(v =>
    v === null ? '<td class="null">NULL</td>' : `<td title="${esc(v)}">${esc(v)}</td>`).join('') + '</tr>').join('');
  document.getElementById('grid').innerHTML =
    `<table><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table>`;
}

function sortBy(i) {
  state.sort = (state.sort && state.sort.i === i) ? { i, dir: -state.sort.dir } : { i, dir: 1 };
  renderRows();
}

document.getElementById('sql').addEventListener('keydown', e => {
  if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) runQuery();
});
loadTables();
</script>
</body>
</html>
"""


def quote_ident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


class Handler(BaseHTTPRequestHandler):
    db_path = None

    def query(self, sql, params=None, max_rows=MAX_ROWS):
        """リクエストごとに read_only 接続を開閉する（ローダーとロック競合させないため）。"""
        con = duckdb.connect(self.db_path, read_only=True)
        try:
            cur = con.execute(sql, params or [])
            columns = [d[0] for d in cur.description] if cur.description else []
            rows = cur.fetchmany(max_rows + 1)
            truncated = len(rows) > max_rows
            return columns, [list(r) for r in rows[:max_rows]], truncated
        finally:
            con.close()

    def send_json(self, obj, status=200):
        body = json.dumps(obj, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        url = urlparse(self.path)
        try:
            if url.path == "/":
                body = PAGE.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            elif url.path == "/api/tables":
                columns, rows, _ = self.query(
                    "SELECT table_name, table_type FROM information_schema.tables "
                    "WHERE table_schema = 'main' ORDER BY table_name"
                )
                tables = []
                for name, _type in rows:
                    _, cnt, _ = self.query(f"SELECT count(*) FROM {quote_ident(name)}")
                    tables.append({"name": name, "rows": cnt[0][0]})
                self.send_json({"db": str(self.db_path), "tables": tables})
            elif url.path == "/api/table":
                params = parse_qs(url.query)
                name = params.get("name", [""])[0]
                limit = min(int(params.get("limit", ["100"])[0]), MAX_ROWS)
                offset = max(int(params.get("offset", ["0"])[0]), 0)
                _, total, _ = self.query(f"SELECT count(*) FROM {quote_ident(name)}")
                columns, rows, _ = self.query(
                    f"SELECT * FROM {quote_ident(name)} LIMIT {limit} OFFSET {offset}"
                )
                self.send_json({"columns": columns, "rows": rows, "total": total[0][0]})
            else:
                self.send_json({"error": "not found"}, status=404)
        except Exception as e:
            self.send_json({"error": str(e)})

    def do_POST(self):
        url = urlparse(self.path)
        if url.path != "/api/query":
            self.send_json({"error": "not found"}, status=404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            sql = payload.get("sql", "")
            if not ALLOWED_SQL.match(sql):
                self.send_json(
                    {"error": "SELECT / WITH / DESCRIBE / SUMMARIZE / SHOW / EXPLAIN のみ実行できます"}
                )
                return
            columns, rows, truncated = self.query(sql)
            self.send_json({"columns": columns, "rows": rows, "truncated": truncated})
        except Exception as e:
            self.send_json({"error": str(e)})

    def log_message(self, fmt, *args):
        pass  # アクセスログは出さない


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--db", default=str(REPO_ROOT / "db" / "knowledge.duckdb"))
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-browser", action="store_true", help="ブラウザを自動で開かない")
    args = parser.parse_args()

    if not Path(args.db).exists():
        raise SystemExit(f"not found: {args.db}")
    # 起動時に read_only で開けることを確認する（ファイル破損や版違いを早期に検出）
    duckdb.connect(args.db, read_only=True).close()

    Handler.db_path = args.db
    server = HTTPServer(("127.0.0.1", args.port), Handler)
    url = f"http://127.0.0.1:{args.port}/"
    print(f"knowledge.duckdb viewer: {url} (Ctrl+C で終了)")
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("stopped")


if __name__ == "__main__":
    main()
