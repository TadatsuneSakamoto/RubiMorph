# Custom Format Profiles

カスタム形式プロファイルは、RubiMorph の内部トークン列を使って独自の入力形式・出力形式を追加する UTF-8 JSON ファイルです。任意の Python、JavaScript、シェルコマンド、外部プログラムは実行しません。

推奨拡張子:

```text
.rubimorph-profile.json
```

登録済みプロファイルの保存場所:

```text
%APPDATA%\RubiMorph\profiles
```

`APPDATA` がない環境では `~/.rubimorph/profiles` を使用します。インストール先や `Program Files` 配下には保存しません。保存時は一時ファイルへ書き込み、検証成功後に置換します。

## 基本構造

```json
{
  "schema_version": 1,
  "profile_id": "example-bracket-format",
  "name": "Example Bracket Format",
  "description": "独自投稿システム用",
  "enabled": true,
  "capabilities": {
    "input": true,
    "output": true
  }
}
```

- `schema_version`: 現在は `1` のみ対応。
- `profile_id`: 英数字で始まり、英数字・ハイフン・アンダースコアを使う識別子。
- `name`: GUI 表示名。日本語を使用可能。
- `description`: 説明。日本語を使用可能。
- `enabled`: 登録済みプロファイルを変換元・変換先に表示するかどうか。
- `capabilities.input`: 入力形式として使用するかどうか。
- `capabilities.output`: 出力形式として使用するかどうか。

同じ登録領域に、同じ `profile_id` の有効なプロファイルを複数置くことはできません。

## 入力規則

入力対応プロファイルでは `parser.rules` を指定します。現在扱う内部要素は `ruby` と `emphasis` です。

```json
{
  "parser": {
    "rules": [
      {
        "id": "ruby",
        "name": "ルビ",
        "kind": "ruby",
        "enabled": true,
        "priority": 100,
        "pattern": "\\[\\[ruby:(?P<base>.+?)\\|(?P<reading>.+?)\\]\\]",
        "flags": []
      },
      {
        "id": "emphasis",
        "name": "傍点",
        "kind": "emphasis",
        "enabled": true,
        "priority": 90,
        "pattern": "\\[\\[em:(?P<text>.+?)\\]\\]",
        "flags": []
      }
    ]
  }
}
```

`ruby` には名前付きグループ `base` と `reading` が必要です。`emphasis` には `text` が必要です。使用可能な flags は `IGNORECASE`、`MULTILINE`、`DOTALL`、`ASCII` です。

複数規則が一致する場合は、次の順で決定します。

1. 一致開始位置が早い
2. `priority` が高い
3. 一致範囲が長い
4. プロファイル内で先に定義されている

一致しなかった文字列は通常テキストとして保持します。ゼロ文字一致する正規表現は禁止です。

## 出力テンプレート

出力対応プロファイルでは `renderer.templates` を指定します。

```json
{
  "renderer": {
    "templates": {
      "ruby": "[[ruby:{base}|{reading}]]",
      "emphasis": "[[em:{text}]]"
    }
  }
}
```

使用可能なプレースホルダー:

- `ruby`: `{base}`, `{reading}`
- `emphasis`: `{text}`

属性アクセス、配列アクセス、関数呼び出し、式評価、`eval`、`exec` は使用しません。不明なプレースホルダーは検証エラーです。波括弧そのものを出力する場合は `{{` と `}}` を使います。

## 前処理と後処理

`transforms.before_parse` は入力解析前、`transforms.after_render` は出力生成後に、上から順に実行します。

```json
{
  "transforms": {
    "before_parse": [
      {
        "id": "normalize-ruby-name",
        "name": "rubyタグ名を正規化",
        "enabled": true,
        "type": "literal",
        "pattern": "[[rb:",
        "replacement": "[[ruby:",
        "flags": []
      }
    ],
    "after_render": [
      {
        "id": "normalize-blank-lines",
        "name": "空行を整理",
        "enabled": true,
        "type": "regex",
        "pattern": "\\n{3,}",
        "replacement": "\\n\\n",
        "flags": []
      }
    ]
  }
}
```

`type` は `literal` または `regex` です。`literal` は単純な文字列置換、`regex` は正規表現置換です。

## 検証

保存時、読み込み時、登録時、CLI の `--validate-profile` 実行時に検証します。検証では、可能な限り複数の問題をまとめて返します。

主な検証項目:

- UTF-8 JSON として読める
- トップレベルがオブジェクト
- `schema_version` が対応範囲内
- 必須項目の存在
- `profile_id` の形式
- capabilities の妥当性
- 規則IDの重複
- 正規表現のコンパイル可否、空パターン、ゼロ文字一致
- 必須名前付きグループ
- 出力テンプレートのプレースホルダー
- 不明な `kind`、flags、JSON項目
- `priority` が整数
- 規則数、パターン長、テンプレート長、置換文字列長、ファイルサイズの上限

エラーがあるプロファイルは変換元・変換先として表示しません。不正なプロファイルが保存領域にあっても、RubiMorph 全体は起動します。

## 正規表現の停止対策

依存関係を増やさず Windows 配布物で確実に動作させるため、カスタムプロファイルを含む変換は子プロセスで実行します。既定のタイムアウトは 5 秒です。タイムアウトした場合は子プロセスを停止し、問題を起こした可能性があるプロファイル変換としてエラーを返します。

加えて、次の上限を設けています。

- プロファイルファイルサイズ: 256 KiB
- 規則数: 100
- 正規表現パターン長: 512 文字
- テンプレート長: 512 文字
- 置換文字列長: 1024 文字

## CLI

```cmd
py -3 src\cli\rubimorph.py --validate-profile examples\custom-profiles\example-bracket-format.rubimorph-profile.json
```

```cmd
py -3 src\cli\rubimorph.py --from-profile source.rubimorph-profile.json --to kakuyomu --input input.txt --output output.txt
```

```cmd
py -3 src\cli\rubimorph.py --from kakuyomu --to-profile target.rubimorph-profile.json --input input.txt --output output.txt
```

```cmd
py -3 src\cli\rubimorph.py --from-profile source.rubimorph-profile.json --to-profile target.rubimorph-profile.json --input input.txt --output output.txt
```

`--from` と `--from-profile`、`--to` と `--to-profile` は同時指定できません。`--validate-profile` はエラーがある場合に終了コード `1`、引数の組み合わせが不正な場合に `2` を返します。

## GUI

メニューの「カスタム形式」→「カスタム形式を管理...」から管理画面を開きます。メイン画面にカスタム形式専用の変換ボタンはありません。

管理画面では、登録済みプロファイルの一覧、検証状態、保存場所、最終更新日時を確認できます。新規作成、編集、複製、検証、登録、登録解除、インポート、エクスポート、削除、保存、名前を付けて保存に対応します。

編集画面では、基本情報、入力規則、出力テンプレート、前処理、後処理、検証とテストを編集できます。検証済みで有効な入力対応プロファイルは変換元へ、出力対応プロファイルは変換先へ `カスタム: 表示名` と表示されます。入出力両対応のプロファイルは両方に表示され、通常の形式と同じ手順で変換できます。

## サンプル

実動サンプル:

```text
examples/custom-profiles/example-bracket-format.rubimorph-profile.json
examples/custom-profiles/RubiMorph_Custom_Profile_Samples.zip
```

対応する記法:

```text
[[ruby:親文字|ルビ]]
[[em:傍点対象]]
```

サンプル一式には、通常の確認用テキストのほか、坂本忠恆による小説本文の抜粋を使った次のファイルを含めています。

- `author-work-sample-kakuyomu.txt`: カクヨム形式の原文
- `author-work-sample-custom-format.txt`: サンプルカスタム形式へ変換した結果
- `author-work-sample-roundtrip-kakuyomu.txt`: カスタム形式からカクヨム形式へ戻した結果

`author-work-sample-custom-format.txt` と `author-work-sample-roundtrip-kakuyomu.txt` は RubiMorph の実変換処理で生成します。逆変換結果は原文と完全一致することを確認します。
