## Windows版

通常のWindowsユーザーは、`RubiMorphSetup-{{VERSION}}.exe` をダウンロードして実行してください。

Pythonを別途インストールする必要はありません。インストール後は、スタートメニューの「RubiMorph」からGUIを起動できます。

ポータブル版を利用する場合は、`RubiMorphPortable-{{VERSION}}.zip` を展開し、フォルダ内の `RubiMorphGUI.exe` を実行してください。

## 主な機能

- Web小説投稿サイト間のルビ・傍点・記法変換
- 「テキスト変換」と「ファイル変換」を分けたGUI
- 共通の形式設定と、変換結果欄に所属するコピー操作
- 「ルビ出力」はプレーンテキスト系の変換先でだけ有効化
- メイン画面下部に直前の成功、警告、失敗、件数、短い警告概要を表示
- 単一ファイル、複数ファイル、フォルダ一括を選べるファイル変換
- ステータスバーと「詳細...」によるログ・警告確認
- CLI対応
- カスタム形式プロファイルの作成・検証・インポート・エクスポート
- 坂本忠恆による小説本文抜粋を使ったカスタム形式サンプル
- カスタム形式プロファイルの変換元・変換先一覧への自動反映
- CLIの `--from-profile`、`--to-profile`、`--validate-profile`
- GUI内のWeb操作マニュアル、使用ガイド、公式サイト、最新版Releaseリンク
- GUI内のバージョン情報・開発者リンク・OSSライセンス表示
- 原稿を外部サーバーへ送信しないローカル処理

## 同梱ファイル

- `RubiMorphSetup-{{VERSION}}.exe`
- `RubiMorphPortable-{{VERSION}}.zip`
- `RubiMorphThirdPartyLicenses-{{VERSION}}.zip`
- `rubimorph.cdx.json`
- `SHA256SUMS.txt`
- `LICENSE`
- `THIRD_PARTY_NOTICES.md`

## 注意

このリリースはコード署名されていないため、Windows SmartScreenの警告が表示される場合があります。
