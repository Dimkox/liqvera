# Methodology and reproduction

## Input

```text
filename: goodcryptoX-2.5.1.apk
sha256:   70ecfc62a62a0c822b310e992e77e477e797ebdc5e87abdb43cc59d50e1acb1c
bytes:    48198914
```

## Static pipeline

1. **APK extraction** — standard ZIP extraction; no code execution.
2. **Android binary XML** — `tools/decode_axml.py` decodes the manifest and selected compiled XML resources.
3. **DEX inventory** — `tools/parse_dex.py` parses string/type/prototype/field/method/class tables and disassembles package-local method instructions.
4. **Embedded web assets** — JS chunks are parsed with the TypeScript compiler AST. `tools/analyze_js.mjs` inventories symbols, calls, strings, imports, exports, routes, storage operations and URLs.
5. **Readable representation** — `tools/pretty_js.mjs` prints an AST-normalized local copy. Full proprietary output is not committed.
6. **Semantic extraction** — `tools/extract_semantics.mjs` identifies Pinia stores, Vue components, class members, private sends/responses, Firebase callables, storage operations, REST calls and WebSockets.
7. **Native libraries** — `file`, `readelf` and selective `strings`; no emulation or execution.
8. **Manual control-flow reconstruction** — high-value order, bot, route, signing, wallet and deep-link functions were reviewed and converted to pseudocode.
9. **Sanitization** — raw APK/DEX/SO/JS bodies and secret-like values are excluded. Only names, signatures, locations, hashes and derived descriptions are published.

## Reproduction commands

```bash
mkdir -p work/apk work/pretty work/analysis
unzip -q goodcryptoX-2.5.1.apk -d work/apk

python3 tools/decode_axml.py work/apk/AndroidManifest.xml work/analysis/AndroidManifest.decoded.xml
python3 tools/parse_dex.py --input-dir work/apk --out-dir work/analysis/dex --code-prefix 'Lapp/goodcrypto/'

for f in work/apk/assets/public/assets/*.js; do
  node tools/pretty_js.mjs "$f" "work/pretty/$(basename "$f")"
done

node tools/analyze_js.mjs work/apk/assets/public/assets work/analysis/js
node tools/extract_semantics.mjs work/pretty work/analysis/semantics
```

Scripts require Python 3.10+ and Node.js with TypeScript. They perform static parsing only.

## Confidence model

- **Confirmed:** literal manifest/bundle/DEX/resource evidence with file and line/member reference.
- **High-confidence reconstruction:** control flow follows directly from client code but names are restored semantically from minified bindings.
- **Inference:** behavior depends on backend validation, exchange adapters, Firebase rules or live chain responses absent from the APK.

## Limitations

- Minification removes many original local variable and TypeScript type names.
- Source maps are absent.
- Server-side exchange adapters and strategy executors cannot be reconstructed from this APK.
- Dynamic behavior, runtime feature flags and server responses were not exercised.
- This is a structural and algorithmic reconstruction, not a buildable clone.
