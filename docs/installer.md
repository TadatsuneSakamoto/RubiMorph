# Installer Notes

Windows 向けに PyInstaller onedir 出力と Inno Setup インストーラーを用意します。一般ユーザーは `RubiMorphSetup-1.0.0.exe` を実行すればよく、Python を別途インストールする必要はありません。

## PyInstaller

設定:

```text
installer\pyinstaller\rubimorph.spec
```

実行:

```cmd
scripts\build_exe.cmd
```

PyInstaller が未導入の場合、スクリプトは導入案内を表示して停止します。自動インストールはしません。

RubiMorph の正式アイコンは `assets\icons\rubimorph.ico` です。PyInstaller の各 `EXE` にはこの ICO を `icon` として指定し、GUI からも同じ ICO を参照します。元 PNG は `assets\icons\rubimorph.png` に置く方針です。PNG から ICO を再生成する場合も、`assets\icons\rubimorph.png` から `assets\icons\rubimorph.ico` を作成してください。

PyInstaller は同じ `dist\RubiMorph` フォルダに次の実行ファイルを生成します。

- `RubiMorph.exe`: CLI 用。既存の `--version`、`--list-platforms`、`--matrix`、変換オプションを維持する。
- `RubiMorphGUI.exe`: GUI 用。Windows GUI subsystem で生成し、起動時に黒いコンソールウィンドウを表示しない。
- `LICENSE`、`THIRD_PARTY_NOTICES.md`、`LICENSES\`: GUI の `ヘルプ` → `OSSライセンス` から表示するライセンス・通知文と第三者ライセンス本文。

## Inno Setup

設定:

```text
installer\inno\rubimorph.iss
```

実行:

```cmd
scripts\build_installer.cmd
```

`iscc` が見つからない場合、スクリプトは停止します。

PyInstaller の onedir 出力では、`dist\RubiMorph` 配下全体をインストーラーに含める必要があります。`RubiMorph.exe` 単体だけを Inno Setup の `[Files]` に含めると、`_internal` フォルダが欠落し、インストール後に `Failed to load Python DLL` や `python*.dll` 読み込みエラーが発生します。

Inno Setup では以下を満たすようにします。

- `dist\RubiMorph\*` を `recursesubdirs createallsubdirs` 付きで `{app}` に配置する。
- `README.md`、`LICENSE`、`THIRD_PARTY_NOTICES.md`、`LICENSES\` を `{app}` に同梱する。
- `assets\icons\rubimorph.ico` を `SetupIconFile` に指定する。
- スタートメニューの `RubiMorph` ショートカットは `{app}\RubiMorphGUI.exe` を起動し、作業フォルダは `{app}` にする。
- インストール時に「デスクトップにショートカットを作成する」を選べるようにし、デスクトップショートカットも `{app}\RubiMorphGUI.exe` を起動する。
- インストール完了画面に「RubiMorphを起動する」を表示し、選択された場合は `{app}\RubiMorphGUI.exe` を起動する。サイレントインストール時は自動起動しない。
- スタートメニュー、デスクトップ、アンインストール表示、インストーラーは正式アイコン `assets\icons\rubimorph.ico` 由来のアイコンを使う。
- 64bit ビルドでは `ArchitecturesAllowed=x64compatible` と `ArchitecturesInstallIn64BitMode=x64compatible` を指定し、標準インストール先を `C:\Program Files\RubiMorph` 側に寄せる。

インストール後も原稿はローカル PC 上で処理され、外部サーバーへ自動送信されません。

## 成果物名

- `RubiMorph.exe`
- `RubiMorphGUI.exe`
- `RubiMorphPortable-1.0.0.zip`
- `RubiMorphSetup-1.0.0.exe`
- `RubiMorphThirdPartyLicenses-1.0.0.zip`

## 未導入時の対処

必要ツールを導入するか、GitHub Releases ではソース zip と CLI/GUI 実行手順のみを先に配布します。
