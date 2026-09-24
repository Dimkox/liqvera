# Lighter Experiments

`private_stream_legacy.py` is quarantined here because its authentication,
channel names, message schemas, quantity scaling, status mapping,
deduplication, and reconciliation behavior were not verified end to end.

Code under `experiments/` is not exported by the package and must not be used
for live order-state decisions. Reintroduce a private stream only with current
protocol fixtures, source-of-truth reconciliation, restart tests, and unknown
status handling.
