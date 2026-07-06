---
name: product-spec-quality-auditor
description: product-spec-normalizer が knowledge.duckdb 上に作った標準化テーブル（products / raw_specs / canonical_specs / spec_mapping / normalized_specs / normalization_issues）と比較ビューの品質を監査するときに使う。データ保全・マッピング妥当性・単位変換・欠損率・重複・要レビュー項目を read_only で点検し、100点満点のスコアと監査レポートを audit_outputs/ に出力する。監査専用であり、DB・SQL・Python・設定ファイルは一切変更しない。
---

# Product Spec Quality Auditor

`product-spec-normalizer` の成果物（標準化テーブル・ビュー）の品質を、読み取り専用で監査するスキル。

## このSkillを使う場面

- `product-spec-normalizer` の実行後、比較ビューを実務に使ってよいか判断したいとき。
- 新しい会社・製品を追加取り込みして標準化を再実行した後の品質確認（回帰監査）。
- マッピング辞書を育てた後、低confidence・混同疑いが減ったかを定点観測したいとき。
- 使わない場面: 標準化の実行・修正（それは `product-spec-normalizer` の仕事）、
  元 Excel の取り込み（`db/scripts/load_excel_raw_to_duckdb.py` の仕事）。

## 入力ファイルの前提

- 対象 DB は `db/knowledge.duckdb` 1つ。DuckDB の操作は必ず Python 経由（CLI・DBeaver 不使用）、
  接続は必ず `read_only=True`。
- 監査対象のテーブル・ビューが存在する想定:
  `products` / `raw_specs` / `canonical_specs` / `spec_mapping` / `normalized_specs` /
  `normalization_issues` / `best_normalized_specs` / `product_comparison_core_view` /
  `product_comparison_full_view`（補助: `spec_synonyms` / `spec_patterns` / `unit_conversions`）。
- **存在しないものがあっても監査は止めない。** 不足として `_run_meta.json` とレポート
  （テーブル設計の減点・第4節）に記録する。
- 参照する規約: normalizer 側の `sql/`・`docs/`（マッピング方針・confidence の付け方）。

## 監査対象

| 観点 | 主な内容 | SQL |
|---|---|---|
| データ保全 | raw 保持、元テーブル・元行・元値・元単位への追跡、normalized→raw の逆引き | sql/02 |
| テーブル設計 | 必要オブジェクト・列・識別子・source 列の有無、件数 | sql/01 |
| raw_specs品質 | 取り込み網羅性、製品整合、値/単位分離、縦持ち化、重複 | sql/03 |
| canonical_specs品質 | 比較軸の妥当性、定義欠落、未使用・会社固有・抽象的項目 | sql/04 |
| spec_mapping品質 | 未マッピング、低confidence、多重割当、意味混同の疑い（重点確認） | sql/05 |
| normalized_specs品質 | 数値・単位変換の正しさ、無理な数値化、重複、notes | sql/06 |
| comparison_view品質 | 1行1製品、重複、欠損率、重要項目の落ち | sql/07 |
| issue管理 | 要レビュー事項の記録・分類・追跡可能性、見逃し検出 | sql/08 |
| 会社別カバレッジ | 会社別の取り込み・マッピング成功率・項目の偏り | sql/09 |
| スコア入力 | 点数化に使う数値指標の一括取得 | sql/10 |

詳細な確認項目と判定基準は `docs/audit_criteria.md` を参照。

## 絶対に守る制約

- **このSkillは監査専用。** DB・SQL・Python スクリプト・設定ファイル・normalizer の成果物を変更しない。
- DB への接続は常に `duckdb.connect(db, read_only=True)`。書き込み系 API は使わない。
- 書き込んでよいのは `audit_outputs/` 配下の新規ファイルのみ。
- 修正案は出してよいが、実際の修正は行わない（修正は `product-spec-normalizer` 側の作業）。
- `run_audit.py` は SELECT 系以外の SQL 文を実行前にブロックする。監査 SQL を書き足す場合も
  SELECT / WITH / SUMMARIZE / DESCRIBE / PRAGMA 以外を書いてはならない。

## 実行手順

```powershell
# 1. SQL 監査を read_only で全実行（audit_outputs/raw/ に CSV、sql_audit_results.md を出力）
python .github/skills/product-spec-quality-auditor/scripts/run_audit.py

# 2. スコアリングとレポート生成（quality_audit_report.md / audit_summary.csv）
python .github/skills/product-spec-quality-auditor/scripts/generate_audit_report.py

# 3. 人間レビュー用の指摘 CSV を出力（suspicious_mappings.csv ほか）
python .github/skills/product-spec-quality-auditor/scripts/export_audit_findings.py
```

その後、必ず意味的レビューを行う:

4. `audit_outputs/suspicious_mappings.csv` と `docs/review_checklist.md` を使い、
   混同疑い・低confidence・高欠損項目を確認する（エージェントが行う場合は
   canonical_definitions と raw 項目名を突き合わせて判断し、根拠をレポートに書く）。
5. レビュー結果を `quality_audit_report.md` の第8・10・12節に反映する。
   点数の補正は下方修正のみ（`docs/score_rubric.md` の原則）。

DB パスや出力先を変える場合は各スクリプトの `--db` / `--out-dir` を使う。

## SQL監査項目

sql/01〜10 が「-- AUDIT: <名前>」単位で以下を出力する（1ブロック = 1 CSV）。

- テーブル一覧・期待オブジェクトの存在・各テーブルの件数・列定義（01）
- source 情報欠落件数、normalized→raw の追跡可否、未取り込み元テーブル（02）
- product数と raw_specs の整合、会社別 raw_item_name 数、値/単位分離漏れ、重複（03）
- canonical 定義全件、定義欠落、未使用・会社固有・抽象名候補、canonical_item別製品カバー率（04）
- raw_specs の未マッピング件数と割合、confidence 0.7 / 0.5 未満件数、多重割当、
  mapping_method別件数、manual_required件数、confidence過大評価候補、
  重点確認（重量・定格/最大・消費電力・寸法・規格/認証・オプション・温度の混同疑い）、
  company別マッピング成功率（05）
- normalized_unit と canonical_unit の不一致件数、numeric なのに数値化できていない件数、
  変換係数の一貫性、同一product×canonical の重複件数、notes 欠落（06）
- comparison_view の製品数・重複・主要列ごとの欠損率（SUMMARIZE）・priority1 カバー（07）
- issue の分類・追跡可能性・低confidence/未マッピングの issue 見逃し（08）
- company別カバレッジ、1社しか持たない項目、会社別の priority1 欠落（09）
- スコア入力指標（metric / value 縦持ち）（10）

## Python監査項目

| スクリプト | 役割 |
|---|---|
| `scripts/run_audit.py` | `knowledge.duckdb` に read_only 接続し、sql/01〜10 を順に実行。結果を `audit_outputs/raw/*.csv`（UTF-8 BOM 付き）と `audit_outputs/sql_audit_results.md` に保存。オブジェクト不足・エラーは `_run_meta.json` に記録。非 SELECT 文はブロック。DB は変更しない |
| `scripts/generate_audit_report.py` | SQL 結果（CSV）を読み込み、`docs/score_rubric.md` の基準で 100 点満点に点数化。問題を重大/中程度/軽微に分類し、`quality_audit_report.md` と `audit_summary.csv` を生成。DB には接続しない |
| `scripts/export_audit_findings.py` | 人間レビューが必要な項目・怪しいマッピング・高欠損項目・重複/単位不整合/低confidence を `audit_outputs/` 直下の CSV に出力。DB には接続しない |

## スコアリング基準

100点満点。90以上=実務利用可能 / 75〜89=軽微な修正後に利用可能 / 60〜74=レビュー前提で限定利用 /
40〜59=設計または実装の見直しが必要 / 39以下=作り直し推奨。

| 評価項目 | 配点 |
|---|---:|
| データ保全 | 15 |
| テーブル設計 | 10 |
| raw_specs品質 | 10 |
| canonical_specs品質 | 10 |
| spec_mapping品質 | 20 |
| normalized_specs品質 | 15 |
| comparison_view品質 | 10 |
| issue管理 | 5 |
| 運用しやすさ | 5 |

spec_mapping と normalized_specs は特に厳しく評価する。意味が違う項目を同じ canonical_item に
統合している可能性がある場合（risky_group_merges 検出、またはレビューで確認）は大きく減点する。
減点規則の全文は `docs/score_rubric.md`。

## レポート出力形式

`audit_outputs/quality_audit_report.md` は次の 12 節構成（generate_audit_report.py が生成）:

1. 総合評価（総合点・判定・主な理由） 2. 評価サマリー表 3. 良い点 4. 重大な問題
5. 中程度の問題 6. 軽微な問題 7. 数値チェック結果 8. 怪しいマッピング例
9. 欠損率が高い比較項目 10. 今すぐ人間が確認すべき項目 11. 修正方針 12. 判定

その他の出力（すべて `audit_outputs/` 配下）:

```text
audit_outputs/
  quality_audit_report.md        最終レポート
  audit_summary.csv              カテゴリ別スコア
  suspicious_mappings.csv        怪しいマッピング（混同疑い候補）
  low_confidence_mappings.csv    confidence<0.7 のマッピング
  unmapped_raw_items.csv         未マッピング項目
  duplicate_canonical_items.csv  同一製品×項目の重複
  unit_mismatches.csv            単位不整合
  comparison_missing_rates.csv   比較ビュー列別欠損率
  company_coverage.csv           会社別カバレッジ
  human_review_required.csv      要レビュー項目の統合リスト
  sql_audit_results.md           SQL 監査の生結果（Markdown）
  raw/                           全 AUDIT ブロックの CSV と _run_meta.json
```

## 人間レビューが必要なケース

`docs/review_checklist.md` に手順がある。特に:

- suspicious_mappings.csv の全件（重量種別・定格/最大・消費電力・寸法分解・規格/認証・
  オプション/標準・使用/保管温度の混同疑い）
- confidence<0.5 のマッピング全件、<0.7 の抜き取り確認
- 同一製品×canonical_item で値が食い違う組の採用値
- 単位不整合行と、不足している変換ルールの判断
- 高欠損の比較列を「残す/priorityを下げる/取り込みを増やす」のどれにするか
- normalization_issues の open 全件と、issue 見逃し（low_confidence_not_issued / unmapped_not_issued）

## 禁止事項

- 既存DBを変更しない（接続は常に read_only。CREATE/INSERT/UPDATE/DELETE/DROP を書かない・実行しない）
- 既存テーブルを上書きしない
- 監査中に標準化結果を修正しない
- マッピングを勝手に補正しない（誤りを見つけても指摘に留める）
- 欠損値を補完しない
- 仕様書にない情報を追加しない
- 問題を隠すためにビューやテーブルを再生成しない
- 根拠のない「問題なし」を書かない（0件を確認した AUDIT ブロック名を必ず添える）

## 関連ドキュメント

- `docs/audit_criteria.md` — 監査観点と AUDIT ブロックの対応・判定基準
- `docs/score_rubric.md` — 減点規則の全文と人間/エージェント補正の原則
- `docs/review_checklist.md` — 監査後の人間レビュー手順
- `.github/skills/product-spec-normalizer/SKILL.md` — 監査対象を作った側の仕様（修正はこちらで行う）
