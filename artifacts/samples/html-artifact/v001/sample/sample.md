---
title: HTML Artifact 新標準サンプル
created: 2026-05-24
type: artifact-source
status: sample
input_wiki:
  - wiki/concepts/Artifacts運用.md
input_raw: []
outputs:
  - artifacts/samples/html-artifact/v001/sample/sample.web.html
  - artifacts/samples/html-artifact/v001/sample/sample.a4.html
  - artifacts/samples/html-artifact/v001/sample/sample.slides.html
purpose: Markdown 正本から Web / A4 / Slides の用途別 HTML を生成する新標準の確認用サンプル。
---

# HTML Artifact 新標準サンプル

## TL;DR

この Markdown は、LLM Wiki の Artifact を作るときの新しい標準フローを確認するためのサンプル正本です。内容はこのファイルに置き、閲覧用の `sample.web.html`、A4印刷用の `sample.a4.html`、16:9スライド用の `sample.slides.html` を別々に生成します。

## このサンプルの目的

旧サンプルは、1つの HTML 内で A4 とスライドを切り替える形式でした。新標準では、Markdown を内容の正本とし、用途ごとに HTML を分けます。

この方式により、内容修正は Markdown 側で一元管理し、A4 やスライドの見た目だけを直したい場合は該当する HTML を個別に調整できます。

## 出力形式

| ファイル | 用途 | レイアウト方針 |
| --- | --- | --- |
| `*.web.html` | ブラウザ閲覧 | 切れ目のない Web ページとして表示する |
| `*.a4.html` | A4印刷/PDF | 用紙単位のページ区切りを持たせる |
| `*.slides.html` | 16:9スライド/PDF/PowerPoint | 1スライド1メッセージを基本に再構成する |

## Markdown と HTML の役割

Markdown は、タイトル、章、節、表、図、根拠などの意味構造を残すための正本です。フォントサイズや余白などの細かな見た目は、出力先 HTML 側で決めます。

HTML は、Markdown の意味構造を人間が読みやすい形に変換した表示物です。Web、A4、Slides では同じ内容を扱っていても、見せ方は同じにしません。

<!-- callout -->
内容を直す場合は Markdown を修正し、A4 や Slides の余白・ページ区切り・文字量だけを直す場合は対応する HTML を調整します。

## 品質チェック

- Markdown に入力元と出力先が明記されている。
- `web.html` から A4 版と Slides 版へ移動できる。
- `a4.html` は印刷時にページ区切りが明確になる。
- `slides.html` は長文をそのまま流し込まず、スライド向けに要点化している。
- 旧形式の単一 HTML サンプルに依存しない。

## Provenance

- 入力元 wiki: `wiki/concepts/Artifacts運用.md`
- 入力 raw: なし
- 作成日: 2026-05-24

## Last Updated

2026-05-24
