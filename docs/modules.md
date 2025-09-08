# Modules

Overview of the main package modules.

## `rng_anomaly/cli.py`

- Defines the CLI with `argparse` and orchestrates execution.
- Launches N `worker` processes, aggregates metrics, emits JSON, and handles TUI/plot.

## `rng_anomaly/worker.py`

- Per-process processing loop.
- Reads bits from the source (device or synthetic) and applies tests:
  - `RCT`: Run Count Test (detect long runs)
  - `APT`: Adaptive Proportion Test (ones proportion in a window)
  - `SPRTDetector`: Sequential Probability Ratio Test (p≈0.5±δ)
  - Optional `ZMonobit` (bilateral Z statistic)
- Reports `ITER`, `STATS`, `ANOMALY`, `DONE` events to the main process.

## `rng_anomaly/sources.py`

- `bit_stream_from_device(path, chunk_size)`: generates LSB-first bits from a byte device.
- `bit_stream_synthetic(p, seed)`: Bernoulli i.i.d. with P(1)=p.
- `derive_process_seed(base_seed, proc_id)`: per-process seed for independence.

## `rng_anomaly/tui.py`

- `LiveUI`: curses UI with scalable ASCII digits, colors, and percentages.
- `stdout_live_update`: one-line or “pretty” framed output.

## `rng_anomaly/utils.py`

- `inv_norm_cdf(p)`: rational approximation of the inverse normal CDF.
- `apt_bounds_binomial(n, alpha)`: approximate bounds for APT (normal + continuity).
- `rct_cutoff_from_alpha(alpha)`: minimum run threshold for RCT.
- `human_bps(bps)`: human-readable bits/s.
- `iso_now()`: ISO timestamp.

## `rng_anomaly/tests_online.py`

- Defines test classes: `RCT`, `APT`, `SPRTDetector`, `ZMonobit`.
- Each `update(bit)` returns `None` or a dict describing an anomaly event.
