import math

try:
    from scipy.stats import norm
    _HAS_SCIPY = True
except Exception:
    _HAS_SCIPY = False


def _norm_cdf(x: float) -> float:
    if _HAS_SCIPY:
        return norm.cdf(x)
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

def _norm_pdf(x: float) -> float:
    if _HAS_SCIPY:
        return norm.pdf(x)
    return (1.0 / math.sqrt(2.0 * math.pi)) * math.exp(-0.5 * x * x)

def _d1_d2(S: float, K: float, T: float, r: float, q: float, sigma: float):
    if T <= 0.0 or sigma <= 0.0 or S <= 0.0 or K <= 0.0:
        return 0.0, 0.0
    num = math.log(S / K) + (r - q + 0.5 * sigma * sigma) * T
    den = sigma * math.sqrt(T)
    d1 = num / den
    d2 = d1 - sigma * math.sqrt(T)
    return d1, d2

def bs_price(S: float, K: float, T: float, r: float, q: float,
             sigma: float, option_type: str = "call") -> float:
    option_type = option_type.lower()

    if T <= 0.0 or sigma <= 0.0:
        if option_type == "call":
            return max(S - K, 0.0)
        elif option_type == "put":
            return max(K - S, 0.0)
        else:
            raise ValueError("option_type must be 'call' or 'put'")

    d1, d2 = _d1_d2(S, K, T, r, q, sigma)

    if option_type == "call":
        return S * math.exp(-q * T) * _norm_cdf(d1) - K * math.exp(-r * T) * _norm_cdf(d2)
    elif option_type == "put":
        return K * math.exp(-r * T) * _norm_cdf(-d2) - S * math.exp(-q * T) * _norm_cdf(-d1)
    else:
        raise ValueError("option_type must be 'call' or 'put'")

def bs_delta(S: float, K: float, T: float, r: float, q: float,
             sigma: float, option_type: str = "call") -> float:
    option_type = option_type.lower()

    if T <= 0.0 or sigma <= 0.0:
        if option_type == "call":
            return 1.0 if S > K else 0.0
        elif option_type == "put":
            return -1.0 if S < K else 0.0
        else:
            raise ValueError("option_type must be 'call' or 'put'")

    d1, _ = _d1_d2(S, K, T, r, q, sigma)

    if option_type == "call":
        return math.exp(-q * T) * _norm_cdf(d1)
    elif option_type == "put":
        return -math.exp(-q * T) * _norm_cdf(-d1)
    else:
        raise ValueError("option_type must be 'call' or 'put'")

def bs_gamma(S: float, K: float, T: float, r: float, q: float,
             sigma: float) -> float:
    if T <= 0.0 or sigma <= 0.0 or S <= 0.0:
        return 0.0

    d1, _ = _d1_d2(S, K, T, r, q, sigma)
    return (math.exp(-q * T) * _norm_pdf(d1)) / (S * sigma * math.sqrt(T))

def bs_vega(S: float, K: float, T: float, r: float, q: float,
            sigma: float) -> float:
    if T <= 0.0 or sigma <= 0.0:
        return 0.0

    d1, _ = _d1_d2(S, K, T, r, q, sigma)
    return S * math.exp(-q * T) * _norm_pdf(d1) * math.sqrt(T)

def bs_theta(S: float, K: float, T: float, r: float, q: float,
             sigma: float, option_type: str = "call") -> float:

    option_type = option_type.lower()

    if T <= 0.0 or sigma <= 0.0:
        return 0.0

    d1, d2 = _d1_d2(S, K, T, r, q, sigma)
    first_term = - (S * math.exp(-q * T) * _norm_pdf(d1) * sigma) / (2.0 * math.sqrt(T))

    if option_type == "call":
        second = -r * K * math.exp(-r * T) * _norm_cdf(d2)
        third = q * S * math.exp(-q * T) * _norm_cdf(d1)
        return first_term + second + third
    elif option_type == "put":
        second = r * K * math.exp(-r * T) * _norm_cdf(-d2)
        third = -q * S * math.exp(-q * T) * _norm_cdf(-d1)
        return first_term + second + third
    else:
        raise ValueError("option_type must be 'call' or 'put'")
    
if __name__ == "__main__":
    S0 = 520.0
    K = 494.0
    T = 1.0 / 12.0
    r = 0.05
    q = 0.018
    sigma = 0.24

    for opt_type in ("call", "put"):
        px = bs_price(S0, K, T, r, q, sigma, opt_type)
        d = bs_delta(S0, K, T, r, q, sigma, opt_type)
        g = bs_gamma(S0, K, T, r, q, sigma)
        v = bs_vega(S0, K, T, r, q, sigma)
        th = bs_theta(S0, K, T, r, q, sigma, opt_type)
        print(f"{opt_type.capitalize()} price={px:.4f}, delta={d:.4f}, "
              f"gamma={g:.6f}, vega={v:.4f}, theta={th:.4f}")
