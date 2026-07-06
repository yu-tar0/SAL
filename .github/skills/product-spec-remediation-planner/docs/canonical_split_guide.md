# canonical_item 分割判断ガイド

risky_group_merges / duplicate_canonical_items から canonical_item の分割案（SPL- 行）を
作るときの基準。分割の確定は人間の `split_canonical` 判断のみで行う。

## 分割する / しないの原則

**分割する**: 測定条件・測定対象・意味が違う値が同じ canonical_item に入っているとき。
同じ列に混ざると製品間比較が成立しない。

**分割しない**: 同じ量の表記ゆれ（言語・記法・略称の違い）。
これはマッピング（synonym）側で1つの canonical_item に寄せるのが正しい。

判断に迷う質問: 「この2つの値を同じ表の同じ列に並べて、製品Aと製品Bを比較してよいか？」
No なら分割。Yes なら表記ゆれ。

## 重点確認する群と典型的な分割案

| 群 | 混同の内容 | 分割案の例 |
|---|---|---|
| 重量系 | 本体重量・キャブ付き重量・キャノピー重量・梱包/輸送重量・カウンタウェイト込み | `operating_weight` → `operating_weight_cab` / `operating_weight_canopy` / `shipping_weight` |
| 定格/最大系 | 定格値・最大値・標準値・平均値・ピーク値 | `engine_power` → `engine_power_rated` / `engine_power_max` |
| 消費電力系 | 消費電力・最大消費電力・待機電力 | `power_consumption` → `power_consumption_rated` / `power_consumption_max` / `power_consumption_standby` |
| 寸法系 | 幅・高さ・奥行と「外形寸法(W×D×H複合値)」の混在、ヒンジピン高さと全高 | `overall_height` → `overall_height` / `height_to_hinge_pin`。複合寸法は分解を指示 |
| 規格/認証系 | 準拠(compliant)・取得認証(certified)・対応規格(supported) | `standards` → `standards_compliant` / `certifications` |
| オプション系 | 標準装備の値とオプション装着時の値 | `aux_hydraulic_flow` → `aux_hydraulic_flow` / `aux_hydraulic_flow_optional` |
| 温度系 | 使用温度と保管温度 | `operating_temp` → `operating_temp` / `storage_temp` |

## 分割を疑うシグナル

- raw_item_name に条件語が含まれる: cab / canopy / 梱包 / shipping / transport / max / 最大 /
  rated / 定格 / peak / standby / 待機 / optional / オプション / storage / 保管 / hinge / with / without
- 同一製品×canonical_item の重複で、値が系統的に2グループに分かれる（例: 常に大小ペア）
- 同一 canonical_item 内で会社ごとに値のレンジが不自然に乖離する

## 分割案（SPL- 行）の必須要素

分割案は必ず次をセットで書く。振り分け先が書けない分割案は不完全であり出さない。

- `current_canonical_item`: 現在の項目
- `new_canonical_item`: 新設する項目（既存の命名規約に合わせた snake_case）
- 分割理由: どの意味が混ざっているか
- 対象 raw_item_name: どの raw 項目がどちらへ行くか（全振り分け先を列挙）
- confidence と、AIが迷っている点

## 分割後の後処理（normalizer への指示に含める）

- `canonical_specs` への新項目追加（display_name_ja / category / canonical_unit / value_type）
- `spec_mapping_v2` での振り替え（旧項目に残す raw と新項目へ移す raw の明示）
- 比較ビュー `_v2` への列追加と priority 設定
- 分割で片側が高欠損になる場合は、その旨と「それでも分割すべき理由」を明記
  （欠損よりも誤比較の方が害が大きい）
