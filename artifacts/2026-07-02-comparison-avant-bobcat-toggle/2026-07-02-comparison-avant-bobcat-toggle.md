---
title: マルチブランド ローダー比較 切替ビュー
created: 2026-07-02
updated: 2026-07-02
type: artifact
status: current-db
input:
  - db/knowledge.duckdb
  - table: loader_specification_import_rows
outputs:
  - artifacts/2026-07-02-comparison-avant-bobcat-toggle/2026-07-02-comparison-avant-bobcat-toggle.md
  - artifacts/2026-07-02-comparison-avant-bobcat-toggle/2026-07-02-comparison-avant-bobcat-toggle.web.html
purpose: 共通 curated テーブルから複数ブランドを選択式で切り替え表示できる Web HTML を作る
---

# マルチブランド ローダー比較 切替ビュー

共通 curated テーブル `loader_specification_import_rows` を入力元に、複数ブランドの表示をボタンで切り替えられる Web Artifact を作成した。既存の AVANT 単独 HTML のレイアウトを踏襲しつつ、ブランド単位で比較レンジ、型式一覧、分類比較をまとめている。

## 要約

- 対象の個別型式は合計 82 行。
- AVANT: AVANT の個別型式 18 行を共通 schema で比較できるようにした。 電動モデル 3 行も同じページ内で切り替えて確認できる。 シリーズは 200 series, 400 series, 500 series, e500 series, 600 series, 700 series, e700 series, 800 series を含む。
- Bobcat: Bobcat の個別型式 3 行を共通 schema で比較できるようにした。 現時点では電動モデル行はなく、すべて燃焼系またはエンジン系として載っている。 シリーズは Small Articulated Loaders を含む。
- Case: Case の個別型式 9 行を共通 schema で比較できるようにした。 現時点では電動モデル行はなく、すべて燃焼系またはエンジン系として載っている。 シリーズは Small Articulated Loaders を含む。
- Gianni Ferrari: Gianni Ferrari の個別型式 2 行を共通 schema で比較できるようにした。 現時点では電動モデル行はなく、すべて燃焼系またはエンジン系として載っている。 シリーズは Turboloader H Series, Turboloader M Series を含む。
- Giant: Giant の個別型式 23 行を共通 schema で比較できるようにした。 現時点では電動モデル行はなく、すべて燃焼系またはエンジン系として載っている。 シリーズは G1200, G1500 Series, G2200E Series, G2300 Series, G2500 Series, G2700 Series, G2700 TELE Series, G2700E Series, G3500 Series, G5000 Series, G5000 TELE Series を含む。
- MultiOne: MultiOne の個別型式 17 行を共通 schema で比較できるようにした。 現時点では電動モデル行はなく、すべて燃焼系またはエンジン系として載っている。 シリーズは 1 Series, 2 Series, 5 Series, 6 Series, 7 Series, 8 Series, 11 Series, EZ Series を含む。
- New Holland: New Holland の個別型式 9 行を共通 schema で比較できるようにした。 現時点では電動モデル行はなく、すべて燃焼系またはエンジン系として載っている。 シリーズは Small Articulated Loaders を含む。
- Yanmar: Yanmar の個別型式 1 行を共通 schema で比較できるようにした。 現時点では電動モデル行はなく、すべて燃焼系またはエンジン系として載っている。 シリーズは Compact Wheel Loaders を含む。

## Provenance

- DuckDB: `db/knowledge.duckdb`
- 参照テーブル: `loader_specification_import_rows`
- 生成スクリプト: `scripts/build_loader_brand_toggle_artifact.py`
- 生成物: `2026-07-02-comparison-avant-bobcat-toggle.md` / `2026-07-02-comparison-avant-bobcat-toggle.web.html`

## 未解決点

- ブランド間で保有列は揃っていても、実際に埋まっている項目数は異なる。
- 電動モデルやシリーズ要約は現状 AVANT 側に偏っている。
- 機能フラグやオプション差分はまだ構造化していない。
