# Internal evidence capture service

Code status: IMPLEMENTED_UNVERIFIED. No capture, test suite, image, or live
request has been executed for this implementation.

Run `mee-evidence-capture-service` or
`python -m mee_public_capture.evidence_service`. Bind port is 8081 by default.
The service is internal only and must never be published by the edge proxy.

Configuration: `LIQVERA_CAPTURE_ROOT` (absolute, owned raw volume),
`LIQVERA_SOURCE_MODE` (`fixture`, default, or `live-public`),
`LIQVERA_CAPTURE_HOST` (default `0.0.0.0`), and `LIQVERA_CAPTURE_PORT` (8081).
Do not pass gateway database, RPC, payment, wallet, token, password, or secret
environment variables. The inherited environment-name guard remains active.

`POST /internal/v1/captures` accepts exactly `{"capture_id":"<canonical UUID>"}`.
It publishes a new sealed directory at `<capture-root>/<capture_id>` and returns
201 with `capture_id`, `source_mode`, and `identity_status`. Existing IDs return
409 and are never overwritten. Errors contain only a stable `code` and
`retryable` boolean. Health and storage readiness use `GET /healthz` and
`GET /readyz`.

Live mode permits exactly two POSTs to `https://api.hyperliquid.xyz/info`:
`{"type":"meta"}` followed by `{"type":"l2Book","coin":"BTC"}`.
Both share a 12-second hard POSIX timer and 2 MiB per-response bound; redirects,
ambient proxies, credentials, and content compression are refused. Exact raw
body bytes, request bodies, HTTP status, UTC timestamps, monotonic elapsed time,
and hashes are retained. Capture is synchronous so timeout cancellation cannot
leave a background request running. There are no retries or fixture fallback.

Live metadata has `identity_status=UNVERIFIED` and no approved mapping. A later
reviewed source artifact and implementation must close the missing economic
identity properties; an environment flag cannot authorize that transition.
Fixture timestamps and mappings are explicitly synthetic. The old Stage A
writer and demo paths retain their existing behavior.

Publication uses an exclusive per-ID lock, an owned staging directory, file and
directory fsync, hash rereads, then rename. On restart a hidden staging directory
or orphan lock is never a completed capture. Operators may inspect and move an
orphan aside only after confirming no capture is active. No automatic cleanup
of sealed input is performed; the gateway retention/recovery policy owns it.
Published directories use mode 0750 and files 0640. Capture, report, and gateway
containers must share an artifact-reader group or runtime UID; volumes remain
unpublished and each reader receives only its specified read-only mount.
