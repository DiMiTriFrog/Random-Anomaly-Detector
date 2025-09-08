# rng-anomaly

Online anomaly detector for bit streams (e.g., /dev/urandom) using real-time statistical tests: RCT (runs), APT (Adaptive Proportion Test), SPRT (Sequential Probability Ratio Test), and optional monobit Z. Supports multiple processes, terminal TUI, and live plotting.

## Goal

- Detect bias or anomalous behavior (p ≠ 0.5) in bit streams.
- Alert in real time and record aggregate metrics.

## How it works

1. One or more processes read bits from a source:
   - Device: `--source /dev/urandom` (default)
   - Synthetic: `--synthetic` with `--p` and `--seed`
2. Each process applies RCT, APT, and SPRT; optionally monobit Z (`--ztest`).
3. The main process aggregates metrics, shows TUI/plot, and emits JSON events (heartbeats, ITER, STATS, ANOMALY, DONE, summary).

## Requirements

- Python 3.10+
- matplotlib (if you use `--mpl-plot`)

## Quick start

```bash
python3 -m rng_anomaly \
  --source /dev/urandom --processes 4 \
  --tui --quiet-json --no-limit
```

More options: see [CLI](cli.md).

## Structure

- Orchestration and CLI: `rng_anomaly/cli.py`
- Per-process logic: `rng_anomaly/worker.py`
- Bit sources: `rng_anomaly/sources.py`
- Terminal UI / pretty output: `rng_anomaly/tui.py`
- Statistical utilities: `rng_anomaly/utils.py`
- Online tests (conceptual): `rng_anomaly/tests_online.py` (classes `RCT`, `APT`, `SPRTDetector`, `ZMonobit`)

## Serve the docs

Without installing anything: open `docs/index.html` in your browser.

With Docsify (recommended):

```bash
npx docsify-cli@latest serve docs --open
```
