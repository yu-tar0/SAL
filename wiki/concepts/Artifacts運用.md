---
type: concept
title: Artifacts運用
created: 2026-05-22
updated: 2026-06-06
tags:
  - artifacts
  - html
  - wiki-operations
summary: wiki と raw を入力元に Markdown 正本と HTML 表示物を管理する Artifact 運用ルール。
---

# Artifacts運用

> One-line summary: wiki と raw を入力元に Markdown 正本と HTML 表示物を管理する Artifact 運用ルール。

## TL;DR

Artifacts は、`wiki/` に蓄積された知識や、必要に応じて `raw/` の一次資料をもとに、人間が読みやすい形へ可視化した成果物を保存する領域である。内容の正本は単一 Markdown として残し、標準では閲覧・共有用の `web.html` を生成する。A4印刷用やスライド用のHTMLは、明示的に必要な場合だけ追加生成する。

## 概要

`artifacts/` は、`wiki/` の概念ページや索引と連動させて使う。知識の主保管先は `wiki/`、一次資料の主保管先は `raw/` とし、`artifacts/` にはそれらを人間向けに再構成した Markdown と、そこから作成したHTMLを置く。

成果物は、関連する概念・エンティティ・分析ページから `[[Wikilink]]` で参照できるようにする。Artifact 内でも、根拠となる wiki ページや raw 資料を明示し、どの情報を可視化したものか追跡できる状態を保つ。

## Markdown と HTML の役割

- Markdown は内容の正本として扱う。
- HTML は Markdown をもとにした可視化・配布用の表示物として扱う。
- 内容修正は原則 Markdown 側に入れる。
- HTML の直接編集は、レイアウト、スタイル、HTML固有の表現調整に限る。
- Markdown と HTML は同じ Artifact フォルダ内に、同じ basename で保存する。

## HTML 出力形式

標準では、1つの Markdown 正本から以下のHTMLを生成する。

- `*.web.html`: ブラウザ閲覧用。切れ目のないWebサイトのような連続ページとして扱う。

A4印刷やプレゼン用途が明示されている場合だけ、以下を追加生成する。

- `*.a4.html`: A4印刷/PDF用。用紙単位のページ区切りを持たせる。
- `*.slides.html`: 16:9スライド/PDF/PowerPoint用。スライド単位のページ区切りを持たせる。

`web.html` を閲覧の入口とする。`a4.html` と `slides.html` を追加生成した場合は、必要に応じて `web.html` からリンクする。1つのHTML内でタブ切り替えする方式は便利だが、A4やスライドだけを手直しする場合にCSSやページ区切りが干渉しやすい。そのため、追加出力が必要な場合は用途別にHTMLファイルを分ける。

## 保存単位

Artifact は `artifacts/` 直下にファイルを展開せず、1つの成果物につき1フォルダを作る。フォルダ名は Artifact ID とし、正本 Markdown と標準の Web HTML を同じフォルダにまとめる。A4版・スライド版を追加生成した場合も同じフォルダに置く。

```text
artifacts/YYYY-MM-DD-[カテゴリ]-[簡潔タイトル]/
├── YYYY-MM-DD-[カテゴリ]-[簡潔タイトル].md
└── YYYY-MM-DD-[カテゴリ]-[簡潔タイトル].web.html
```

必要に応じて `*.a4.html` と `*.slides.html` を同じフォルダへ追加する。

## 色テーマ

HTML の色は表示レイヤーのテーマとして扱い、Markdown 正本からは分離する。テーマ定義の正本は `.github/skills/html-artifact/assets/themes.json` に置き、標準テーマは `wiki-teal-v1` とする。

Artifact 生成時にはテーマを1つ選び、各HTMLの `<head>` 内に `Artifact Theme` コメントと `artifact-theme-metadata` JSON を残す。これにより、後からHTML単体を見ても、どのテーマID・バージョン・色値で生成されたかを確認できる。

テーマを追加・改訂した場合は、`themes.json` の `history` と `wiki/log.md` に履歴を残す。生成済みHTMLの色は、再生成または明示的な更新時にだけ変更する。

## 変換の考え方

Markdown は、フォントサイズや余白を指定するレイアウト原稿ではなく、タイトル、章、節、表、図、根拠などの意味構造を持つ正本として扱う。各HTMLは、その意味構造を用途に合わせた視覚文法へ変換する。

- `web.html`: Markdown を読みやすい連続ページとして表示する。
- `a4.html`: 追加生成する場合、Markdown を印刷資料として比較的忠実に整形する。
- `slides.html`: 追加生成する場合、Markdown をプレゼン向けに要約・分割して再構成する。

`slides.html` を追加生成する場合は、逐語変換ではなく、1スライド1メッセージを基本に、長い段落や大きな表を短い要点・分割スライド・画像中心スライドへ変換してよい。ただし、意味を変えたり、根拠のない主張を追加してはならない。

## 品質基準

- 冒頭に `TL;DR` があり、要点が短く分かる。
- 何を入力元として可視化したかが分かる。
- Markdown に入力元 wiki ページ、入力元 raw 資料、変換先 HTML が明記されている。
- HTML に元 Markdown への参照が含まれている。
- HTML に使用テーマIDと色値のメタデータが含まれている。
- 正本 Markdown と Web HTML が同じ Artifact フォルダにまとまっている。
- `web.html` が標準の閲覧入口になっている。
- `a4.html`、`slides.html` を追加生成した場合は用途が分かれ、`web.html` から他形式へ移動できる。
- 後日読んでも前提と用途が分かる。
- 出典がある場合は明示し、出典がない場合は内部メモやサンプルであることを明記する。
- `wiki/index.md` と `wiki/log.md` に反映し、孤立させない。

## Samples

`artifacts/samples/` は、本番 Artifact ではなく、Artifact 生成スキルやテンプレートの品質を確認するための検証領域である。通常の知識成果物と混ぜず、バージョンごとに出力を残して差分確認できるようにする。

推奨構成:

- `artifacts/samples/html-artifact/v001/sample/sample.md`
- `artifacts/samples/html-artifact/v001/sample/sample.web.html`

A4版・スライド版を検証するサンプルでは、必要に応じて以下も置く。

- `artifacts/samples/html-artifact/v001/sample/sample.a4.html`
- `artifacts/samples/html-artifact/v001/sample/sample.slides.html`

Samples は通常の `wiki/index.md` の Artifacts 一覧には載せない。スキル修正の節目や基準サンプル更新は `wiki/log.md` に記録する。

## 関連 Artifact

- `artifacts/2026-06-01-summary-artifact-web-default-test/2026-06-01-summary-artifact-web-default-test.md`: 標準生成を `web.html` のみにした運用を確認する試作。

## Related Links

- [[overview]]
- [[Rawデータ運用]]

## Provenance

- `artifacts/2026-05-23-summary-html-artifact-sample.html` 作成に伴い更新。
- 2026-05-24 に、Artifacts を `wiki/` および必要に応じた `raw/` の可視化レイヤーとして再定義。
- 2026-05-24 に、Markdown を内容の正本、HTML を表示物とする `md -> html` フローを追加。
- 2026-05-24 に、`web.html`、`a4.html`、`slides.html` の3系統HTML生成を標準化。
- 2026-05-24 に、Markdown を意味構造として扱い、Web/A4/Slidesへ用途別に変換する方針を追加。
- 2026-05-24 に、新標準サンプル `artifacts/samples/html-artifact/v001/sample.*` を作成し、旧HTMLサンプルを削除。
- 2026-05-24 に、サンプル生成物を `artifacts/samples/html-artifact/vNNN/` に分離する方針を追加。
- 2026-05-26 に、`raw/` 側の入力資料フローとして [[Rawデータ運用]] への関連リンクを追加。
- 2026-06-01 に、HTML Artifact の色テーマを `themes.json` で管理し、各HTMLに使用テーマメタデータを残す方針を追加。
- 2026-06-01 に、Artifact を `artifacts/<artifact-id>/` 単位で保存する方針へ変更。
- 2026-06-01 に、標準生成を `web.html` のみに変更し、`a4.html` と `slides.html` は明示依頼時の追加出力とした。
- 外部一次資料には基づかない内部運用メモ。

## Last Updated

2026-06-06
