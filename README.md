# LLM Wiki

研究用の個人 LLM Wiki の default 構成です。

一次資料を `raw/` に置き、Codex / LLM が内容を読んで `wiki/` に要約・概念・関連項目・索引・作業ログとして整理します。単なるファイル置き場ではなく、資料を取り込むたびに知識を構造化して育てるためのリポジトリです。

この repository は、個別テーマを入れる前の標準形として、`raw/`、`wiki/`、`db/`、`artifacts/`、運用スキル、軽量 lint を揃えています。

## まず読むもの

- `wiki/index.md`: wiki 全体の索引。調べものはここから始めます。
- `wiki/overview.md`: 研究テーマ全体の概観。
- `wiki/log.md`: いつ何を更新したかの作業ログ。
- `AGENTS.md`: Codex / LLM が守る運用ルール。

## ディレクトリ構成

- `raw/inbox/`: これから取り込む未処理の一次資料。
- `raw/sources/`: 処理済みの一次資料。
- `raw/data/`: CSV、Excel、JSON、Parquet など、DB に取り込む元データ。
- `raw/archives/`: 古い版や廃止版など、再現のために残す過去データ。
- `raw/assets/`: 画像や添付ファイルなどの素材。
- `db/`: DuckDB を中心とした構造化データ層。標準 DB は `db/knowledge.duckdb`。SQL 定義は `db/schema.sql` に置き、DuckDB のテーブル変更と同じ変更で同期します。
- `wiki/sources/`: 個別ソースの要約ページ。
- `wiki/concepts/`: 概念・テーマ・手法の整理ページ。
- `wiki/entities/`: 人物・組織・論文・データセットなどの固有項目ページ。
- `wiki/analyses/`: 比較、論点整理、質問から生まれた分析ページ。
- `artifacts/`: `wiki/` の知識や、必要に応じて `raw/` の一次資料をもとに、人間が読みやすい形へ可視化した成果物を保存する場所。内容の正本は Markdown、標準の表示物は Web HTML として保存します。印刷・スライド用 HTML は明示的に必要な場合だけ追加します。

## 基本の使い方

### 新しい wiki として使い始める

1. `wiki/overview.md` の研究テーマ欄を、自分のテーマに合わせて書き換えます。
2. 取り込みたい資料を `raw/inbox/` に置きます。
3. Codex に `ingest ファイル名` と依頼し、Triage を確認します。
4. 承認後、source summary、関連ページ、索引、ログを一体で更新します。

既存の `raw/assets/sample_*` と `artifacts/samples/` は、PDF 画像化や HTML Artifact の検証用サンプルです。通常の知識本体とは分けて扱います。

### 資料を取り込む

1. 取り込みたい資料を `raw/inbox/` に置きます。
2. Codex に `ingest ファイル名` と依頼します。
3. Codex がまず Triage を返します。
4. 内容を確認して承認すると、関連する `wiki/` ページ、索引、ログが更新されます。

表データを CSV に変換するなら、`python scripts/xlsx_to_csv.py raw/inbox/資料.xlsx` のように実行すると既定で `raw/data/` に出力します。

Triage では、document classification、主なテーマ、影響を受ける既存ページ、新規作成・更新が必要なページ、潜在的な矛盾や注意点を先に確認します。

ingest の実行時は、まず `wiki/index.md` を読み、関連する既存ページを探します。そのうえで `Read -> Classify -> Extract -> Update/Create pages -> Cross-link -> Update index/log` の順に進めます。詳細な手順は `.github/skills/wiki-ingest/SKILL.md` に分離し、必要なときだけ読み込む想定です。

source summary を作るときは、取得元を後から追えるように、少なくとも `source_path`、`origin_type`、`origin_reference`、`origin_captured_on`、`origin_captured_by`、`provenance_status` を frontmatter に入れます。URL が無い添付資料でも、受領経路を `origin_reference` に残します。

構造化データを含む資料では、承認後に `db/knowledge.duckdb` と `db/schema.sql` を同じ変更で更新する候補も整理します。DuckDB のテーブルを削除したら対応する SQL 定義も削除し、xlsx から新しい表を追加したら対応する SQL 定義も追加します。DB は比較・集計・条件抽出に使い、要約や解釈は `wiki/` に残します。

使い分けの基本は、保存と人間編集は `raw/data/` の CSV / Excel / JSON / Parquet、活用と分析は `db/knowledge.duckdb` です。

モデル系の表データは、raw と curated を分けて扱います。Excel をそのまま保持したいときは `db/scripts/load_excel_raw_to_duckdb.py` で raw テーブルへ入れ、日常の確認や分析では `loader_specifications_current` view を入口にします。curated 更新は `db/scripts/load_loader_specifications_curated.py` を使います。

page 作成時の基本ルール:

- `raw/` は既存ファイルを編集しません。
- 既存ページがあれば原則 merge し、新規ページ乱立を避けます。
- 矛盾があれば上書きせず、`競合` または `未確定` として残して人間確認に回します。
- concept / entity / source の各ページ先頭には、関連性判定のための 1 行 summary を置きます。
- 主要 claim には、可能な限り source summary または `raw/` / page Markdown への参照を添えます。
- `[[Wikilinks]]` は片方向で終えず、必要な範囲で双方向に保ちます。
- DB に入れる値は、可能な限り `source_id` や `source_path` で原本へ辿れるようにします。

テンプレート:

- `wiki/sources/_source_template.md`
- `wiki/concepts/_concept_template.md`
- `wiki/entities/_entity_template.md`

命名規則:

- concept は `wiki/concepts/概念名.md`
- entity の人物名は `wiki/entities/Firstname-Lastname.md`
- 既存ページと表記差がある場合は、新規作成より先に merge 先を探します

PDF の標準処理フロー:

1. PDF 原本は `raw/inbox/` に置いたまま保持します。
2. `python scripts/pdf_to_page_images.py raw/inbox/資料名.pdf --dpi 400` で `raw/assets/{資料名}/pages/page-001.png` 形式へ画像化します。
3. VS Code 上の AI エージェントでページ画像を `raw/assets/{資料名}/md/page-001.md` 形式へ Markdown 化します。
4. Markdown 化は原則 1 ページずつ行い、各ページを人間が確認してから次ページへ進みます。
5. 必要に応じてページ単位 Markdown を結合し、その後に通常の ingest フローへ進みます。

ページ単位 Markdown の先頭コメントでは、元画像を `source: ../pages/page-001.png` のような相対パスで持たせます。

### wiki に質問する

Codex に質問するときは、原則として `wiki/index.md` から関連ページを探し、必要なページを読んだうえで回答します。

数値比較、条件抽出、ランキング、時系列整理などが必要な場合は、`db/knowledge.duckdb` を使って SQL で確認し、必要に応じて結果を `wiki/analyses/` や `artifacts/` に整理します。

重要な比較や再利用価値のある整理が生まれた場合は、必要に応じて `wiki/analyses/` に整理し、さらに人間が読みやすい形で見せたいものは `artifacts/` に Markdown 正本と Web HTML として可視化します。印刷・スライド用途が明確な場合だけ、A4版やスライド版も追加します。

### 構造化データを扱う

最初は DuckDB を1つだけ使います。

- 標準 DB: `db/knowledge.duckdb`
- SQL 定義: `db/schema.sql`
- 元データ置き場: `raw/data/`

CSV などの元データは原本・編集用として残し、AI が比較、集計、結合、ランキングを行うときは DuckDB を使います。

モデル仕様のように内部で正規化しているデータでも、普段は `loader_specifications_current` のような参照用 view から見る運用を基本にします。

Python の `duckdb` パッケージを導入した後、以下のように初期化できます。

```powershell
python -m pip install -r requirements.txt
python -c "import duckdb; con=duckdb.connect('db/knowledge.duckdb'); con.execute(open('db/schema.sql', encoding='utf-8').read()); con.close()"
```

現時点では、空の `.duckdb` バイナリではなく `db/schema.sql` を更新対象にします。Python 依存関係は `requirements.txt` にまとめています。

### HTML Artifact として可視化する

後から参照したい内容は、`wiki/` に蓄積された知識や、必要に応じて `raw/` の一次資料をもとに、`artifacts/` へ Markdown 正本と Web HTML として可視化します。印刷・PDF・スライド出力が必要な場合だけ、用途別 HTML を追加します。

`artifacts/` は一次情報の主保管場所ではありません。主な知識は `wiki/` に置き、`artifacts/` はそれをレポート、スライド、比較表、図解、ダッシュボードなどとして見やすく提示するための表示レイヤーです。

Artifact は `artifacts/<artifact-id>/` にフォルダ単位で保存します。フォルダ内の `*.md` が内容の正本です。HTML は、その Markdown をもとに作る表示物です。内容を直す場合は、原則として Markdown 側を直します。A4やスライドを追加生成した場合、その見た目だけを直すときは対応するHTMLを個別に調整します。

標準の出力形式:

- `*.web.html`: ブラウザ閲覧用の切れ目のないページ。

明示的に必要な場合だけ追加する出力形式:

- `*.a4.html`: A4印刷/PDF用のページ区切りがある資料。
- `*.slides.html`: 16:9スライド/PDF/PowerPoint用のページ区切りがある資料。

同じ Markdown から生成しますが、追加出力する場合でも各HTMLは同じ見た目にはしません。Markdown はタイトル、章、節、表、図、根拠などの意味構造として扱い、Web は連続ページ、A4 は印刷資料、Slides は発表資料としてそれぞれ最適化します。

例:

- `artifacts/samples/html-artifact/v001/sample/sample.md`
- `artifacts/samples/html-artifact/v001/sample/sample.web.html`

このサンプルは、`md -> web html` の標準フローを確認するための検証用サンプルです。A4版・スライド版の検証が必要な場合は、同じフォルダに `*.a4.html` と `*.slides.html` も置きます。

生成スキルやテンプレートの検証用サンプルは、通常の成果物と分けて `artifacts/samples/html-artifact/vNNN/<sample-id>/` に置きます。各サンプルフォルダに同じ basename の `*.md` と `*.web.html` を置くことで、差分確認しやすくします。A4版・スライド版を検証する場合だけ、`*.a4.html` と `*.slides.html` も置きます。

## 運用方針

- 回答、要約、ログは日本語で書きます。
- `raw/` は一次資料の保管庫として扱い、既存ファイルは原則編集しません。
- `wiki/` は LLM が保守する知識ベースです。
- 断定的な記述には、できるだけ出典を添えます。
- 新しい情報が既存記述と矛盾する場合は、上書きせず「競合」「未確定」として残します。
- 1回の ingest では、要約、関連ページ更新、索引更新、ログ追記までを1セットで行います。

## Codex への依頼例

```text
ingest raw/inbox/example.pdf
```

```text
wiki の中で HTML Artifact 運用について説明して
```

```text
artifacts のサンプル HTML を初見向けに解説して
```

```text
lint して、孤立ページやリンク不足を確認して
```

## 保守コマンド

wiki の基本整合性は、次のコマンドで確認できます。

```powershell
python scripts/lint_wiki.py
python -m py_compile scripts/lint_wiki.py scripts/pdf_to_page_images.py
```

`scripts/lint_wiki.py` は、必須ディレクトリ、必須ファイル、`[[Wikilink]]` の解決、`wiki/index.md` のパス参照、主要ページの基本セクション、`wiki/log.md` の見出し形式を確認します。

## 現在の状態

現時点では、LLM Wiki default として、raw / wiki / db / artifacts の標準ディレクトリ、source / concept / entity テンプレート、PDF ページ画像化スクリプト、wiki lint スクリプトが揃っています。wiki 全体の現在地は `wiki/index.md` を確認してください。
