# RubiMorph Naming

## 正式名称

正式名称は `RubiMorph` です。

`Rubi` は日本語の「ルビ」を ASCII 表記へ寄せた語です。HTML ruby やプログラミング言語 Ruby との混同を避けつつ、ふりがな・ルビ記法を中心に扱うソフトであることを示します。

`Morph` は形を変える、別の形態へ移すという意味です。単なる置換ではなく、投稿サイトごとの記法体系へ本文内メタ記法を変形・変換することを示します。

RubiMorph はルビ専用ではありません。ルビを中心に、傍点、注記、HTML ruby、pixiv特殊タグ、青空文庫風注記、Markdown、plain text、HTML なども扱います。正式説明では「ルビ・傍点・注記などの小説投稿サイト記法変換ソフト」と書きます。

## 成果物名

| 項目 | 値 |
| --- | --- |
| Product name | RubiMorph |
| Repository display name | RubiMorph |
| Repository root | `<repository-root>` |
| Current GitHub repository | `https://github.com/TadatsuneSakamoto/RubiMorph` |
| Repository name | `RubiMorph` |
| Python package name | `rubimorph` |
| Primary CLI file | `src\cli\rubimorph.py` |
| CLI command name | `rubimorph` |
| Compatibility CLI | `src\cli\nmc.py` |
| Main executable | `RubiMorph.exe` |
| Installer filename | `RubiMorphSetup-1.0.0.exe` |
| Portable zip filename | `RubiMorphPortable-1.0.0.zip` |
| Third-party licenses zip filename | `RubiMorphThirdPartyLicenses-1.0.0.zip` |
| SBOM filename | `rubimorph.cdx.json` |
| Checksums filename | `SHA256SUMS.txt` |

## 今すぐ変更した範囲

- README のタイトルと説明
- docs の命名・設計・配布候補名
- core package `rubimorph`
- primary CLI `src\cli\rubimorph.py`
- CLI `--version` 表示
- GUI タイトルと About 表示
- PyInstaller / Inno Setup / Release docs の成果物候補名
- GitHub repository とリポジトリルートの正式名

## 互換方針

既存の `src\cli\nmc.py` は互換入口として残します。既存の `src/core/novel_markup` package も `rubimorph` への互換 wrapper として残します。

## 今後確認すべき範囲

- インストーラ署名や配布名の最終確定
- PyPI など外部 package registry への公開名
- 既存 API の完全移行と互換 wrapper の廃止時期
