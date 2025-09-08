# Results and outputs

The main process emits JSON events. If you use `--quiet-json`, heartbeats and intermediate events are suppressed for a cleaner output.

## Heartbeat / STATS

Periodic aggregate summary across all processes.

```json
{
  "ts": "2024-01-01T00:00:00Z",
  "heartbeat": true,
  "elapsed_sec": 12.345,
  "procs_reporting": 12,
  "bits_total": 123456789,
  "ones_total": 61728395,
  "ones_ratio_global": 0.5,
  "ones_percent_global": 50.0,
  "window_len_total": 12288,
  "window_ones_total": 6148,
  "ones_ratio_window": 0.5003,
  "ones_percent_window": 50.03,
  "aggregate_bps": 8.7e6,
  "aggregate_bps_human": "8.70 Mbps"
}
```

## ITER

Per-iteration samples (if `--per-iter`, typical with `--tui` or `--stdout-live`).

```json
{
  "ts": "...",
  "event": "ITER",
  "proc": 3,
  "bits_processed": 1048576,
  "ones_total": 524300,
  "zeros_total": 524276,
  "ones_pct": 0.500002
}
```

## ANOMALY

An anomaly detected by any of the tests.

```json
{
  "ts": "...",
  "event": "ANOMALY",
  "proc": 7,
  "bits_processed": 1234567,
  "ones_total": 630000,
  "ones_pct": 0.51,
  "apt_window": 1024,
  "apt_len": 1024,
  "apt_ones": 560,
  "apt_pct": 0.547,
  "rct_run_len": 18,
  "sprt_up": 12.3,
  "sprt_dn": -11.8,
  "bps": 8700000.0
}
```

## DONE and summary

Emitted when each process finishes, and a final summary at the end.

```json
{
  "ts": "...",
  "event": "DONE",
  "proc": 2,
  "bits_processed": 999999,
  "ones_total": 500121,
  "bps": 9000000.0
}
```

```json
{
  "ts": "...",
  "summary": {
    "elapsed_sec": 3600.0,
    "processes": 12,
    "anomalies": 0,
    "total_bits": 3.1e10,
    "ones_ratio_global": 0.5,
    "aggregate_bps": 8.5e6,
    "aggregate_bps_human": "8.50 Mbps"
  }
}
```

## Interpretation (expected)

- Under normal conditions, the global bias should fluctuate around 0 (50% ones).
- Recurrent `ANOMALY` events indicate persistent bias or atypical behavior.
- Use the live plot (`--mpl-plot`) or TUI to observe bias over time.
