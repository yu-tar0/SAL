<!-- page: 002 source: ../pages/page-002.png -->

# 1. このサンプルの目的

旧サンプルは、1つの HTML 内で A4 とスライドを切り替える形式でした。新標準では、Markdown を内容の正本とし、用途ごとに HTML を分けます。

この方式により、内容修正は Markdown 側で一元管理し、A4 やスライドの見た目だけを直したい場合は該当する HTML を個別に調整できます。

# 2. 出力形式

| ファイル | 用途 | レイアウト方針 |
|---|---|---|
| `*.web.html` | ブラウザ閲覧 | 切れ目のない Web ページとして表示する |
| `*.a4.html` | A4印刷/PDF | 用紙単位のページ区切りを持たせる |
| `*.slides.html` | 16:9スライド/PDF/PowerPoint | 1スライド1メッセージを基本に再構成する |

<!-- check: table_ok=true; reading_order_ok=true; uncertain_parts=none; review_status=auto_generated -->
