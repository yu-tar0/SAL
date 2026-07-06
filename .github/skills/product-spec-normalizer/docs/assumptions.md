# 初期構築の仮定とスコープ（2026-07 時点の knowledge.duckdb に対して）

このスキルの sql/03（取り込み）と sql/04（辞書）は、調査時点の 155 テーブル・7社
（Avant / Bobcat / Case / Gianni Ferrari / GIANT / MultiOne / Yanmar）に合わせて書かれている。
以下は初期構築で置いた仮定。誤りが見つかったら該当 SQL と一緒にこのファイルも更新する。

## データ構造の認識

| 会社 | 形状 | 単位系 | 備考 |
|---|---|---|---|
| Avant | 縦持ち(仕様一覧) + 横持ち(型式一覧/旧型モデル) | metric | 縦横で内容が重複 → 縦持ちを rank1、横持ちを rank2 |
| Bobcat | 項目行 × 製品列(L23/L28/L35) × US/メートル併記 | 両方 | "1534\n Ext 888" のような複合値あり |
| Case | 型式別シート(仕様/寸法/転倒荷重, US+メートル列) + カタログ集約 | 両方 | カタログは 'US値 (メートル値)' 併記 → rank3 |
| Gianni Ferrari | 縦持ち(M280 / H440-2s) | metric | 'Length / Width / Height' の複合項目あり |
| GIANT | 縦持ち仕様比較 ×12ファイル + 型式分類一覧 | us | ファイル間で行が完全重複 → 取り込み時に排除 |
| MultiOne | 縦持ち ×3系統の列構成(標準9機種 / 11.x / EZ) | 両方 | EZ8 と EZ8 Long Range が1テーブルに同居 |
| Yanmar | 縦持ち(CL26のみ) | us | 記事由来のプロトタイプ仕様 |

## 主な仮定（要レビュー）

1. **product_id**: `会社キー:型式の正規化形`（例 `case:sl12_tr`）。GIANT の '(Wheels)' 等の括弧は
   製品名から除いて同一製品とみなす。'G2700 HD+' は 'g2700_hdplus' として HD と区別。
2. **Case TR モデル** は Telescopic Reach 仕様とみなし telescopic='あり' とした。
3. **MultiOne EZ8 テーブル**の 'EZ 8 / EZ 8 Long Range' 共通行は両製品に複製した
   （raw_notes に複製元を記録）。
4. **カタログ併記 'US値 (メートル値)'** は括弧内=メートル系と解釈（単位列 'lb (kg)' の表記に基づく）。
   メートル値の空白千位区切り（'1 100'）は除去して数値化。
5. **運転質量はオープンキャブ/ROPS 仕様を標準**とみなす（Case 'Open Cab'、Gianni 'with ROPS'）。
   キャブ付は operating_weight_enclosed に分離。
6. **速度レンジがある機種は高速側を最高速度**とみなす（Bobcat High Range、Case Rabbit、
   MultiOne high、GIANT high）。inferred 0.65–0.7 でレビュー対象。
7. **GIANT 'Working hydraulics'（GPM）** は補助油圧流量に相当すると推定（inferred 0.6）。
8. **GIANT 'Engine'（hp 数値のみ）** はエンジン出力と解釈（unit_based 0.75）。
9. **'battery capacity' は単位で判別**: kWh→走行用 battery_capacity、Ah→補機 starter_battery_capacity。
   GIANT の 'Ah / 48V' は kWh への導出をせずテキスト保持（issue に記録）。
10. **転倒荷重**: 直進/屈曲の明記がない GIANT/Yanmar/MultiOne は `tipping_load`（条件不明）として
    `tipping_load_straight` と別項目で比較する。
11. **hp→kW は機械馬力 0.7457** を使用。メーカーが PS（メートル馬力）表記の可能性があれば cv ルールを使う。
12. **Avant '出力規格'**（'14.9 kW (20 hp)'）から kW を採用し、'馬力/出力'（hp）より confidence を高く設定。
    同一製品で engine_power が2系統出るのは想定内（採用は kW 側）。

## v1 スコープ外（raw_specs に取り込んでいないもの）

- 装備・オプション・特徴系: `case_*_装備`, `multione_*_オプション・特徴`, Bobcat の
  MACHINE FEATURES / SAFETY EQUIPMENT / FEATURES FOR ATTACHMENTS セクション, Case カタログの FEATURES 行
- 注記・原文・概要（定性情報）: `*_注記*`, `*_原文`, `*_概要`（products の属性としてのみ利用）
- アタッチメント関連: `gianni_*_アタッチメント*`, `giant_*_タイヤ・アタッチメント`, `multione_wheels_*`
- タイヤ別寸法: MultiOne の タイヤサイズ別寸法/タイヤ別寸法/タイヤ寸法 区分
- マーケ用サマリー: MultiOne サマリー表示/カード表示/カタログ概要（丸め値の重複でノイズになるため）
- `avant_型式_仕様一覧_油圧システム`（型式一覧と重複）
- `giant_型式分類一覧_分類メモ`, Case 転倒荷重の記号別詳細（記号の意味が資料にないため manual）

これらは normalization_issues に issue_type='scope_excluded' として記録される。
装備・オプションを比較したくなったら、canonical に boolean 項目群を設計してから対象に加える。

## 既知の残課題

- Bobcat の "標準 / Ext(延長)" 複合値は数値化していない（numeric_parse_failed として一覧化）。
- Gianni 'Length / Width / Height with ROPS/CAB' は3寸法の複合値のため manual のまま。
- Case 転倒荷重シート（TIPPING LOADS / 記号 A..）は記号の定義が無いため manual のまま。
- Yanmar は記事由来のプロトタイプ値であり、確定仕様ではない（products.notes に記載）。
- GIANT の g1200 と g1200_tele、g5000 と g5000_tele のファイルは同一内容の重複。取り込み時に
  完全一致行を排除しているが、値が更新されて食い違った場合は duplicate_values チェックに現れる。
