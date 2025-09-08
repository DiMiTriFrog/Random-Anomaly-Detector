# CLI y argumentos

Ejecuta desde el directorio padre del paquete o tras instalarlo:

```bash
python3 -m rng_anomaly --help
# o si instalaste el entrypoint
rng-anomaly --help
```

## Ejemplo completo

```bash
python3 -m rng_anomaly \
  --source /dev/urandom --processes 12 \
  --tui --tui-scale 2 --tui-gap 4 --pct-decimals 8 \
  --quiet-json --no-limit \
  --mpl-plot --mpl-bucket-sec 30 --mpl-window-min 60 --mpl-interval 0.5
```

## Opciones principales

- **--source str**: Ruta del dispositivo (por defecto `/dev/urandom`). Ignorado si `--synthetic`.
- **--processes int**: Número de procesos en paralelo (por defecto `cpu_count()`).
- **--alpha float**: Nivel α para RCT/APT y SPRT (falsos positivos, por defecto `1e-6`).
- **--beta float**: Nivel β para SPRT (falsos negativos, por defecto `1e-2`).
- **--delta float**: Sesgo mínimo detectable para SPRT (p=0.5±δ, por defecto `1e-4`).
- **--apt-window int**: Tamaño de ventana para APT (por defecto `1024`).
- **--bits int**: Límite de bits por proceso (opcional).
- **--time float**: Límite de tiempo por proceso en segundos (por defecto `30`).
- **--chunk int**: Tamaño de lectura en bytes del dispositivo (por defecto `65536`).
- **--live-interval float**: Intervalo de reporte (seg, por defecto `0.5`).
- **--stop-on-anomaly**: Detiene todos los procesos al primer evento ANOMALY.

## Salida en vivo (TUI/stdout)

- **--tui**: UI en terminal (curses) con dígitos ASCII “1” y “0” y porcentajes.
- **--tui-refresh float**: Refresco mínimo de TUI (s, por defecto `0.1`).
- **--tui-scale int**: Escala del arte ASCII (por defecto `1`).
- **--tui-gap int**: Espacio entre “1” y “0” (por defecto `2`).
- **--pct-decimals int**: Decimales para porcentajes en TUI/pretty (por defecto `6`).
- **--stdout-live**: Línea en stdout con métricas en vivo.
- **--stdout-pretty**: Marco ASCII “bonito” con 1/0 y porcentajes.
- **--pretty-scale int**, **--pretty-gap int**: Parámetros de pretty.

## Control de límites

- **--no-limit**: Ignora `--bits` y `--time` para ejecución continua.
- Si no usas `--no-limit`, puedes fijar `--bits` y/o `--time`.

## Fuente sintética

- **--synthetic**: Usa Bernoulli i.i.d.
- **--p float**: Probabilidad P(1)=p (por defecto `0.5`).
- **--seed int**: Semilla base (opcional, derivación por proceso).

## Z monobit

- **--ztest**: Habilita test Z monobit online bilateral.
- **--z-alpha float**: Nivel α para Z (por defecto usa `--alpha`).
- **--z-min-bits int**: Mínimo de bits antes de evaluar Z (por defecto `10000`).

## Gráficos (matplotlib)

- **--mpl-plot**: Gráfico en vivo del sesgo (1s-0s).
- **--mpl-interval float**: Intervalo mínimo de refresco (s, por defecto `0.5`).
- **--mpl-bucket-sec float**: Agrega puntos cada N segundos (por defecto `30`).
- **--mpl-window-min float**: Ventana X deslizante en minutos (por defecto `60`).
- (Macro) **--macro-plot**, **--macro-window-hours**, **--macro-bucket-hours**, **--macro-save**.

## Notas

- Con `--tui` o `--stdout-live` se activa `--per-iter` automáticamente y, si `--iter-sample == 1`, se ajusta a `1000` para evitar exceso de eventos.
- Si `--mpl-plot` no puede importar matplotlib, se desactiva y muestra un aviso.
