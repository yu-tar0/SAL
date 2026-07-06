---
title: AVANT SAL比較表 現行DuckDB版
created: 2026-07-02
updated: 2026-07-02
type: artifact
status: current-db
input:
  - db/knowledge.duckdb
  - table: avant_loader_specs_raw
outputs:
  - artifacts/2026-07-02-comparison-avant-loader-specs-current-db/2026-07-02-comparison-avant-loader-specs-current-db.md
  - artifacts/2026-07-02-comparison-avant-loader-specs-current-db/2026-07-02-comparison-avant-loader-specs-current-db.web.html
purpose: 現行 knowledge.duckdb の AVANT raw 仕様を、比較しやすい Markdown 正本と Web HTML に整理する
---

# AVANT SAL比較表 現行DuckDB版

現行の `db/knowledge.duckdb` に入っている `avant_loader_specs_raw` を直接参照し、添付試作の見せ方を踏まえて再構成した比較 Artifact です。旧 `loader_specifications_current` ではなく、現在の raw テーブルにある値をそのまま基準にしています。

## 要約

- 現行 DuckDB には、AVANT の個別機種 15 台の燃焼系モデル、3 台の電動個別モデル、2 行のシリーズ要約が入っています。
- 燃焼系の最大リフト容量は AVANT 855i の 1900 kg、最高速度は AVANT 860i の 0-30 km/h です。
- 最小幅は AVANT 225 の 980 mm で、コンパクト側の基準点として見やすくなっています。
- HTML では、燃焼系個別モデルの主要数値をレンジ表示し、電動モデルとシリーズ要約は別表に分けています。

## 比較対象の区分

- 燃焼系個別モデル: 200 / 400 / 500 / 600 / 700 / 800 series の個別型式
- 電動個別モデル: e513 / e527 / e727
- シリーズ要約: e500 series / e700 series のシリーズ行

## 燃焼系個別モデル一覧

| シリーズ | 型式 | 動力 | 馬力 | リフト容量 | リフト高 | 最高速度 | 全幅 | 運転質量 | トランスミッション |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 200 series | AVANT 220 | Petrol | 20 hp | 350 kg | 1400 mm | 0-10 km/h | 995/1025 mm | 700 kg | - |
| 200 series | AVANT 225 | Petrol | 25 hp | 320 kg | 1,450 mm | 10 km/h | 980 mm | 720 kg | Hydrostatic |
| 400 series | AVANT 423 | Diesel | 22 hp | 550 kg | 2,751 mm | 12 km/h | 1,049 mm | 1,080 kg | Hydrostatic |
| 500 series | AVANT 523 | Diesel | 22 hp | 800 kg | 2790 mm | 0-12 km/h | 1130 mm | 1370 kg | hydrostatic Avant Optidrive® |
| 500 series | AVANT 528 | Diesel | 25 hp | 950 kg | 2,789 mm | 12 km/h | 1,140 mm | 1,420 kg | Hydrostatic, Avant Optidrive® |
| 500 series | AVANT 530 | Diesel | 25 hp | 950 kg | 2,789 mm | 19 km/h | 1,140 mm | 1,460 kg | Hydrostatic, Avant Optidrive® |
| 600 series | AVANT 635i | Diesel | 26 hp | 1,190 kg | 2,835 mm | 12 km/h | 1,290 mm | 1,610 kg | Hydrostatic Avant Optidrive® |
| 600 series | AVANT 640i | Diesel | 26 hp | 1190 kg | 2835 mm | 0-23 km/h | 1290 mm | 1580 kg | hydrostatic Avant Optidrive® |
| 600 series | AVANT 645i | Diesel | 44 hp | 1,190 kg | 2,835 mm | 12 km/h | 1,290 mm | 1,620 kg | Hydrostatic, Avant Optidrive® |
| 600 series | AVANT 650i | Diesel | 44 hp | 1,190 kg | 2,835 mm | 23 km/h | 1,290 mm | 1,630 kg | Hydrostatic, Avant Optidrive® |
| 700 series | AVANT 735i | Diesel | 26 hp | 1400 kg | 3080 mm | 0-12 km/h | 1295 mm | 1810 kg | hydrostatic Avant Optidrive® |
| 700 series | AVANT 755i | Diesel | 56 hp | 1400 kg | 3080 mm | 0-16 km/h | 1295 mm | 1970 kg | hydrostatic Avant Optidrive® |
| 700 series | AVANT 760i | Diesel | 56 hp | 1400 kg | 3100 mm | 0-26 km/h | 1450 mm | 2100 kg | hydrostatic Avant Optidrive® |
| 800 series | AVANT 855i | Diesel | 56 hp | 1900 kg | 3500 mm | 0-15 km/h | 1490 mm | 2490 kg | hydrostatic Avant Optidrive® |
| 800 series | AVANT 860i | Diesel | 56 hp | 1900 kg | 3500 mm | 0-30 km/h | 1490 mm | 2540 kg | hydrostatic Avant Optidrive® |

## 電動モデル比較

| シリーズ | 型式 | 動力 | リフト容量 | リフト高 | 最高速度 | 運転質量 | バッテリー容量 | 充電時間 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| e500 series | Avant e513 | Electric | 900 kg | 2790 mm | 10 km/h | 1420 kg | 13 kWh | - |
| e500 series | Avant e527 | Electric | 900 kg | 2790 mm | 10 km/h | 1500 kg | 27 kWh | - |
| e700 series | Avant e727 | Electric | 1400 kg | 3.1 m | 14 km/h | - | 27 kWh | - |

## シリーズ要約行

| シリーズ行 | リフト容量 | リフト高 | 最高速度 | バッテリー容量 | 充電時間 | 備考 |
| --- | --- | --- | --- | --- | --- | --- |
| AVANT e500 series | 907 kg | 2,794 mm | 10 km/h | 13-27 kWh | e513: onboard 3 kW 2h50min / rapid 400 V 16 A 1h10min; e527: onboard 3 kW 5h40min / rapid 400 V 16 A 2h20min / rapid 400 V 32 A 1h10min | e513/e527はAuxiliary pumps 1。e500 seriesは1 pumpで整理。 |
| AVANT e700 series | 1,400 kg | 3,081 mm | 14 km/h | 27 kWh | Avant e727: onboard 3 kW 5h30min; onboard 9 kW 1h50min; rapid 400 V 16 A 2h10min; rapid 400 V 32 A 1h5min | e727はAuxiliary pumps 2。e700 seriesはe727基準で2 pump整理。 |

## 分類比較

| 型式 | シリーズ | 動力区分 | 燃料 | トランスミッション | 備考 |
| --- | --- | --- | --- | --- | --- |
| AVANT 220 | 200 series | Petrol | Petrol | - | 200 series parts listで作業機側ギヤポンプを確認。 |
| AVANT 225 | 200 series | Petrol | Gasoline min RON 95 | Hydrostatic | 公式HPは流量42 L/minまで。ポンプ数は200 series parts listの構成を参考。 |
| AVANT 423 | 400 series | Diesel | Diesel | Hydrostatic | 423は1 Gear Pump 34 L/minの記載を確認。 |
| AVANT 523 | 500 series | Diesel | Diesel | hydrostatic Avant Optidrive® | 500 seriesはpump selection lever / auxiliary hydraulics pump selection switchの記載から1/2 pump切替で整理。 |
| AVANT 528 | 500 series | Diesel | Diesel | Hydrostatic, Avant Optidrive® | 500 seriesはpump selection lever / auxiliary hydraulics pump selection switchの記載から1/2 pump切替で整理。 |
| AVANT 530 | 500 series | Diesel | Diesel | Hydrostatic, Avant Optidrive® | 500 seriesはpump selection lever / auxiliary hydraulics pump selection switchの記載から1/2 pump切替で整理。 |
| AVANT 635i | 600 series | Diesel | Diesel | Hydrostatic Avant Optidrive® | 600 seriesは補助油圧2 pumpsおよび1/2 pump切替の記載を確認。 |
| AVANT 640i | 600 series | Diesel | diesel | hydrostatic Avant Optidrive® | 600 seriesは補助油圧2 pumpsおよび1/2 pump切替の記載を確認。 |
| AVANT 645i | 600 series | Diesel | Diesel | Hydrostatic, Avant Optidrive® | 645i/650iは1-pump setting / auxiliary hydraulics pump speedの記載を確認。 |
| AVANT 650i | 600 series | Diesel | Diesel | Hydrostatic, Avant Optidrive® | 645i/650iは1-pump setting / auxiliary hydraulics pump speedの記載を確認。 |
| AVANT 735i | 700 series | Diesel | diesel | hydrostatic Avant Optidrive® | 700 seriesは1-pump settingおよび2/2 pump selection部品の記載を確認。 |
| AVANT 755i | 700 series | Diesel | diesel | hydrostatic Avant Optidrive® | 700 seriesは1-pump settingおよび2/2 pump selection部品の記載を確認。 |
| AVANT 760i | 700 series | Diesel | diesel | hydrostatic Avant Optidrive® | 700 seriesは1-pump settingおよび2/2 pump selection部品の記載を確認。 |
| AVANT 855i | 800 series | Diesel | diesel | hydrostatic Avant Optidrive® | 800 seriesは1 PUMP / 2 PUMP selection switchの記載を確認。 |
| AVANT 860i | 800 series | Diesel | diesel | hydrostatic Avant Optidrive® | 800 seriesは1 PUMP / 2 PUMP selection switchの記載を確認。 |
| Avant e513 | e500 series | Electric | electric | hydrostatic Avant Optidrive® | e513はAuxiliary pumps 1。 |
| Avant e527 | e500 series | Electric | electric | hydrostatic Avant Optidrive® | e527はAuxiliary pumps 1。 |
| Avant e727 | e700 series | Electric | - | - | e727はAuxiliary pumps 2。 |

## 読み方

- HTML のレンジ図は、各項目の最小値から最大値までの間に個別型式を置いたものです。
- 速度のような `0-10 km/h` 形式は、比較用に上限値を採用しています。
- `3.1 m` のように mm 列へ m 表記が入っている値は、HTML 生成時に mm へ換算して位置合わせしています。

## Provenance

- DuckDB: `db/knowledge.duckdb`
- 参照テーブル: `avant_loader_specs_raw`
- 生成スクリプト: `scripts/build_avant_loader_comparison_artifact.py`
- 生成物: `2026-07-02-comparison-avant-loader-specs-current-db.md` / `2026-07-02-comparison-avant-loader-specs-current-db.web.html`
- 旧試作との違い: `loader_specifications_current` ではなく、現行DBに存在する raw テーブルを直接参照

## 未解決点

- 燃焼系と電動系で幅や油圧補機の記述粒度が揃っていない行があります。
- オプション / 標準 / なし を横並びにする機能比較列は、現行DBにはまだ構造化されていません。
- 電動モデルの一部は重量や充電時間の書き方に差があるため、厳密な比較用には追加の正規化が必要です。
