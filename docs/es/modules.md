# Módulos

Descripción de los principales módulos del paquete.

## `rng_anomaly/cli.py`

- Define el CLI con `argparse` y orquesta la ejecución.
- Lanza N procesos `worker`, agrega métricas, emite JSON y maneja TUI y gráfico.

## `rng_anomaly/worker.py`

- Bucle de procesamiento por proceso.
- Lee bits de la fuente (dispositivo o sintética) y aplica tests:
  - `RCT`: Run Count Test (detección de rachas largas)
  - `APT`: Adaptive Proportion Test (proporción de 1s en ventana)
  - `SPRTDetector`: Sequential Probability Ratio Test (p≈0.5±δ)
  - Opcional `ZMonobit` (estadístico Z bilateral)
- Informa eventos `ITER`, `STATS`, `ANOMALY`, `DONE` al proceso principal.

## `rng_anomaly/sources.py`

- `bit_stream_from_device(path, chunk_size)`: genera bits LSB-first desde un dispositivo de bytes.
- `bit_stream_synthetic(p, seed)`: Bernoulli i.i.d. con P(1)=p.
- `derive_process_seed(base_seed, proc_id)`: semilla por proceso para independencia.

## `rng_anomaly/tui.py`

- `LiveUI`: UI curses con dígitos ASCII escalables, colores y porcentajes.
- `stdout_live_update`: salida en una línea o marco “pretty”.

## `rng_anomaly/utils.py`

- `inv_norm_cdf(p)`: aproximación racional de la CDF inversa normal.
- `apt_bounds_binomial(n, alpha)`: cotas aproximadas para APT (normal + continuidad).
- `rct_cutoff_from_alpha(alpha)`: umbral mínimo de racha para RCT.
- `human_bps(bps)`: formato humano de bits/s.
- `iso_now()`: timestamp ISO.

## `rng_anomaly/tests_online.py`

- Define las clases de test: `RCT`, `APT`, `SPRTDetector`, `ZMonobit`.
- Cada `update(bit)` devuelve `None` o un dict con campos del evento de anomalía.
