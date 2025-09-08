# Resultados y salidas

El proceso principal emite eventos JSON. Si usas `--quiet-json`, se suprimen heartbeats y eventos intermedios para limpiar la salida.

## Heartbeat / STATS

Resumen periódico agregado de todos los procesos.

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

Muestras por iteración (si `--per-iter`, típico con `--tui` o `--stdout-live`).

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

Anomalía detectada por alguno de los tests.

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

## DONE y summary

Al finalizar cada proceso y al final de toda la ejecución.

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

## Interpretación (esperado)

- En condiciones normales, el sesgo global debe oscilar alrededor de 0 (50% 1s).
- Eventos `ANOMALY` recurrentes indican un sesgo persistente o comportamiento atípico.
- Revisa el gráfico en vivo (`--mpl-plot`) o la TUI para observar la evolución temporal del sesgo.
