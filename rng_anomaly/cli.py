import os
import sys
import json
import time
import argparse
import multiprocessing as mp

from .utils import iso_now, human_bps
from .worker import worker
from .tui import LiveUI, stdout_live_update


def run():
    ap = argparse.ArgumentParser(
        description="Online anomaly detector for /dev/(u)random (RCT, APT, SPRT)."
    )
    ap.add_argument("--source", default="/dev/urandom",
                    help="Device path (default: /dev/urandom). Ignored if --synthetic.")
    ap.add_argument("--processes", type=int, default=max(1, os.cpu_count() or 1),
                    help="Number of parallel processes.")
    ap.add_argument("--alpha", type=float, default=1e-6,
                    help="Alpha level for RCT/APT and SPRT (false positive rate).")
    ap.add_argument("--beta", type=float, default=1e-2,
                    help="Beta level for SPRT (false negative rate).")
    ap.add_argument("--delta", type=float, default=1e-4,
                    help="Minimum bias to detect with SPRT (p=0.5±δ).")
    ap.add_argument("--apt-window", type=int, default=1024,
                    help="Window size for APT.")
    ap.add_argument("--bits", type=int, default=None,
                    help="Bit limit per process (optional).")
    ap.add_argument("--time", type=float, default=30.0,
                    help="Time limit per process in seconds (default 30s).")
    ap.add_argument("--chunk", type=int, default=1 << 16,
                    help="Read chunk size in bytes (default 65536).")
    ap.add_argument("--live-interval", type=float, default=0.5,
                    help="Live report interval in seconds.")
    ap.add_argument("--stop-on-anomaly", action="store_true", default=False,
                    help="Stop all processes at the first anomaly event.")
    ap.add_argument("--per-iter", action="store_true", default=False,
                    help="Print 1s/0s percentage every iteration (high volume).")
    ap.add_argument("--iter-sample", type=int, default=1,
                    help="Sample 1 out of N iterations when reporting per-iter.")
    ap.add_argument("--tui", action="store_true", default=False,
                    help="Terminal UI (curses): shows 1/0 and live percentages.")
    ap.add_argument("--tui-refresh", type=float, default=0.1,
                    help="Minimum TUI refresh interval in seconds.")
    ap.add_argument("--tui-scale", type=int, default=1,
                    help="ASCII art scale factor for TUI (default 1).")
    ap.add_argument("--tui-gap", type=int, default=2,
                    help="Spaces between '1' and '0' in TUI (default 2).")
    ap.add_argument("--pct-decimals", type=int, default=6,
                    help="Number of decimals for percentages in TUI/pretty (default 6).")
    ap.add_argument("--stdout-live", action="store_true", default=False,
                    help="Update one line in stdout with %1s/%0s each iteration.")
    ap.add_argument("--quiet-json", action="store_true", default=False,
                    help="Suppress heartbeats/STATS/ITER in JSON for clean output.")
    ap.add_argument("--no-limit", action="store_true", default=False,
                    help="Ignore time and bit limits; run indefinitely.")
    ap.add_argument("--stdout-pretty", action="store_true", default=False,
                    help="Pretty stdout with big 1/0 and percentages (ANSI).")
    ap.add_argument("--pretty-scale", type=int, default=1,
                    help="ASCII art scale factor for pretty (default 1).")
    ap.add_argument("--pretty-gap", type=int, default=3,
                    help="Spaces between '1' and '0' in pretty (default 3).")
    ap.add_argument("--synthetic", action="store_true", default=False,
                    help="Use synthetic Bernoulli (i.i.d.) source instead of device.")
    ap.add_argument("--p", type=float, default=0.5,
                    help="Probability P(1)=p for synthetic source (default 0.5).")
    ap.add_argument("--seed", type=int, default=None,
                    help="Base seed for synthetic source (optional).")
    ap.add_argument("--ztest", action="store_true", default=False,
                    help="Enable bilateral online monobit Z-test.")
    ap.add_argument("--z-alpha", type=float, default=None,
                    help="Bilateral α for monobit Z (defaults to --alpha).")
    ap.add_argument("--z-min-bits", type=int, default=10000,
                    help="Minimum bits before evaluating Z (default 10000).")
    ap.add_argument("--mpl-plot", action="store_true", default=False,
                    help="Live matplotlib plot of bias (1s-0s).")
    ap.add_argument("--mpl-interval", type=float, default=0.5,
                    help="Minimum refresh interval for the plot in seconds.")
    ap.add_argument("--mpl-save", type=str, default=None,
                    help="Path to save plot PNG at the end.")
    ap.add_argument("--mpl-bucket-sec", type=float, default=30.0,
                    help="Aggregate and plot points every N seconds (default 30s).")
    ap.add_argument("--mpl-x-minutes", action="store_true", default=False,
                    help="X axis in minutes (0..RANGE) instead of seconds.")
    ap.add_argument("--mpl-x-range-min", type=float, default=60.0,
                    help="X range in minutes when --mpl-x-minutes is active (default 60).")
    ap.add_argument("--mpl-window-min", type=float, default=60.0,
                    help="Visible sliding window on X axis (minutes, default 60).")
    ap.add_argument("--macro-plot", action="store_true", default=False,
                    help="Macro plot with hourly aggregation of bias.")
    ap.add_argument("--macro-window-hours", type=float, default=24.0,
                    help="Visible window in hours for the macro plot (default 24h).")
    ap.add_argument("--macro-bucket-hours", type=float, default=1.0,
                    help="Aggregate points every N hours (default 1h).")
    ap.add_argument("--macro-save", type=str, default=None,
                    help="Path to save macro plot PNG at the end.")
    args = ap.parse_args()

    if args.tui and not args.per_iter:
        args.per_iter = True
        if args.iter_sample == 1:
            args.iter_sample = 1000
    if args.stdout_live and not args.per_iter:
        args.per_iter = True
        if args.iter_sample == 1:
            args.iter_sample = 1000
    if args.no_limit:
        args.bits = None
        args.time = None

    if not args.synthetic:
        if not os.path.exists(args.source):
            print(f"Error: path does not exist {args.source}", file=sys.stderr)
            sys.exit(1)

    if not args.quiet_json:
        print(json.dumps({
            "ts": iso_now(),
            "config": {
                "source": args.source,
                "processes": args.processes,
                "alpha": args.alpha,
                "beta": args.beta,
                "delta": args.delta,
                "apt_window": args.apt_window,
                "bits_limit": args.bits,
                "time_limit_sec": args.time,
                "chunk_bytes": args.chunk,
                "live_interval_sec": args.live_interval,
                "stop_on_anomaly": args.stop_on_anomaly,
                "per_iter": args.per_iter,
                "iter_sample": args.iter_sample,
                "tui": args.tui,
                "stdout_live": args.stdout_live,
                "quiet_json": args.quiet_json,
                "no_limit": args.no_limit,
                "synthetic": args.synthetic,
                "p": args.p,
                "seed": args.seed,
                "ztest": args.ztest,
                "z_alpha": args.z_alpha,
                "z_min_bits": args.z_min_bits,
                "macro_plot": args.macro_plot,
                "macro_window_hours": args.macro_window_hours,
                "macro_bucket_hours": args.macro_bucket_hours,
                "macro_save": args.macro_save,
            },
        }, ensure_ascii=False))

    q = mp.Queue()
    procs = []
    for i in range(args.processes):
        p = mp.Process(
            target=worker,
            args=(
                i,
                args.source,
                args.alpha,
                args.beta,
                args.delta,
                args.apt_window,
                q,
                args.bits,
                args.time,
                args.chunk,
                args.live_interval,
                args.stop_on_anomaly,
                args.per_iter,
                args.iter_sample,
                args.synthetic,
                args.p,
                args.seed,
                args.ztest,
                args.z_alpha,
                args.z_min_bits,
            ),
            daemon=True,
        )
        p.start()
        procs.append(p)

    active = len(procs)
    t_start = time.perf_counter()
    last_hb = t_start
    anomalies = 0
    totals_bits = 0
    per_proc_bps = {}
    per_proc_bits = {}
    per_proc_ones = {}
    per_proc_win_ones = {}
    per_proc_win_len = {}

    ui = LiveUI(args.tui, args.tui_refresh, pct_decimals=args.pct_decimals, scale=args.tui_scale, gap=args.tui_gap)
    ui.start()
    pretty_state = {"printed": False, "lines": 0}

    # Matplotlib state
    mpl = {"enabled": False, "ax": None, "xs": [], "ys": [], "last_draw": 0.0, "line": None}
    if args.mpl_plot:
        try:
            import matplotlib.pyplot as plt  # type: ignore
            import matplotlib.ticker as mticker  # type: ignore
            plt.ion()
            fig, ax = plt.subplots()
            ax.set_title("Bias per window — 100*(1s-0s) = 200*ones% - 100")
            ax.set_xlabel("Time (min)")
            ax.set_ylabel("Bias (percentage points)")
            ax.grid(True, alpha=0.3)
            line, = ax.plot([], [], "-", lw=2.0)
            ax.xaxis.set_major_formatter(mticker.FormatStrFormatter('%.1f'))
            mpl.update({"enabled": True, "ax": ax, "line": line})
        except Exception as e:
            if not args.quiet_json:
                print(json.dumps({"ts": iso_now(), "event": "WARN", "mpl": "disabled", "error": repr(e)}, ensure_ascii=False))

    def mpl_update(now_t: float, ones_ratio: float | None):
        if not mpl["enabled"] or ones_ratio is None:
            return
        bias_pp = (2.0 * ones_ratio - 1.0) * 100.0
        x_val = now_t / 60.0
        mpl["xs"].append(x_val)
        mpl["ys"].append(bias_pp)
        if len(mpl["xs"]) > 10000:
            mpl["xs"] = mpl["xs"][-5000:]
            mpl["ys"] = mpl["ys"][-5000:]
        now = time.perf_counter()
        if (now - mpl["last_draw"]) >= args.mpl_interval:
            mpl["last_draw"] = now
            try:
                ax = mpl["ax"]
                xs = mpl["xs"]
                ys = mpl["ys"]
                win_min = max(0.5, float(args.mpl_window_min))
                x_max = xs[-1] if xs else 0.0
                x_min = max(0.0, x_max - win_min)
                ax.set_xlim(x_min, x_max if x_max > x_min else x_min + win_min)
                line = mpl["line"]
                line.set_data(xs, ys)
                ax.relim()
                ax.autoscale_view(scalex=False, scaley=True)
                ax.axhline(0.0, color="#888", lw=0.8)
                import matplotlib.pyplot as plt  # type: ignore
                plt.draw()
                plt.pause(0.001)
            except Exception:
                pass

    macro = {"enabled": False, "ax": None, "xs": [], "ys": [], "last_draw": 0.0, "line": None}
    if args.macro_plot:
        try:
            import matplotlib.pyplot as plt  # type: ignore
            import matplotlib.ticker as mticker  # type: ignore
            plt.ion()
            fig2, ax2 = plt.subplots()
            ax2.set_title("Hourly bias — 100*(1s-0s)")
            ax2.set_xlabel("Time (hours)")
            ax2.set_ylabel("Bias (percentage points)")
            ax2.grid(True, alpha=0.3)
            line2, = ax2.plot([], [], "-", lw=2.0)
            ax2.xaxis.set_major_formatter(mticker.FormatStrFormatter('%.1f'))
            macro.update({"enabled": True, "ax": ax2, "line": line2})
        except Exception as e:
            if not args.quiet_json:
                print(json.dumps({"ts": iso_now(), "event": "WARN", "macro": "disabled", "error": repr(e)}, ensure_ascii=False))

    def macro_update(now_t: float, ones_ratio: float | None):
        if not macro["enabled"] or ones_ratio is None:
            return
        bias_pp = (2.0 * ones_ratio - 1.0) * 100.0
        x_val = now_t / 3600.0
        macro["xs"].append(x_val)
        macro["ys"].append(bias_pp)
        if len(macro["xs"]) > 20000:
            macro["xs"] = macro["xs"][-10000:]
            macro["ys"] = macro["ys"][-10000:]
        now = time.perf_counter()
        if (now - macro["last_draw"]) >= max(0.5, float(args.mpl_interval)):
            macro["last_draw"] = now
            try:
                ax2 = macro["ax"]
                xs2 = macro["xs"]
                ys2 = macro["ys"]
                win_h = max(1.0, float(args.macro_window_hours))
                x_max = xs2[-1] if xs2 else 0.0
                x_min = max(0.0, x_max - win_h)
                ax2.set_xlim(x_min, x_max if x_max > x_min else x_min + win_h)
                line2 = macro["line"]
                line2.set_data(xs2, ys2)
                ax2.relim()
                ax2.autoscale_view(scalex=False, scaley=True)
                ax2.axhline(0.0, color="#888", lw=0.8)
                import matplotlib.pyplot as plt  # type: ignore
                plt.draw()
                plt.pause(0.001)
            except Exception:
                pass

    bucket_state = {"t_ref": None, "t_bucket_start": None, "bits_at_start": 0, "ones_at_start": 0}
    macro_bucket_state = {"t_ref": None, "t_bucket_start": None, "bits_at_start": 0, "ones_at_start": 0}

    def init_buckets(now_perf: float):
        bucket_state["t_ref"] = now_perf
        bucket_state["t_bucket_start"] = now_perf
        bucket_state["bits_at_start"] = 0
        bucket_state["ones_at_start"] = 0

    def init_macro_buckets(now_perf: float):
        macro_bucket_state["t_ref"] = now_perf
        macro_bucket_state["t_bucket_start"] = now_perf
        macro_bucket_state["bits_at_start"] = 0
        macro_bucket_state["ones_at_start"] = 0

    def maybe_emit_buckets(now_perf: float, bits_total: int, ones_total: int):
        if bucket_state["t_ref"] is None:
            init_buckets(now_perf)
        out_points = []
        bucket_len = max(0.1, float(args.mpl_bucket_sec))
        while (now_perf - bucket_state["t_bucket_start"]) >= bucket_len:
            delta_bits = bits_total - bucket_state["bits_at_start"]
            delta_ones = ones_total - bucket_state["ones_at_start"]
            if delta_bits > 0:
                ratio = delta_ones / delta_bits
                t_rel = (bucket_state["t_bucket_start"] + bucket_len) - bucket_state["t_ref"]
                out_points.append((t_rel, ratio))
            bucket_state["t_bucket_start"] += bucket_len
            bucket_state["bits_at_start"] = bits_total
            bucket_state["ones_at_start"] = ones_total
        return out_points

    def maybe_emit_macro_buckets(now_perf: float, bits_total: int, ones_total: int):
        if macro_bucket_state["t_ref"] is None:
            init_macro_buckets(now_perf)
        out_points = []
        bucket_len = max(1800.0, float(args.macro_bucket_hours) * 3600.0)
        while (now_perf - macro_bucket_state["t_bucket_start"]) >= bucket_len:
            delta_bits = bits_total - macro_bucket_state["bits_at_start"]
            delta_ones = ones_total - macro_bucket_state["ones_at_start"]
            if delta_bits > 0:
                ratio = delta_ones / delta_bits
                t_rel = (macro_bucket_state["t_bucket_start"] + bucket_len) - macro_bucket_state["t_ref"]
                out_points.append((t_rel, ratio))
            macro_bucket_state["t_bucket_start"] += bucket_len
            macro_bucket_state["bits_at_start"] = bits_total
            macro_bucket_state["ones_at_start"] = ones_total
        return out_points

    try:
        while active > 0:
            try:
                tag, payload = q.get(timeout=0.5)
            except Exception:
                elapsed = time.perf_counter() - t_start
                agg_bps = sum(per_proc_bps.values()) if per_proc_bps else 0.0
                bits_total = sum(per_proc_bits.values()) if per_proc_bits else 0
                ones_total = sum(per_proc_ones.values()) if per_proc_ones else 0
                ones_ratio = (ones_total / bits_total) if bits_total > 0 else None
                ones_percent = (ones_ratio * 100.0) if ones_ratio is not None else None
                window_len_total = sum(per_proc_win_len.values()) if per_proc_win_len else 0
                window_ones_total = sum(per_proc_win_ones.values()) if per_proc_win_ones else 0
                window_ratio = (window_ones_total / window_len_total) if window_len_total > 0 else None
                window_percent = (window_ratio * 100.0) if window_ratio is not None else None
                if not args.quiet_json:
                    print(json.dumps({
                        "ts": iso_now(),
                        "heartbeat": True,
                        "elapsed_sec": round(elapsed, 3),
                        "procs_reporting": len(per_proc_bits),
                        "bits_total": bits_total,
                        "ones_total": ones_total,
                        "ones_ratio_global": ones_ratio,
                        "ones_percent_global": ones_percent,
                        "window_len_total": window_len_total,
                        "window_ones_total": window_ones_total,
                        "ones_ratio_window": window_ratio,
                        "ones_percent_window": window_percent,
                        "aggregate_bps": agg_bps,
                        "aggregate_bps_human": human_bps(agg_bps),
                    }, ensure_ascii=False))
                last_hb = time.perf_counter()
                zeros_ratio = (1 - ones_ratio) if ones_ratio is not None else None
                ui.update(ones_ratio, zeros_ratio)
                if bits_total > 0:
                    pts = maybe_emit_buckets(time.perf_counter(), bits_total, ones_total)
                    for t_rel, r in pts:
                        mpl_update(t_rel, r)
                    if args.macro_plot:
                        pts2 = maybe_emit_macro_buckets(time.perf_counter(), bits_total, ones_total)
                        for t_rel, r in pts2:
                            macro_update(t_rel, r)
                continue

            if tag == "ANOMALY":
                anomalies += 1
                totals_bits += payload.get("bits_processed", 0)
                per_proc_bps[payload["proc"]] = payload.get("bps", 0.0)
                per_proc_bits[payload["proc"]] = payload.get("bits_processed", 0)
                per_proc_ones[payload["proc"]] = payload.get("ones_total", 0)
                per_proc_win_ones[payload["proc"]] = payload.get("apt_ones", 0)
                per_proc_win_len[payload["proc"]] = payload.get("apt_len", 0)
                if not args.quiet_json:
                    print(json.dumps({"ts": iso_now(), "event": "ANOMALY", **payload}, ensure_ascii=False))
                if args.stop_on_anomaly:
                    for p in procs:
                        if p.is_alive():
                            p.terminate()
                    break

            elif tag == "STATS":
                pid = payload["proc"]
                per_proc_bps[pid] = payload.get("bps", 0.0)
                per_proc_bits[pid] = payload.get("bits_processed", 0)
                per_proc_ones[pid] = payload.get("ones_total", 0)
                per_proc_win_ones[pid] = payload.get("apt_ones", 0)
                per_proc_win_len[pid] = payload.get("apt_len", 0)
                now = time.perfCounter()
                if (now - last_hb) >= args.live_interval:
                    elapsed = now - t_start
                    agg_bps = sum(per_proc_bps.values()) if per_proc_bps else 0.0
                    bits_total = sum(per_proc_bits.values()) if per_proc_bits else 0
                    ones_total = sum(per_proc_ones.values()) if per_proc_ones else 0
                    ones_ratio = (ones_total / bits_total) if bits_total > 0 else None
                    ones_percent = (ones_ratio * 100.0) if ones_ratio is not None else None
                    window_len_total = sum(per_proc_win_len.values()) if per_proc_win_len else 0
                    window_ones_total = sum(per_proc_win_ones.values()) if per_proc_win_ones else 0
                    window_ratio = (window_ones_total / window_len_total) if window_len_total > 0 else None
                    window_percent = (window_ratio * 100.0) if window_ratio is not None else None
                    if not args.quiet_json:
                        print(json.dumps({
                            "ts": iso_now(),
                            "heartbeat": True,
                            "elapsed_sec": round(elapsed, 3),
                            "procs_reporting": len(per_proc_bits),
                            "bits_total": bits_total,
                            "ones_total": ones_total,
                            "ones_ratio_global": ones_ratio,
                            "ones_percent_global": ones_percent,
                            "window_len_total": window_len_total,
                            "window_ones_total": window_ones_total,
                            "ones_ratio_window": window_ratio,
                            "ones_percent_window": window_percent,
                            "aggregate_bps": agg_bps,
                            "aggregate_bps_human": human_bps(agg_bps),
                        }, ensure_ascii=False))
                    last_hb = now
                    zeros_ratio = (1 - ones_ratio) if ones_ratio is not None else None
                    ui.update(ones_ratio, zeros_ratio)
                    if bits_total > 0 and args.macro_plot:
                        pts2 = maybe_emit_macro_buckets(time.perf_counter(), bits_total, ones_total)
                        for t_rel, r in pts2:
                            macro_update(t_rel, r)

            elif tag == "ITER":
                if not args.quiet_json:
                    print(json.dumps({"ts": iso_now(), "event": "ITER", **payload}, ensure_ascii=False))
                pid = payload["proc"]
                per_proc_bits[pid] = payload.get("bits_processed", per_proc_bits.get(pid, 0))
                per_proc_ones[pid] = payload.get("ones_total", per_proc_ones.get(pid, 0))
                bits_total = sum(per_proc_bits.values()) if per_proc_bits else 0
                ones_total = sum(per_proc_ones.values()) if per_proc_ones else 0
                ones_ratio = (ones_total / bits_total) if bits_total > 0 else None
                zeros_ratio = (1 - ones_ratio) if ones_ratio is not None else None
                ui.update(ones_ratio, zeros_ratio)
                if bits_total > 0:
                    pts = maybe_emit_buckets(time.perf_counter(), bits_total, ones_total)
                    for t_rel, r in pts:
                        mpl_update(t_rel, r)
                ui.update(ones_ratio, zeros_ratio)
                if bits_total > 0:
                    pts = maybe_emit_buckets(time.perf_counter(), bits_total, ones_total)
                    for t_rel, r in pts:
                        mpl_update(t_rel, r)
                if bits_total > 0 and args.macro_plot:
                    pts2 = maybe_emit_macro_buckets(time.perf_counter(), bits_total, ones_total)
                    for t_rel, r in pts2:
                        macro_update(t_rel, r)
                if args.stdout_live and ones_ratio is not None:
                    stdout_live_update(
                        getattr(args, "stdout_pretty", False),
                        bits_total,
                        ones_ratio,
                        pretty_state,
                        getattr(args, "pretty_scale", 1),
                        getattr(args, "pretty_gap", 3),
                        getattr(args, "pct_decimals", 6),
                    )

            elif tag == "DONE":
                totals_bits += payload.get("bits_processed", 0)
                per_proc_bps[payload["proc"]] = payload.get("bps", 0.0)
                per_proc_bits[payload["proc"]] = payload.get("bits_processed", 0)
                per_proc_ones[payload["proc"]] = payload.get("ones_total", 0)
                per_proc_win_ones[payload["proc"]] = payload.get("apt_ones", 0)
                per_proc_win_len[payload["proc"]] = payload.get("apt_len", 0)
                if not args.quiet_json:
                    print(json.dumps({"ts": iso_now(), "event": "DONE", **payload}, ensure_ascii=False))
                active -= 1

            elif tag == "ERROR":
                if not args.quiet_json:
                    print(json.dumps({"ts": iso_now(), "event": "ERROR", **payload}, ensure_ascii=False))
                active -= 1

        elapsed = time.perf_counter() - t_start
        agg_bps = sum(per_proc_bps.values()) if per_proc_bps else 0.0
        bits_total = sum(per_proc_bits.values()) if per_proc_bits else 0
        ones_total = sum(per_proc_ones.values()) if per_proc_ones else 0
        ones_ratio = (ones_total / bits_total) if bits_total > 0 else None
        ones_percent = (ones_ratio * 100.0) if ones_ratio is not None else None
        window_len_total = sum(per_proc_win_len.values()) if per_proc_win_len else 0
        window_ones_total = sum(per_proc_win_ones.values()) if per_proc_win_ones else 0
        window_ratio = (window_ones_total / window_len_total) if window_len_total > 0 else None
        window_percent = (window_ratio * 100.0) if window_ratio is not None else None
        if not args.quiet_json:
            print(json.dumps({
                "ts": iso_now(),
                "summary": {
                    "elapsed_sec": round(elapsed, 3),
                    "processes": args.processes,
                    "anomalies": anomalies,
                    "total_bits": bits_total,
                    "ones_total": ones_total,
                    "ones_ratio_global": ones_ratio,
                    "ones_percent_global": ones_percent,
                    "window_len_total": window_len_total,
                    "window_ones_total": window_ones_total,
                    "ones_ratio_window": window_ratio,
                    "ones_percent_window": window_percent,
                    "aggregate_bps": agg_bps,
                    "aggregate_bps_human": human_bps(agg_bps),
                },
            }, ensure_ascii=False))
        if args.stdout_live and not args.quiet_json:
            sys.stdout.write("\n")
    finally:
        ui.stop()
        for p in procs:
            if p.is_alive():
                p.terminate()
        for p in procs:
            p.join(timeout=1.0)


def main():
    run()


