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

### TUI preview

The following command opens the terminal UI exactly like the screenshot (big ASCII 1/0 on screen and live percentages at the bottom), and updates continuously while reading bits:

```bash
python3 -m rng_anomaly \
  --source /dev/urandom --processes 12 \
  --tui --tui-scale 2 --tui-gap 4 --pct-decimals 8 \
  --quiet-json --no-limit \
  --mpl-plot --mpl-bucket-sec 30 --mpl-window-min 60 --mpl-interval 0.5
```
<img width="475" height="347" alt="Screenshot 2025-09-08 at 08 51 56" src="https://github.com/user-attachments/assets/c4ebff80-b698-4386-a22a-5e711b62503b" />
<img width="495" height="615" alt="Screenshot 2025-09-08 at 09 39 41" src="https://github.com/user-attachments/assets/74c5b2a8-5c87-4d8f-8790-3fb0730b1b1a" />



- The green “1” and cyan “0” ASCII digits reflect the TUI mode.
- The bottom line shows live percentages for 1s and 0s (e.g., ~50% each for unbiased sources).

## Notes

- If matplotlib cannot be imported when `--mpl-plot` is enabled, plotting disables itself and a warning is printed.
- The TUI (`--tui`) uses the standard `curses` library.
