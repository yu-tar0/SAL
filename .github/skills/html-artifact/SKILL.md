---
name: html-artifact
description: Use this skill when visualizing LLM Wiki knowledge, and optionally raw source material, by creating a Markdown source artifact and converting it into a web HTML artifact by default; create A4 or slide HTML only when explicitly requested.
---

# HTML Artifact

LLM Wiki の知識や、必要に応じて raw の一次資料を、まず単一 Markdown Artifact として整理し、それを人間が読みやすい Web HTML Artifact へ変換するためのスキル。A4版・スライド版は明示依頼時だけ追加する。

## 適用条件

単なる会話ではなく、後から参照・印刷・PDF出力する価値がある内容を、`wiki/` や必要に応じた `raw/` を入力元にして、比較表・分析・まとめ・コード・図案・フレームワーク・レポート・ダッシュボードとして可視化する場合に使う。

Markdown は内容の正本、HTML は閲覧・共有・印刷・PDF出力のための表示物として扱う。標準ではブラウザ閲覧用の `web.html` のみを生成する。A4印刷用の `a4.html` と16:9スライド用の `slides.html` は、ユーザーが明示的に求めた場合だけ追加生成する。

HTML は原則として Markdown 正本の内容を忠実に表示する。可読性やスライド化のために分割・圧縮してよいが、元本にある見出し、表の列、行、主要箇条書き、Provenance、未解決点、出典・根拠を黙って削除しない。表示形式の都合で省略・要約・統合する場合は、作業前または成果物内でその判断を明示する。

## 厳格ワークフロー

1. 価値評価と提案（Triage）
   - 何を入力元として可視化するかを説明する。
   - Artifacts 化の価値を説明する。
   - 提案保存先を以下の1フォルダ + 2ファイルで示す。
     - `artifacts/YYYY-MM-DD-[カテゴリ]-[簡潔タイトル]/`
     - `artifacts/YYYY-MM-DD-[カテゴリ]-[簡潔タイトル]/YYYY-MM-DD-[カテゴリ]-[簡潔タイトル].md`
     - `artifacts/YYYY-MM-DD-[カテゴリ]-[簡潔タイトル]/YYYY-MM-DD-[カテゴリ]-[簡潔タイトル].web.html`
   - A4版またはスライド版を求められている場合だけ、追加保存先として以下も示す。
     - `artifacts/YYYY-MM-DD-[カテゴリ]-[簡潔タイトル]/YYYY-MM-DD-[カテゴリ]-[簡潔タイトル].a4.html`
     - `artifacts/YYYY-MM-DD-[カテゴリ]-[簡潔タイトル]/YYYY-MM-DD-[カテゴリ]-[簡潔タイトル].slides.html`
   - Markdown を内容の正本、HTML を高品質な可視化出力（純粋 CSS）として保存することを示す。
   - `web.html` は切れ目のないブラウザ閲覧用の標準出力であることを示す。
   - 追加生成する場合は、`a4.html` はA4印刷/PDF用、`slides.html` は16:9スライド/PDF/PowerPoint用であることを示す。
   - 関連する wiki ページ（`entities` / `concepts` / `sources` など）と、必要に応じて raw 資料を示す。
   - 保存前にユーザー承認を得る。

2. Markdown Artifact 作成（承認後）
   - `artifacts/YYYY-MM-DD-[カテゴリ]-[簡潔タイトル]/` を作成する。
   - `artifacts/YYYY-MM-DD-[カテゴリ]-[簡潔タイトル]/YYYY-MM-DD-[カテゴリ]-[簡潔タイトル].md` を作成する。
   - 冒頭に、タイトル、作成日、入力元 wiki ページ、入力元 raw 資料、変換先 HTML、用途を明記する。
   - 本文には言語に応じた要約セクション（日本語は `要約`、英語は `Summary`）、主要セクション、表、箇条書き、出典・根拠、未解決点を含める。
   - Markdown はレイアウト指定ではなく意味構造として書く。見た目は出力先HTML側で決める。
   - 内容修正は原則として Markdown 側に入れる。

3. HTML Artifact 変換
   - `assets/template.html` を正本テンプレートとして使う。
   - 色は `assets/themes.json` のテーマを1つ選び、標準では `wiki-teal-v1` を使う。
   - Markdown Artifact の内容をもとに `[タイトル]` と `[メインタイトル]` を成果物の内容に合わせて置換する。
   - `YYYY-MM-DD` を作成日に置換する。
   - 正本 Markdown と同じArtifactフォルダ内に `web.html` を生成する。
   - `web.html` は、章を連続したWebページとして表示する。
   - ユーザーが明示的に求めた場合だけ、`a4.html` と `slides.html` を追加生成し、`web.html` からリンクを置く。
   - 追加生成する場合、`a4.html` は、A4印刷/PDF化を前提に用紙単位のページ区切りを持たせる。
   - 追加生成する場合、`slides.html` は、16:9スライドを前提に `1 section = 1ページ` として扱う。
   - ユーザーが PowerPoint 版を明示的に求めた場合だけ、`scripts/html_slides_to_pptx.py` で `slides.html` から `*.slides-native.pptx` を生成する。既存の正常な PPTX がある場合は `--template` で指定するか、スクリプトの自動検出に任せ、PowerPoint が期待する `presProps.xml` / `viewProps.xml` / `tableStyles.xml` などの補助部品を保持する。
   - `columns`、`kpi-grid`、`table`、`callout` を必要に応じて使う。
   - 変換前に Markdown 正本の構造 inventory を作る。少なくとも `#` / `##` / `###` 見出し、表のタイトルまたは直前見出し、表の列名、箇条書き数、Provenance / Sources / 未解決点の有無を確認する。
   - 変換後に Markdown 正本と HTML の coverage check を行う。全ての主要見出し、表、表の列名、主要箇条書き、Provenance が HTML に反映されているか確認する。
   - 表を分割する場合も、列名と行の意味を保持する。列を削る、行を代表例だけにする、本文を大幅に短縮する場合は、HTML 内に「要約版」「主要列のみ」などのラベルを付けるか、完了報告で明示する。
   - HTML 内に元 Markdown Artifact への参照を含める。
   - HTML 内に使用テーマを `Artifact Theme: ...` コメントと `artifact-theme-metadata` JSON として埋め込む。
   - HTML を直接編集する場合は、各出力形式のレイアウト、スタイル、HTML固有の表現調整に限る。
   - A4やスライドを追加生成した場合、それらだけを手直しするときは該当する `a4.html` または `slides.html` を個別に調整してよい。
   - PPTX を生成した場合は、ZIP 整合性、スライド数、`ppt/presProps.xml`、`ppt/viewProps.xml`、`ppt/tableStyles.xml`、`ppt/theme/theme1.xml` の存在を確認する。PowerPoint で修復警告が出る場合は、正常に開ける既存 PPTX をテンプレートにして再生成する。

4. Wiki との統合
   - 関連する `wiki/` 内のページ、特に `concepts/` と `entities/` を更新する。
   - 適切な `[[Wikilink]]` を追加して相互リンクを張る。
   - 必要に応じて `wiki/index.md` に Markdown、Web のリンクを記載する。A4、Slides を追加生成した場合だけ、そのリンクも記載する。
   - `wiki/log.md` に Artifacts 作成ログを追記する。

5. 完了報告
   - 保存した Markdown ファイル名、HTMLファイル名、主な関連リンクを報告する。
   - 案内として、次の文を含める。
     - 「ブラウザ閲覧は `web.html` を開いてください。」
   - A4、Slides を追加生成した場合だけ、次の案内も含める。
     - 「A4印刷/PDF保存は `a4.html`、16:9スライド/PDF保存は `slides.html` を開いてください。」

## テンプレート要件

`assets/template.html` または派生テンプレートには以下を含める。

- Web閲覧用の切れ目のないページレイアウト。
- A4レポート用の白背景・濃色本文と用紙単位のページ区切り。
- 16:9スライドPDF用の `@page slide { size: 297mm 167.0625mm; margin: 0; }` とスライド単位のページ区切り。
- `columns`、`kpi-grid`、`table`、`callout` の基本部品。
- 追加生成した形式間を移動するためのリンク。1ファイル内のタブ切り替えは必須ではない。

## 色テーマ運用

HTML Artifact の色は、Markdown 正本ではなく表示レイヤーのテーマとして管理する。テーマ定義の正本は `assets/themes.json` とし、生成時に1つのテーマを選ぶ。標準テーマは `wiki-teal-v1`。

標準CSS変数は以下に統一する。

- `--page-bg`: ページ全体の背景。
- `--paper-bg`: 本文・紙面・スライドの背景。
- `--ink`: 見出しや本文の主文字色。
- `--muted`: 補助テキスト。
- `--accent`: 見出し罫線、表ヘッダー、強調要素。
- `--line`: 罫線。
- `--soft`: callout などの淡い強調背景。
- `--warn`: 注意喚起の罫線や文字。
- `--warn-bg`: 注意喚起の淡い背景。

各HTMLには、使用テーマを追跡できるように `<head>` 内へ以下を必ず残す。

- `<!-- Artifact Theme: テーマID -->`
- `<script type="application/json" id="artifact-theme-metadata">...</script>`

`artifact-theme-metadata` には `theme_id`、`theme_name`、`theme_version`、`applied_on`、`source_theme_file`、`colors` を含める。HTML固有のレイアウト調整をしても、実際に使った色値はこのメタデータとCSS変数で一致させる。

新しいテーマを追加・既存テーマを改訂した場合は、`assets/themes.json` の `history` に追記し、`wiki/log.md` にも人間向けの要約を残す。生成済みHTMLのテーマは原則として自動変更せず、再生成または明示的な更新時にだけ変更する。

## Markdown 構造ルール

Markdown は内容の正本であり、以下の意味構造として扱う。

- frontmatter: タイトル、作成日、入力元、出力先、用途、ステータスを記録する。
- `#`: 成果物全体のタイトル。
- `##`: 主要セクション。A4では章、Slidesではスライド候補、Webではページ内セクションとして扱う。
- `###`: サブセクション。A4では節、Slidesではスライド内小見出しまたは分割候補として扱う。
- `####`: 小項目。A4/Webでは本文内見出し、Slidesでは原則として本文要素へ圧縮する。
- `要約` / `Summary`: Web/A4では冒頭要約、Slidesではエグゼクティブサマリー候補として扱う。本文言語に合わせ、日本語では `要約`、英語では `Summary` を使う。
- `Provenance` / `Sources`: Web/A4では末尾の根拠セクション、Slidesでは最終スライドまたは小さな脚注として扱う。
- 表: 意味上必要な比較・一覧として扱う。列名と行は本文情報の一部であり、表示都合だけで黙って削らない。Slidesでは大きな表を分割してよいが、要点化や代表値化をする場合は「要約版」と明示する。
- 画像: 図・スクリーンショット・概念図として扱い、可能な限りキャプションを付ける。

## 忠実変換ルール

HTML 化では、見た目の最適化よりも Markdown 正本との対応関係を優先する。

- 見出し保持: Markdown の `#` と `##` は原則として HTML に対応するタイトルまたはセクションとして残す。削る場合は理由を明示する。
- 表保持: Markdown の表は、Web/A4 では原則として全列・全行を保持する。Slides では複数スライドへ分割してよいが、元表の列を落とす場合は「主要列のみ」「要約版」などと表示する。
- 箇条書き保持: 要約セクションや注意点の箇条書きは、原則として全項目を保持する。スライド化で圧縮する場合は、意味単位を保持し、削除した項目があることを明示する。
- Provenance 保持: 入力元 raw、正本 Markdown、生成先 HTML、作成日、備考などの Provenance は各 HTML に必ず残す。
- 追加主張禁止: Markdown 正本にない判断、比較評価、数値、出典を HTML 側で追加しない。追加が必要な場合は、先に Markdown 正本を更新する。
- 直接編集制限: HTML への直接編集はレイアウト、CSS、表示形式に限る。内容修正、項目追加、評価変更は原則として Markdown 正本へ入れてから再変換する。
- coverage check: 完了前に、Markdown 正本の主要見出し、表の列名、重要な固有名詞、Provenance が HTML に存在することを確認する。欠落がある場合は、意図的な要約か変換ミスかを区別して報告する。

Markdown に細かなフォントサイズ、余白、ページ番号、スライド内座標などを直接書かない。必要な場合のみ、最小限のヒントをHTMLコメントで入れる。

許可する最小ヒント:

- `<!-- slide: split -->`: Slidesで複数スライドへ分割する。
- `<!-- slide: image-focus -->`: Slidesで画像を主役として大きく扱う。
- `<!-- layout: wide-table -->`: Web/A4で幅広の表として扱う。
- `<!-- callout -->`: 直後の段落またはブロックを強調枠として扱う。

## 形式別変換ルール

### Web HTML

`web.html` は Markdown を読みやすい連続ページとして表示する。

- `#` はページタイトル。
- `##` はページ内の主要セクション。
- `###` は小見出し。
- 長文を許容する。
- 目次またはページ内ナビを必要に応じて置く。
- 図表は本文中に自然に配置し、キャプションを付ける。
- Markdown 正本の表は原則として全列・全行を保持する。横幅が大きい表は横スクロール、縮小、または `wide-table` として扱う。
- `a4.html` と `slides.html` を追加生成した場合だけ、それらへのリンクを置く。

### A4 HTML

`a4.html` は Markdown を印刷資料として比較的忠実に整形する。

- `#` は表紙または文書タイトル。
- `##` は章見出し。必要に応じて改ページ候補にする。
- `###` は節見出し。
- `####` は本文中の小見出しとして扱う。
- `要約` / `Summary` は冒頭の要約ボックスとして扱う。
- `##` が4つ以上ある場合は目次を入れることを基本とする。
- 表はA4幅に収める。大きい表はフォント縮小、列の整理、分割を検討する。
- 列の整理で情報を省く場合は、削った列を明示するか、別表・注記で補う。
- 画像は図番号・キャプション付きで扱い、可能な限りページをまたがない。
- Provenance / Sources は巻末にまとめる。

### Slides HTML

`slides.html` は Markdown をプレゼン資料として再構成する。

- `#` はタイトルスライド。
- `要約` / `Summary` はエグゼクティブサマリースライド候補。
- `##` は原則として1枚のスライド候補。
- 1つの `##` が長い場合は、複数スライドへ分割してよい。
- `###` はスライド内小見出し、または内容が重い場合の分割候補。
- 1スライドは1メッセージを基本とする。
- 1スライドの箇条書きは4〜6行程度を目安にする。
- 長い段落はそのまま載せず、短い要点へ圧縮してよい。
- 大きな表は1枚に詰め込まず、複数スライドへ分割する。元表の列を保持することを優先し、列削減・要点化・代表値化をする場合は「要約版」「主要列のみ」と明示する。
- 画像は大きく扱い、画像が主役のスライドでは本文量を抑える。
- Provenance / Sources は最終スライドまたは脚注として扱う。

SlidesはMarkdownの逐語変換ではなく、プレゼンとして成立するように要約・分割してよい。ただし、意味を変えたり、根拠のない主張を追加してはならない。情報の欠落を避けるため、詳細表・比較表・出典表はまず分割で対応し、それでも収まらない場合だけ明示的に要約する。

## Output

- Markdown は内容の正本として保存できる形にする。
- HTML は Markdown から作成された単体ファイルとして保存できる形にする。
- LLM Wiki の Artifact は `artifacts/<artifact-id>/` に Markdown / Web HTML のセットで配置する。A4 HTML / Slides HTML は明示依頼がある場合だけ追加する。
- 画像・図は必要に応じて `artifacts/assets/` に配置し、HTML から相対リンクで参照する。
- Artifact は一次情報や知識の主保管場所ではなく、`wiki/` / `raw/` を入力元にした表示レイヤーとして扱う。
- 断定的な情報には、可能な範囲で wiki 内リンク、raw 資料、または外部出典を添える。

## Samples

Artifact 生成スキルやテンプレートの品質確認用サンプルは、本番 Artifact と分けて `artifacts/samples/html-artifact/vNNN/` に配置する。

推奨構成:

- `artifacts/samples/html-artifact/v001/sample/sample.md`
- `artifacts/samples/html-artifact/v001/sample/sample.web.html`

A4版・スライド版を検証するサンプルでは、必要に応じて以下も置く。

- `artifacts/samples/html-artifact/v001/sample/sample.a4.html`
- `artifacts/samples/html-artifact/v001/sample/sample.slides.html`
- `artifacts/samples/html-artifact/v001/sample/sample.slides-native.pptx`

Samples は通常の知識成果物ではなく、スキル修正と出力品質確認のためのテストケースとして扱う。差分比較をしやすくするため、各バージョン内のファイル名は固定する。日付や作成意図は `sample.md` の frontmatter に記録する。

Samples は原則として `wiki/index.md` の通常 Artifacts 一覧には載せない。重要なテンプレート変更や基準サンプル更新を行った場合のみ、`wiki/log.md` に記録する。
