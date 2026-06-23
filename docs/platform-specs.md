# Platform Specs

| platform id | サイト名 | 公式仕様確認状況 | ルビ入力 | ルビ出力 | 傍点入力 | 傍点出力 | 注記 | 独自タグ | HTML | Markdown | 変換時の注意 | 未対応項目 | 参考URL |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `kakuyomu` | カクヨム | 公式確認済み | `｜親文字《ルビ》`, `|親文字《ルビ》`, `漢字《ルビ》` | 同左 | `《《対象》》` | 同左 | 要確認 | カクヨム記法 | 不可 | 不可 | 改行またぎ無効、ルビと傍点同時指定不可 | 見出し等 | https://kakuyomu.jp/help/entry/notation |
| `narou` | 小説家になろう | 公式確認済み | `｜親文字《ルビ》`, `|親文字《ルビ》`, `漢字《ルビ》`, `漢字(ルビ)` | `｜親文字《ルビ》` | 要確認 | 現在は警告付き | 要確認 | 入力補助機能 | 不可 | 不可 | 丸括弧ルビの扱い、傍点は要確認 | 傍点 | https://syosetu.com/helpcenter/helppage/helppageid/42 |
| `estar` | エブリスタ | 公式確認済み | `｜親文字《ルビ》`, `|親文字《ルビ》`, `漢字《ルビ》` | `｜親文字《ルビ》` | `《《対象》》` | 同左 | 要確認 | エブリスタ記法 | 不可 | 不可 | 改行またぎ無効、最大文字数あり | 注記 | https://support.estar.jp/hc/ja/articles/360020301874 |
| `novelup` | ノベルアップ＋ | 公式一部確認 | 入力補助あり、詳細要確認 | `｜親文字《ルビ》` に暫定 | 入力補助あり、詳細要確認 | `《《対象》》` に暫定 | 要確認 | 要確認 | 要確認 | 要確認 | 公式詳細未確認のため partial | 詳細仕様 | https://novelup.plus/help/detail/%E5%85%A5%E5%8A%9B%E8%A3%9C%E5%8A%A9%E6%A9%9F%E8%83%BD%E3%81%AB%E3%81%A4%E3%81%84%E3%81%A6 |
| `pixiv` | pixiv小説 | 公式確認済み | `[[rb: 親文字 > ルビ]]` | 同左 | `[[emphasismark: 対象 > ﹅]]` | 同左 | 要確認 | pixiv特殊タグ | 不可 | 不可 | 独自タグを他形式へ移すとタグ種別が失われる場合あり | 全特殊タグ | https://www.pixiv.help/hc/ja/articles/39197091470105 |
| `aozora` | 青空文庫 | 公式確認済み | `｜親文字《ルビ》`, `漢字《ルビ》` | `｜親文字《ルビ》` | `［＃「対象」に傍点］` | 同左 | `［＃...］` | 青空文庫注記 | 不可 | 不可 | 注記形式が広いため現在は一部対応 | 注記全般 | https://www.aozora.gr.jp/aozora-manual/index-input.html |
| `note` | note | 公式確認済み | `｜親文字《ルビ》`, `|親文字《ルビ》` | 同左 | 要確認 | 現在は簡略 | 要確認 | note記事記法 | 要確認 | 要確認 | 太字・リンクとの組み合わせは要確認 | 複合装飾 | https://www.help-note.com/hc/ja/articles/4406430353817 |
| `html` | HTML ruby | 仕様一部確認 | `<ruby><rt>` | 同左 | `<span class="emphasis">` 近似 | 同左 | HTMLコメント等は未対応 | HTMLタグ | 可 | 不可 | 不明タグは警告 | HTML全般 | https://html.spec.whatwg.org/multipage/text-level-semantics.html#the-ruby-element |
| `markdown` | Markdown | 一部確認 | 標準なし | `親文字（ルビ）` | 標準なし | `**対象**` 簡略 | 標準なし | Markdown | 一部可 | 可 | ルビ・傍点は lossy | 厳密なエスケープ | https://spec.commonmark.org/ |
| `plain` | プレーンテキスト | 対象仕様なし | なし | 削除または括弧保持 | なし | 本文のみ | なし | なし | 不可 | 不可 | 装飾情報は失われる | なし |  |
