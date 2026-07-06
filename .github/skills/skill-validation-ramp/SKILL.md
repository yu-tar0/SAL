---
name: skill-validation-ramp
description: Use this skill when validating a newly created or substantially revised repository skill through lightweight staged checks, before optionally escalating to empirical-prompt-tuning for rigorous evaluation.
---

# Skill Validation Ramp

新規作成または大きく改訂したリポジトリ内スキルを、いきなり本番運用せず、軽量な段階評価で確認するためのスキル。通常はこのスキルで素早く確認し、曖昧さや再発失敗が残る場合のみ `empirical-prompt-tuning` にエスカレーションする。内容の正しさ、原文との意味ズレ、採用可否の最終判断は人間が行う。

## 適用条件

- `.github/skills/{skill-name}/SKILL.md` を新規作成した。
- 既存スキルの用途、保存規則、出力形式、ワークフローを大きく変えた。
- 本番投入前に、説明と本文が噛み合っているか確認したい。
- 実サンプルで段階的に試し、改善点を小さく見つけたい。

## 軽量評価フロー

1. Trigger確認
   - frontmatter `description` が、使ってほしい場面を具体的に表しているか確認する。
   - 広すぎる、狭すぎる、本文にない用途を含む場合は修正する。

2. Body整合性確認
   - description に書いた用途を、本文の手順・ルール・出力先が支えているか確認する。
   - 本文にしかない重要用途があれば description へ反映する。

3. 最小サンプル実行
   - 一番簡単で成功しやすい実例を1つ選ぶ。
   - 例: `pdf-page-image-markdown` なら `raw/assets/sample_a4/pages/page-001.png`。
   - 成功条件を3〜5項目で書いてから実行する。

4. 中程度サンプル実行
   - 少し複雑な実例を1つ選ぶ。
   - 見出し、複数セクション、図、箇条書き、表など、通常運用で出やすい要素を含める。

5. 難ケース実行
   - 失敗しやすい実例を1つ選ぶ。
   - スキルの対象に応じて、表、脚注、数式、長文、ファイル分割、保存先指定、例外処理などを含める。

6. チェックリスト評価
   - 成功/失敗だけでなく、項目ごとに `OK` / `partial` / `NG` で評価する。
   - AI 側は出力形式、保存先、禁止事項、曖昧箇所の扱い、再実行しやすさを確認する。
   - 内容の正しさ、原文との意味ズレ、読み落としの有無は人間確認欄として残し、AI が最終判定しない。

7. 最小修正
   - 1回の修正では1テーマだけ直す。
   - 例: 「保存先の明確化」「不確実性の表記」「出力フォーマット固定」など。

8. 再確認
   - 修正したテーマに関係するサンプルだけ再実行する。
   - 関係ない箇所を同時に評価し直して、原因追跡を曖昧にしない。

## 評価メモ形式

軽量評価では、必要に応じて以下の短い形式で記録する。

```md
## Skill Validation | {skill-name} | YYYY-MM-DD

- Scenario: {最小 / 中程度 / 難ケース}
- Sample: {入力ファイルや状況}
- Expected:
  - {成功条件1}
  - {成功条件2}
- Result:
  - {OK / partial / NG}
- Human Review:
  - {pending / OK / needs_fix}
- Issue:
  - {失敗や曖昧さ}
- Fix:
  - {最小修正}
```

継続的に使う重要スキルでは、評価メモを対象スキルの `references/evaluation-log.md` に残してよい。小さな確認だけなら `wiki/log.md` への要約で足りる。

## empirical-prompt-tuning へのエスカレーション

以下に該当する場合は、軽量評価を止めて `empirical-prompt-tuning` を使う。

- 同じ種類の失敗が2回以上出る。
- description と本文のズレが修正後も残る。
- 出力形式や保存先が安定しない。
- 実行者の裁量補完が多い。
- 改善案が複数あり、主観で選べない。
- 今後繰り返し使う重要スキルで、品質の根拠が必要。
- 評価サンプルを増やして客観的に比べる必要がある。
- 自分で読み直しても、失敗原因が instruction 側か実行側か切り分けられない。
- 人間確認で内容ズレが複数回見つかり、どの instruction が原因か切り分けにくい。

エスカレーション時は、対象スキル、評価済みサンプル、失敗内容、軽量評価で試した修正を渡す。`empirical-prompt-tuning` 側では、blank-slate executor と固定チェックリストで評価する。

## 完了条件

- description と本文の用途が一致している。
- 最小サンプルで期待出力が得られる。
- 中程度サンプルで出力形式と保存先が安定している。
- 難ケースで不確実性や失敗を明示できる。
- 内容の正しさと原文とのズレについて、人間確認が `OK` または既知の制約として記録されている。
- 残る制約や既知の弱点がスキル本文または評価メモに残っている。
