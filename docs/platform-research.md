# Platform Research

確認日: 2026-06-11

公式ヘルプ、公式マニュアル、公式サポートページを優先して確認しました。公式情報が見つからない、または本文内記法の詳細を確認しきれていない項目は「要確認」とします。

## 最優先対応

| platform id | サイト | 調査状態 | 公式URL | メモ |
| --- | --- | --- | --- | --- |
| `kakuyomu` | カクヨム | 公式確認済み | https://kakuyomu.jp/help/entry/notation | ルビ、傍点、縦線、省略ルビ、改行またぎ無効、同時指定不可を確認。 |
| `narou` | 小説家になろう | 公式確認済み | https://syosetu.com/helpcenter/helppage/helppageid/42 | `｜親文字《ルビ》`、半角縦線、省略ルビ、丸括弧ルビを確認。傍点の本文内記法は追加確認が必要。 |
| `estar` | エブリスタ | 公式確認済み | https://support.estar.jp/hc/ja/articles/360020301874 | ルビ、縦線、傍点、最大文字数、改行またぎ無効を確認。 |
| `novelup` | ノベルアップ＋ | 公式一部確認 | https://novelup.plus/help/detail/%E5%85%A5%E5%8A%9B%E8%A3%9C%E5%8A%A9%E6%A9%9F%E8%83%BD%E3%81%AB%E3%81%A4%E3%81%84%E3%81%A6 | 入力補助機能にルビ・傍点があることを確認。本文内記法の詳細は要確認。 |
| `pixiv` | pixiv小説 | 公式確認済み | https://www.pixiv.help/hc/ja/articles/39197091470105 | 記法変換機能で `[[rb: 漢字 > かんじ]]`、`[[emphasismark: 漢字 > •]]` を確認。 |
| `pixiv` | pixiv小説 | 公式確認済み | https://www.pixiv.help/hc/ja/articles/235584168 | 特殊タグのルビ、傍点、太字、斜体などを確認。 |
| `aozora` | 青空文庫 | 公式確認済み | https://www.aozora.gr.jp/aozora-manual/index-input.html | `《》`、`｜`、`［＃...］` を使う注記形式を確認。 |
| `note` | note | 公式確認済み | https://www.help-note.com/hc/ja/articles/4406430353817 | `｜親文字《ルビ》`、半角/全角縦線、太字・リンクとの組み合わせ注意を確認。 |

## 次点対応候補

| platform id | 表示名 | 調査状態 | 備考 |
| --- | --- | --- | --- |
| `alphapolis` | アルファポリス | 要調査 | 公式本文内記法ページ未確認。 |
| `hameln` | ハーメルン | 要調査 | 公式取扱説明書の確認が必要。 |
| `novelpia` | ノベルピア | 要調査 | 公式仕様未確認。 |
| `maho_i_land` | 魔法のiらんど | 要調査 | 公式仕様未確認。 |
| `berry_cafe` | ベリーズカフェ | 要調査 | 公式仕様未確認。 |
| `noichigo` | 野いちご | 要調査 | 公式仕様未確認。 |
| `tapnovel` | TapNovel | 要調査 | 台本形式の可能性があり、通常本文記法とは別設計が必要。 |
| `pri_shosetsu` | プリ小説 | 要調査 | 公式仕様未確認。 |
| `uranai_tkool` | 占いツクール | 要調査 | 公式仕様未確認。 |
| `arcadia` | Arcadia | 要調査 | 仕様・運用状態の確認が必要。 |
| `fc2_novel` | FC2小説 | 要調査 | 公式仕様未確認。 |

## 追加調査候補

| platform id | 表示名 | 調査状態 | 備考 |
| --- | --- | --- | --- |
| `wordpress` | WordPress | 要調査 | HTML / ブロックエディタ / プラグイン依存。 |
| `hatena_blog` | はてなブログ | 要調査 | 編集モード依存。 |
| `epub_xhtml` | EPUB / XHTML | 要調査 | HTML ruby と CSS 傍点の互換性確認が必要。 |
| `markdown` | Markdown | 一部確認 | CommonMark には標準ルビ・傍点がないため簡略化。 |
| `plain` | plain text | 対象仕様なし | 装飾情報は削除または括弧保持。 |

## 未確認事項

- 小説家になろうの傍点本文内記法。
- ノベルアップ＋の直接入力できる本文内記法。
- note のルビと太字・リンク以外の複合装飾。
- pixiv の特殊タグで `>` や `]]` を本文に含める場合のエスケープ。
- 青空文庫注記の全パターンと入れ子構造。
- 次点対応候補の公式仕様。
