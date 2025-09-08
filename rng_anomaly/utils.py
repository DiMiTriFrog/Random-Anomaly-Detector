import math
import datetime as dt


def inv_norm_cdf(p: float) -> float:
    """
    Inverse CDF for N(0,1) using Acklam's rational approximation.
    Accuracy ~1e-9 in double precision; suitable for thresholding.
    """
    if not (0.0 < p < 1.0):
        if p == 0.0:
            return -math.inf
        if p == 1.0:
            return math.inf
        raise ValueError("p must be in (0,1)")

    a = [-3.969683028665376e+01,  2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01,  2.506628277459239e+00]
    b = [-5.447609879822406e+01,  1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00,  4.374664141464968e+00,  2.938163982698783e+00]
    d = [ 7.784695709041462e-03,  3.224671290700398e-01,  2.445134137142996e+00,
          3.754408661907416e+00]

    plow = 0.02425
    phigh = 1 - plow
    if p < plow:
        q = math.sqrt(-2*math.log(p))
        num = (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5])
        den = ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
        x = num/den
    elif p > phigh:
        q = math.sqrt(-2*math.log(1-p))
        num = -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5])
        den = ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
        x = num/den
    else:
        q = p - 0.5
        r = q*q
        num = (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q
        den = (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)
        x = num/den
    return x


def apt_bounds_binomial(n: int, alpha_two_sided: float):
    """
    Approximate two-sided binomial bounds for APT with window n and alpha.
    Uses normal approximation with continuity correction.
    Returns inclusive bounds (lo, hi) for the count of ones.
    """
    if n <= 0:
        raise ValueError("n must be > 0")
    if not (0 < alpha_two_sided < 1):
        raise ValueError("alpha must be in (0,1)")

    p = 0.5
    mu = n * p
    sigma = math.sqrt(n * p * (1 - p))
    z = inv_norm_cdf(1 - alpha_two_sided / 2.0)
    lo = int(math.ceil(mu - z * sigma - 0.5))
    hi = int(math.floor(mu + z * sigma + 0.5))
    lo = max(lo, 0)
    hi = min(hi, n)
    return lo, hi


def rct_cutoff_from_alpha(alpha_one_sided: float) -> int:
    """
    For RCT, the false positive rate for a run of length r is ~(1/2)^r.
    Pick r so (1/2)^r <= alpha, i.e., r = ceil(log(alpha)/log(1/2)).
    A minimum of 8 is enforced as a reasonable floor.
    """
    if not (0 < alpha_one_sided < 1):
        raise ValueError("alpha must be in (0,1)")
    r = math.ceil(math.log(alpha_one_sided, 0.5))
    return max(r, 8)


def human_bps(bps: float) -> str:
    if not math.isfinite(bps):
        return "n/a"
    units = ["bps", "Kbps", "Mbps", "Gbps"]
    i = 0
    while bps >= 1000.0 and i < len(units)-1:
        bps /= 1000.0
        i += 1
    return f"{bps:,.2f} {units[i]}"


def iso_now() -> str:
    try:
        return dt.datetime.now(dt.timezone.utc).isoformat()
    except Exception:
        return dt.datetime.utcnow().isoformat() + "Z"


