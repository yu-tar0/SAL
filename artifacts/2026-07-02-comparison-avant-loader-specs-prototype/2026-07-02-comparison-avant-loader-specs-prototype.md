---
title: AVANT SAL比較表 試作
created: 2026-07-02
updated: 2026-07-02
type: artifact
status: prototype
input:
  - db/knowledge.duckdb
  - raw/data/AVANT_型式_仕様一覧.csv
outputs:
  - artifacts/2026-07-02-comparison-avant-loader-specs-prototype/2026-07-02-comparison-avant-loader-specs-prototype.md
  - artifacts/2026-07-02-comparison-avant-loader-specs-prototype/2026-07-02-comparison-avant-loader-specs-prototype.web.html
purpose: DuckDBに入っている既存のAVANT SAL仕様データを比較表レイアウトとして試作する
---

# AVANT SAL比較表 試作

DuckDB にある AVANT の既存仕様データを使い、数値比較と分類比較を 1 ページで見られる形にした試作です。

## 要約

- 比較の主軸は、数値が比較的そろっている個別機種 7 モデルです。
- 系列ページしか取得できていない 700 / 800 / e500 / e700 は、補足表として分離しています。
- 現在の DuckDB には、添付イメージ下段のような機能オンオフ表を作るための十分な機能項目は入っていません。
- そのため今回は、数値比較と分類比較を中心にした HTML 試作にしています。

## 比較対象

### 個別機種 7 モデル

| 型式 | 馬力 | リフト容量 | リフト高 | 最高速度 | 全幅 | 運転質量 | 動力 | トランスミッション |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AVANT 225 | 25 hp | 705 lb | 57.1 in | 6.2 mph | 38.6 in | 1587.3 lb | Gasoline min RON 95 | Hydrostatic |
| AVANT 423 | 22 hp | 1213 lb | 108.3 in | 7.5 mph | 41.3 in | 2381 lb | Diesel | Hydrostatic |
| AVANT 528 | 25 hp | 2094 lb | 109.8 in | 7.5 mph | 44.9 in | 3130.5 lb | Diesel | Hydrostatic, Avant Optidrive(R) |
| AVANT 530 | 25 hp | 2094 lb | 109.8 in | 11.8 mph | 44.9 in | 3218.7 lb | Diesel | Hydrostatic, Avant Optidrive(R) |
| AVANT 635i | 26 hp | 2623 lb | 111.6 in | 7.5 mph | 50.8 in | 3549.4 lb | Diesel | Hydrostatic Avant Optidrive(R) |
| AVANT 645i | 44 hp | 2623 lb | 111.6 in | 7.5 mph | 50.8 in | 3571.5 lb | Diesel | Hydrostatic, Avant Optidrive(R) |
| AVANT 650i | 44 hp | 2623 lb | 111.6 in | 14.3 mph | 50.8 in | 3593.5 lb | Diesel | Hydrostatic, Avant Optidrive(R) |

### 補足対象 4 モデル

| 型式 | 取得状態 | 比較に使える主な項目 | 備考 |
| --- | --- | --- | --- |
| AVANT 700 series | シリーズページ由来 | 馬力レンジ、リフト容量、リフト高、速度レンジ | 幅、重量、詳細機能は未取得 |
| AVANT 800 series | シリーズページ由来 | 馬力レンジ、リフト容量、リフト高、最高速度 | 幅、重量、詳細機能は未取得 |
| AVANT e500 series | シリーズページ由来 | リフト容量、リフト高、速度、バッテリー容量、充電時間 | 電動。馬力は HP 記載なし |
| AVANT e700 series | シリーズページ由来 | リフト容量、リフト高、速度、バッテリー容量、充電時間 | 電動。馬力は HP 記載なし |

## 数値比較の見方

- HTML では、項目ごとに最小値から最大値までのレンジを横棒で示し、その上に各型式の位置を置いています。
- 位置は DuckDB の元データから数値部分を抜き出して正規化したものです。
- 単位変換はしておらず、今回は取得値をそのまま使っています。

## 分類比較の見方

- 現行 DB で離散値として比較しやすいのは、動力とトランスミッションです。
- テレスコピック有無や油圧系の詳細は、行によって記述密度が違うため、今回の分類表では備考扱いにとどめています。

## 補足メモ

- 700 / 800 / e500 / e700 はシリーズページ由来のため、個別機種と同列には比較していません。
- e500 / e700 は電動シリーズとして、バッテリー容量と充電時間を別枠で保持しています。
- 機能比較表を追加したい場合は、別 CSV で `自動水平制御` `キャビン` `倍速ターン` のような離散項目を持たせるのが早いです。

## Provenance

- DuckDB: `db/knowledge.duckdb`
- 参照 view: `loader_specifications_current`
- 元 CSV: `raw/data/AVANT_型式_仕様一覧.csv`
- 作成日: 2026-07-02
- 生成物: `2026-07-02-comparison-avant-loader-specs-prototype.web.html`

## 未解決点

- 機能比較表に必要なオプション / 標準 / なし の列は、現行 DB には未収録です。
- 幅、重量、油圧系の比較を全シリーズへ広げるには、700 / 800 / e500 / e700 の詳細仕様取得が必要です。
- 本試作はブラウザ閲覧用の `web.html` のみで、A4 や Slides はまだ作っていません。