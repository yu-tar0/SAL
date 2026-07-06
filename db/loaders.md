# 入力ファイルとローダーの対応

`db/knowledge.duckdb` への取り込み元と使用ローダーの対応表。取り込み履歴の詳細は DB 内の `excel_imports` テーブルで確認できる。

| 入力ファイル | ローダー | テーブル | 取り込み日 |
|---|---|---|---|
| `raw/inbox/CASE_SAL/Case_SL12_仕様項目一覧.xlsx` | `db/scripts/load_excel_raw_to_duckdb.py` | `case_sl12_仕様項目一覧_{概要,仕様,寸法,転倒荷重,装備,注記}` | 2026-07-04 |
| `raw/inbox/CASE/Case_SAL_catalog_specs_with_features_revised.xlsx` | `db/scripts/load_excel_raw_to_duckdb.py` | `case_sal_catalog_specs_with_features_revised_Case_SALカタログ` | 2026-07-05 |
| `raw/inbox/CASE/Case_SL12TR_仕様項目一覧.xlsx` | `db/scripts/load_excel_raw_to_duckdb.py` | `case_sl12tr_仕様項目一覧_{概要,仕様,寸法,転倒荷重,装備,注記}` | 2026-07-05 |
| `raw/inbox/CASE/Case_SL15_仕様項目一覧.xlsx` | `db/scripts/load_excel_raw_to_duckdb.py` | `case_sl15_仕様項目一覧_{概要,仕様,寸法,転倒荷重,装備,注記}` | 2026-07-05 |
| `raw/inbox/CASE/Case_SL22EV_仕様項目一覧.xlsx` | `db/scripts/load_excel_raw_to_duckdb.py` | `case_sl22ev_仕様項目一覧_{概要,仕様,寸法,転倒荷重,装備,注記}` | 2026-07-05 |
| `raw/inbox/CASE/Case_SL23_仕様項目一覧.xlsx` | `db/scripts/load_excel_raw_to_duckdb.py` | `case_sl23_仕様項目一覧_{概要,仕様,寸法,転倒荷重,装備,注記}` | 2026-07-05 |
| `raw/inbox/CASE/Case_SL27TR_仕様項目一覧.xlsx` | `db/scripts/load_excel_raw_to_duckdb.py` | `case_sl27tr_仕様項目一覧_{概要,仕様,寸法,転倒荷重,装備,注記}` | 2026-07-05 |
| `raw/inbox/CASE/Case_SL27_仕様項目一覧.xlsx` | `db/scripts/load_excel_raw_to_duckdb.py` | `case_sl27_仕様項目一覧_{概要,仕様,寸法,転倒荷重,装備,注記}` | 2026-07-05 |
| `raw/inbox/CASE/Case_SL35TR_仕様項目一覧.xlsx` | `db/scripts/load_excel_raw_to_duckdb.py` | `case_sl35tr_仕様項目一覧_{概要,仕様,寸法,転倒荷重,装備,注記}` | 2026-07-05 |
| `raw/inbox/CASE/Case_SL50TR_仕様項目一覧.xlsx` | `db/scripts/load_excel_raw_to_duckdb.py` | `case_sl50tr_仕様項目一覧_{概要,仕様,寸法,転倒荷重,装備,注記}` | 2026-07-05 |
| `raw/inbox/AVANT/AVANT_型式_仕様一覧.xlsx` | `db/scripts/load_excel_raw_to_duckdb.py` | `avant_型式_仕様一覧_{型式一覧,仕様一覧,油圧システム,旧型モデル}` | 2026-07-05 |
| `raw/inbox/GIanniFerrari/Gianni_Ferrari_Turboloader_仕様一覧.xlsx` | `db/scripts/load_excel_raw_to_duckdb.py` | `gianni_ferrari_turboloader_仕様一覧_{概要,仕様一覧,機能説明,アタッチメント一覧,アタッチメント仕様,荷重図メモ}` | 2026-07-05 |
| `raw/inbox/GIANT/Giant_G1200_TELE_仕様一覧.xlsx` | `db/scripts/load_excel_raw_to_duckdb.py` | `giant_g1200_tele_仕様一覧_{概要,仕様比較,タイヤ・アタッチメント}` | 2026-07-05 |
| `raw/inbox/GIANT/Giant_G1200_仕様一覧.xlsx` | `db/scripts/load_excel_raw_to_duckdb.py` | `giant_g1200_仕様一覧_{概要,仕様比較,タイヤ・アタッチメント}` | 2026-07-05 |
| `raw/inbox/GIANT/Giant_G1500_Series_仕様一覧.xlsx` | `db/scripts/load_excel_raw_to_duckdb.py` | `giant_g1500_series_仕様一覧_{概要,仕様比較,タイヤ・アタッチメント}` | 2026-07-05 |
| `raw/inbox/GIANT/Giant_G2200E_Series_仕様一覧.xlsx` | `db/scripts/load_excel_raw_to_duckdb.py` | `giant_g2200e_series_仕様一覧_{概要,仕様比較,タイヤ・アタッチメント}` | 2026-07-05 |
| `raw/inbox/GIANT/Giant_G2300_HD_仕様一覧.xlsx` | `db/scripts/load_excel_raw_to_duckdb.py` | `giant_g2300_hd_仕様一覧_{概要,仕様比較,タイヤ・アタッチメント}` | 2026-07-05 |
| `raw/inbox/GIANT/Giant_G2500_Series_仕様一覧.xlsx` | `db/scripts/load_excel_raw_to_duckdb.py` | `giant_g2500_series_仕様一覧_{概要,仕様比較,タイヤ・アタッチメント}` | 2026-07-05 |
| `raw/inbox/GIANT/Giant_G2700_Series_仕様一覧.xlsx` | `db/scripts/load_excel_raw_to_duckdb.py` | `giant_g2700_series_仕様一覧_{概要,仕様比較,タイヤ・アタッチメント}` | 2026-07-05 |
| `raw/inbox/GIANT/Giant_G3500_Series_仕様一覧.xlsx` | `db/scripts/load_excel_raw_to_duckdb.py` | `giant_g3500_series_仕様一覧_{概要,仕様比較,タイヤ・アタッチメント,原文}` | 2026-07-05 |
| `raw/inbox/GIANT/Giant_G5000_Series_仕様一覧.xlsx` | `db/scripts/load_excel_raw_to_duckdb.py` | `giant_g5000_series_仕様一覧_{概要,仕様比較,タイヤ・アタッチメント,原文}` | 2026-07-05 |
| `raw/inbox/GIANT/Giant_G5000_TELE_Series_仕様一覧.xlsx` | `db/scripts/load_excel_raw_to_duckdb.py` | `giant_g5000_tele_series_仕様一覧_{概要,仕様比較,タイヤ・アタッチメント,原文}` | 2026-07-05 |
| `raw/inbox/GIANT/Giant_GS_Series_仕様一覧.xlsx` | `db/scripts/load_excel_raw_to_duckdb.py` | `giant_gs_series_仕様一覧_{概要,仕様比較,タイヤ・アタッチメント}` | 2026-07-05 |
| `raw/inbox/GIANT/Giant_GT5048_Series_仕様一覧.xlsx` | `db/scripts/load_excel_raw_to_duckdb.py` | `giant_gt5048_series_仕様一覧_{概要,仕様比較,タイヤ・アタッチメント,原文}` | 2026-07-05 |
| `raw/inbox/GIANT/GIANT_型式分類一覧.xlsx` | `db/scripts/load_excel_raw_to_duckdb.py` | `giant_型式分類一覧_{GIANT型式分類,分類メモ}` | 2026-07-05 |
| `raw/inbox/MultiOne/MultiOne_1_1_仕様一覧.xlsx` | `db/scripts/load_excel_raw_to_duckdb.py` | `multione_1_1_仕様一覧_{仕様一覧,オプション・特徴,注記・原文}` | 2026-07-05 |
| `raw/inbox/MultiOne/MultiOne_2_3_EFI_仕様一覧.xlsx` | `db/scripts/load_excel_raw_to_duckdb.py` | `multione_2_3_efi_仕様一覧_{仕様一覧,オプション・特徴,注記・原文}` | 2026-07-05 |
| `raw/inbox/MultiOne/MultiOne_5_2_K_iD_仕様一覧.xlsx` | `db/scripts/load_excel_raw_to_duckdb.py` | `multione_5_2_k_id_仕様一覧_{仕様一覧,オプション・特徴,注記・原文}` | 2026-07-05 |
| `raw/inbox/MultiOne/MultiOne_5_3_K_iD_仕様一覧.xlsx` | `db/scripts/load_excel_raw_to_duckdb.py` | `multione_5_3_k_id_仕様一覧_{仕様一覧,オプション・特徴,注記・原文}` | 2026-07-05 |
| `raw/inbox/MultiOne/MultiOne_6_3_iDS_仕様一覧.xlsx` | `db/scripts/load_excel_raw_to_duckdb.py` | `multione_6_3_ids_仕様一覧_{仕様一覧,オプション・特徴,注記・原文}` | 2026-07-05 |
| `raw/inbox/MultiOne/MultiOne_7_2_K_仕様一覧.xlsx` | `db/scripts/load_excel_raw_to_duckdb.py` | `multione_7_2_k_仕様一覧_{仕様一覧,オプション・特徴,注記・原文}` | 2026-07-05 |
| `raw/inbox/MultiOne/MultiOne_8_4_TurboS_仕様一覧.xlsx` | `db/scripts/load_excel_raw_to_duckdb.py` | `multione_8_4_turbos_仕様一覧_{仕様一覧,オプション・特徴,注記・原文}` | 2026-07-05 |
| `raw/inbox/MultiOne/MultiOne_8_5_Y_仕様一覧.xlsx` | `db/scripts/load_excel_raw_to_duckdb.py` | `multione_8_5_y_仕様一覧_{仕様一覧,オプション・特徴,注記・原文}` | 2026-07-05 |
| `raw/inbox/MultiOne/MultiOne_8_5S_K_仕様一覧.xlsx` | `db/scripts/load_excel_raw_to_duckdb.py` | `multione_8_5s_k_仕様一覧_{仕様一覧,オプション・特徴,注記・原文}` | 2026-07-05 |
| `raw/inbox/MultiOne/MultiOne_11_5_Y_仕様一覧.xlsx` | `db/scripts/load_excel_raw_to_duckdb.py` | `multione_11_5_y_仕様一覧_{仕様一覧,オプション・特徴,注記・原文}` | 2026-07-05 |
| `raw/inbox/MultiOne/MultiOne_11_6_K_TurboS_仕様一覧.xlsx` | `db/scripts/load_excel_raw_to_duckdb.py` | `multione_11_6_k_turbos_仕様一覧_{仕様一覧,オプション・特徴,注記・原文}` | 2026-07-05 |
| `raw/inbox/MultiOne/MultiOne_EZ7_仕様一覧.xlsx` | `db/scripts/load_excel_raw_to_duckdb.py` | `multione_ez7_仕様一覧_{仕様一覧,オプション・特徴,注記・原文}` | 2026-07-05 |
| `raw/inbox/MultiOne/MultiOne_EZ8_EZ8_Long_Range_仕様一覧.xlsx` | `db/scripts/load_excel_raw_to_duckdb.py` | `multione_ez8_ez8_long_range_仕様一覧_{仕様一覧,オプション・特徴,注記・原文}` | 2026-07-05 |
| `raw/inbox/MultiOne/MultiOne_WHEELS_仕様一覧.xlsx` | `db/scripts/load_excel_raw_to_duckdb.py` | `multione_wheels_仕様一覧_{WHEELS互換表,記号説明,原文}` | 2026-07-05 |
| `raw/inbox/Yanmar/Yanmar_CL26_仕様一覧.xlsx` | `db/scripts/load_excel_raw_to_duckdb.py` | `yanmar_cl26_仕様一覧_{概要,仕様一覧,特徴,注記・原文}` | 2026-07-05 |

## load_excel_raw_to_duckdb.py の使い方

```powershell
python db/scripts/load_excel_raw_to_duckdb.py raw/inbox/CASE_SAL/Case_SL12_仕様項目一覧.xlsx
```

- シートごとに `{プレフィックス}_{シート名}` テーブルを作る。プレフィックスは省略時ファイル名から自動生成、`--prefix` で指定可能。
- 列名は Excel の先頭行をそのまま使う（ファイルごとに列名が違っても独立した raw テーブルなので問題ない）。
- 数値と注記文字列が混在する列（例: `2425` と `N/A`）は原文保持のため VARCHAR になる。
- 各行に `raw_path` / `sheet_name` / `row_no`（Excel 上の行番号）が付き、原本へ辿れる。
- 同じプレフィックスで再実行すると既存テーブルを削除してから作り直す。削除済みシート由来の旧テーブルも残さない（再取り込み可能）。
- 実行のたびに `db/schema.sql` を DB の実テーブルから再生成して同期する。
