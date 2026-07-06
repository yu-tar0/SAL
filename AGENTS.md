# LLM Wiki 運用スキーマ

このリポジトリは、研究用の個人 LLM Wiki です。LLM はこのスキーマに従って wiki を保守します。

## 基本原則

- 回答・要約・ログ記述は日本語で行う。
- 要約セクションの見出しは、資料・成果物の本文言語に合わせる。日本語では `要約`、英語では `Summary` を使い、原則として `TL;DR` は使わない。
- `raw/` は一次資料の保管庫であり、LLM は既存ファイルを編集しない。
- `wiki/` は LLM が保守する知識ベースであり、Markdown を中心に更新する。
- 断定的な記述には、可能な限り出典ページを添える。
- 新しい情報が既存記述と矛盾する場合は、上書きせず「競合」「未確定」として明示する。
- 1回の ingest では、要約・関連ページ更新・索引更新・ログ追記までを1セットで行う。

## ディレクトリ構成

- `raw/inbox/`: 未処理の一次資料。
- `raw/sources/`: 処理済み一次資料。ファイル名は保持してよい。
- `raw/data/`: CSV、Excel、JSON、Parquet など、DB 取り込み元になる表形式・構造化データ。
- `raw/archives/`: 古い版、廃止版、再現用に保持する過去データ。
- `raw/assets/`: 画像や添付ファイル。
- `db/`: DuckDB を中心とした構造化データ層。標準 DB は `db/knowledge.duckdb`。SQL 定義は `db/schema.sql` に置き、DuckDB のテーブル変更と同じ変更で同期する。
- `wiki/index.md`: wiki 全体の索引。
- `wiki/log.md`: 作業ログ。追記専用。
- `wiki/overview.md`: 研究テーマ全体の概観。
- `wiki/sources/`: 各ソースの要約ページ。
- `wiki/concepts/`: 概念・テーマ・手法ページ。
- `wiki/entities/`: 人物・組織・論文・データセットなど固有項目ページ。
- `wiki/analyses/`: 比較、論点整理、質問から生まれた分析ページ。
- `artifacts/`: `wiki/` の知識や、必要に応じて `raw/` の一次資料をもとに、Markdown 正本と標準の Web HTML として可視化した成果物の永続化先。A4版・スライド版は明示依頼時だけ追加する。

## 命名規則

- ソース要約ページ: `wiki/sources/YYYYMMDD_短い識別子.md`
- 概念ページ: `wiki/concepts/概念名.md`
- エンティティページ: `wiki/entities/項目名.md`
- 分析ページ: `wiki/analyses/YYYYMMDD_トピック.md`

英数字と日本語の混在は許容するが、過度に長いファイル名は避ける。

## 必須ワークフロー

### 1. ingest

あなたは私の LLM Wiki の知識コンパイラとして機能する。初期構成はすでに完了している。以降の ingest は、以下の厳格な手順で実行する。

ingest のコアルールはこの `AGENTS.md` に残し、詳細な手順・分類・更新チェックリストは `.github/skills/wiki-ingest/SKILL.md` を正とする。実際に ingest を行うときは、必要なときだけその skill を読む。

#### 基本コマンド

- ユーザーが `ingest [filename]` または `ingest` と言ったら、このワークフローを開始する。

#### 必須処理ステップ

以下を必ずこの順番で実行する。

1. 既存ページ探索
   - まず `wiki/index.md` を読み、既存の source / concept / entity / analysis の関連ページ候補を洗い出す。
   - 既存ページがあれば、原則として新規乱立ではなく更新候補として扱う。

2. ソース読み込み
   - `raw/` フォルダ内の指定ファイルを読み込む。
   - `raw/` は一次資料の保管庫として扱い、既存ファイルは編集しない。

3. Document Classification
   - ソースを最初に分類する。少なくとも `research_paper` `proposal` `meeting_notes` `book_chapter` `web_article` `video_summary` `tweet_or_short_post` `dataset` `image` `other` のどれに近いかを判定する。
   - 分類結果に応じて抽出深度を変える。長大な論文・提案書・書籍章はセクション単位で処理し、短い投稿や短文資料は主な洞察と明示的な事実に絞る。
   - 用語ゆれがありそうな主要語は、この段階で既存ページ名と照合し、正規の表記候補を決める。

4. Triage（影響範囲レポート）
   - まず最初に以下をレポートする。
   - このソースの document classification と、想定する抽出深度
   - このソースの主なテーマ・キーポイント
   - 影響を受けると考えられる既存ページ（`entity` / `concept` / `sources` など）
   - DB 更新が必要な場合は、対象テーブル、キー、追加・更新・競合候補
   - 作成・更新が必要なページの一覧
   - 特に注意すべきリンクや潜在的な矛盾
   - 既存ページへ merge するか、新規作成するかの初期判断
   - 1つのソースで 10〜15 ページ程度に影響することは普通とみなす。
   - ここで一旦ユーザーの承認を待つ。これを `Triage-first ingest` とする。

5. 人間との議論（Key Takeaways）
   - 重要な takeaway を簡潔にまとめ、ユーザーと議論する。
   - 特に初回や重要な資料では、`one at a time` で確認しながら進める。

6. Extract
   - 分類結果に応じた粒度で、主要 claim、観察事実、数値、固有名詞、未確定点、既存知識と衝突する点を抽出する。
   - 長文資料ではセクションごとに抽出メモを作り、最後に統合する。
   - claim は可能な限り `raw/` または page Markdown を根拠として参照できる形で残す。
   - 構造化できる観察事実は、`db/schema.sql` に入れる候補として整理する。

7. Wiki 更新実行（承認後）
   - DB 更新が必要な場合は、`db/knowledge.duckdb` と `db/schema.sql` を同じ変更で更新する。テーブルを削除したら対応する SQL 定義も削除し、xlsx からテーブルを追加したら対応する SQL 定義も追加する。更新前に対象行、キー、source_id、競合扱いを確認する。
   - `wiki/sources/` にサマリーページを作成または更新する。
   - 関連する `entity` ページと `concept` ページを適切に更新する。既存ページがあれば原則 merge を優先し、重複ページは避ける。
   - 必要に応じて `wiki/overview.md` も更新する。
   - `wiki/index.md` を更新する。カテゴリ別目次、1行サマリ、必要なメタデータを含める。
   - `wiki/log.md` に追記する。時系列順、prefix 統一、grep しやすい形式を維持する。
   - 適切な `[[Wikilink]]` を関連ページに張る。新規ページから既存ページへの片方向リンクで終えず、必要なら関連先にも戻りリンクを足して双方向の導線を保つ。
   - 1つのソースから複数ページを積極的に更新する。

8. Cross-link と整合確認
   - 新しく追加した概念名・固有項目名が、既存の命名規則と整合しているかを確認する。
   - 矛盾があれば上書きせず、`競合` `未確定` などの明示的ラベルを付けて人間確認事項として残す。
   - 用語の代表表記を 1 つに寄せ、別名は `aliases` などで補助する。

#### 重要原則

- LLM Wiki の価値は、知識を ingest 時に構造化・統合し、複数ページへ反映して複利的に育てる点にある。
- RAG のように「検索して終わり」ではなく、ingest 時点で知識をコンパイルする。
- 人間の監督を優先する。特に序盤は丁寧に確認しながら進める。

#### ベストプラクティス

- Page Template を厳守する。
- source summary を含む各ページには、少なくとも `frontmatter`、ページ先頭の 1 行 summary、言語に応じた要約セクション（日本語は `要約`、英語は `Summary`）、`Related Links`、`Provenance`、`Last Updated` を入れる。
- claim は可能な限り source summary または `raw/` / page Markdown にひもづく出典を添える。
- concept / entity / source で文書構造をそろえ、先頭の 1 行 summary で関連性を素早く判断できるようにする。
- 命名は一貫させる。概念ページは `wiki/concepts/概念名.md`、人物エンティティは `wiki/entities/Firstname-Lastname.md`、組織・資料名は既存の代表表記に合わせる。
- トークン効率を意識し、重いロジックは専用スキルや専用ワークフローに分離できる前提で、本体の指示は簡潔に保つ。
- 定期的に lint を実行し、矛盾検知、孤立ページ、陳腐化を点検する。

### 2. query

質問に答えるときは、まず `wiki/index.md` を見て関連ページを特定し、その後に該当ページを読む。重要な比較や新しい整理が生まれた場合は、`wiki/analyses/` に保存して再利用可能にする。

### 3. lint

定期的に以下を点検する。

- 孤立ページ
- 相互リンク不足
- 古い記述
- 出典不明の断定
- 矛盾の未整理
- 重要概念のページ不足

lint を実行したら `wiki/log.md` に記録する。

### 4. artifacts

クエリに対する回答・分析・比較・まとめなどで再利用価値の高い整理が生まれた場合、`wiki/` の知識や必要に応じた `raw/` の一次資料をもとに、まず単一 Markdown Artifact として内容を整理し、それを標準の Web HTML として `artifacts/` に可視化し、`wiki/` と統合する。A4版・スライド版は明示依頼時だけ追加する。

`artifacts/` は一次情報や知識の主保管場所ではなく、`wiki/` / `raw/` を入力元にした表示レイヤーとして扱う。

Markdown は内容の正本、HTML は閲覧・共有・印刷・PDF出力のための表示物として扱う。標準では `web.html` のみを生成する。`a4.html` と `slides.html` は、ユーザーが明示的に求めた場合だけ追加生成する。内容修正は原則 Markdown 側に入れ、HTML の直接編集は各形式のレイアウトやHTML固有の表現調整に限る。

Markdown はレイアウト指定ではなく意味構造として扱う。`web.html` は連続ページとして表示する。追加生成する場合、`a4.html` は印刷資料として比較的忠実に整形し、`slides.html` はプレゼン向けに要約・分割して再構成してよい。

詳細な作成手順とテンプレート要件は `.github/skills/html-artifact/SKILL.md` を正とする。

#### 適用条件

単なる会話ではなく、後から参照・印刷・PDF出力する価値がある場合に適用します。
対象例は、比較表、深い分析、合成洞察、スライド案、コード、図案、フレームワーク、レポート、ダッシュボードなどです。
基本的に Triage-first を徹底し、保存前にユーザー承認を得る。

#### 命名規則

`artifacts/YYYY-MM-DD-[カテゴリ]-[簡潔タイトル]/YYYY-MM-DD-[カテゴリ]-[簡潔タイトル].md`
`artifacts/YYYY-MM-DD-[カテゴリ]-[簡潔タイトル]/YYYY-MM-DD-[カテゴリ]-[簡潔タイトル].web.html`

必要に応じた追加出力:

- `artifacts/YYYY-MM-DD-[カテゴリ]-[簡潔タイトル]/YYYY-MM-DD-[カテゴリ]-[簡潔タイトル].a4.html`
- `artifacts/YYYY-MM-DD-[カテゴリ]-[簡潔タイトル]/YYYY-MM-DD-[カテゴリ]-[簡潔タイトル].slides.html`

例:

- `artifacts/2026-05-22-comparison-claude4-vs-grok4/2026-05-22-comparison-claude4-vs-grok4.md`
- `artifacts/2026-05-22-comparison-claude4-vs-grok4/2026-05-22-comparison-claude4-vs-grok4.web.html`

#### ベストプラクティス

- 人間の監督を尊重する。特に最初は必ず承認を得る。
- 1つの Artifacts 作成で関連 wiki ページを複数更新してもよい。
- Markdown には入力元 wiki ページ、入力元 raw 資料、変換先 HTML を明記する。
- HTML には元 Markdown への参照を入れる。
- `web.html` は切れ目のないブラウザ閲覧用の標準出力とする。
- A4印刷/PDF用の `a4.html`、16:9スライド/PDF/PowerPoint用の `slides.html` は、ユーザーが明示的に求めた場合だけ追加生成する。
- 追加生成した場合は、`web.html` を閲覧入口とし、必要に応じて `a4.html` と `slides.html` へリンクする。
- Artifact 生成スキルやテンプレート検証用のサンプルは、通常の成果物と分けて `artifacts/samples/html-artifact/vNNN/` に配置する。
- 画像・図は Artifact フォルダ内の `assets/` に保存し、HTML 内から相対リンクで参照する。
- 定期的に lint を実行し、孤立 Artifacts を防ぐ。

## ソース要約ページの形式

ソース要約ページには、最低限以下を含める。

- frontmatter
- 要約（英語資料・英語成果物では `Summary`）
- 書誌情報
- 要点3-7件
- 詳細メモ
- Related Links
- Provenance
- Last Updated
- 既存 wiki への反映先
- 未解決の問い

`wiki/sources/_source_template.md` を source summary の雛形として使う。`wiki/concepts/_concept_template.md` と `wiki/entities/_entity_template.md` を、概念ページとエンティティページの雛形として使う。

## トラクタ・インプルメント整理方針

トラクタ関連資料を整理する際は、製品カタログ起点ではなく「ユーザーが行いたい作業」を主語にする。
基本関係は `作業 → 必要なインプルメント → 使用可能なトラクタ → 必要条件・制約・注意点` として扱う。

トラクタはユーザーにとって仕事道具であるため、単体スペックだけでなく「何の作業ができるか」を重視する。トラクタとインプルメントの組み合わせは中核情報とみなし、作業適合性、互換性、必要能力、制約、未確定点を構造化する。

CSV や DB に整理する場合は、少なくとも `tasks`、`tractors`、`implements`、`tractor_capabilities`、`implement_requirements`、`task_implement_options`、`tractor_implement_compatibility` に相当する情報を分けて扱う。対応可否は根拠に応じて `confirmed` / `candidate` / `uncertain` / `conflict` などの状態を持たせ、資料上の候補を断定的な適合として扱わない。

## DB運用方針

- 最初は `db/knowledge.duckdb` 1つで運用する。複数 DB は、データ量、更新頻度、共有範囲、再生成単位を分ける必要が出てから検討する。
- SQL 定義は `db/schema.sql` にまとめ、DuckDB のテーブル追加・削除と同じ変更で管理する。ドメイン固有テーブルは、汎用の `sources` / `entities` / `observations` / `relationships` では扱いにくい反復用途が出てから追加する。
- `raw/data/` は DB 取り込み元の元データ置き場であり、既存ファイルは編集しない。古い版は必要に応じて `raw/archives/` に保持する。
- DB の各行は、可能な限り `source_id` や `source_path` によって `raw/` または source summary へ辿れるようにする。行単位で raw の具体位置を示す必要がある場合は、`raw_path` と `raw_locator` を使う。
- wiki ページには、必要に応じて `db_entity_id` や `db_source_id` を frontmatter に持たせる。
- 定量仕様、日付、分類、状態は DB の固定列や `observations` に置く。短い定性メモは DB の `notes` / `value_text` に置いてよい。長文、自由記述、判断理由、思考メモは wiki の Markdown に置き、DB 側の `wiki_path` や `note_id` から相互参照する。
- 同じ対象・属性に異なる値が出た場合は、既存値を黙って上書きせず、DB では `conflict_status`、wiki では `競合` / `未確定` として残す。
- DuckDB は比較・集計・分析のためのローカル DB として扱う。定性情報、解釈、長文の文脈は wiki に置く。

### source summary の最小メタデータ

source summary の frontmatter では、少なくとも以下を固定項目として持つ。

- `type: source`
- `title`: 資料の短い題名
- `created`: source summary 作成日
- `updated`: source summary 更新日
- `source_type`: `pdf` `web` `email_attachment` `shared_file` `dataset` `image` `note` `other` などの資料種別
- `source_path`: `raw/inbox/` または `raw/sources/` 上の原本パス
- `origin_type`: `url` `email` `shared_drive` `manual_scan` `local_file` `unknown` などの取得元種別
- `origin_reference`: URL、共有パス、メール件名、受領経路など、取得元を再特定するための主参照
- `origin_captured_on`: 取得日または受領日
- `origin_captured_by`: 取得者
- `provenance_status`: `confirmed` `partial` `uncertain` のいずれか

URL がある資料は `origin_reference` に URL を入れる。URL がない添付資料や手渡し資料は、`origin_reference` に「誰から、どの経路で受領したか」を再特定できる粒度で書く。詳細事情や未確定点は本文の `Provenance` に追記する。

## リンク方針

- 関連概念・人物・論文名は、対応ページがある場合 `[[ページ名]]` 形式でリンクする。
- ページ未作成なら平文で残し、必要なら後でページ化する。
- 新規ページを作ったら、可能な限り関連先にも戻り導線を置き、backlinks を双方向で維持する。
- 外部 URL は必要最小限にとどめ、知識の主保管先は wiki に置く。

## 命名方針

- concept は `wiki/concepts/概念名.md` を使う。
- entity は代表表記をファイル名にする。人物は `Firstname-Lastname.md`、組織・製品・資料名は既存の代表表記に合わせる。
- 既存ページと表記ゆれがある場合は、新規作成より先に merge 先を検討する。
- 用語統一を優先し、別名・略称・表記差は frontmatter の `aliases` または本文冒頭で吸収する。

## ログ方針

`wiki/log.md` の各エントリは次の見出し形式で始める。

`## [YYYY-MM-DD] 種別 | タイトル`

種別は `ingest` `query` `lint` を使う。

## 判断基準

- 不確実なときは、断定よりも選択肢の列挙を優先する。
- 研究上重要な対立点は、消さずに残す。
- 細部より再利用性を優先し、複数ページから参照できる形で整理する。

## 一般的な作業指針

LLM の作業ミスを減らすため、速度よりも明確さと小さな変更を優先する。軽微な作業では過度に形式化しない。

### 1. 実装前に考える

- 前提を明示する。不明点が重要なら質問する。
- 解釈が複数ある場合は、黙って選ばず選択肢を示す。
- より単純な方法がある場合は、その理由とともに提示する。

### 2. 単純さを優先する

- 依頼されていない機能や抽象化を足さない。
- 1回しか使わないものを汎用化しない。
- 不要な柔軟性や設定項目を増やさない。
- 複雑になったら、同じ目的をより短く達成できないか見直す。

### 3. 変更は最小限にする

- 依頼と無関係なリファクタリングや整形をしない。
- 既存の文体・構成・命名に合わせる。
- 自分の変更で不要になったものだけを片付ける。
- 無関係な問題を見つけた場合は、削除せず報告に留める。

### 4. 検証可能に進める

- 成功条件と確認方法を先に置く。
- バグ修正なら再現条件、リファクタリングなら既存挙動の維持を確認する。
- 複数ステップの作業では、短い計画を示してから進める。
