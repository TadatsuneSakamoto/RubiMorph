# SBOM

SBOM は CycloneDX JSON を優先形式にします。

成果物候補:

```text
dist\sbom\rubimorph.cdx.json
```

生成スクリプト:

```cmd
scripts\generate_sbom.cmd
```

スクリプトは `requirements-build.txt` を入力にして、RubiMorph のビルドに使う Python パッケージを CycloneDX JSON として出力します。`cyclonedx-py` が PATH にない場合は、`py -3 -m cyclonedx_py` または `python -m cyclonedx_py` を試します。いずれも使えない場合は導入案内を表示して停止します。

## 確認事項

- 生成された SBOM に環境固有の秘密情報が含まれないこと。
- `requirements-build.txt` と SBOM の対象が一致していること。
- `THIRD_PARTY_NOTICES.md` と整合していること。
- Release assets の `RubiMorphThirdPartyLicenses-<VERSION>.zip`、Portable ZIP、インストーラーに含める第三者ライセンス本文と矛盾しないこと。
