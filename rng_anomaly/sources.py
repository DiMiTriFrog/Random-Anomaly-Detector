import time
import random


def bit_stream_from_device(path: str, chunk_size: int = 1 << 16):
    """
    Generate a stream of bits (0/1) from a byte device. LSB-first.
    """
    with open(path, "rb", buffering=0) as f:
        while True:
            data = f.read(chunk_size)
            if not data:
                break
            for b in data:
                yield (b >> 0) & 1
                yield (b >> 1) & 1
                yield (b >> 2) & 1
                yield (b >> 3) & 1
                yield (b >> 4) & 1
                yield (b >> 5) & 1
                yield (b >> 6) & 1
                yield (b >> 7) & 1


def bit_stream_synthetic(p: float = 0.5, seed: int | None = None):
    """
    Generate i.i.d. Bernoulli bits with probability p for 1s.
    """
    if not (0.0 <= p <= 1.0):
        raise ValueError("p must be in [0,1]")
    rng = random.Random(seed)
    while True:
        yield 1 if rng.random() < p else 0


def derive_process_seed(base_seed: int | None, proc_id: int) -> int:
    """
    Derive a per-process seed from a base seed and process id to avoid
    correlation across synthetic generators.
    """
    if base_seed is None:
        base_seed = time.time_ns()
    return (base_seed ^ (proc_id * 0x9E3779B97F4A7C15)) & ((1 << 64) - 1)


