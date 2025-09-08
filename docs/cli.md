# CLI and arguments

Run from the package's parent directory or after installing it:

```bash
python3 -m rng_anomaly --help
# or if you installed the entrypoint
rng-anomaly --help
```

## Full example

```bash
python3 -m rng_anomaly \
  --source /dev/urandom --processes 12 \
  --tui --tui-scale 2 --tui-gap 4 --pct-decimals 8 \
  --quiet-json --no-limit \
  --mpl-plot --mpl-bucket-sec 30 --mpl-window-min 60 --mpl-interval 0.5
```

## Main options

- **--source str**: Device path (default `/dev/urandom`). Ignored if `--synthetic`.
- **--processes int**: Number of parallel processes (default `cpu_count()`).
- **--alpha float**: Alpha level for RCT/APT and SPRT (false positives, default `1e-6`).
- **--beta float**: Beta level for SPRT (false negatives, default `1e-2`).
- **--delta float**: Minimum detectable bias for SPRT (p=0.5±δ, default `1e-4`).
- **--apt-window int**: Window size for APT (default `1024`).
- **--bits int**: Per-process bit limit (optional).
- **--time float**: Per-process time limit in seconds (default `30`).
- **--chunk int**: Device read chunk size in bytes (default `65536`).
- **--live-interval float**: Report interval (s, default `0.5`).
- **--stop-on-anomaly**: Stop all processes at the first ANOMALY event.

## Live output (TUI/stdout)

- **--tui**: Terminal UI (curses) with ASCII “1” and “0” and percentages.
- **--tui-refresh float**: Minimum TUI refresh (s, default `0.1`).
- **--tui-scale int**: ASCII art scale (default `1`).
- **--tui-gap int**: Space between “1” and “0” (default `2`).
- **--pct-decimals int**: Decimals for percentages in TUI/pretty (default `6`).
- **--stdout-live**: Single-line stdout with live metrics.
- **--stdout-pretty**: Pretty ASCII frame on stdout with 1/0 and percentages.
- **--pretty-scale int**, **--pretty-gap int**: Pretty parameters.

## Limits control

- **--no-limit**: Ignore `--bits` and `--time` for continuous execution.
- If not using `--no-limit`, you can set `--bits` and/or `--time`.

## Synthetic source

- **--synthetic**: Use a Bernoulli i.i.d. source.
- **--p float**: Probability P(1)=p (default `0.5`).
- **--seed int**: Base seed (optional, per-process derivation).

## Monobit Z

- **--ztest**: Enable bilateral online monobit Z-test.
- **--z-alpha float**: Alpha for Z (defaults to `--alpha`).
- **--z-min-bits int**: Minimum bits before evaluating Z (default `10000`).

## Plotting (matplotlib)

- **--mpl-plot**: Live bias plot (1s-0s).
- **--mpl-interval float**: Minimum refresh interval (s, default `0.5`).
- **--mpl-bucket-sec float**: Aggregate points every N seconds (default `30`).
- **--mpl-window-min float**: Sliding X window in minutes (default `60`).
- (Macro) **--macro-plot**, **--macro-window-hours**, **--macro-bucket-hours**, **--macro-save**.

## Notes

- With `--tui` or `--stdout-live`, `--per-iter` is enabled automatically and, if `--iter-sample == 1`, it is set to `1000` to avoid excessive events.
- If `--mpl-plot` cannot import matplotlib, it disables itself and shows a warning.
