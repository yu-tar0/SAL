# Log

## [2026-07-02] query | DuckDB現行rawテーブル版のAVANT比較表生成

- `db/knowledge.duckdb` の現行テーブル `avant_loader_specs_raw` を直接参照し、旧 `loader_specifications_current` 依存を外した current-db 版の比較表を作成。
- `scripts/build_avant_loader_comparison_artifact.py` を追加し、現行DBから Markdown 正本と `web.html` を再生成できるようにした。
- `artifacts/2026-07-02-comparison-avant-loader-specs-current-db/2026-07-02-comparison-avant-loader-specs-current-db.md` を内容正本として生成。
- `artifacts/2026-07-02-comparison-avant-loader-specs-current-db/2026-07-02-comparison-avant-loader-specs-current-db.web.html` をブラウザ閲覧用として生成。
- 燃焼系は個別モデル 15 台をレンジ比較し、電動個別モデル 3 台とシリーズ要約 2 行は別表に分離。
- `wiki/index.md` に current-db 版 Artifact 一覧を追記。

## [2026-07-02] query | DuckDB 既存SALデータの比較表試作

- `db/knowledge.duckdb` の `loader_specifications_current` view を使い、AVANT の既存 SAL 仕様データから比較表の試作を作成。
- `artifacts/2026-07-02-comparison-avant-loader-specs-prototype/2026-07-02-comparison-avant-loader-specs-prototype.md` を内容正本として追加。
- `artifacts/2026-07-02-comparison-avant-loader-specs-prototype/2026-07-02-comparison-avant-loader-specs-prototype.web.html` をブラウザ閲覧用として追加。
- 数値レンジ比較は個別機種 7 モデルに限定し、700 / 800 / e500 / e700 は補足表として分離。
- `wiki/index.md` に Artifact 一覧を追記。

## [2026-06-30] query | SAL成立背景メモのHTML Artifact化

- `raw/inbox/sal_birth_evolution_electric.md` を入力元に、SAL の成立背景、多用途化、電動油圧構成の整理を Artifact 化。
- `artifacts/2026-06-30-summary-sal-birth-evolution-electric/2026-06-30-summary-sal-birth-evolution-electric.md` を内容正本として作成。
- `artifacts/2026-06-30-summary-sal-birth-evolution-electric/2026-06-30-summary-sal-birth-evolution-electric.web.html` をブラウザ閲覧用として生成。
- `wiki/index.md` に Artifact 一覧を追記。

## [2026-06-07] lint | LLM Wiki default 全体リファクタリング

- LLM Wiki default として再利用しやすいように、ルート `.gitignore` を追加し、Python キャッシュ、ローカル仮想環境、DuckDB 実体・一時ファイル、OS / editor ノイズを除外。
- `scripts/lint_wiki.py` を追加し、必須パス、Wikilink、`wiki/index.md` のパス参照、主要ページの基本セクション、`wiki/log.md` の見出し形式を確認できるようにした。
- source / concept / entity テンプレートの固定日付を `YYYY-MM-DD` プレースホルダへ変更し、default テンプレートとして使い回しやすくした。
- `README.md` と `wiki/index.md` を更新し、使い始め、保守コマンド、主要保守ファイルへの導線を整理。

## [2026-06-07] query | DuckDB raw 行単位参照の追加

- `db/schema.sql` の `observations` と `relationships` に `raw_path` / `raw_locator` を追加し、原本ファイル内のページ、行、時刻などへ行単位で辿れるようにした。
- `wiki/concepts/構造化データ運用.md`、`db/README.md`、`AGENTS.md` に、`raw_path` / `raw_locator` は原本位置、`wiki_path` / `note_id` は解釈メモ位置として使い分ける方針を追記。

## [2026-06-07] query | DuckDB と定性メモの分担ルール追加

- `wiki/concepts/構造化データ運用.md` に、定量仕様、短い定性メモ、長文メモの置き場所を整理。
- `db/schema.sql` の `observations` と `relationships` に `wiki_path` / `note_id` を追加し、行単位で Markdown メモへ辿れるようにした。
- `db/README.md` と `AGENTS.md` に、長文・自由記述・思考メモは wiki に置き、DB から相互参照する方針を追記。

## [2026-06-07] query | DuckDB 構造化データ層の初期構成

- `db/schema.sql`、`db/README.md`、`db/.gitignore` を追加し、標準 DB を `db/knowledge.duckdb` とする汎用構成を定義。
- Python 依存関係を `requirements.txt` にまとめ、DuckDB、PDF 画像化、画像テーマ生成の初期セットアップを再現しやすくした。
- `raw/data/` と `raw/archives/` を追加し、表形式元データと過去版の置き場所を分離。
- `AGENTS.md`、`README.md`、`.github/skills/wiki-ingest/SKILL.md`、`wiki/index.md`、`wiki/overview.md`、wiki テンプレート、`wiki/concepts/Rawデータ運用.md` を更新。
- `wiki/concepts/構造化データ運用.md` を追加し、DB と wiki の役割分担、競合値の扱い、provenance 方針を整理。

## [2026-06-01] query | batch-page-image-markdown 実サンプル検証

- `batch-page-image-markdown` の挙動確認として、`raw/assets/sample_a4/pages/page-002.png` と `page-003.png` を連続で視覚確認し Markdown 化。
- 既存の `raw/assets/sample_a4/md/page-001.md` は上書きせず、未処理だった `page-002.md` と `page-003.md` を追加。
- ページごとの確認待ちは行わず、`pdf-page-image-markdown` と同じページコメント・check コメント形式で出力。

## [2026-06-01] query | batch-page-image-markdown スキル修正

- `.github/skills/batch-page-image-markdown/SKILL.md` を、ユーザーが普段 `pdf-page-image-markdown` で1ページずつ行っている処理を Codex が連続代行するスキルとして明確化。
- 添付画像または指定フォルダ内のページ画像を1ページずつ視覚確認し、ページごとの確認待ちなしで最後まで Markdown 化する方針に整理。
- `md/_batch_manifest.md` は必須ではなく、ページ数が多い場合や途中再開が必要な場合だけ使う扱いに変更。
- 事前チェック、ステータス管理、出力テンプレートを追加。
- manifest と任意のスケルトンを作成する補助スクリプト `.github/skills/batch-page-image-markdown/scripts/prepare_batch_manifest.py` を追加。
- `python -m py_compile` で補助スクリプトの構文を確認。

## [2026-06-01] query | html-artifact スキルで web のみ生成を試作

- `wiki/concepts/Artifacts運用.md` を入力元に、試作用 Artifact を作成。
- `artifacts/2026-06-01-summary-artifact-web-default-test/2026-06-01-summary-artifact-web-default-test.md` を正本として作成。
- 標準出力として `artifacts/2026-06-01-summary-artifact-web-default-test/2026-06-01-summary-artifact-web-default-test.web.html` のみを生成。
- `a4.html` と `slides.html` は明示依頼がないため生成しないことを確認。
- `wiki/concepts/Artifacts運用.md` と `wiki/index.md` を更新。

## [2026-06-01] query | kubota theme 追加

- `raw/assets/image-color-theme/kubota-v1/source.png` から生成した `kubota-v1` theme を `.github/skills/html-artifact/assets/themes.json` に追加。
- 作成ファイル: `raw/assets/image-color-theme/kubota-v1/kubota-v1.theme.json`, `raw/assets/image-color-theme/kubota-v1/kubota-v1.preview.html`。
- 注意: accent `#00A8A9` と paper `#FFFFFF` のコントラスト比は 2.93。ボタン・リンク色として使う場合は、必要に応じて `--accessible` で 4.5:1 以上に再生成する。
## [2026-06-01] query | Artifact HTML 標準生成を web のみに変更

- 正本 Markdown からのHTML生成標準を `web.html` のみに変更。
- `a4.html` と `slides.html` は、ユーザーが明示的に求めた場合だけ追加生成する方針に整理。
- `AGENTS.md`、`.github/skills/html-artifact/SKILL.md`、`README.md`、`wiki/concepts/Artifacts運用.md`、`wiki/index.md` を更新。

## [2026-05-22] lint | Initial wiki scaffold

- 初期ディレクトリ構成を作成。
- `AGENTS.md` を追加。
- 初回 ingest 用のテンプレートと手順書を追加。

## [2026-05-26] query | source取得元メタデータの標準化

- `AGENTS.md` に source summary の最小メタデータ項目を追加。
- `wiki/concepts/Rawデータ運用.md` に取得元管理の実務ルールを追加。
- `wiki/sources/_source_template.md` を追加し、初回ソース投入用のテンプレートを明文化。
- `README.md` と `wiki/index.md` を更新し、テンプレート参照導線を追加。

## [2026-05-22] query | Artifact 品質サンプル作成

- `artifacts/2026-05-22-summary-artifact-quality-sample.md` を作成。
- `wiki/concepts/Artifacts運用.md` を作成。
- `wiki/index.md` に Artifacts セクションと関連概念を追加。

## [2026-05-23] query | HTML Artifact サンプル作成

- `artifacts/2026-05-23-summary-html-artifact-sample.html` を作成。
- `wiki/concepts/Artifacts運用.md` をHTML専用運用に合わせて更新。
- `wiki/index.md` の Artifacts 項目をHTMLサンプルへ更新。

## [2026-05-24] query | Artifacts 定義の明確化

- `artifacts/` を、`wiki/` の知識や必要に応じた `raw/` 資料を人間向けHTMLとして可視化するレイヤーとして再定義。
- `README.md`、`AGENTS.md`、`.github/skills/html-artifact/SKILL.md`、`wiki/concepts/Artifacts運用.md`、`wiki/index.md` を更新。

## [2026-05-24] query | Artifact md-to-html フロー追加

- Artifacts 作成時に、単一 Markdown を内容の正本として作成し、それを HTML へ変換する標準フローを追加。
- `AGENTS.md`、`.github/skills/html-artifact/SKILL.md`、`README.md`、`wiki/concepts/Artifacts運用.md`、`wiki/index.md` を更新。
- 既存の HTML サンプルは Markdown 正本未作成として索引上に明記。

## [2026-05-24] query | Artifact 用途別HTML生成の標準化

- 1つの Markdown 正本から `web.html`、`a4.html`、`slides.html` の3系統HTMLを生成する標準フローを追加。
- `web.html` はブラウザ閲覧入口、`a4.html` はA4印刷/PDF用、`slides.html` は16:9スライド/PDF/PowerPoint用として定義。
- `.github/skills/html-artifact/SKILL.md`、`AGENTS.md`、`README.md`、`wiki/concepts/Artifacts運用.md`、`wiki/index.md` を更新。

## [2026-05-24] query | Artifact 形式別変換ルール追加

- Markdown をレイアウト指定ではなく意味構造の正本として扱う方針を追加。
- `web.html` は連続ページ、`a4.html` は印刷資料として忠実整形、`slides.html` はプレゼン向けに要約・分割して再構成する方針を追加。
- `.github/skills/html-artifact/SKILL.md`、`AGENTS.md`、`README.md`、`wiki/concepts/Artifacts運用.md` を更新。

## [2026-05-24] query | HTML Artifact 新標準サンプル作成

- `artifacts/samples/html-artifact/v001/sample.md` を正本として作成。
- `artifacts/samples/html-artifact/v001/sample.web.html`、`artifacts/samples/html-artifact/v001/sample.a4.html`、`artifacts/samples/html-artifact/v001/sample.slides.html` を作成。
- `wiki/index.md`、`wiki/concepts/Artifacts運用.md`、`README.md` を新サンプルへ更新。
- 旧形式の `artifacts/2026-05-23-summary-html-artifact-sample.html` を削除。

## [2026-05-24] query | Artifact samples 運用追加

- Artifact 生成スキルやテンプレート検証用サンプルを `artifacts/samples/html-artifact/vNNN/` に分離する方針を追加。
- 既存の新標準サンプルを `artifacts/samples/html-artifact/v001/` へ移動し、ファイル名を `sample.*` に統一。
- `.github/skills/html-artifact/SKILL.md`、`wiki/concepts/Artifacts運用.md`、`AGENTS.md`、`README.md`、`wiki/index.md` を更新。

## [2026-05-26] query | rawデータ運用フロー整理

- `raw/` に置く一次資料の種類ごとの対応フローとして `wiki/concepts/Rawデータ運用.md` を作成。
- 論文、Web記事、書籍メモ、会話ログ、表データ、画像、コード・実験ログの保存先、ingest観点、wiki反映先、Artifact化条件を整理。
- `wiki/index.md` と `wiki/concepts/Artifacts運用.md` に関連リンクを追加。

## [2026-05-26] query | PDFからMarkdown変換品質メモ

- PDF を raw データとして扱う際の Markdown 変換品質メモとして `wiki/analyses/2026-05-26_PDFからMarkdown変換品質.md` を作成。
- 自宅環境と会社環境で利用できる AI / 開発ツールの違いを整理し、資料の機密性を優先して処理場所を分ける方針を記録。
- `wiki/concepts/Rawデータ運用.md` に PDF 変換方針を追記し、`wiki/index.md` から分析ページへ辿れるように更新。

## [2026-05-26] query | PDF変換ルート見直し

- 日本語資料を前提に、ページ画像を 5 ページ単位 ZIP にまとめて LLM に渡す画像LLM軽量ルートを第一候補として整理。
- 自宅環境では GPT-5.5 専用プロジェクト、会社環境では M365 Copilot Premium 専用エージェントを使う方針を記録。
- Docling / Marker は必須の前処理ではなく、大量処理、再現性、比較検証が必要な場合の拡張候補として位置づけ直した。

## [2026-05-26] query | PDFページ画像化スクリプト追加

- 会社環境で M365 Copilot Premium にページ画像を直接渡す前提に合わせ、PDF を `page-001.png` 形式へ変換する `scripts/pdf_to_page_images.py` を追加。
- 5ページ単位 ZIP 前提を廃止し、`wiki/analyses/2026-05-26_PDFからMarkdown変換品質.md` と `wiki/concepts/Rawデータ運用.md` をページ画像直接入力の方針へ更新。

## [2026-05-26] query | PDF Markdown 化の主処理環境見直し

- 自宅環境では Codex CLI + VS Code、会社環境では GitHub Copilot Enterprise + VS Code を主軸にして、ページ画像からページ単位 Markdown を作成する方針へ更新。
- ChatGPT 5.5 / M365 Copilot は主処理ではなく、補助・比較・難ページ対応として扱う。
- ページ単位 Markdown の保存先として `raw/assets/{資料名}/md/page-001.md` と、結合版 `{資料名}.pages.md` の運用を追加。

## [2026-05-26] query | PDFページ画像Markdown化スキル追加

- ページ番号付きPDF画像を原文忠実な Markdown に変換するためのリポジトリ内スキル `.github/skills/pdf-page-image-markdown/SKILL.md` を追加。
- `raw/assets/{資料名}/pages/page-001.png` から `raw/assets/{資料名}/md/page-001.md` へ変換する保存規則、品質チェック、ページブロック形式を定義。

## [2026-05-26] query | スキル段階評価フロー追加

- 新規作成・大幅改訂したリポジトリ内スキルを軽量に段階評価する `.github/skills/skill-validation-ramp/SKILL.md` を追加。
- Trigger確認、本文整合性、最小サンプル、中程度サンプル、難ケース、最小修正、再確認の流れを定義。
- 同種失敗の再発や出力形式の不安定さがある場合は `empirical-prompt-tuning` にエスカレーションする条件を明記。

## [2026-05-26] query | PDFページ画像Markdown化スキル最小評価

- `skill-validation-ramp` を使い、`.github/skills/pdf-page-image-markdown/SKILL.md` の Trigger確認、本文整合性確認、最小サンプル実行を実施。
- `raw/assets/sample_a4/pages/page-001.png` を `raw/assets/sample_a4/md/page-001.md` に Markdown 化し、評価ログを `.github/skills/pdf-page-image-markdown/references/evaluation-log.md` に記録。

## [2026-05-26] query | スキル評価フローの人間確認前提追加

- `skill-validation-ramp` を更新し、内容の正しさ、原文との意味ズレ、採用可否の最終判断は人間が行う前提を明記。
- AI 側の評価範囲を、出力形式、保存先、禁止事項、曖昧箇所の扱い、再実行しやすさの確認に寄せた。
- `pdf-page-image-markdown` の評価ログに `Human Review: pending` を追加。

## [2026-05-26] query | PDFページ画像Markdown化スキル人間確認

- `raw/assets/sample_a4/pages/page-001.png` から作成した `raw/assets/sample_a4/md/page-001.md` について、人間確認で内容のズレがないことを確認。
- `.github/skills/pdf-page-image-markdown/references/evaluation-log.md` を `Human Review: OK` に更新し、現段階では最小サンプルに対するスキル性能は十分と記録。

## [2026-07-04] ingest | Case SL12 仕様項目一覧を knowledge.duckdb へ raw 取り込み

- `raw/inbox/CASE_SAL/Case_SL12_仕様項目一覧.xlsx` を新規作成した汎用ローダー `db/scripts/load_excel_raw_to_duckdb.py` で `db/knowledge.duckdb` に取り込み。
- シートごとに raw テーブル化: `case_sl12_仕様項目一覧_{概要,仕様,寸法,転倒荷重,装備,注記}`（計 139 行）。列名は Excel の原文のまま、各行に `raw_path` / `sheet_name` / `row_no` を付与。
- 取り込み履歴テーブル `excel_imports` を新設し、`db/schema.sql` を DB から自動生成して同期。対応表は `db/loaders.md` に記録。
- wiki ページ（sources / entities）への反映は未実施。必要になった時点で通常の ingest フローで作成する。

## [2026-07-04] query | knowledge.duckdb 用の読み取り専用ブラウザビューア追加

- 人間がテーブルを確認するための `db/scripts/view_duckdb.py` を追加。Python 標準ライブラリ + duckdb パッケージのみで動くローカル Web ビューア（localhost:8765）。
- テーブル一覧・プレビュー・ページ送り・ソート・絞り込み・SELECT 系クエリ実行に対応。接続は常に read_only かつリクエスト単位で開閉し、書き込み不可・ローダーとの同時実行可を確認済み。
- `db/README.md` の「中身の確認」にビューアの使い方を追記。

## [2026-07-05] ingest | raw/inbox/CASE の未追加 xlsx を knowledge.duckdb へ raw 取り込み

- `raw/inbox/CASE/` の xlsx 10 件を確認し、既存の `case_sl12_仕様項目一覧_*` とプレフィックスが衝突する `Case_SL12_仕様項目一覧.xlsx` は上書き回避のため除外。
- 未追加の 9 件を `db/scripts/load_excel_raw_to_duckdb.py` で `db/knowledge.duckdb` に取り込み、シートごとに raw テーブル化（計 49 テーブル、1,168 行）。
- 取り込み対象: `Case_SAL_catalog_specs_with_features_revised.xlsx`、`Case_SL12TR_仕様項目一覧.xlsx`、`Case_SL15_仕様項目一覧.xlsx`、`Case_SL22EV_仕様項目一覧.xlsx`、`Case_SL23_仕様項目一覧.xlsx`、`Case_SL27TR_仕様項目一覧.xlsx`、`Case_SL27_仕様項目一覧.xlsx`、`Case_SL35TR_仕様項目一覧.xlsx`、`Case_SL50TR_仕様項目一覧.xlsx`。
- `db/schema.sql` を DB の実テーブルから自動再生成し、対応表を `db/loaders.md` に追記。wiki ページ（sources / entities）への反映は未実施。

## [2026-07-05] ingest | AVANT 型式・仕様一覧を knowledge.duckdb へ raw 取り込み

- `raw/inbox/AVANT/AVANT_型式_仕様一覧.xlsx` を `db/scripts/load_excel_raw_to_duckdb.py` で `db/knowledge.duckdb` に取り込み。
- シートごとに raw テーブル化: `avant_型式_仕様一覧_{型式一覧,仕様一覧,油圧システム,旧型モデル,シリーズ行_除外,修正メモ}`（計 6 テーブル、641 行）。
- `db/schema.sql` を DB の実テーブルから自動再生成し、対応表を `db/loaders.md` に追記。wiki ページ（sources / entities）への反映は未実施。

## [2026-07-05] ingest | AVANT 型式・仕様一覧のシート削除反映

- 更新済みの `raw/inbox/AVANT/AVANT_型式_仕様一覧.xlsx` を再取り込みし、現行シート `型式一覧`、`仕様一覧`、`油圧システム`、`旧型モデル` の 4 テーブルへ更新（計 633 行）。
- 削除済みシート `シリーズ行_除外`、`修正メモ` 由来の旧テーブルが DB に残らないよう、`db/scripts/load_excel_raw_to_duckdb.py` を同一プレフィックスの既存テーブル削除後に再作成する挙動へ修正。
- `db/schema.sql` を DB の実テーブルから自動再生成し、`db/loaders.md` の AVANT 行を現行 4 テーブルに更新。

## [2026-07-05] ingest | Gianni Ferrari Turboloader 仕様一覧を knowledge.duckdb へ raw 取り込み

- `raw/inbox/GIanniFerrari/Gianni_Ferrari_Turboloader_仕様一覧.xlsx` を `db/scripts/load_excel_raw_to_duckdb.py` で `db/knowledge.duckdb` に取り込み。
- シートごとに raw テーブル化: `gianni_ferrari_turboloader_仕様一覧_{概要,仕様一覧,機能説明,アタッチメント一覧,アタッチメント仕様,荷重図メモ}`（計 6 テーブル、345 行）。
- `db/schema.sql` を DB の実テーブルから自動再生成し、対応表を `db/loaders.md` に追記。wiki ページ（sources / entities）への反映は未実施。

## [2026-07-05] ingest | GIANT xlsx 一式を knowledge.duckdb へ raw 取り込み

- `raw/inbox/GIANT/` の xlsx 13 件を `db/scripts/load_excel_raw_to_duckdb.py` で `db/knowledge.duckdb` に取り込み。
- 対象は `Giant_G1200_TELE_仕様一覧.xlsx`、`Giant_G1200_仕様一覧.xlsx`、`Giant_G1500_Series_仕様一覧.xlsx`、`Giant_G2200E_Series_仕様一覧.xlsx`、`Giant_G2300_HD_仕様一覧.xlsx`、`Giant_G2500_Series_仕様一覧.xlsx`、`Giant_G2700_Series_仕様一覧.xlsx`、`Giant_G3500_Series_仕様一覧.xlsx`、`Giant_G5000_Series_仕様一覧.xlsx`、`Giant_G5000_TELE_Series_仕様一覧.xlsx`、`Giant_GS_Series_仕様一覧.xlsx`、`Giant_GT5048_Series_仕様一覧.xlsx`、`GIANT_型式分類一覧.xlsx`。
- シートごとに raw テーブル化（計 42 テーブル、565 行）。`db/schema.sql` を DB の実テーブルから自動再生成し、対応表を `db/loaders.md` に追記。
- wiki ページ（sources / entities）への反映は未実施。

## [2026-07-05] ingest | MultiOne xlsx 一式を knowledge.duckdb へ raw 取り込み

- `raw/inbox/MultiOne/` の xlsx 14 件を `db/scripts/load_excel_raw_to_duckdb.py` で `db/knowledge.duckdb` に取り込み。
- 対象は `MultiOne_1_1_仕様一覧.xlsx`、`MultiOne_2_3_EFI_仕様一覧.xlsx`、`MultiOne_5_2_K_iD_仕様一覧.xlsx`、`MultiOne_5_3_K_iD_仕様一覧.xlsx`、`MultiOne_6_3_iDS_仕様一覧.xlsx`、`MultiOne_7_2_K_仕様一覧.xlsx`、`MultiOne_8_4_TurboS_仕様一覧.xlsx`、`MultiOne_8_5_Y_仕様一覧.xlsx`、`MultiOne_8_5S_K_仕様一覧.xlsx`、`MultiOne_11_5_Y_仕様一覧.xlsx`、`MultiOne_11_6_K_TurboS_仕様一覧.xlsx`、`MultiOne_EZ7_仕様一覧.xlsx`、`MultiOne_EZ8_EZ8_Long_Range_仕様一覧.xlsx`、`MultiOne_WHEELS_仕様一覧.xlsx`。
- シートごとに raw テーブル化（計 42 テーブル、1,486 行）。`db/schema.sql` を DB の実テーブルから自動再生成し、対応表を `db/loaders.md` に追記。
- wiki ページ（sources / entities）への反映は未実施。

## [2026-07-05] ingest | Yanmar CL26 仕様一覧を knowledge.duckdb へ raw 取り込み

- `raw/inbox/Yanmar/Yanmar_CL26_仕様一覧.xlsx` を `db/scripts/load_excel_raw_to_duckdb.py` で `db/knowledge.duckdb` に取り込み。
- シートごとに raw テーブル化: `yanmar_cl26_仕様一覧_{概要,仕様一覧,特徴,注記・原文}`（計 4 テーブル、32 行）。
- `db/schema.sql` を DB の実テーブルから自動再生成し、対応表を `db/loaders.md` に追記。wiki ページ（sources / entities）への反映は未実施。
