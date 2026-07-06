---
title: マルチブランド ローダー比較 同一数値バー版
created: 2026-07-02
updated: 2026-07-02
type: artifact
status: current-db
input:
  - db/knowledge.duckdb
  - table: loader_specification_import_rows
outputs:
  - artifacts/2026-07-02-comparison-avant-bobcat-shared-bars/2026-07-02-comparison-avant-bobcat-shared-bars.md
  - artifacts/2026-07-02-comparison-avant-bobcat-shared-bars/2026-07-02-comparison-avant-bobcat-shared-bars.web.html
purpose: 複数ブランドの個別型式を同じ数値バー上に重ねて比較できる Web HTML を作る
---

# マルチブランド ローダー比較 同一数値バー版

共通 curated テーブル `loader_specification_import_rows` を入力元に、複数ブランドの個別型式を同一レンジバー上へ重ねて比較できる Web Artifact を作成した。ブランド色でマーカーを分け、表示オンオフで見比べられる。

## 要約

- 比較対象の個別型式は合計 82 行。登録済みブランドを同一数値バー上で比較できる。
- 最大リフト容量は Giant の G5000 X-TRA で、値は 転倒荷重 4,468 kg。
- 最高速度は New Holland の ML50 Telescopic で、値は Turtle-Low 6.7 km/h / Rabbit-Low 30 km/h / Turtle-High 13.1 km/h / Rabbit-High 34.7 km/h。
- HTML では同一数値バー上に複数ブランドの型式を重ね、ブランドごとの表示オンオフと SI / US 切替を共通で使える。

## Provenance

- DuckDB: `db/knowledge.duckdb`
- 参照テーブル: `loader_specification_import_rows`
- 生成スクリプト: `scripts/build_loader_brand_overlay_artifact.py`
- 生成物: `2026-07-02-comparison-avant-bobcat-shared-bars.md` / `2026-07-02-comparison-avant-bobcat-shared-bars.web.html`

## シリーズ要約行

| ブランド | シリーズ行 | リフト容量 | リフト高 | 最高速度 | バッテリー容量 | 充電時間 |
| --- | --- | --- | --- | --- | --- | --- |
| AVANT | AVANT e500 series | 907 kg | 2,794 mm | 10 km/h | 13-27 kWh | e513: onboard 3 kW 2h50min / rapid 400 V 16 A 1h10min; e527: onboard 3 kW 5h40min / rapid 400 V 16 A 2h20min / rapid 400 V 32 A 1h10min |
| AVANT | AVANT e700 series | 1,400 kg | 3,081 mm | 14 km/h | 27 kWh | Avant e727: onboard 3 kW 5h30min; onboard 9 kW 1h50min; rapid 400 V 16 A 2h10min; rapid 400 V 32 A 1h5min |

## 未解決点

- ブランドごとに埋まっている列の密度は異なる。
- Bobcat の一部は容量列に複数条件の値が混在しており、比較上は記載文字列をそのまま残している。
- 電動モデルやシリーズ要約は現状 AVANT 側に偏っている。
