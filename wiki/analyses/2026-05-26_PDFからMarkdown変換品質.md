---
type: analysis
title: PDFからMarkdown変換品質
created: 2026-05-26
updated: 2026-05-26
---

# PDFからMarkdown変換品質

## TL;DR

PDF を raw データとして扱う場合、変換品質は「文字が抜けないこと」だけでは足りない。日本語資料が多い前提では、当面は PDF を高解像度のページ画像へ変換し、VS Code 上の AI エージェントでページ単位 Markdown 化する画像LLM軽量ルートを第一候補として試す。自宅環境は Codex CLI、会社環境は GitHub Copilot Enterprise を主軸にし、ChatGPT 5.5 / M365 Copilot は補助・比較・難ページ対応に回す。

## 背景

PDF は論文、社内資料、仕様書、レポートなどで頻出するが、そのままでは LLM Wiki の知識として再利用しにくい。`raw/` には一次資料として PDF を残し、Markdown 化した内容を ingest や分析の入力にすることで、後から要約・比較・Artifact 化しやすくなる。

ただし、PDF から Markdown への変換は失敗しやすい。段組み、ヘッダー・フッター、表、脚注、図表、数式、OCR の誤認識が混ざると、LLM が誤った構造で理解する可能性がある。そのため、変換後の Markdown は一次資料そのものではなく、レビュー対象の派生資料として扱う。

## 環境別の使い分け

| 環境 | 利用可能な主なツール | 向いている用途 | 注意点 |
| --- | --- | --- | --- |
| 環境1: 自宅環境 | ChatGPT Plus、VS Code、Codex CLI | 個人研究資料・公開 PDF をページ画像化し、Codex CLI + VS Code でページ単位 Markdown 化・wiki 統合・差分管理を行う | 会社資料や機密資料は扱わない |
| 環境2: 会社環境 | GitHub Copilot Enterprise、M365 Copilot Premium、VS Code | 社内資料・会社関連 PDF をページ画像化し、GitHub Copilot Enterprise + VS Code でページ単位 Markdown 化・差分管理を行う | ZIP 前提にせず、リポジトリ内の画像・Markdownファイルを直接扱う |

基本方針として、資料の内容が会社由来の場合は会社環境内で処理する。自宅環境は、個人研究資料、公開論文、公開レポート、持ち出し制約のない資料に限定する。

## 品質観点

- 見出し構造: PDF の章・節・小節が Markdown の `#` / `##` / `###` として再現されているか。
- 段落: 改行位置だけで細切れにならず、意味のある段落として読めるか。
- 表: セルの対応、列名、注記、単位が崩れていないか。
- 図表キャプション: 図番号、表番号、本文中の参照と対応しているか。
- 脚注・参考文献: 本文と混ざらず、参照先として追えるか。
- ページ番号: ヘッダー・フッター由来のノイズが本文に混入していないか。
- 引用: 引用符、ブロック引用、出典表示が失われていないか。
- 数式: 意味が壊れていないか。壊れる場合は画像参照や原文ページ参照を残す。
- OCR: 誤字、文字化け、全角半角、ハイフネーション、文字間スペースの崩れがないか。

## 画像LLM軽量ルート

日本語 PDF では、Docling / Marker などの変換器を使わず、ページ画像を AI エージェントに読ませて Markdown 化する軽量ルートを第一候補として試す。特に、スキャン PDF、縦書き、表・図・注釈が多い資料、文字化けしやすい PDF では有効な可能性がある。主処理は ChatGPT 5.5 や M365 Copilot の画面操作ではなく、VS Code 上でファイルを管理しながら進める。

### 基本方針

- PDF をページ単位で高解像画像化する。
- 画像ファイル名にはページ番号を入れる。
- VS Code 上の AI エージェントにページ画像を読ませ、ページ番号順に Markdown 化させる。
- 変換結果は、要約ではなく原文忠実な Markdown として扱う。

### 命名規則

画像:

```text
page-001.png
page-002.png
page-003.png
page-004.png
page-005.png
```

出力 Markdown:

```text
raw/assets/{資料名}/md/page-001.md
raw/assets/{資料名}/md/page-002.md
raw/assets/{資料名}/{資料名}.pages.md
```

補助スクリプト:

```text
python scripts/pdf_to_page_images.py raw/inbox/sample.pdf --dpi 400
```

標準出力先:

```text
raw/assets/sample/pages/page-001.png
raw/assets/sample/pages/page-002.png
```

ページ単位 Markdown は `raw/assets/{資料名}/md/page-001.md` のように保存し、必要に応じて `{資料名}.pages.md` に結合する。ページ単位ファイルを残すことで、途中再開、差分確認、特定ページの再処理をしやすくする。

### LLMへの指示方針

- 画像ファイル名をページ番号として扱う。
- ページ番号の昇順で処理する。
- 1 ページにつき 1 つの Markdown ブロックを出力する。
- 要約、補足、言い換え、推測、翻訳をしない。
- 見えている内容だけを Markdown 化する。
- 判読不能箇所は `[illegible]` とする。
- ページごとに自己チェックコメントを残す。

各ページの先頭:

```md
<!-- page: 001 source: ../pages/page-001.png -->
```

`source` には、各 Markdown ファイルから見た元画像の相対パスを入れる。単体で見たときの自己記述性を優先し、絶対パスは使わない。

各ページの末尾:

```md
<!-- check: table_ok=true/false; reading_order_ok=true/false; uncertain_parts=... -->
```

## Docling / Marker の位置づけ

Docling / Marker は、現時点では必須の前処理ではなく、必要に応じて使う補助・比較ルートとする。主な目的は、再現可能な機械変換結果を残すこと、画像LLM出力との比較対象を作ること、大量処理時の下書きを得ることにある。

このルートは以下の場合に使う。

- ページ数が多い。
- 同種資料を継続的に処理する。
- 変換結果の再現性や差分確認が必要。
- Markdown 化の下書きを機械的に作りたい。
- 画像LLM出力の妥当性を別系統で確認したい。
- 表、数値、引用の検証ログを残したい。

LLM は、Docling / Marker の出力を無条件に正とせず、元 PDF 画像またはページ画像を基準にレビューする。役割は、要約や補完ではなく、Markdown 構造の確認、読み順の確認、表・脚注・図表キャプションの崩れ検出、不確実箇所の明示である。

## 推奨フロー

1. PDF は `raw/inbox/` に置き、一次資料として保持する。
2. `scripts/pdf_to_page_images.py` で `raw/assets/{資料名}/pages/page-001.png` 形式へ画像化する。
3. VS Code 上の AI エージェントで、ページ画像から `raw/assets/{資料名}/md/page-001.md` 形式の Markdown を作成する。
4. 必要に応じてページ単位 Markdown を `{資料名}.pages.md` に結合する。
5. 品質が不安なページ、表・数式・図が多いページは ChatGPT 5.5 / M365 Copilot / Docling / Marker を補助的に使って比較する。
6. 最重要資料では、ページ画像、生成 Markdown、必要に応じた別系統出力を比較し、元 PDF で人間が確認する。
7. wiki へ反映する際は、PDF 由来の要約、解釈、未確定点を分けて記録する。

## 判断ルール

- 変換 Markdown は一次資料ではなく、PDF の読み取りを助ける中間表現として扱う。
- 重要な断定や数値は、可能な限り元 PDF のページや図表へ戻って確認する。
- 会社資料は会社環境内で完結させ、自宅環境の ChatGPT Plus や Codex CLI へ投入しない。
- 公開資料でも、再配布や Artifact 化する場合は出典、取得日、引用範囲を明示する。
- 変換の失敗や不確実性は隠さず、wiki 側に「未確定」「要確認」として残す。

## Related Links

- [[Rawデータ運用]]
- [[Artifacts運用]]

## Provenance

- 2026-05-26 に、PDF を raw データとして扱う際の Markdown 変換品質メモとして作成。
- 2026-05-26 に、日本語資料を前提とした画像LLM軽量ルートを第一候補にし、Docling / Marker を拡張候補として位置づけ直した。
- 2026-05-26 に、会社環境では ZIP を使わずページ画像を直接渡す方針に変更し、PDF 画像化スクリプトを追加。
- 2026-05-26 に、自宅環境は Codex CLI + VS Code、会社環境は GitHub Copilot Enterprise + VS Code を主軸にし、ChatGPT 5.5 / M365 Copilot を補助扱いへ変更。
- ユーザーから共有された利用環境の前提に基づく内部運用メモ。

## Last Updated

2026-05-26
