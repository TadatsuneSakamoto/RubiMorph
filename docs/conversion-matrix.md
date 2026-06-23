# Conversion Matrix

状態:

- `supported`: 現在の実装とテストあり
- `partial`: 一部対応
- `lossy`: 情報欠落あり
- `warning-required`: 警告付きで参考出力
- `research-needed`: 仕様調査が必要
- `unsupported`: 未対応
- `not-applicable`: 同一形式または対象外

| from / to | kakuyomu | narou | estar | pixiv | aozora | html | markdown | plain |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| kakuyomu | not-applicable | partial: ルビ対応、傍点要確認 | supported | supported | partial | supported | lossy | lossy |
| narou | supported | not-applicable | supported | supported | partial | supported | lossy | lossy |
| estar | supported | partial | not-applicable | supported | partial | supported | lossy | lossy |
| pixiv | supported | partial | supported | not-applicable | partial | supported | lossy | lossy |
| aozora | partial | partial | partial | partial | not-applicable | partial | lossy | lossy |
| html | supported | partial | supported | supported | partial | not-applicable | lossy | lossy |
| markdown | partial | partial | partial | partial | partial | partial | not-applicable | lossy |
| plain | partial | partial | partial | partial | partial | partial | partial | not-applicable |

## 詳細

- ルビ: `kakuyomu`, `narou`, `estar`, `pixiv`, `aozora`, `html`, `plain` の主要経路を実装。
- 傍点: `kakuyomu` / `estar` / `pixiv` / `aozora` / `html` / `plain` を実装。`narou` は warning-required。
- 注記: 青空文庫注記の全体は未実装。現在の実装は傍点注記のみ。
- 独自タグ: pixiv の `rb` と `emphasismark` を実装。その他の特殊タグは一部保持または警告。
- テスト: core、fileops、CLI、golden test を追加。
