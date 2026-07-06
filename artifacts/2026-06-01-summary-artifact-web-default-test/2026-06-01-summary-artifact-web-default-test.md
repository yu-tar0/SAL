---
type: artifact
title: Artifact Web Default Test
created: 2026-06-01
updated: 2026-06-01
status: draft
source_wiki_pages:
  - wiki/concepts/Artifacts運用.md
source_raw_materials: []
outputs:
  - artifacts/2026-06-01-summary-artifact-web-default-test/2026-06-01-summary-artifact-web-default-test.web.html
purpose: html-artifact スキルの標準出力が web.html のみになっていることを確認する試作
---

# Artifact Web Default Test

## TL;DR

この Artifact は、正本 Markdown から HTML を生成するときの標準出力を `web.html` のみに変更した運用を確認するための試作である。A4版とスライド版は作成していない。

## 入力元

| 種別 | パス | 内容 |
|---|---|---|
| wiki concept | `wiki/concepts/Artifacts運用.md` | Artifact の役割、保存単位、標準HTML出力、追加出力の扱い |

## 確認したいこと

- `artifacts/<artifact-id>/` に正本 Markdown と Web HTML だけを置く。
- `*.web.html` を標準の閲覧入口として扱う。
- `*.a4.html` と `*.slides.html` は、明示依頼がない限り生成しない。
- HTML には元 Markdown への参照とテーマメタデータを含める。

## 生成結果

| ファイル | 役割 | 生成有無 |
|---|---|---|
| `2026-06-01-summary-artifact-web-default-test.md` | 内容の正本 | 生成 |
| `2026-06-01-summary-artifact-web-default-test.web.html` | ブラウザ閲覧用HTML | 生成 |
| `2026-06-01-summary-artifact-web-default-test.a4.html` | A4印刷/PDF用HTML | 未生成 |
| `2026-06-01-summary-artifact-web-default-test.slides.html` | 16:9スライド用HTML | 未生成 |

## 運用メモ

標準生成を Web HTML のみにすると、通常の分析・まとめ・比較表では成果物数が減り、更新対象が明確になる。印刷資料や発表資料が必要な場合だけ、同じ Markdown 正本から追加形式を作る。

## Sources

- [[Artifacts運用]]
- `.github/skills/html-artifact/SKILL.md`

## 未解決点

- A4版・スライド版を後から追加生成するときのコマンド化やテンプレート分岐は、まだ運用検証が必要。

