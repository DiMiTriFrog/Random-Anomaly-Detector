import time
import math
import multiprocessing as mp

from .tests_online import RCT, APT, SPRTDetector, ZMonobit
from .sources import bit_stream_from_device, bit_stream_synthetic, derive_process_seed


def worker(
    proc_id: int,
    source_path: str,
    alpha: float,
    beta: float,
    delta: float,
    apt_window: int,
    queue_out: mp.Queue,
    max_bits: int | None = None,
    max_seconds: float | None = None,
    chunk_size: int = 1 << 16,
    report_interval: float = 0.5,
    stop_on_anomaly: bool = True,
    per_iter: bool = False,
    iter_sample: int = 1,
    use_synthetic: bool = False,
    synthetic_p: float = 0.5,
    synthetic_seed: int | None = None,
    ztest_enabled: bool = False,
    z_alpha: float | None = None,
    z_min_bits: int = 10000,
):
    """
    Worker loop that reads bits from a source and applies RCT, APT, SPRT,
    and optionally Z-test. Reports the first anomaly found or termination.
    """
    rct = RCT(alpha=alpha)
    apt = APT(window=apt_window, alpha=alpha)
    sprt = SPRTDetector(delta=delta, alpha=alpha, beta=beta)
    tests = [rct, apt, sprt]
    if ztest_enabled:
        z_alpha_eff = z_alpha if (z_alpha is not None) else alpha
        tests.append(ZMonobit(alpha=z_alpha_eff, min_bits=z_min_bits))

    bits_seen = 0
    t0 = time.perf_counter()
    ones_seen = 0
    last_report = t0

    try:
        if use_synthetic:
            base_seed = synthetic_seed
            seed_eff = derive_process_seed(base_seed, proc_id)
            bit_gen = bit_stream_synthetic(p=synthetic_p, seed=seed_eff)
        else:
            bit_gen = bit_stream_from_device(source_path, chunk_size=chunk_size)

        for bit in bit_gen:
            bits_seen += 1
            ones_seen += bit

            if per_iter and (bits_seen % max(1, iter_sample) == 0):
                zeros_seen = bits_seen - ones_seen
                queue_out.put((
                    "ITER",
                    {
                        "proc": proc_id,
                        "bits_processed": bits_seen,
                        "ones_total": ones_seen,
                        "zeros_total": zeros_seen,
                        "ones_pct": (ones_seen / bits_seen),
                        "zeros_pct": (zeros_seen / bits_seen),
                    },
                ))

            for test in tests:
                evt = test.update(bit)
                if evt is not None:
                    now = time.perf_counter()
                    rate = bits_seen / (now - t0) if now > t0 else float("nan")
                    apt_len = len(apt.buf)
                    evt.update(
                        {
                            "proc": proc_id,
                            "bits_processed": bits_seen,
                            "ones_total": ones_seen,
                            "ones_pct": (ones_seen / bits_seen) if bits_seen else None,
                            "apt_window": apt.window,
                            "apt_len": apt_len,
                            "apt_ones": apt.ones,
                            "apt_pct": (apt.ones / apt_len) if apt_len > 0 else None,
                            "rct_run_len": rct.run_len,
                            "sprt_up": sprt.s_up,
                            "sprt_dn": sprt.s_dn,
                            "bps": rate,
                        }
                    )
                    queue_out.put(("ANOMALY", evt))
                    if stop_on_anomaly:
                        return

            now = time.perf_counter()
            if (now - last_report) >= report_interval:
                rate = bits_seen / (now - t0) if now > t0 else float("nan")
                apt_len = len(apt.buf)
                queue_out.put(
                    (
                        "STATS",
                        {
                            "proc": proc_id,
                            "bits_processed": bits_seen,
                            "ones_total": ones_seen,
                            "ones_pct": (ones_seen / bits_seen) if bits_seen else None,
                            "apt_window": apt.window,
                            "apt_len": apt_len,
                            "apt_ones": apt.ones,
                            "apt_pct": (apt.ones / apt_len) if apt_len > 0 else None,
                            "rct_run_len": rct.run_len,
                            "sprt_up": sprt.s_up,
                            "sprt_dn": sprt.s_dn,
                            "bps": rate,
                        },
                    )
                )
                last_report = now

            if max_bits is not None and bits_seen >= max_bits:
                break
            if max_seconds is not None and (time.perf_counter() - t0) >= max_seconds:
                break

        now = time.perf_counter()
        apt_len = len(apt.buf)
        queue_out.put(
            (
                "DONE",
                {
                    "proc": proc_id,
                    "bits_processed": bits_seen,
                    "ones_total": ones_seen,
                    "ones_pct": (ones_seen / bits_seen) if bits_seen else None,
                    "apt_window": apt.window,
                    "apt_len": apt_len,
                    "apt_ones": apt.ones,
                    "apt_pct": (apt.ones / apt_len) if apt_len > 0 else None,
                    "bps": bits_seen / (now - t0) if now > t0 else float("nan"),
                },
            )
        )

    except Exception as e:
        queue_out.put(("ERROR", {"proc": proc_id, "error": repr(e)}))


