# Platform Inventory

## 最優先対応

| platform id | 表示名 | 調査状態 | 実装状態 | 将来対応可能性 |
| --- | --- | --- | --- | --- |
| `kakuyomu` | カクヨム | 公式確認済み | supported | 高い |
| `narou` | 小説家になろう | 公式確認済み | supported | 高い。傍点は追加確認が必要。 |
| `estar` | エブリスタ | 公式確認済み | supported | 高い |
| `novelup` | ノベルアップ＋ | 公式一部確認 | partial | 公式本文内記法の確認後に拡張。 |
| `pixiv` | pixiv小説 | 公式確認済み | supported | 高い。特殊タグ拡張余地あり。 |
| `aozora` | 青空文庫 | 公式確認済み | supported | 中。注記全体は大きい。 |
| `note` | note | 公式確認済み | partial | 中。複合装飾に注意。 |

## 次点対応候補

`alphapolis`, `hameln`, `novelpia`, `maho_i_land`, `berry_cafe`, `noichigo`, `tapnovel`, `pri_shosetsu`, `uranai_tkool`, `arcadia`, `fc2_novel` は profile 登録済みですが、現在の実装では `research-needed` です。

## 追加調査候補

`wordpress`, `hatena_blog`, `epub_xhtml`, `markdown`, `plain` は投稿サイト外または汎用形式として扱います。Markdown と plain は現在の実装で簡略出力に対応しています。
