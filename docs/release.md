# Release

RubiMorph の正式リリースは、`main` 上の `vX.Y.Z` タグを起点に GitHub Actions で作成します。手元で生成した exe を個別にアップロードして終わらせず、同じ手順を次回以降のバージョンにも再利用します。

## 利用者向け配布物

GitHub Releases:

- https://github.com/TadatsuneSakamoto/RubiMorph/releases
- https://github.com/TadatsuneSakamoto/RubiMorph/releases/latest

通常の Windows ユーザーは `RubiMorphSetup-1.0.0.exe` をダウンロードして実行します。Python を別途インストールする必要はありません。インストール後はスタートメニューの `RubiMorph` から GUI を起動できます。

ポータブル版を使う場合は `RubiMorphPortable-1.0.0.zip` を展開し、展開先の `RubiMorph\RubiMorphGUI.exe` を実行します。`_internal` フォルダを含む onedir 一式が必要なため、exe 単体だけを別の場所へ移動しないでください。

## 自動リリース手順

1. `VERSION` を更新する。
2. 必要に応じて `pyproject.toml` の `version` も同じ値に更新する。
3. `scripts\run_tests.cmd` とビルド確認を通す。
4. Pull Request を `main` へマージする。
5. `main` を最新化し、`VERSION` と一致する `vX.Y.Z` タグを `main` の commit へ作成する。
6. タグを `origin` へ push する。
7. GitHub Actions の `Build and publish Windows release` が Windows 上でテスト、exe ビルド、インストーラービルド、Portable ZIP、SBOM、SHA-256 を生成し、Release を公開する。
8. Release assets と `SHA256SUMS.txt` を確認する。

例:

```powershell
git switch main
git pull --ff-only origin main
git tag -a vX.Y.Z -m "RubiMorph X.Y.Z"
git push origin vX.Y.Z
```

同じタグを使い回さないでください。公開済み Release のタグを別 commit へ移動しないでください。`VERSION` とタグが一致しない場合、workflow は Release を作成せず失敗します。

## Release assets

workflow は `release\` に次のファイルを集め、GitHub Release へ添付します。

- `RubiMorphSetup-1.0.0.exe`
- `RubiMorphPortable-1.0.0.zip`
- `RubiMorphThirdPartyLicenses-1.0.0.zip`
- `SHA256SUMS.txt`
- `rubimorph.cdx.json`
- `THIRD_PARTY_NOTICES.md`
- `LICENSE`

`RubiMorphPortable-1.0.0.zip` は `RubiMorph\` フォルダを含み、その中に `RubiMorph.exe`、`RubiMorphGUI.exe`、`_internal\`、`README.md`、`LICENSE`、`THIRD_PARTY_NOTICES.md`、`LICENSES\`、docs、examples、schemas を入れます。

## ローカル確認

```cmd
scripts\run_tests.cmd
py -3 -m compileall -q src tests
scripts\build_exe.cmd
scripts\build_installer.cmd
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\prepare_release_assets.ps1
```

確認対象:

- `dist\RubiMorph\RubiMorph.exe`
- `dist\RubiMorph\RubiMorphGUI.exe`
- `dist\RubiMorph\_internal\python*.dll`
- `dist\installer\RubiMorphSetup-1.0.0.exe`
- `release\RubiMorphPortable-1.0.0.zip`
- `release\RubiMorphThirdPartyLicenses-1.0.0.zip`
- `release\SHA256SUMS.txt`
- `release\rubimorph.cdx.json`

## コード署名

現在の Release 成果物はコード署名していません。Windows SmartScreen の警告が表示される場合があります。署名していない成果物を、署名済みまたは安全確認済みとして説明しないでください。
