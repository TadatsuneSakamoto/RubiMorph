# License Review

## プロジェクト本体

MIT License を採用しています。`LICENSE` を参照してください。

## 現在の依存と同梱物

実行時の変換処理は Python 標準ライブラリ中心です。Tkinter も標準同梱の GUI ライブラリです。

Windows バイナリ配布では、PyInstaller が Python ランタイム、標準ライブラリ、Tk/Tcl 関連ファイル、PyInstaller bootloader/runtime 部分を同梱します。Inno Setup インストーラーには、生成された setup/uninstaller runtime も含まれます。

## ファイルの役割

- `THIRD_PARTY_NOTICES.md`: 第三者コンポーネント、用途、バージョン、同梱区分の一覧。
- `LICENSES/`: 実際のビルド環境またはインストール済みパッケージメタデータから取得した正式なライセンス本文。
- `rubimorph.cdx.json`: `requirements-build.txt` から生成する機械可読SBOM。

GUIの `ヘルプ` → `OSSライセンス` は、`LICENSE`、`THIRD_PARTY_NOTICES.md`、`LICENSES/` の主要ファイルを表示対象にします。

## 配布時に確認するもの

- Python 実行環境を同梱する場合のライセンス本文が、実際のビルドに使った Python バージョンと一致すること。
- Tk/Tcl 関連ファイルのライセンス本文またはPython配布物内の記載が同梱されていること。
- PyInstaller bootloader のライセンス本文が、実際に使用した PyInstaller バージョンと一致すること。
- Inno Setup を使う場合の配布条件とライセンス本文が同梱されていること。
- Portable ZIP とインストーラーに `LICENSE`、`THIRD_PARTY_NOTICES.md`、`LICENSES/` が含まれること。
- GitHub Release に `RubiMorphThirdPartyLicenses-<VERSION>.zip`、SBOM、チェックサムが含まれること。
- SBOM と `THIRD_PARTY_NOTICES.md` が矛盾しないこと。
- 同梱するサンプル本文が権利上問題ないこと。

## OSSクレジット

`THIRD_PARTY_NOTICES.md` に記録します。依存またはビルド環境を変更した場合は、名前、URL、ライセンス、バージョン、同梱有無を更新し、必要なライセンス本文を `LICENSES/` に追加または差し替えます。
