# Release Process

正式なリリース手順は [Release](release.md) にまとめています。

`main` 上の `vX.Y.Z` タグを push すると、GitHub Actions が Windows 版のテスト、exe ビルド、インストーラービルド、Portable ZIP、SBOM、SHA-256、GitHub Release 公開を実行します。
