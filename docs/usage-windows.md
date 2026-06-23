# Windows Usage

## GUI

```cmd
scripts\run_gui.cmd
```

1. 変換元を選びます。
2. 変換先を選びます。
3. 変換先がプレーンテキスト系の場合だけ、必要に応じてルビ出力を選びます。HTML、カクヨム、なろう、カスタム形式など対象外の変換先では `対象外` と表示されます。
4. 「テキスト変換」タブに本文を貼り付けて「変換」を押します。
5. 変換結果欄の「コピー」で結果をコピーします。
6. ステータスバーの警告件数を確認し、必要に応じて「詳細...」でログと警告を確認します。
7. 投稿前に変換結果を目視確認します。

ファイル変換を使う場合:

1. 「ファイル変換」タブを開きます。
2. 処理単位を「単一ファイル」「複数ファイル」「フォルダ一括」から選びます。
3. 入力ファイル、選択ファイル、入力フォルダなど、現在のモードに必要な入力元を指定します。
4. 出力先または出力フォルダを指定します。
5. 「変換開始」を押します。
6. ステータスバーと「詳細...」で結果、警告、エラーを確認します。

カスタム形式を使う場合:

1. メニューの「カスタム形式」→「カスタム形式を管理...」を開きます。
2. 新規作成、編集、インポートのいずれかでプロファイルを用意します。
3. 「検証」でエラーがないことを確認します。
4. 登録状態を有効にします。
5. 入力対応プロファイルは変換元に、出力対応プロファイルは変換先に `カスタム: ...` と表示されます。
6. 通常の形式と同じように、テキスト変換またはファイル変換で使います。

サンプル一式は `examples\custom-profiles\RubiMorph_Custom_Profile_Samples.zip` にあります。`author-work-sample-kakuyomu.txt` をカクヨムからサンプルカスタム形式へ変換し、`author-work-sample-custom-format.txt` と比較できます。逆変換結果は `author-work-sample-roundtrip-kakuyomu.txt` で確認できます。

ヘルプ:

- 「操作マニュアルを開く」: https://www.tadatsune.com/RubiMorph/manual.html
- 「使用ガイドを開く」: https://www.tadatsune.com/RubiMorph/guide.html
- 「公式サイトを開く」: https://www.tadatsune.com/
- 「最新版とRelease」: https://github.com/TadatsuneSakamoto/RubiMorph/releases/latest

## CLI

```cmd
py -3 src\cli\rubimorph.py --version
py -3 src\cli\rubimorph.py --list-platforms
py -3 src\cli\rubimorph.py --matrix
```

直接入力:

```cmd
py -3 src\cli\rubimorph.py --from kakuyomu --to pixiv --text "これは｜禁猟の園《きんりょうのその》です。"
```

ファイル変換:

```cmd
py -3 src\cli\rubimorph.py --from kakuyomu --to html --input input.txt --output output.txt
```

フォルダ変換:

```cmd
py -3 src\cli\rubimorph.py --from kakuyomu --to pixiv --input-dir manuscripts --output-dir converted
```

dry-run:

```cmd
py -3 src\cli\rubimorph.py --from kakuyomu --to pixiv --input-dir manuscripts --output-dir converted --dry-run
```

カスタム形式プロファイル:

```cmd
py -3 src\cli\rubimorph.py --validate-profile examples\custom-profiles\example-bracket-format.rubimorph-profile.json
py -3 src\cli\rubimorph.py --from-profile source.rubimorph-profile.json --to kakuyomu --input input.txt --output output.txt
py -3 src\cli\rubimorph.py --from kakuyomu --to-profile target.rubimorph-profile.json --input input.txt --output output.txt
py -3 src\cli\rubimorph.py --from-profile source.rubimorph-profile.json --to-profile target.rubimorph-profile.json --input input.txt --output output.txt
```

## 注意

入力ファイルは上書きしません。同じパスへ出力しようとした場合は `_converted` を付けます。カスタム形式プロファイルは任意コードを実行しません。正規表現を含む変換にはタイムアウトを設けています。各投稿サイトの仕様変更により結果が変わる可能性があるため、投稿前に必ず目視確認してください。
