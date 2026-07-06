-- db/schema.sql
-- db/scripts/load_excel_raw_to_duckdb.py が knowledge.duckdb の実テーブルから自動生成。
-- 最終更新: 2026-07-06

CREATE TABLE "avant_型式_仕様一覧_仕様一覧"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "メーカー名" VARCHAR, "型式" VARCHAR, "販売状況" VARCHAR, "シリーズ" VARCHAR, "仕様カテゴリ" VARCHAR, "仕様項目" VARCHAR, "仕様値" VARCHAR, "数値" VARCHAR, "単位" VARCHAR, "備考" VARCHAR, "参照URL1" VARCHAR, "参照URL2" VARCHAR);

CREATE TABLE "avant_型式_仕様一覧_型式一覧"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "メーカー名" VARCHAR, "型式" VARCHAR, "販売状況" VARCHAR, "シリーズ" VARCHAR, "動力区分" VARCHAR, "一般的な製品分類" VARCHAR, "SAL分類" VARCHAR, "HP上の説明" VARCHAR, "製品URL" VARCHAR, "馬力_出力" VARCHAR, "エンジン型式" VARCHAR, "出力規格" VARCHAR, "最大トルク" VARCHAR, "燃料_バッテリー" VARCHAR, "バッテリー容量" VARCHAR, "充電時間" VARCHAR, "リフト容量_kg" BIGINT, "リフト高_mm" BIGINT, "テレスコ搭載" VARCHAR, "テレスコ長_mm" BIGINT, "補助油圧流量_Lmin" DOUBLE, "補助油圧圧力_bar" BIGINT, "補助油圧圧力_MPa" DOUBLE, "最大ブレークアウト力_kgf" BIGINT, "最大牽引力_kgf" BIGINT, "最高速度_kmh" VARCHAR, "運転質量_kg" BIGINT, "全幅_mm" BIGINT, "全長_mm" BIGINT, "全高_mm" BIGINT, "旋回半径内側_mm" BIGINT, "旋回半径外側_mm" BIGINT, "標準タイヤ" VARCHAR, "タイヤトレッド" VARCHAR, "ホイールサイズ" VARCHAR, "トランスミッション" VARCHAR, "走行系油圧システム" VARCHAR, "作業機系油圧システム" VARCHAR, "油圧システムメモ" VARCHAR, "備考" VARCHAR, Product_no VARCHAR, "仕様参照URL1" VARCHAR, "仕様参照URL2" VARCHAR);

CREATE TABLE "avant_型式_仕様一覧_旧型モデル"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "メーカー名" VARCHAR, "型式" VARCHAR, "販売状況" VARCHAR, "シリーズ" VARCHAR, "動力区分" VARCHAR, "一般的な製品分類" VARCHAR, "SAL分類" VARCHAR, "HP上の説明" VARCHAR, "製品URL" VARCHAR, "馬力_出力" VARCHAR, "エンジン型式" VARCHAR, "出力規格" VARCHAR, "最大トルク" VARCHAR, "燃料_バッテリー" VARCHAR, "バッテリー容量" VARCHAR, "充電時間" VARCHAR, "リフト容量_kg" BIGINT, "リフト高_mm" BIGINT, "テレスコ搭載" VARCHAR, "テレスコ長_mm" VARCHAR, "補助油圧流量_Lmin" BIGINT, "補助油圧圧力_bar" BIGINT, "補助油圧圧力_MPa" DOUBLE, "最大ブレークアウト力_kgf" VARCHAR, "最大牽引力_kgf" BIGINT, "最高速度_kmh" VARCHAR, "運転質量_kg" BIGINT, "全幅_mm" BIGINT, "全長_mm" BIGINT, "全高_mm" BIGINT, "旋回半径内側_mm" VARCHAR, "旋回半径外側_mm" VARCHAR, "標準タイヤ" VARCHAR, "タイヤトレッド" VARCHAR, "ホイールサイズ" VARCHAR, "トランスミッション" VARCHAR, "走行系油圧システム" VARCHAR, "作業機系油圧システム" VARCHAR, "油圧システムメモ" VARCHAR, "備考" VARCHAR, Product_no VARCHAR, "仕様参照URL1" VARCHAR, "仕様参照URL2" VARCHAR);

CREATE TABLE "avant_型式_仕様一覧_油圧システム"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "メーカー名" VARCHAR, "型式" VARCHAR, "販売状況" VARCHAR, "シリーズ" VARCHAR, "走行系油圧システム" VARCHAR, "作業機系油圧システム" VARCHAR, "補助油圧流量_Lmin" DOUBLE, "補助油圧圧力_MPa" DOUBLE, "油圧システムメモ" VARCHAR, "参照URL1" VARCHAR, "参照URL2" VARCHAR);

CREATE TABLE "bobcat_sal_仕様値_Bobcat_SAL仕様"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "セクション" VARCHAR, "仕様項目" VARCHAR, "L23_US数値" VARCHAR, "L23_US単位" VARCHAR, "L23_メートル数値" VARCHAR, "L23_メートル単位" VARCHAR, "L28_US数値" VARCHAR, "L28_US単位" VARCHAR, "L28_メートル数値" VARCHAR, "L28_メートル単位" VARCHAR, "L35_US数値" VARCHAR, "L35_US単位" VARCHAR, "L35_メートル数値" VARCHAR, "L35_メートル単位" VARCHAR);

CREATE TABLE canonical_specs(canonical_item VARCHAR PRIMARY KEY, display_name_ja VARCHAR NOT NULL, display_name_en VARCHAR NOT NULL, category VARCHAR NOT NULL, canonical_unit VARCHAR, value_type VARCHAR NOT NULL, priority INTEGER NOT NULL, description VARCHAR, comparison_flag BOOLEAN DEFAULT(CAST('t' AS BOOLEAN)));

CREATE TABLE "case_sal_catalog_specs_with_features_revised_Case_SALカタログ"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "区分" VARCHAR, "項目" VARCHAR, "単位" VARCHAR, SL12 VARCHAR, SL12_TR VARCHAR, SL15 VARCHAR, SL23 VARCHAR, SL27 VARCHAR, SL27_TR VARCHAR, SL35_TR VARCHAR, SL50_TR VARCHAR, SL22EV VARCHAR);

CREATE TABLE "case_sl12_仕様項目一覧_仕様"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "No" BIGINT, "大分類" VARCHAR, "中分類" VARCHAR, "項目" VARCHAR, "仕様_US値" VARCHAR, "US単位" VARCHAR, "メートル値" DOUBLE, "メートル単位" VARCHAR);

CREATE TABLE "case_sl12_仕様項目一覧_寸法"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "記号" VARCHAR, "項目" VARCHAR, "US値" DOUBLE, "US単位" VARCHAR, "メートル値" BIGINT, "メートル単位" VARCHAR);

CREATE TABLE "case_sl12_仕様項目一覧_概要"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "項目" VARCHAR, "内容" VARCHAR);

CREATE TABLE "case_sl12_仕様項目一覧_注記"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "No" BIGINT, "区分" VARCHAR, "内容" VARCHAR);

CREATE TABLE "case_sl12_仕様項目一覧_装備"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "No" BIGINT, "区分" VARCHAR, "大分類" VARCHAR, "項目" VARCHAR, "備考" VARCHAR);

CREATE TABLE "case_sl12_仕様項目一覧_転倒荷重"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "記号" VARCHAR, "項目" VARCHAR, "US値" BIGINT, "US単位" VARCHAR, "メートル値" BIGINT, "メートル単位" VARCHAR);

CREATE TABLE "case_sl12tr_仕様項目一覧_仕様"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "No" BIGINT, "大分類" VARCHAR, "中分類" VARCHAR, "項目" VARCHAR, "仕様_US値" VARCHAR, "US単位" VARCHAR, "メートル値" DOUBLE, "メートル単位" VARCHAR);

CREATE TABLE "case_sl12tr_仕様項目一覧_寸法"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "記号" VARCHAR, "項目" VARCHAR, "US値" DOUBLE, "US単位" VARCHAR, "メートル値" BIGINT, "メートル単位" VARCHAR);

CREATE TABLE "case_sl12tr_仕様項目一覧_概要"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "項目" VARCHAR, "内容" VARCHAR);

CREATE TABLE "case_sl12tr_仕様項目一覧_注記"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "No" BIGINT, "区分" VARCHAR, "内容" VARCHAR);

CREATE TABLE "case_sl12tr_仕様項目一覧_装備"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "No" BIGINT, "区分" VARCHAR, "大分類" VARCHAR, "項目" VARCHAR, "備考" VARCHAR);

CREATE TABLE "case_sl12tr_仕様項目一覧_転倒荷重"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "記号" VARCHAR, "項目" VARCHAR, "US値" BIGINT, "US単位" VARCHAR, "メートル値" BIGINT, "メートル単位" VARCHAR);

CREATE TABLE "case_sl15_仕様項目一覧_仕様"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "No" BIGINT, "大分類" VARCHAR, "中分類" VARCHAR, "項目" VARCHAR, "仕様_US値" VARCHAR, "US単位" VARCHAR, "メートル値" VARCHAR, "メートル単位" VARCHAR);

CREATE TABLE "case_sl15_仕様項目一覧_寸法"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "記号" VARCHAR, "項目" VARCHAR, "US値" DOUBLE, "US単位" VARCHAR, "メートル値" BIGINT, "メートル単位" VARCHAR);

CREATE TABLE "case_sl15_仕様項目一覧_概要"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "項目" VARCHAR, "内容" VARCHAR);

CREATE TABLE "case_sl15_仕様項目一覧_注記"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "No" BIGINT, "区分" VARCHAR, "内容" VARCHAR);

CREATE TABLE "case_sl15_仕様項目一覧_装備"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "No" BIGINT, "区分" VARCHAR, "大分類" VARCHAR, "項目" VARCHAR);

CREATE TABLE "case_sl15_仕様項目一覧_転倒荷重"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "記号" VARCHAR, "項目" VARCHAR, "US値" BIGINT, "US単位" VARCHAR, "メートル値" BIGINT, "メートル単位" VARCHAR);

CREATE TABLE "case_sl22ev_仕様項目一覧_仕様"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "No" BIGINT, "大分類" VARCHAR, "中分類" VARCHAR, "項目" VARCHAR, "仕様_US値" VARCHAR, "US単位" VARCHAR, "メートル値" VARCHAR, "メートル単位" VARCHAR);

CREATE TABLE "case_sl22ev_仕様項目一覧_寸法"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "記号" VARCHAR, "項目" VARCHAR, "US値" VARCHAR, "US単位" VARCHAR, "メートル値" VARCHAR, "メートル単位" VARCHAR);

CREATE TABLE "case_sl22ev_仕様項目一覧_概要"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "項目" VARCHAR, "内容" VARCHAR);

CREATE TABLE "case_sl22ev_仕様項目一覧_注記"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "No" BIGINT, "区分" VARCHAR, "内容" VARCHAR);

CREATE TABLE "case_sl22ev_仕様項目一覧_装備"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "No" BIGINT, "区分" VARCHAR, "大分類" VARCHAR, "項目" VARCHAR, "備考" VARCHAR);

CREATE TABLE "case_sl22ev_仕様項目一覧_転倒荷重"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "記号" VARCHAR, "項目" VARCHAR, "US値" VARCHAR, "US単位" VARCHAR, "メートル値" VARCHAR, "メートル単位" VARCHAR);

CREATE TABLE "case_sl23_仕様項目一覧_仕様"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "No" BIGINT, "大分類" VARCHAR, "中分類" VARCHAR, "項目" VARCHAR, "仕様_US値" VARCHAR, "US単位" VARCHAR, "メートル値" DOUBLE, "メートル単位" VARCHAR);

CREATE TABLE "case_sl23_仕様項目一覧_寸法"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "記号" VARCHAR, "項目" VARCHAR, "US値" DOUBLE, "US単位" VARCHAR, "メートル値" BIGINT, "メートル単位" VARCHAR);

CREATE TABLE "case_sl23_仕様項目一覧_概要"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "項目" VARCHAR, "内容" VARCHAR);

CREATE TABLE "case_sl23_仕様項目一覧_注記"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "No" BIGINT, "区分" VARCHAR, "内容" VARCHAR);

CREATE TABLE "case_sl23_仕様項目一覧_装備"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "No" BIGINT, "区分" VARCHAR, "大分類" VARCHAR, "項目" VARCHAR);

CREATE TABLE "case_sl23_仕様項目一覧_転倒荷重"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "記号" VARCHAR, "項目" VARCHAR, "US値" BIGINT, "US単位" VARCHAR, "メートル値" BIGINT, "メートル単位" VARCHAR);

CREATE TABLE "case_sl27_仕様項目一覧_仕様"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "No" BIGINT, "大分類" VARCHAR, "中分類" VARCHAR, "項目" VARCHAR, "仕様_US値" VARCHAR, "US単位" VARCHAR, "メートル値" VARCHAR, "メートル単位" VARCHAR);

CREATE TABLE "case_sl27_仕様項目一覧_寸法"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "記号" VARCHAR, "項目" VARCHAR, "US値" VARCHAR, "US単位" VARCHAR, "メートル値" VARCHAR, "メートル単位" VARCHAR);

CREATE TABLE "case_sl27_仕様項目一覧_概要"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "項目" VARCHAR, "内容" VARCHAR);

CREATE TABLE "case_sl27_仕様項目一覧_注記"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "No" BIGINT, "区分" VARCHAR, "内容" VARCHAR);

CREATE TABLE "case_sl27_仕様項目一覧_装備"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "No" BIGINT, "区分" VARCHAR, "大分類" VARCHAR, "項目" VARCHAR, "備考" VARCHAR);

CREATE TABLE "case_sl27_仕様項目一覧_転倒荷重"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "記号" VARCHAR, "項目" VARCHAR, "US値" VARCHAR, "US単位" VARCHAR, "メートル値" VARCHAR, "メートル単位" VARCHAR);

CREATE TABLE "case_sl27tr_仕様項目一覧_仕様"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "No" BIGINT, "大分類" VARCHAR, "中分類" VARCHAR, "項目" VARCHAR, "仕様_US値" VARCHAR, "US単位" VARCHAR, "メートル値" VARCHAR, "メートル単位" VARCHAR);

CREATE TABLE "case_sl27tr_仕様項目一覧_寸法"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "記号" VARCHAR, "項目" VARCHAR, "US値" VARCHAR, "US単位" VARCHAR, "メートル値" VARCHAR, "メートル単位" VARCHAR);

CREATE TABLE "case_sl27tr_仕様項目一覧_概要"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "項目" VARCHAR, "内容" VARCHAR);

CREATE TABLE "case_sl27tr_仕様項目一覧_注記"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "No" BIGINT, "区分" VARCHAR, "内容" VARCHAR);

CREATE TABLE "case_sl27tr_仕様項目一覧_装備"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "No" BIGINT, "区分" VARCHAR, "大分類" VARCHAR, "項目" VARCHAR, "備考" VARCHAR);

CREATE TABLE "case_sl27tr_仕様項目一覧_転倒荷重"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "記号" VARCHAR, "項目" VARCHAR, "US値" VARCHAR, "US単位" VARCHAR, "メートル値" VARCHAR, "メートル単位" VARCHAR);

CREATE TABLE "case_sl35tr_仕様項目一覧_仕様"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "No" BIGINT, "大分類" VARCHAR, "中分類" VARCHAR, "項目" VARCHAR, "仕様_US値" VARCHAR, "US単位" VARCHAR, "メートル値" VARCHAR, "メートル単位" VARCHAR);

CREATE TABLE "case_sl35tr_仕様項目一覧_寸法"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "記号" VARCHAR, "項目" VARCHAR, "US値" VARCHAR, "US単位" VARCHAR, "メートル値" VARCHAR, "メートル単位" VARCHAR);

CREATE TABLE "case_sl35tr_仕様項目一覧_概要"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "項目" VARCHAR, "内容" VARCHAR);

CREATE TABLE "case_sl35tr_仕様項目一覧_注記"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "No" BIGINT, "区分" VARCHAR, "内容" VARCHAR);

CREATE TABLE "case_sl35tr_仕様項目一覧_装備"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "No" BIGINT, "区分" VARCHAR, "大分類" VARCHAR, "項目" VARCHAR, "備考" VARCHAR);

CREATE TABLE "case_sl35tr_仕様項目一覧_転倒荷重"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "記号" VARCHAR, "項目" VARCHAR, "US値" VARCHAR, "US単位" VARCHAR, "メートル値" VARCHAR, "メートル単位" VARCHAR);

CREATE TABLE "case_sl50tr_仕様項目一覧_仕様"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "No" BIGINT, "大分類" VARCHAR, "中分類" VARCHAR, "項目" VARCHAR, "仕様_US値" VARCHAR, "US単位" VARCHAR, "メートル値" VARCHAR, "メートル単位" VARCHAR);

CREATE TABLE "case_sl50tr_仕様項目一覧_寸法"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "記号" VARCHAR, "項目" VARCHAR, "US値" VARCHAR, "US単位" VARCHAR, "メートル値" VARCHAR, "メートル単位" VARCHAR);

CREATE TABLE "case_sl50tr_仕様項目一覧_概要"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "項目" VARCHAR, "内容" VARCHAR);

CREATE TABLE "case_sl50tr_仕様項目一覧_注記"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "No" BIGINT, "区分" VARCHAR, "内容" VARCHAR);

CREATE TABLE "case_sl50tr_仕様項目一覧_装備"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "No" BIGINT, "区分" VARCHAR, "大分類" VARCHAR, "項目" VARCHAR, "備考" VARCHAR);

CREATE TABLE "case_sl50tr_仕様項目一覧_転倒荷重"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "記号" VARCHAR, "項目" VARCHAR, "US値" VARCHAR, "US単位" VARCHAR, "メートル値" VARCHAR, "メートル単位" VARCHAR);

CREATE TABLE excel_imports(table_name VARCHAR, raw_path VARCHAR, sheet_name VARCHAR, "columns" VARCHAR, row_count BIGINT, loaded_at TIMESTAMP);

CREATE TABLE "gianni_ferrari_turboloader_仕様一覧_アタッチメント一覧"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "No" BIGINT, "アタッチメント名" VARCHAR, "備考" VARCHAR);

CREATE TABLE "gianni_ferrari_turboloader_仕様一覧_アタッチメント仕様"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "No" BIGINT, "アタッチメント名" VARCHAR, "仕様項目" VARCHAR, "仕様値" VARCHAR, "数値" DOUBLE, "単位" VARCHAR, "備考" VARCHAR);

CREATE TABLE "gianni_ferrari_turboloader_仕様一覧_仕様一覧"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "型式" VARCHAR, "大項目" VARCHAR, "仕様項目" VARCHAR, "仕様値" VARCHAR, "数値" DOUBLE, "単位" VARCHAR, "備考" VARCHAR);

CREATE TABLE "gianni_ferrari_turboloader_仕様一覧_概要"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "項目" VARCHAR, "内容" VARCHAR, "備考" VARCHAR);

CREATE TABLE "gianni_ferrari_turboloader_仕様一覧_機能説明"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "カテゴリ" VARCHAR, "内容" VARCHAR, "備考" VARCHAR);

CREATE TABLE "gianni_ferrari_turboloader_仕様一覧_荷重図メモ"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "対象" VARCHAR, "値1" BIGINT, "値2" BIGINT, "値3" BIGINT, "単位" VARCHAR, "備考" VARCHAR);

CREATE TABLE "giant_g1200_tele_仕様一覧_タイヤ・アタッチメント"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "分類" VARCHAR, "内容" VARCHAR, "備考" VARCHAR);

CREATE TABLE "giant_g1200_tele_仕様一覧_仕様比較"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "型式" VARCHAR, "仕様項目" VARCHAR, "仕様値" VARCHAR, "数値" DOUBLE, "単位" VARCHAR, "備考" VARCHAR);

CREATE TABLE "giant_g1200_tele_仕様一覧_概要"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "項目" VARCHAR, "内容" VARCHAR, "備考" VARCHAR);

CREATE TABLE "giant_g1200_仕様一覧_タイヤ・アタッチメント"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "区分" VARCHAR, "項目" VARCHAR, "内容" VARCHAR);

CREATE TABLE "giant_g1200_仕様一覧_仕様比較"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "型式" VARCHAR, "仕様項目" VARCHAR, "仕様値" VARCHAR, "数値" DOUBLE, "単位" VARCHAR, "備考" VARCHAR);

CREATE TABLE "giant_g1200_仕様一覧_概要"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "区分" VARCHAR, "項目" VARCHAR, "内容" VARCHAR);

CREATE TABLE "giant_g1500_series_仕様一覧_タイヤ・アタッチメント"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "区分" VARCHAR, "内容" VARCHAR, "備考" VARCHAR);

CREATE TABLE "giant_g1500_series_仕様一覧_仕様比較"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "型式" VARCHAR, "仕様項目" VARCHAR, "仕様値" VARCHAR, "数値" DOUBLE, "単位" VARCHAR, "備考" VARCHAR);

CREATE TABLE "giant_g1500_series_仕様一覧_概要"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "項目" VARCHAR, "内容" VARCHAR, "備考" VARCHAR);

CREATE TABLE "giant_g2200e_series_仕様一覧_タイヤ・アタッチメント"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "区分" VARCHAR, "内容" VARCHAR, "備考" VARCHAR);

CREATE TABLE "giant_g2200e_series_仕様一覧_仕様比較"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "型式" VARCHAR, "仕様項目" VARCHAR, "仕様値" VARCHAR, "数値" DOUBLE, "単位" VARCHAR, "備考" VARCHAR);

CREATE TABLE "giant_g2200e_series_仕様一覧_概要"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "項目" VARCHAR, "内容" VARCHAR, "備考" VARCHAR);

CREATE TABLE "giant_g2300_hd_仕様一覧_タイヤ・アタッチメント"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "区分" VARCHAR, "内容" VARCHAR, "備考" VARCHAR);

CREATE TABLE "giant_g2300_hd_仕様一覧_仕様比較"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "型式" VARCHAR, "仕様項目" VARCHAR, "仕様値" VARCHAR, "数値" DOUBLE, "単位" VARCHAR, "備考" VARCHAR);

CREATE TABLE "giant_g2300_hd_仕様一覧_概要"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "項目" VARCHAR, "内容" VARCHAR, "備考" VARCHAR);

CREATE TABLE "giant_g2500_series_仕様一覧_タイヤ・アタッチメント"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "区分" VARCHAR, "内容" VARCHAR, "備考" VARCHAR);

CREATE TABLE "giant_g2500_series_仕様一覧_仕様比較"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "型式" VARCHAR, "仕様項目" VARCHAR, "仕様値" VARCHAR, "数値" DOUBLE, "単位" VARCHAR, "備考" VARCHAR);

CREATE TABLE "giant_g2500_series_仕様一覧_概要"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "項目" VARCHAR, "内容" VARCHAR, "備考" VARCHAR);

CREATE TABLE "giant_g2700_series_仕様一覧_タイヤ・アタッチメント"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "項目" VARCHAR, "内容" VARCHAR, "備考" VARCHAR);

CREATE TABLE "giant_g2700_series_仕様一覧_仕様比較"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "型式" VARCHAR, "仕様項目" VARCHAR, "仕様値" VARCHAR, "数値" DOUBLE, "単位" VARCHAR, "備考" VARCHAR);

CREATE TABLE "giant_g2700_series_仕様一覧_概要"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "項目" VARCHAR, "内容" VARCHAR, "備考" VARCHAR);

CREATE TABLE "giant_g3500_series_仕様一覧_タイヤ・アタッチメント"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "区分" VARCHAR, "項目" VARCHAR, "内容" VARCHAR);

CREATE TABLE "giant_g3500_series_仕様一覧_仕様比較"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "型式" VARCHAR, "仕様項目" VARCHAR, "仕様値" VARCHAR, "数値" DOUBLE, "単位" VARCHAR, "備考" VARCHAR);

CREATE TABLE "giant_g3500_series_仕様一覧_原文"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "項目" VARCHAR, "内容" VARCHAR);

CREATE TABLE "giant_g3500_series_仕様一覧_概要"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "項目" VARCHAR, "内容" VARCHAR, "備考" VARCHAR);

CREATE TABLE "giant_g5000_series_仕様一覧_タイヤ・アタッチメント"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "区分" VARCHAR, "項目" VARCHAR, "内容" VARCHAR);

CREATE TABLE "giant_g5000_series_仕様一覧_仕様比較"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "型式" VARCHAR, "仕様項目" VARCHAR, "仕様値" VARCHAR, "数値" DOUBLE, "単位" VARCHAR, "備考" VARCHAR);

CREATE TABLE "giant_g5000_series_仕様一覧_原文"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "項目" VARCHAR, "内容" VARCHAR);

CREATE TABLE "giant_g5000_series_仕様一覧_概要"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "項目" VARCHAR, "内容" VARCHAR, "備考" VARCHAR);

CREATE TABLE "giant_g5000_tele_series_仕様一覧_タイヤ・アタッチメント"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "区分" VARCHAR, "内容" VARCHAR, "備考" VARCHAR);

CREATE TABLE "giant_g5000_tele_series_仕様一覧_仕様比較"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "型式" VARCHAR, "仕様項目" VARCHAR, "仕様値" VARCHAR, "数値" DOUBLE, "単位" VARCHAR, "備考" VARCHAR);

CREATE TABLE "giant_g5000_tele_series_仕様一覧_原文"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "No" BIGINT, "原文" VARCHAR);

CREATE TABLE "giant_g5000_tele_series_仕様一覧_概要"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "項目" VARCHAR, "内容" VARCHAR, "備考" VARCHAR);

CREATE TABLE "giant_gs_series_仕様一覧_タイヤ・アタッチメント"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "区分" VARCHAR, "項目" VARCHAR, "内容" VARCHAR);

CREATE TABLE "giant_gs_series_仕様一覧_仕様比較"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "型式" VARCHAR, "仕様項目" VARCHAR, "仕様値" VARCHAR, "数値" DOUBLE, "単位" VARCHAR, "備考" VARCHAR);

CREATE TABLE "giant_gs_series_仕様一覧_概要"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "区分" VARCHAR, "項目" VARCHAR, "内容" VARCHAR);

CREATE TABLE "giant_gt5048_series_仕様一覧_タイヤ・アタッチメント"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "区分" VARCHAR, "内容" VARCHAR, "備考" VARCHAR);

CREATE TABLE "giant_gt5048_series_仕様一覧_仕様比較"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "型式" VARCHAR, "仕様項目" VARCHAR, "仕様値" VARCHAR, "数値" DOUBLE, "単位" VARCHAR, "備考" VARCHAR);

CREATE TABLE "giant_gt5048_series_仕様一覧_原文"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "No" BIGINT, "原文" VARCHAR);

CREATE TABLE "giant_gt5048_series_仕様一覧_概要"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "区分" VARCHAR, "項目" VARCHAR, "内容" VARCHAR);

CREATE TABLE "giant_型式分類一覧_GIANT型式分類"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "メーカー" VARCHAR, "シリーズ" VARCHAR, "型式" VARCHAR, "調査用分類" VARCHAR, "一般的な製品分類" VARCHAR, "英語分類" VARCHAR, "動力" VARCHAR, "走行・足回り" VARCHAR, "ブーム・仕様" VARCHAR, "テレスコ有無" VARCHAR, "判定メモ" VARCHAR);

CREATE TABLE "giant_型式分類一覧_分類メモ"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "項目" VARCHAR, "内容" VARCHAR);

CREATE TABLE "multione_11_5_y_仕様一覧_オプション・特徴"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "区分" VARCHAR, "項目" VARCHAR, "コード" VARCHAR, "メモ" VARCHAR);

CREATE TABLE "multione_11_5_y_仕様一覧_仕様一覧"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "区分" VARCHAR, "仕様項目" VARCHAR, "サブ項目" VARCHAR, "仕様値" VARCHAR, "メートル数値" VARCHAR, "メートル単位" VARCHAR, "US数値" VARCHAR, "US単位" VARCHAR, "メモ" VARCHAR);

CREATE TABLE "multione_11_5_y_仕様一覧_注記・原文"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "区分" VARCHAR, "内容" VARCHAR);

CREATE TABLE "multione_11_6_k_turbos_仕様一覧_オプション・特徴"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "区分" VARCHAR, "項目" VARCHAR, "コード" VARCHAR, "メモ" VARCHAR);

CREATE TABLE "multione_11_6_k_turbos_仕様一覧_仕様一覧"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "区分" VARCHAR, "仕様項目" VARCHAR, "サブ項目" VARCHAR, "仕様値" VARCHAR, "メートル数値" DOUBLE, "メートル単位" VARCHAR, "US数値" DOUBLE, "US単位" VARCHAR, "メモ" VARCHAR);

CREATE TABLE "multione_11_6_k_turbos_仕様一覧_注記・原文"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "区分" VARCHAR, "内容" VARCHAR);

CREATE TABLE "multione_1_1_仕様一覧_オプション・特徴"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "No" BIGINT, "区分" VARCHAR, "項目" VARCHAR, "コード" VARCHAR);

CREATE TABLE "multione_1_1_仕様一覧_仕様一覧"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "No" BIGINT, "区分" VARCHAR, "仕様項目" VARCHAR, "仕様値" VARCHAR, "メートル数値" DOUBLE, "メートル単位" VARCHAR, "US数値" DOUBLE, "US単位" VARCHAR);

CREATE TABLE "multione_1_1_仕様一覧_注記・原文"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "No" BIGINT, "区分" VARCHAR, "内容" VARCHAR);

CREATE TABLE "multione_2_3_efi_仕様一覧_オプション・特徴"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "No" BIGINT, "区分" VARCHAR, "項目" VARCHAR, "コード" VARCHAR);

CREATE TABLE "multione_2_3_efi_仕様一覧_仕様一覧"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "No" BIGINT, "区分" VARCHAR, "仕様項目" VARCHAR, "仕様値" VARCHAR, "メートル数値" DOUBLE, "メートル単位" VARCHAR, "US数値" DOUBLE, "US単位" VARCHAR);

CREATE TABLE "multione_2_3_efi_仕様一覧_注記・原文"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "No" BIGINT, "区分" VARCHAR, "内容" VARCHAR);

CREATE TABLE "multione_5_2_k_id_仕様一覧_オプション・特徴"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "No" BIGINT, "区分" VARCHAR, "項目" VARCHAR, "コード" VARCHAR);

CREATE TABLE "multione_5_2_k_id_仕様一覧_仕様一覧"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "No" BIGINT, "区分" VARCHAR, "仕様項目" VARCHAR, "仕様値" VARCHAR, "メートル数値" DOUBLE, "メートル単位" VARCHAR, "US数値" DOUBLE, "US単位" VARCHAR);

CREATE TABLE "multione_5_2_k_id_仕様一覧_注記・原文"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "No" BIGINT, "区分" VARCHAR, "内容" VARCHAR);

CREATE TABLE "multione_5_3_k_id_仕様一覧_オプション・特徴"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "No" BIGINT, "区分" VARCHAR, "項目" VARCHAR, "コード" VARCHAR);

CREATE TABLE "multione_5_3_k_id_仕様一覧_仕様一覧"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "No" BIGINT, "区分" VARCHAR, "仕様項目" VARCHAR, "仕様値" VARCHAR, "メートル数値" DOUBLE, "メートル単位" VARCHAR, "US数値" DOUBLE, "US単位" VARCHAR);

CREATE TABLE "multione_5_3_k_id_仕様一覧_注記・原文"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "No" BIGINT, "区分" VARCHAR, "内容" VARCHAR);

CREATE TABLE "multione_6_3_ids_仕様一覧_オプション・特徴"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "No" BIGINT, "区分" VARCHAR, "項目" VARCHAR, "コード" VARCHAR);

CREATE TABLE "multione_6_3_ids_仕様一覧_仕様一覧"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "No" BIGINT, "区分" VARCHAR, "仕様項目" VARCHAR, "仕様値" VARCHAR, "メートル数値" DOUBLE, "メートル単位" VARCHAR, "US数値" DOUBLE, "US単位" VARCHAR);

CREATE TABLE "multione_6_3_ids_仕様一覧_注記・原文"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "No" BIGINT, "区分" VARCHAR, "内容" VARCHAR);

CREATE TABLE "multione_7_2_k_仕様一覧_オプション・特徴"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "No" BIGINT, "区分" VARCHAR, "項目" VARCHAR, "コード" VARCHAR);

CREATE TABLE "multione_7_2_k_仕様一覧_仕様一覧"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "No" BIGINT, "区分" VARCHAR, "仕様項目" VARCHAR, "仕様値" VARCHAR, "メートル数値" DOUBLE, "メートル単位" VARCHAR, "US数値" DOUBLE, "US単位" VARCHAR);

CREATE TABLE "multione_7_2_k_仕様一覧_注記・原文"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "No" BIGINT, "区分" VARCHAR, "内容" VARCHAR);

CREATE TABLE "multione_8_4_turbos_仕様一覧_オプション・特徴"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "No" BIGINT, "区分" VARCHAR, "項目" VARCHAR, "コード" VARCHAR);

CREATE TABLE "multione_8_4_turbos_仕様一覧_仕様一覧"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "No" BIGINT, "区分" VARCHAR, "仕様項目" VARCHAR, "仕様値" VARCHAR, "メートル数値" DOUBLE, "メートル単位" VARCHAR, "US数値" DOUBLE, "US単位" VARCHAR);

CREATE TABLE "multione_8_4_turbos_仕様一覧_注記・原文"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "No" BIGINT, "区分" VARCHAR, "内容" VARCHAR);

CREATE TABLE "multione_8_5_y_仕様一覧_オプション・特徴"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "No" BIGINT, "区分" VARCHAR, "項目" VARCHAR, "コード" VARCHAR);

CREATE TABLE "multione_8_5_y_仕様一覧_仕様一覧"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "No" BIGINT, "区分" VARCHAR, "仕様項目" VARCHAR, "仕様値" VARCHAR, "メートル数値" DOUBLE, "メートル単位" VARCHAR, "US数値" DOUBLE, "US単位" VARCHAR);

CREATE TABLE "multione_8_5_y_仕様一覧_注記・原文"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "No" BIGINT, "区分" VARCHAR, "内容" VARCHAR);

CREATE TABLE "multione_8_5s_k_仕様一覧_オプション・特徴"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "No" BIGINT, "区分" VARCHAR, "項目" VARCHAR, "コード" VARCHAR);

CREATE TABLE "multione_8_5s_k_仕様一覧_仕様一覧"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "No" BIGINT, "区分" VARCHAR, "仕様項目" VARCHAR, "仕様値" VARCHAR, "メートル数値" DOUBLE, "メートル単位" VARCHAR, "US数値" DOUBLE, "US単位" VARCHAR);

CREATE TABLE "multione_8_5s_k_仕様一覧_注記・原文"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "No" BIGINT, "区分" VARCHAR, "内容" VARCHAR);

CREATE TABLE "multione_ez7_仕様一覧_オプション・特徴"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "メーカー" VARCHAR, "SAL型式" VARCHAR, "種別" VARCHAR, "項目" VARCHAR, "コード" VARCHAR, "対象・条件" VARCHAR, "メモ" VARCHAR);

CREATE TABLE "multione_ez7_仕様一覧_仕様一覧"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "メーカー" VARCHAR, "SAL型式" VARCHAR, "分類" VARCHAR, "仕様項目" VARCHAR, "条件" VARCHAR, "仕様値" VARCHAR, "メートル数値" DOUBLE, "メートル単位" VARCHAR, "US数値" DOUBLE, "US単位" VARCHAR, "メモ" VARCHAR);

CREATE TABLE "multione_ez7_仕様一覧_注記・原文"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "メーカー" VARCHAR, "SAL型式" VARCHAR, "種別" VARCHAR, "内容" VARCHAR);

CREATE TABLE "multione_ez8_ez8_long_range_仕様一覧_オプション・特徴"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "メーカー" VARCHAR, "SAL型式" VARCHAR, "種別" VARCHAR, "項目" VARCHAR, "コード" VARCHAR);

CREATE TABLE "multione_ez8_ez8_long_range_仕様一覧_仕様一覧"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "メーカー" VARCHAR, "SAL型式" VARCHAR, "分類" VARCHAR, "仕様項目" VARCHAR, "条件" VARCHAR, "仕様値" VARCHAR, "メートル数値" DOUBLE, "メートル単位" VARCHAR, "US数値" DOUBLE, "US単位" VARCHAR, "メモ" VARCHAR);

CREATE TABLE "multione_ez8_ez8_long_range_仕様一覧_注記・原文"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "メーカー" VARCHAR, "SAL型式" VARCHAR, "種別" VARCHAR, "内容" VARCHAR);

CREATE TABLE "multione_wheels_仕様一覧_WHEELS互換表"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, Code VARCHAR, Size VARCHAR, Profile VARCHAR, "1_1" VARCHAR, "2_3_EFI" VARCHAR, "5_2_K_iD" VARCHAR, "5_3_K_iD" VARCHAR, "6_3_iDS" VARCHAR, "7_2_K" VARCHAR, EZ_5 VARCHAR, EZ_7_EZ_8 VARCHAR, "8_4_TurboS" VARCHAR, "8_5_K" VARCHAR, "11_6_K_11_9_K" VARCHAR, "メモ" VARCHAR);

CREATE TABLE "multione_wheels_仕様一覧_原文"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, LOADERS_AND_OPTIONS VARCHAR);

CREATE TABLE "multione_wheels_仕様一覧_記号説明"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "記号" VARCHAR, "意味" VARCHAR);

CREATE TABLE normalization_issues(issue_id BIGINT DEFAULT(nextval('normalization_issue_seq')), issue_type VARCHAR NOT NULL, severity VARCHAR DEFAULT('review'), company VARCHAR, product_id VARCHAR, source_table VARCHAR, raw_item_name VARCHAR, raw_value VARCHAR, detail VARCHAR, status VARCHAR DEFAULT('open'), created_at TIMESTAMP DEFAULT(current_timestamp));

CREATE TABLE normalized_specs(normalized_id BIGINT DEFAULT(nextval('normalized_spec_seq')), product_id VARCHAR NOT NULL, company VARCHAR NOT NULL, product_name VARCHAR, canonical_item VARCHAR NOT NULL, normalized_value_numeric DOUBLE, normalized_value_text VARCHAR, normalized_unit VARCHAR, original_value VARCHAR, original_unit VARCHAR, value_type VARCHAR, value_status VARCHAR DEFAULT('present'), confidence DOUBLE, source_table VARCHAR, source_column VARCHAR, source_row_id BIGINT, unit_system VARCHAR, source_rank INTEGER, notes VARCHAR);

CREATE TABLE products(product_id VARCHAR PRIMARY KEY, company VARCHAR NOT NULL, product_name VARCHAR NOT NULL, model_code VARCHAR, series VARCHAR, market_segment VARCHAR, power_type VARCHAR, telescopic VARCHAR, sales_status VARCHAR, product_url VARCHAR, source_table VARCHAR, confidence DOUBLE DEFAULT(1.0), notes VARCHAR);

CREATE TABLE raw_specs(raw_spec_id BIGINT DEFAULT(nextval('raw_spec_seq')), company VARCHAR NOT NULL, product_id VARCHAR NOT NULL, product_name VARCHAR, source_table VARCHAR NOT NULL, source_sheet VARCHAR, source_row_id BIGINT, source_column VARCHAR, raw_category VARCHAR, raw_item_name VARCHAR NOT NULL, raw_value_text VARCHAR, raw_value_numeric DOUBLE, raw_unit VARCHAR, unit_system VARCHAR DEFAULT('unspecified'), source_rank INTEGER DEFAULT(1), raw_notes VARCHAR);

CREATE TABLE spec_mapping(company VARCHAR NOT NULL, product_id VARCHAR NOT NULL, source_table VARCHAR NOT NULL, raw_item_name VARCHAR NOT NULL, canonical_item VARCHAR, raw_unit VARCHAR, canonical_unit VARCHAR, mapping_method VARCHAR NOT NULL, confidence DOUBLE NOT NULL, notes VARCHAR);

CREATE TABLE spec_patterns(pattern_id INTEGER NOT NULL, item_regex VARCHAR NOT NULL, company_regex VARCHAR, category_regex VARCHAR, unit_regex VARCHAR, canonical_item VARCHAR NOT NULL, mapping_method VARCHAR NOT NULL, confidence DOUBLE NOT NULL, notes VARCHAR);

CREATE TABLE spec_synonyms(synonym_key VARCHAR NOT NULL, canonical_item VARCHAR NOT NULL, match_type VARCHAR DEFAULT('synonym'), notes VARCHAR);

CREATE TABLE unit_conversions(from_unit VARCHAR NOT NULL, to_unit VARCHAR NOT NULL, factor DOUBLE NOT NULL, notes VARCHAR);

CREATE TABLE "yanmar_cl26_仕様一覧_仕様一覧"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "メーカー" VARCHAR, "型式" VARCHAR, "仕様項目" VARCHAR, "仕様値" VARCHAR, "数値" DOUBLE, "単位" VARCHAR, "備考" VARCHAR, "参照URL1" VARCHAR, "参照URL2" VARCHAR);

CREATE TABLE "yanmar_cl26_仕様一覧_概要"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "項目" VARCHAR, "内容" VARCHAR, "備考" VARCHAR, "参照URL1" VARCHAR, "参照URL2" VARCHAR);

CREATE TABLE "yanmar_cl26_仕様一覧_注記・原文"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "区分" VARCHAR, "内容" VARCHAR, "参照URL1" VARCHAR, "参照URL2" VARCHAR);

CREATE TABLE "yanmar_cl26_仕様一覧_特徴"(raw_path VARCHAR, sheet_name VARCHAR, row_no BIGINT, "メーカー" VARCHAR, "型式" VARCHAR, "区分" VARCHAR, "内容" VARCHAR, "備考" VARCHAR, "参照URL1" VARCHAR, "参照URL2" VARCHAR);

CREATE VIEW best_normalized_specs AS SELECT * FROM normalized_specs WHERE (value_status IN ('present', 'optional')) QUALIFY (row_number() OVER (PARTITION BY product_id, canonical_item ORDER BY confidence DESC, source_rank ASC, CASE  WHEN ((unit_system = 'metric')) THEN (1) WHEN ((unit_system = 'us')) THEN (2) ELSE 3 END, normalized_id) = 1);

CREATE VIEW product_comparison_core_view AS SELECT p.product_id, p.company, p.product_name, p.model_code, p.market_segment, p.power_type, p.telescopic, p.sales_status, max(b.normalized_value_numeric) FILTER (WHERE (b.canonical_item = 'operating_weight')) AS operating_weight_kg, max(b.normalized_value_numeric) FILTER (WHERE (b.canonical_item = 'engine_power')) AS engine_power_kw, max(b.normalized_value_numeric) FILTER (WHERE (b.canonical_item = 'lift_height')) AS lift_height_mm, max(b.normalized_value_numeric) FILTER (WHERE (b.canonical_item = 'lift_capacity')) AS lift_capacity_kg, max(b.normalized_value_numeric) FILTER (WHERE (b.canonical_item = 'tipping_load_straight')) AS tipping_load_straight_kg, max(b.normalized_value_numeric) FILTER (WHERE (b.canonical_item = 'tipping_load')) AS tipping_load_unspec_kg, max(b.normalized_value_numeric) FILTER (WHERE (b.canonical_item = 'rated_operating_capacity')) AS rated_operating_capacity_kg, max(b.normalized_value_numeric) FILTER (WHERE (b.canonical_item = 'max_travel_speed')) AS max_travel_speed_kmh, max(b.normalized_value_numeric) FILTER (WHERE (b.canonical_item = 'aux_hydraulic_flow')) AS aux_hydraulic_flow_lmin, max(b.normalized_value_numeric) FILTER (WHERE (b.canonical_item = 'aux_hydraulic_pressure')) AS aux_hydraulic_pressure_mpa, max(b.normalized_value_numeric) FILTER (WHERE (b.canonical_item = 'overall_length')) AS overall_length_mm, max(b.normalized_value_numeric) FILTER (WHERE (b.canonical_item = 'overall_width')) AS overall_width_mm, max(b.normalized_value_numeric) FILTER (WHERE (b.canonical_item = 'overall_height')) AS overall_height_mm FROM products AS p LEFT JOIN best_normalized_specs AS b USING (product_id) GROUP BY ALL;

CREATE VIEW product_comparison_full_view AS SELECT p.product_id, p.company, p.product_name, p.model_code, p.series, p.market_segment, p.power_type, p.telescopic, p.sales_status, max(b.normalized_value_numeric) FILTER (WHERE (b.canonical_item = 'operating_weight')) AS operating_weight_kg, max(b.normalized_value_numeric) FILTER (WHERE (b.canonical_item = 'lift_height')) AS lift_height_mm, max(b.normalized_value_numeric) FILTER (WHERE (b.canonical_item = 'lift_capacity')) AS lift_capacity_kg, max(b.normalized_value_numeric) FILTER (WHERE (b.canonical_item = 'tipping_load_straight')) AS tipping_load_straight_kg, max(b.normalized_value_numeric) FILTER (WHERE (b.canonical_item = 'tipping_load_articulated')) AS tipping_load_articulated_kg, max(b.normalized_value_numeric) FILTER (WHERE (b.canonical_item = 'tipping_load')) AS tipping_load_unspec_kg, max(b.normalized_value_numeric) FILTER (WHERE (b.canonical_item = 'rated_operating_capacity')) AS rated_operating_capacity_kg, max(b.normalized_value_numeric) FILTER (WHERE (b.canonical_item = 'rated_operating_capacity_articulated')) AS roc_articulated_kg, max(b.normalized_value_numeric) FILTER (WHERE (b.canonical_item = 'breakout_force')) AS breakout_force_kn, max(b.normalized_value_numeric) FILTER (WHERE (b.canonical_item = 'traction_force')) AS traction_force_kn, max(b.normalized_value_numeric) FILTER (WHERE (b.canonical_item = 'pushing_force')) AS pushing_force_kn, max(b.normalized_value_numeric) FILTER (WHERE (b.canonical_item = 'max_travel_speed')) AS max_travel_speed_kmh, max(b.normalized_value_numeric) FILTER (WHERE (b.canonical_item = 'bucket_capacity')) AS bucket_capacity_m3, max(b.normalized_value_text) FILTER (WHERE (b.canonical_item = 'telescopic_boom')) AS telescopic_boom, max(b.normalized_value_numeric) FILTER (WHERE (b.canonical_item = 'telescopic_length')) AS telescopic_length_mm, max(b.normalized_value_numeric) FILTER (WHERE (b.canonical_item = 'ground_pressure')) AS ground_pressure_kgm2, max(b.normalized_value_text) FILTER (WHERE (b.canonical_item = 'engine_model')) AS engine_model, max(b.normalized_value_numeric) FILTER (WHERE (b.canonical_item = 'engine_power')) AS engine_power_kw, max(b.normalized_value_numeric) FILTER (WHERE (b.canonical_item = 'engine_torque')) AS engine_torque_nm, max(b.normalized_value_numeric) FILTER (WHERE (b.canonical_item = 'engine_displacement')) AS engine_displacement_cc, max(b.normalized_value_numeric) FILTER (WHERE (b.canonical_item = 'engine_cylinders')) AS engine_cylinders, max(b.normalized_value_text) FILTER (WHERE (b.canonical_item = 'fuel_type')) AS fuel_type, max(b.normalized_value_numeric) FILTER (WHERE (b.canonical_item = 'fuel_tank_capacity')) AS fuel_tank_capacity_l, max(b.normalized_value_text) FILTER (WHERE (b.canonical_item = 'emissions_standard')) AS emissions_standard, max(b.normalized_value_numeric) FILTER (WHERE (b.canonical_item = 'battery_capacity')) AS battery_capacity_kwh, max(b.normalized_value_numeric) FILTER (WHERE (b.canonical_item = 'charge_time')) AS charge_time_h, max(b.normalized_value_numeric) FILTER (WHERE (b.canonical_item = 'motor_power_drive')) AS motor_power_drive_kw, max(b.normalized_value_numeric) FILTER (WHERE (b.canonical_item = 'motor_power_implement')) AS motor_power_implement_kw, max(b.normalized_value_numeric) FILTER (WHERE (b.canonical_item = 'aux_hydraulic_flow')) AS aux_hydraulic_flow_lmin, max(b.normalized_value_numeric) FILTER (WHERE (b.canonical_item = 'aux_hydraulic_pressure')) AS aux_hydraulic_pressure_mpa, max(b.normalized_value_numeric) FILTER (WHERE (b.canonical_item = 'aux_hydraulic_flow_high')) AS aux_hydraulic_flow_high_lmin, max(b.normalized_value_numeric) FILTER (WHERE (b.canonical_item = 'overall_length')) AS overall_length_mm, max(b.normalized_value_numeric) FILTER (WHERE (b.canonical_item = 'overall_length_with_bucket')) AS length_with_bucket_mm, max(b.normalized_value_numeric) FILTER (WHERE (b.canonical_item = 'overall_width')) AS overall_width_mm, max(b.normalized_value_numeric) FILTER (WHERE (b.canonical_item = 'overall_height')) AS overall_height_mm, max(b.normalized_value_numeric) FILTER (WHERE (b.canonical_item = 'wheelbase')) AS wheelbase_mm, max(b.normalized_value_numeric) FILTER (WHERE (b.canonical_item = 'ground_clearance')) AS ground_clearance_mm, max(b.normalized_value_numeric) FILTER (WHERE (b.canonical_item = 'turning_radius_inner')) AS turning_radius_inner_mm, max(b.normalized_value_numeric) FILTER (WHERE (b.canonical_item = 'turning_radius_outer')) AS turning_radius_outer_mm, max(b.normalized_value_numeric) FILTER (WHERE (b.canonical_item = 'dump_height')) AS dump_height_mm, max(b.normalized_value_text) FILTER (WHERE (b.canonical_item = 'transmission')) AS transmission, max(b.normalized_value_text) FILTER (WHERE (b.canonical_item = 'standard_tires')) AS standard_tires, max(b.normalized_value_text) FILTER (WHERE (b.canonical_item = 'warranty')) AS warranty FROM products AS p LEFT JOIN best_normalized_specs AS b USING (product_id) GROUP BY ALL;

CREATE VIEW product_comparison_view AS SELECT * FROM product_comparison_core_view;
