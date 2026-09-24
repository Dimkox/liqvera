# Security and privacy findings

Severity reflects static client evidence only. No live credential was validated and no backend exploit was attempted.

## GCX-01 — Build-host environment and credential-like value embedded in production bundle

**Severity:** High; potentially critical if the credential remains valid  
**Evidence:** `index-DHlB7G7_.js:3712` and `:4402`

Two production bundle objects contain a broad snapshot of the build machine environment. Confirmed key names include local identity/path variables, SDK/JDK, Ruby/NVM/Gradle metadata, `SSH_AUTH_SOCK`, and `ANDROID_KEYSTORE_PASSWORD`. The APK therefore discloses build provenance and a credential-like keystore password value to every recipient. Actual values are not retained in this repository.

**Impact:** signing-key compromise becomes possible if the leaked password is valid and the corresponding keystore is obtained; build-host usernames and paths aid targeting.

**Remediation:** rotate the Android keystore password; review signing-key access, CI logs and historical artifacts; replace broad environment serialization with an explicit allowlist; fail builds when credential/path patterns occur in produced assets.

## GCX-02 — Request-signature canonicalization does not bind field names or structure

**Severity:** Medium; potentially high if backend schemas accept a colliding form  
**Evidence:** `index-DHlB7G7_.js:961-974`

The signature preimage recursively flattens values only, sorts object keys but omits the names, maps `null` to an empty string, flattens arrays and joins elements with `|`. Structurally distinct objects can therefore produce the same preimage. Backend schema validation may prevent practical substitution, so exploitability cannot be concluded from the APK alone.

**Remediation:** sign a deterministic typed serialization that includes field names, type tags, array boundaries and lengths; reject unknown fields; version and domain-separate the signing format.

## GCX-03 — User RSA private signing key is delivered to and held by JavaScript

**Severity:** High architectural exposure  
**Evidence:** `index-DHlB7G7_.js:921-958`, `:3601`

The `keys` Pinia store subscribes to `/users/{uid}/keys`, receives a base64 PKCS#8 private signing key, imports it into WebCrypto with `extractable=true`, and assigns the original encoded value to reactive state. Code executing in the WebView origin with sufficient access can therefore sign commands or exfiltrate key material.

**Remediation:** keep long-lived signing keys in Android Keystore or non-exportable hardware-backed storage; use non-extractable/short-lived scoped session keys; never retain raw PKCS#8 text in reactive state; enforce strict CSP and dependency integrity controls.

## GCX-04 — Sensitive signing preimage is written to the JavaScript console

**Severity:** Medium  
**Evidence:** `index-DHlB7G7_.js:974`

Before signing, the client calls `console.debug(preimage)`. The preimage contains flattened order, position or strategy values and nonce.

**Remediation:** remove payload logging from production; log only opaque request IDs and event types; strip debug logging at build time.

## GCX-05 — Firebase ID token is used as WebSocket subprotocol and duplicated in messages

**Severity:** Medium  
**Evidence:** `index-DHlB7G7_.js:1721-1725`, `:2106-2109`

The private socket passes the Firebase ID token as the WebSocket subprotocol and adds the token to each authenticated payload. TLS protects transit, but headers and message bodies have different logging paths. Duplication expands the credential-retention surface.

**Remediation:** use a short-lived one-time connection ticket or explicit auth message; do not echo a bearer token in every command; redact WebSocket headers and bodies at all logging layers.

## GCX-06 — Android backup rules broadly permit application data

**Severity:** Medium, device/backup-model dependent  
**Evidence:** decoded manifest and backup-rule XML

`allowBackup=true`. Cloud/device-transfer rules exclude AppsFlyer files only. No broad exclusion is visible for WebView storage, preferences, databases or wallet/session metadata.

**Remediation:** set `allowBackup=false` for a trading/wallet application or explicitly exclude WebView, IndexedDB, preferences, databases, cached deep links and key/session material; test cloud restore and device transfer.

## GCX-07 — Deep-link and AppsFlyer payloads are logged and cached

**Severity:** Low to Medium privacy risk  
**Evidence:** `index-DHlB7G7_.js:12703-12744`, `:12832-12849`

Incoming URLs, normalized routes and complete AppsFlyer UDL objects are logged. The UDL object is stored in `localStorage` under `dl.registerDeepLink`. Such links may contain referral, email-verification or password-reset parameters.

**Remediation:** redact query strings and OOB codes; store only minimal attribution fields with expiry; clear after consumption.

## GCX-08 — Manifest accepts `goodcryptox://`, sanitizer explicitly strips only `app.goodcrypto://`

**Severity:** Low hardening issue  
**Evidence:** manifest deep links; `index-DHlB7G7_.js:12735`

The exported activity accepts both custom schemes, while the normalizer explicitly handles `app.goodcrypto://` but not `goodcryptox://`. Matched-route checks limit arbitrary navigation, but the mismatch can cause inconsistent interpretation.

**Remediation:** use a strict URL parser; allowlist schemes/hosts/query keys; normalize both schemes explicitly.

## GCX-09 — FileProvider exposes the full external-path namespace when a URI grant is issued

**Severity:** Low hardening issue  
**Evidence:** decoded FileProvider paths XML

The non-exported FileProvider maps `<external-path path=".">` and enables URI grants. It is not directly world-readable, but a grant bug can address any externally visible file within storage permissions.

**Remediation:** replace `.` with a dedicated export directory.

## Informational observations

- Firebase API keys, ReCAPTCHA site keys, project IDs and WalletConnect/Reown client identifiers in a frontend bundle are not automatically server secrets; they require backend restrictions and rules.
- `MainActivity` is exported for launcher/deep links; FileProviders and Firebase messaging service are non-exported.
- Source maps were absent; JavaScript is minified but not encrypted or packed.
