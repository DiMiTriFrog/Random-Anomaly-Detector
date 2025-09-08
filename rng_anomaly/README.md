# rng-anomaly

Online anomaly detector for /dev/(u)random bit streams using RCT, APT, SPRT, and monobit Z.

## Requirements

- Python 3.10+
- matplotlib for live plots (included by default).

## Installation

Editable (development):

```bash
pip install -e .
```

Regular install:

```bash
pip install .
```

## Usage

As a module:

```bash
python -m rng_anomaly \
  --source /dev/urandom --processes 12 \
  --tui --tui-scale 2 --tui-gap 4 --pct-decimals 8 \
  --quiet-json --no-limit \
  --mpl-plot --mpl-bucket-sec 30 --mpl-window-min 60 --mpl-interval 0.5
```

Installed script (entry point):

```bash
rng-anomaly \
  --source /dev/urandom --processes 12 \
  --tui --tui-scale 2 --tui-gap 4 --pct-decimals 8 \
  --quiet-json --no-limit \
  --mpl-plot --mpl-bucket-sec 30 --mpl-window-min 60 --mpl-interval 0.5
```

## Notes

- If matplotlib cannot be imported when `--mpl-plot` is enabled, plotting disables itself and a warning is printed.
- The TUI (`--tui`) uses the standard `curses` library.
