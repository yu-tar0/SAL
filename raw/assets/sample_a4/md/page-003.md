<!-- page: 003 source: ../pages/page-003.png -->

# 3. Markdown と HTML の役割

Markdown は、タイトル、章、節、表、図、根拠などの意味構造を残すための正本です。フォントサイズや余白などの細かな見た目は、出力先 HTML 側で決めます。

HTML は、Markdown の意味構造を人間が読みやすい形に変換した表示物です。Web、A4、Slides では同じ内容を扱っていても、見せ方は同じにしません。

> 内容を直す場合は Markdown を修正し、A4 や Slides の余白・ページ区切り・文字量だけを直す場合は対応する HTML を調整します。

# 4. 品質チェック

- Markdown に入力元と出力先が明記されている。
- `web.html` から A4 版と Slides 版へ移動できる。
- `a4.html` は印刷時にページ区切りが明確になる。
- `slides.html` は長文をそのまま流し込まず、スライド向けに要点化している。
- 旧形式の単一 HTML サンプルに依存しない。

# 5. Provenance

入力元 wiki: wiki/concepts/Artifacts運用.md

入力 raw: なし

作成日: 2026-05-24

<!-- check: table_ok=true; reading_order_ok=true; uncertain_parts=none; review_status=auto_generated -->
