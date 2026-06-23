# RubiMorph Web Assets

`src/web/public/` is the managed source for the static RubiMorph web pages that are deployed under:

```text
https://www.tadatsune.com/RubiMorph/
```

Current managed files:

- `guide.html`
- `manual.html`
- `rubimorph-guide.css`
- `rubimorph-guide.js`
- `rubimorph-manual.css`
- `assets/rubimorph-guide.png`
- `assets/rubimorph-guide.ico`
- `samples/`

The files in `samples/` are copied from `examples/custom-profiles/`. Do not edit the repository sample and web sample copies independently. Refresh the web copy from the repository sample source, then regenerate or recopy `RubiMorph_Custom_Profile_Samples.zip`.

Before deploying to the VPS, back up the current `/var/www/html/RubiMorph/` tree and verify the public URLs after upload.
