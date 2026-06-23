# RubiMorph

RubiMorph は、カクヨム、小説家になろう、エブリスタ、pixiv小説、青空文庫、HTML、Markdown、plain text などの間で、ルビ・傍点・注記などの小説投稿サイト記法を変換する Windows ローカル実行中心の創作者向けソフトです。

単なる文字列置換ではなく、本文をいったん中間トークン列へ解析し、変換先プラットフォーム向けに再出力します。組み込み形式に加えて、利用者が JSON で定義するカスタム形式プロファイルを利用できます。

RubiMorph は Web 専用ツールではありません。原稿本文を外部サーバーへ送信せず、手元の PC 上で変換します。ログイン、クラウド保存、外部 API 連携、投稿先への直接送信は実装していません。

## 現在対応済み

- `kakuyomu`: カクヨム
- `narou`: 小説家になろう
- `estar`: エブリスタ
- `pixiv`: pixiv小説
- `aozora`: 青空文庫
- `html`: HTML ruby
- `markdown`: Markdownへの簡略出力
- `plain`: プレーンテキスト

`note` と `novelup` は一部対応として platform profile に登録しています。その他の投稿サイトは調査・拡張用 profile を用意していますが、未対応または要確認です。

## 対応している主な記法

- ルビ: `｜親文字《ルビ》`
- ルビ: `|親文字《ルビ》`
- ルビ: `漢字《ルビ》`
- ルビ: `漢字(ルビ)`
- HTML ruby: `<ruby>親文字<rt>ルビ</rt></ruby>`
- pixivルビ: `[[rb: 親文字 > ルビ]]`
- 傍点: `《《傍点対象》》`
- pixiv傍点: `[[emphasismark: 傍点対象 > ﹅]]`
- 青空文庫風傍点: `［＃「対象」に傍点］`

プレーンテキスト出力では、ルビを削除するモードと `親文字（ルビ）` 形式で残すモードを選べます。この「ルビ出力」はプレーンテキスト系の変換先を選んだときだけ有効になり、HTML、カクヨム、なろう、カスタム形式など対象外の変換先では `対象外` と表示されます。

## 必要環境

- Windows

一般ユーザー向けの `RubiMorphSetup-1.0.0.exe` には実行に必要な Python ランタイムを同梱するため、Python を別途インストールする必要はありません。

ソースから開発・テストする場合は Python 3 を使用します。`py -3 --version` または `python --version` が動く環境を想定しています。変換実行とテストには外部 Python パッケージを使っていません。

## ダウンロード

Windows版は GitHub Releases からダウンロードできます。

- Releases: https://github.com/TadatsuneSakamoto/RubiMorph/releases
- Latest Release: https://github.com/TadatsuneSakamoto/RubiMorph/releases/latest

通常は `RubiMorphSetup-1.0.0.exe` を利用してください。Python を別途インストールする必要はありません。

## GUI 起動

インストール後:

```text
スタートメニュー → RubiMorph
```

インストール時に「デスクトップにショートカットを作成する」を選ぶと、デスクトップの `RubiMorph` ショートカットからも GUI を起動できます。インストール完了画面では「RubiMorphを起動する」を選ぶと、そのまま GUI を開けます。

開発環境:

```cmd
scripts\run_gui.cmd
```

GUI では、上段の「形式設定」で変換元、変換先、ルビ出力を共通設定として選びます。「ルビ出力」は変換先がプレーンテキスト系のときだけ操作でき、対象外の変換先では無効化されます。主作業は「テキスト変換」と「ファイル変換」のタブに分かれ、テキスト変換では入力欄と変換結果欄を左右に並べて使います。結果のコピーは変換結果欄の「コピー」から行います。

ファイル変換では、処理単位として「単一ファイル」「複数ファイル」「フォルダ一括」を選びます。各モードで入力元と出力先を指定し、必須項目がそろうと「変換開始」を実行できます。入力ファイルは上書きせず、既存の安全な出力規則を使います。

メイン画面下部のステータス領域には、直前の操作結果、処理件数、警告件数、短い警告概要が表示されます。ログ全文、対象ファイル、詳細な警告は「詳細...」から確認できます。

メニューの「カスタム形式」→「カスタム形式を管理...」から、カスタム形式プロファイルの管理画面を開けます。新規作成、編集、複製、検証、登録、登録解除、インポート、エクスポート、削除、保存、名前を付けて保存に対応します。検証済みで有効な入力対応プロファイルは変換元へ、出力対応プロファイルは変換先へ `カスタム: ...` と表示され、通常の形式と同じ手順で変換できます。

インストール後の GUI 用実行ファイルは `RubiMorphGUI.exe` です。GUI では原稿本文をローカル PC 上で処理し、外部サーバーへ自動送信しません。

`ヘルプ` メニューから、操作マニュアル、使用ガイド、公式サイト、最新版とRelease、RubiMorph のバージョン、開発者リンク、OSS通知、RubiMorph本体ライセンスを確認できます。

Web上の安定URL:

- 使用ガイド: https://www.tadatsune.com/RubiMorph/guide.html
- 操作マニュアル: https://www.tadatsune.com/RubiMorph/manual.html

## CLI 使用方法

バージョン表示:

```cmd
py -3 src\cli\rubimorph.py --version
```

対応 platform profile 一覧:

```cmd
py -3 src\cli\rubimorph.py --list-platforms
```

変換マトリクス:

```cmd
py -3 src\cli\rubimorph.py --matrix
```

直接テキスト変換:

```cmd
py -3 src\cli\rubimorph.py --from kakuyomu --to pixiv --text "これは｜禁猟の園《きんりょうのその》です。"
```

単一ファイル変換:

```cmd
py -3 src\cli\rubimorph.py --from kakuyomu --to html --input input.txt --output output.txt
```

フォルダ一括変換:

```cmd
py -3 src\cli\rubimorph.py --from kakuyomu --to narou --input-dir input_texts --output-dir converted_texts
```

書き込み前確認:

```cmd
py -3 src\cli\rubimorph.py --from kakuyomu --to pixiv --input-dir input_texts --output-dir converted_texts --dry-run
```

診断レポート出力:

```cmd
py -3 src\cli\rubimorph.py --from kakuyomu --to pixiv --input input.txt --output output.txt --report report.json
```

カスタム形式プロファイルの検証:

```cmd
py -3 src\cli\rubimorph.py --validate-profile examples\custom-profiles\example-bracket-format.rubimorph-profile.json
```

カスタム形式を変換元にする:

```cmd
py -3 src\cli\rubimorph.py --from-profile source.rubimorph-profile.json --to kakuyomu --input input.txt --output output.txt
```

カスタム形式を変換先にする:

```cmd
py -3 src\cli\rubimorph.py --from kakuyomu --to-profile target.rubimorph-profile.json --input input.txt --output output.txt
```

カスタム形式同士で変換する:

```cmd
py -3 src\cli\rubimorph.py --from-profile source.rubimorph-profile.json --to-profile target.rubimorph-profile.json --input input.txt --output output.txt
```

旧入口として `src\cli\nmc.py` も残していますが、正式 CLI は `src\cli\rubimorph.py` です。

インストール後の CLI 用実行ファイルは `RubiMorph.exe` です。`--version`、`--list-platforms`、`--matrix`、`--from`、`--to`、`--from-profile`、`--to-profile`、`--validate-profile`、ファイル変換、フォルダ変換などを利用できます。

## カスタム形式プロファイル

カスタム形式プロファイルは UTF-8 JSON ファイルです。拡張子は `.rubimorph-profile.json` を推奨します。登録済みプロファイルはユーザー設定領域に保存します。

```text
%APPDATA%\RubiMorph\profiles
```

プロファイルには `schema_version`、`profile_id`、`name`、`capabilities`、入力規則、出力テンプレート、前処理、後処理を記述できます。入力規則では正規表現の名前付きグループを使い、ルビは `base` と `reading`、傍点は `text` を内部トークンへ変換します。出力テンプレートではルビに `{base}` と `{reading}`、傍点に `{text}` を使えます。

任意コード実行、式評価、外部プログラム実行は行いません。カスタムプロファイルを含む変換は子プロセスで実行し、既定で 5 秒のタイムアウトを設けています。詳細は [カスタム形式プロファイル仕様](docs/custom-format-profiles.md) を参照してください。

実動サンプル:

```text
examples/custom-profiles/example-bracket-format.rubimorph-profile.json
```

サンプル一式:

```text
examples/custom-profiles/RubiMorph_Custom_Profile_Samples.zip
```

サンプルには、坂本忠恆による小説本文の抜粋を使ったカクヨム形式、カスタム形式、逆変換確認用ファイルを含めています。

## ファイル変換の安全方針

- `.txt` と `.md` を対象にします。
- 入力ファイルは上書きしません。
- 入力先と出力先が同じファイルになる場合、`_converted` を付けた別ファイルへ出力します。
- フォルダ一括変換ではサブフォルダ構成を維持します。
- ログやレポートはファイル名、警告、件数を中心にし、原稿本文の保存を避けます。

## テスト

```cmd
scripts\run_tests.cmd
```

Python から直接実行する場合:

```cmd
py -3 -m unittest discover -s tests -v
```

## 配布

GitHub Releases では以下を配布します。

- `RubiMorphPortable-1.0.0.zip`
- `RubiMorphSetup-1.0.0.exe`
- `rubimorph.cdx.json`
- `RubiMorphThirdPartyLicenses-1.0.0.zip`
- `THIRD_PARTY_NOTICES.md`
- `LICENSE`
- `SHA256SUMS.txt`

PyInstaller / Inno Setup / SBOM 生成用のスクリプトと設定を用意しています。必要ツールが未導入の場合、スクリプトは導入手順を表示して停止します。

正式アイコンは `assets\icons\rubimorph.ico` です。元 PNG は `assets\icons\rubimorph.png` に置く方針で、PNG から ICO を再生成する場合もこの PNG から同じ ICO 名へ生成します。

PyInstaller は onedir 出力を使います。`dist\RubiMorph` には CLI 用の `RubiMorph.exe`、GUI 用の `RubiMorphGUI.exe`、Python ランタイムを含む `_internal` フォルダ、`LICENSE`、`THIRD_PARTY_NOTICES.md`、`LICENSES\`、docs、examples、schemas が生成されます。Inno Setup へ exe 単体だけを含めると `_internal` フォルダが欠落し、インストール後に Python DLL 読み込みエラーになります。インストーラーには必ず `dist\RubiMorph` 配下全体を含めます。exe 単体を別の場所へ移動すると動作しない可能性があります。

## 現在の制限

- 投稿サイトごとの細かな制約は完全再現していません。
- 青空文庫入力の注記解析は一部対応です。
- HTML 入力は HTML ruby を中心に扱います。
- HTML ruby 以外の HTML タグは警告対象です。
- Markdown と plain text にはルビや傍点の同等表現がないため、情報欠落または簡略化が起きます。
- 小説家になろう向け傍点出力は公式本文内記法の追加確認が必要です。
- カスタム形式プロファイルの正規表現は検証とタイムアウトで保護しますが、複雑な正規表現は処理時間が長くなる場合があります。

変換後は投稿前に必ず目視確認してください。各投稿サイトの仕様変更により、変換結果が期待と異なる可能性があります。

## ドキュメント

- [命名方針](docs/naming.md)
- [設計](docs/design.md)
- [プラットフォーム調査](docs/platform-research.md)
- [仕様整理](docs/platform-specs.md)
- [変換マトリクス](docs/conversion-matrix.md)
- [カスタム形式プロファイル仕様](docs/custom-format-profiles.md)
- [対応範囲監査](docs/coverage-audit.md)
- [Windowsでの使い方](docs/usage-windows.md)
- [インストーラ方針](docs/installer.md)
- [リリース手順](docs/release.md)
- [セキュリティとプライバシー](docs/security-and-privacy.md)
- [公開情報管理方針](docs/publication-policy.md)

## ライセンスとOSSクレジット

プロジェクト本体は MIT License です。依存関係と同梱物の確認方針は [license-review](docs/license-review.md)、SBOM 方針は [sbom](docs/sbom.md)、OSS クレジットは [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) を参照してください。

## 要望・不具合

対応サイト追加、記法追加、変換結果の問題は GitHub Issues で受け付ける想定です。未対応サイトの仕様は、公式ヘルプまたは公式マニュアルのURLと一緒に報告してください。
