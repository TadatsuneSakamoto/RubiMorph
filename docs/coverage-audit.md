# Coverage Audit

## 完全対応ではない前提

RubiMorph は、すべての投稿サイト記法に完全対応していません。「完全対応済み」と「将来対応可能」は分けて扱います。

## 現時点で対応済み

- カクヨム系ルビの入力と出力
- 小説家になろう系ルビの入力と出力
- エブリスタ系ルビと傍点の入力と出力
- pixiv `[[rb: ... > ...]]`
- pixiv `[[emphasismark: ... > ...]]`
- HTML ruby 入出力
- 青空文庫風ルビと傍点注記の一部
- plain text への削除または括弧保持
- Markdown への簡略出力

## 一部対応

- `note`: ルビは対応。太字・リンクとの複合は未対応。
- `novelup`: profile はあるが公式本文内記法の詳細未確認。
- `aozora`: 注記が広いため傍点注記以外は未対応。
- `html`: HTML ruby 以外のタグは変換品質保証外。

## 調査済みだが未実装

- pixiv の太字・斜体など一部特殊タグ。
- note の複合装飾。
- 青空文庫の注記一覧全体。

## 要調査

`alphapolis`, `hameln`, `novelpia`, `maho_i_land`, `berry_cafe`, `noichigo`, `tapnovel`, `pri_shosetsu`, `uranai_tkool`, `arcadia`, `fc2_novel`。

## 情報欠落が起きる変換

- 任意形式から `plain`: ルビ・傍点・注記は削除または括弧保持へ簡略化。
- 任意形式から `markdown`: 標準 Markdown にルビ・傍点がないため lossy。
- `aozora` から他形式: 注記の意味を完全に保持できない場合がある。
- `pixiv` から他形式: pixiv 独自タグの種類が失われる場合がある。

## 追加しやすいプラットフォーム

`｜親文字《ルビ》` と `《《傍点》》` 系であれば profile と renderer の追加で対応しやすいです。

## 追加が難しいプラットフォーム

- GUI操作だけで本文内記法が公開されていないもの。
- 独自タグが入れ子構造を持つもの。
- HTMLやMarkdownを部分的に許可し、サニタイズ結果が投稿先依存になるもの。
- TapNovel のような台本・演出情報中心のもの。

## ラウンドトリップ可能性

| 経路 | 結果 | 理由 |
| --- | --- | --- |
| kakuyomu -> html -> kakuyomu | おおむね可能 | HTML ruby のみなら復元可能。 |
| kakuyomu -> pixiv -> kakuyomu | おおむね可能 | ルビと傍点の基本形は復元可能。 |
| html -> kakuyomu -> html | 一部可能 | HTML ruby 以外のタグは保持保証外。 |
| kakuyomu -> plain -> kakuyomu | 不可 | ルビ情報が失われる。 |
| aozora -> html -> aozora | 一部のみ | 注記全体の意味を保持できない。 |

## 残っている課題

- 公式仕様が未確認のプラットフォーム調査。
- platform profile 項目の増強。
- parser / renderer / diagnostics の platform 別分割。
- 青空文庫注記の広範な対応。
- pixiv特殊タグ全体の対応。
- 投稿前プレビューとの差分検証。
- より多い golden test とラウンドトリップ test。
