# Stage A n8n orchestration checkpoint

The importable workflow is `deploy/n8n/stage-a-orchestrator.workflow.json`.
It targets n8n `2.31.3`, is inactive by default, and has manual plus five-minute
schedule triggers.

## Authority boundary

n8n is a control-plane observer only. It calls the internal falsifier service
through its Docker DNS name and performs no market-data collection, WebSocket
processing, L2 reconstruction, persistence, execution, or account work. The
deterministic Go falsifier remains the sole evidence and decision authority.

The only permitted requests are these internal GET routes:

- `/healthz`
- `/readyz`
- `/v1/experiment/status`
- `/v1/ops/data-quality`
- `/v1/business/operator-revenue` (planned for Task 9)

The final Code node rejects the run unless both relevant envelopes declare
`execution_available:false` and the operator-revenue contract states
`contract_complete:true` with nonempty source, rate, turnover basis, payout
terms, collection mechanism, and infrastructure cost. This verifies that a
rate was supplied by the evidence authority; it neither selects nor computes a
fee rate itself. Until the owner resolves the revenue contract, this is
expected to fail closed.

## Validation

Run from the repository root:

```powershell
& .\scripts\validate-stage-a-n8n.ps1
```

The validator rejects an active workflow, credentials, forbidden node types or
execution-related strings, non-GET HTTP methods, external URLs, missing routes,
or an incomplete final gate. It is intentionally independent of Go and Docker.
