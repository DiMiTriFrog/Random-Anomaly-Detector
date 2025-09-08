from dataclasses import dataclass
from collections import deque
import math

from .utils import apt_bounds_binomial, rct_cutoff_from_alpha, inv_norm_cdf


@dataclass
class RCT:
    """Repetition Count Test (SP 800-90B).

    Online test that flags an anomaly when a run of identical bits reaches or
    exceeds a cutoff determined by the target false positive rate alpha.
    """
    alpha: float
    cutoff: int = None
    last_bit: int = None
    run_len: int = 0

    def __post_init__(self):
        self.cutoff = rct_cutoff_from_alpha(self.alpha)

    def update(self, bit: int):
        if self.last_bit is None:
            self.last_bit = bit
            self.run_len = 1
            return None
        if bit == self.last_bit:
            self.run_len += 1
            if self.run_len >= self.cutoff:
                return {
                    "test": "RCT",
                    "cutoff": self.cutoff,
                    "message": f"Run of {self.run_len} identical bits (≥ {self.cutoff})"
                }
        else:
            self.last_bit = bit
            self.run_len = 1
        return None


@dataclass
class APT:
    """Adaptive Proportion Test (SP 800-90B) with sliding window.

    Sliding-window test that checks whether the number of ones within the
    last N bits stays within two-sided binomial bounds derived from alpha.
    """
    window: int
    alpha: float
    ones: int = 0
    buf: deque = None
    lo: int = None
    hi: int = None

    def __post_init__(self):
        self.buf = deque(maxlen=self.window)
        self.lo, self.hi = apt_bounds_binomial(self.window, self.alpha)

    def update(self, bit: int):
        if len(self.buf) == self.window:
            old = self.buf.popleft()
            self.ones -= old
        self.buf.append(bit)
        self.ones += bit
        if len(self.buf) == self.window:
            if not (self.lo <= self.ones <= self.hi):
                return {
                    "test": "APT",
                    "window": self.window,
                    "bounds": [self.lo, self.hi],
                    "ones": self.ones,
                    "message": f"Proportion out of [{self.lo},{self.hi}] in window {self.window}"
                }
        return None


@dataclass
class SPRTDetector:
    """Wald SPRT for bias around p=0.5 (both directions).

    We signal when the log-likelihood ratio crosses A. B is computed but not
    used for early acceptance of H0.
    """
    delta: float
    alpha: float
    beta: float
    s_up: float = 0.0
    s_dn: float = 0.0
    A: float = None
    B: float = None

    def __post_init__(self):
        self.A = math.log((1 - self.beta) / self.alpha)
        self.B = math.log(self.beta / (1 - self.alpha))
        if not (0 < self.delta < 0.5):
            raise ValueError("delta must be in (0, 0.5)")

        self.p0 = 0.5
        self.p1u = 0.5 + self.delta
        self.p1d = 0.5 - self.delta
        eps = 1e-12
        self.p1u = min(max(self.p1u, eps), 1 - eps)
        self.p1d = min(max(self.p1d, eps), 1 - eps)

    def update(self, bit: int):
        if bit == 1:
            self.s_up += math.log(self.p1u / self.p0)
            self.s_dn += math.log(self.p1d / self.p0)
        else:
            self.s_up += math.log((1 - self.p1u) / (1 - self.p0))
            self.s_dn += math.log((1 - self.p1d) / (1 - self.p0))

        if self.s_up >= self.A:
            return {
                "test": "SPRT",
                "direction": "p > 0.5",
                "delta": self.delta,
                "stat": self.s_up,
                "threshold": self.A,
                "message": f"Positive bias detected (δ≈{self.delta})"
            }
        if self.s_dn >= self.A:
            return {
                "test": "SPRT",
                "direction": "p < 0.5",
                "delta": self.delta,
                "stat": self.s_dn,
                "threshold": self.A,
                "message": f"Negative bias detected (δ≈{self.delta})"
            }
        return None


@dataclass
class ZMonobit:
    """Online two-sided Z-test for the monobit proportion.

    Triggers when |Z| exceeds threshold after at least min_bits observations.
    """
    alpha: float
    min_bits: int = 10000
    n: int = 0
    ones: int = 0
    z_threshold: float = None

    def __post_init__(self):
        if not (0 < self.alpha < 1):
            raise ValueError("alpha must be in (0,1)")
        if self.min_bits <= 0:
            raise ValueError("min_bits must be > 0")
        self.z_threshold = inv_norm_cdf(1 - self.alpha / 2.0)

    def update(self, bit: int):
        self.n += 1
        self.ones += bit
        if self.n < self.min_bits:
            return None
        mean = 0.5 * self.n
        var = 0.25 * self.n
        if var <= 0:
            return None
        z = (self.ones - mean) / math.sqrt(var)
        if abs(z) >= self.z_threshold:
            direction = "p > 0.5" if z > 0 else "p < 0.5"
            return {
                "test": "ZMONO",
                "direction": direction,
                "stat": z,
                "threshold": self.z_threshold,
                "n": self.n,
                "ones": self.ones,
                "message": f"Monobit Z exceeds threshold (|Z|≥{self.z_threshold:.3f})"
            }
        return None


