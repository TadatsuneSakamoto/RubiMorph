# RubiMorph Design

## local-first

RubiMorph は、創作者が手元の原稿ファイルを安心して変換するためのツールです。現在の公開版ではログイン、クラウド保存、外部 API 連携を持たず、Windows ローカルで完結する GUI と CLI を優先します。

原稿本文はユーザーの PC 内で読み書きされます。アプリ側から外部サーバーへ送信しません。将来 Web 版を作る場合も、本文送信の有無を設計上明示し、ローカル版とは分離して扱います。

## core / cli / desktop / web

変換エンジンは `src/core/rubimorph` に置き、UI から独立させます。

- `core`: platform profile、parser、renderer、diagnostics、fileops
- `cli`: 一括変換、dry-run、診断レポート
- `desktop`: Windows ローカル GUI
- `web`: 将来の Web 版に向けた置き場

同じ core を CLI、GUI、将来の Web 版で共有することで、入口ごとに変換結果がずれることを避けます。

## 中間トークン

入力文字列は直接置換せず、まず中間トークン列へ変換します。現在の実装では以下のトークンを定義しています。

- `TextToken`
- `RubyToken`
- `EmphasisToken`
- `AnnotationToken`
- `StrongToken`
- `BreakToken`
- `HeadingToken`
- `HorizontalRuleToken`
- `PageBreakToken`
- `RawToken`
- `RawHtmlToken`
- `MarkdownToken`
- `PlatformSpecificToken`
- `UnknownMarkupToken`
- `UnsupportedToken`

基本処理は以下です。

```text
入力本文
-> source platform parser
-> 中間トークン列
-> diagnostics
-> target platform renderer
-> 出力本文
```

この構成により、カクヨム、なろう、エブリスタ、pixiv、青空文庫、HTML、plain の差分を parser / renderer / diagnostics に分離できます。

## platform profile

各プラットフォームは `platform_profiles.py` で定義します。profile は以下を持ちます。

- platform id
- 表示名
- 公式URL
- 仕様確認状態
- 対応状態
- 入力対応記法
- 出力対応記法
- ルビ記法
- 傍点記法
- 注記記法
- HTML / Markdown 許可
- エスケープ規則
- 情報欠落リスク
- 警告条件

対応状態は `supported` / `partial` / `planned` / `research-needed` / `unsupported` です。未調査のプラットフォームも profile として登録し、変換時には警告を出します。

## CLI と GUI を両方持つ理由

GUI は直接貼り付け変換と日常的な確認に向きます。CLI は複数話、複数章、フォルダ単位の一括変換に向きます。どちらも同じ core を使い、入力ファイルを上書きしない方針を共有します。

## 将来 Web 版

Web 版は将来候補です。現在の公開版では Web 専用ツールにせず、core を UI から分離しておくことで移植可能性を残します。Web 版を作る場合も、原稿本文をどこで処理するか、保存するか、通信するかを明確にします。

## 配布

Windows ユーザーが使いやすい導線として、GitHub Releases、Portable zip、Windows インストーラ、SBOM、チェックサムを用意します。必要ツールが未導入の場合は導入案内を表示して停止します。

## 継続開発

投稿サイトの仕様は変わる可能性があります。公式ヘルプの確認日、未確認事項、変換マトリクス、テストを docs と tests に残し、GitHub 上で継続的に更新できる構成にします。
