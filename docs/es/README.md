# rng-anomaly

Detector online de anomalías para flujos de bits (p.ej. /dev/urandom) mediante tests estadísticos en tiempo real: RCT (runs), APT (Adaptive Proportion Test), SPRT (Sequential Probability Ratio Test) y opcionalmente Z monobit. Soporta múltiples procesos, TUI en consola y gráfico en vivo.

## Objetivo

- Detectar sesgos o comportamientos anómalos (p ≠ 0.5) en streams de bits.
- Alertar en tiempo real y registrar métricas agregadas.

## Cómo funciona

1. Uno o más procesos leen bits de una fuente:
   - Dispositivo: `--source /dev/urandom` (por defecto)
   - Sintética: `--synthetic` con `--p` y `--seed`
2. Cada proceso aplica RCT, APT y SPRT; opcionalmente Z monobit (`--ztest`).
3. El proceso principal agrega métricas, muestra TUI/gráfico y emite eventos JSON (heartbeats, ITER, STATS, ANOMALY, DONE, summary).

## Requisitos

- Python 3.10+
- matplotlib (si usas `--mpl-plot`)

## Ejecución rápida

```bash
python3 -m rng_anomaly \
  --source /dev/urandom --processes 4 \
  --tui --quiet-json --no-limit
```

Más opciones: ver [CLI](cli.md).
