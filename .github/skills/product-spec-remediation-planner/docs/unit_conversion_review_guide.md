# 単位変換レビューガイド（unit_mismatches）

## 6分類の基準

### `missing_conversion_rule` — 変換ルールが不足しているだけ

- 単位の別表記・同義（`km/hr.` → `km/h`、`kmh` → `km/h`）: 実質エイリアス。最も安全
- 既知の確定換算（`hp` → `kW` ×0.7457、`in3` → `cc` ×16.387、`L` → `cc` ×1000）
- → `unit_rule_candidates.csv` に conversion_rule（係数または alias）付きで載せる
- 換算係数に複数流儀があるもの（PS/hp の別、米ガロン/英ガロン）は係数を明記し人間確認必須

### `wrong_canonical_unit` — canonical 側の単位設計が実態に合わない

- ほぼ全社が別単位で公表している（例: canonical が kWh だが全社 Ah 表記）
- → canonical_unit の変更案。既存 normalized 値への影響範囲を必ず添える

### `wrong_raw_unit_extraction` — 元値からの単位切り出しが誤り

- original_unit が値の一部を巻き込んでいる、複合表記の誤分解（`hp (kW)` など）
- → 修正は変換ルールではなく抽出ロジック側（raw_specs / normalize 処理）

### `not_convertible` — 原理的に一意換算できない

- 追加情報なしに換算できない（`Ah / 48V` → kWh は電圧を掛ける必要があり、
  電圧が値に含まれる場合のみ計算可能。ルール化は複合パースが前提）
- → `conversion_blocklist_candidates.csv` へ。テキスト保持を正式な扱いにする

### `value_contains_condition` — 値に条件が付いていて数値化できない

- `62 Nm @ 1600 rpm`、レンジ表記 `12-14`、複数値 `2740/2820` など
- → 数値化しない/条件ごと保持/代表値抽出のどれにするかは人間判断。
  代表値抽出を提案する場合は規則（最小値? 定格側?）を明記する

### `manual_review_required` — 上記で判断できない

- 迷っている理由を必ず書く

## 変換ルールを追加してよいもの / 変換禁止にすべきもの

**追加してよい（候補に載せる）**: 物理的に一意な換算。単位エイリアス。
係数が一意に定まり、値が単独の数値であるもの。

**変換禁止（blocklist 候補）にすべき**:

- 複合単位で追加情報が要る（Ah/48V）
- 値に条件・レンジが含まれ、換算すると意味が変わる
- 同じ表記で複数の意味がありうる単位（トン: t/ st / lt など、文脈で係数が変わる）
- 換算式が「曖昧」なもの全般。**曖昧なものを確定しない**のが原則

blocklist は「変換しない」ことの明示的な記録であり、放置とは違う。
比較ビューではテキスト保持列または対象外として扱う。

## unit_rule_candidates.csv の書き方

| 列 | 内容 |
|---|---|
| `review_id` | 由来の UNI- 行 |
| `canonical_item` | 対象項目 |
| `original_unit` / `target_unit` | 変換元 → 変換先 |
| `conversion_rule` | `alias`（表記ゆれ）または `multiply:<係数>` |
| `affected_count` | 影響行数 |
| `confidence` | 係数の確からしさ |

conversion_rule が書けない（式にできない）ものはこのCSVに載せず blocklist 候補へ。
