# Expired quote and payment recovery deployment — 2026-10-26

PR #35 merged the recovery changes from source commit `bf3309b8f6bd09ed55fb645e473a8c7c4c5816b1`. PR verification [run 40335863520](https://github.com/Dimkox/liqvera/actions/runs/40335863520) and post-merge main verification [run 40348122753](https://github.com/Dimkox/liqvera/actions/runs/40348122753) passed. An independent read-only review found no replay or double-charge blocker and confirmed that `Check status` does not invoke the manual recovery endpoint.

## Rollout

Built and deployed only `gateway-live` and `web-live` from the exact source commit above:

| Service | Image | Result |
| --- | --- | --- |
| `gateway-live` | `sha256:9748f507b03aecbf58f5a527537f22fdf6753eb58c1e8b15008b095d0194df75` | Healthy |
| `web-live` | `sha256:045466a49d1a3c8dc6351e98c3e560422096ad261c943b4537844da9371749d2` | Healthy |

The previous gateway container remains stopped as `liqvera-live-gateway-live-1-before-bf3309b` for rollback. The other five service containers and images were not changed. The retained database, artifacts and payment state were not inspected or modified; no SQL migration, payment, wallet action, or BTC swap occurred.

## Published checks

- `https://liqvera.site/healthz`, `/readyz` and `/v1/capabilities` returned HTTP 200. Readiness reports `payment_ready=true` on `eip155:31611`.
- The public web bundle contains `Start new report` and `Recover report`.
- All seven Liqvera containers reported healthy after rollout.
- No new signed payment was made, and the incident report has not yet been recovered or accepted as delivered.

The user’s open tab was not accessed. Reload the page to load the new JavaScript; session storage remains in the browser. For the reported transaction, use **Recover report** with the full transaction hash and block `16382097` if the fields are not already populated. **Check status** polls the quote and does not call the recovery endpoint.
