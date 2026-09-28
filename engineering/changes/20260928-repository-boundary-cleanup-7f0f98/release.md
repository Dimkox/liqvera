# Release plan — Repository boundary cleanup

## Deployment

None. This repository-boundary change does not deploy product or tooling.

## Feature flags / staged rollout

Use coherent reversible commits: analysis/design, factory boundary, then Go
retirement. Do not publish or merge as part of this route without separate
authority.

## Metrics and alerts

Record tracked file/byte reduction, zero active Go paths, zero dangling
inventory/conformance references, and unchanged protected product hashes.

## Go/no-go criteria

Go only when the final design choice is approved, product verification has not
lost coverage, all selected reviews pass on the same fingerprint, and no
product status is promoted. Otherwise revert the affected cleanup unit.
