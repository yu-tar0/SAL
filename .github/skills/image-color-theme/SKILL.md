---
name: image-color-theme
description: 画像、ロゴ、写真、ブランド素材からHTML Artifact向けの9色カラーテーマを生成する。ユーザーが画像を渡して「この色でHTMLを作って」「この画像の色設定にして」「ロゴに合わせた配色」「ブランドカラーのテーマ」などと言った場合、または既存テーマを画像基準で作り直す場合に使う。出力は page_bg, paper_bg, ink, muted, accent, line, soft, warn, warn_bg とテーマ管理メタデータを持つJSON。
---

# image-color-theme

画像から主役のブランド色を抽出し、HTML Artifact の色テーマJSONと確認用HTMLを一気通貫で生成するスキル。既定は「忠実モード」で、`accent` は画像の最も顕著な有彩色をそのまま使う。

## Workflow

1. 入力画像のパスを確認する。リポジトリ内に保存する場合は `raw/assets/image-color-theme/<theme-id>/` を使い、画像・テーマJSON・確認用HTMLを同じフォルダにまとめる。
2. Pillow が使えるか確認する。なければユーザー承認を得てインストールする。
3. `scripts/image_to_theme.py` を実行し、テーマJSONとプレビューHTMLを同時に作る。

```bash
python scripts/image_to_theme.py <画像パス> \
  --name "<テーマ名>" \
  --description "<説明>" \
  --out raw/assets/image-color-theme/<theme-id>/<theme-id>.theme.json \
  --preview-out raw/assets/image-color-theme/<theme-id>/<theme-id>.preview.html
```

必要に応じて指定する。

- `--id <theme-id>`: 省略時はテーマ名から `name-v1` を生成する。
- `--accessible`: `accent` も `paper_bg` に対して 4.5:1 以上になるまで暗くする。忠実さよりリンク・ボタン可読性を優先する場合だけ使う。
- `--out <path>`: 省略時はJSONを標準出力する。
- `--preview-out <path>`: 省略時はプレビューHTMLを作らない。ユーザーが画像パスを渡して色テーマ抽出を依頼した場合は、原則として指定する。

4. 標準エラーに出る抽出パレットとコントラスト注記を確認する。
5. `accent` のコントラストが低い場合は、その事実と `--accessible` の選択肢をユーザーに伝える。
6. 生成したJSONと確認用HTMLのパスを報告する。

`--preview-out` を使わずに後から確認HTMLだけ作る場合は、`scripts/preview.py <theme.json> --out preview.html` を実行する。

## File Layout

画像からテーマを作る場合は、1テーマにつき1フォルダにまとめる。

```text
raw/assets/image-color-theme/<theme-id>/
├── source.<ext>
├── <theme-id>.theme.json
└── <theme-id>.preview.html
```

元画像のファイル名を保持したい場合は保持してよい。ただし、成果物が増える場合も同じ `<theme-id>/` 配下に置き、`raw/assets/image-color-theme/` 直下へテーマJSONやHTMLを直接置かない。

## Output Schema

テーマJSONは以下の形にする。色は必ず9キーすべてを埋める。

```json
{
  "id": "theme-id-v1",
  "name": "Theme Name",
  "version": 1,
  "status": "active",
  "created": "YYYY-MM-DD",
  "updated": "YYYY-MM-DD",
  "description": "テーマの説明",
  "colors": {
    "page_bg": "#......",
    "paper_bg": "#......",
    "ink": "#......",
    "muted": "#......",
    "accent": "#......",
    "line": "#......",
    "soft": "#......",
    "warn": "#8A5A00",
    "warn_bg": "#FFF4D8"
  }
}
```

## Color Rules

- `accent`: 画像内で最も顕著な有彩色。占有率と彩度から選び、既定では改変しない。
- `page_bg`, `paper_bg`, `ink`, `muted`, `line`, `soft`: `accent` と同じ色相をもとに低彩度・高可読な色として生成する。
- `warn`, `warn_bg`: 意味機能を優先し、標準アンバー `#8A5A00` / `#FFF4D8` に固定する。
- `ink`: `paper_bg` に対して 7:1 以上のコントラストを目指す。
- 画像の白が微妙に色づいていても、十分高明度なら `paper_bg` は `#FFFFFF` に丸める。
- 白黒ロゴなど有彩色がない画像では、白背景を除外し、黒やグレーのロゴ本体を `accent` にする。背景・罫線・soft はニュートラルグレーで生成する。

## HTML Artifact Integration

このリポジトリのHTML Artifactへ適用する場合は、生成JSONの `colors` を `.github/skills/html-artifact/assets/themes.json` の `themes[]` に追加する。CSS変数は次に対応させる。

- `page_bg` -> `--page-bg`
- `paper_bg` -> `--paper-bg`
- `ink` -> `--ink`
- `muted` -> `--muted`
- `accent` -> `--accent`
- `line` -> `--line`
- `soft` -> `--soft`
- `warn` -> `--warn`
- `warn_bg` -> `--warn-bg`

テーマを採用・改訂した場合は、`themes.json` の `history` と `wiki/log.md` に履歴を残す。
