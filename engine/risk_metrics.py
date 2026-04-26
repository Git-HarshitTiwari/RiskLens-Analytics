import numpy as np
import pandas as pd
from scipy import stats


def compute_var(
    returns: pd.Series,
    confidence: float = 0.95,
    method: str = "historical"
) -> float:
    """
    Value at Risk — max expected loss at confidence level.

    Methods:
    - historical : uses actual return distribution (preferred for Indian markets
                   which have fat tails and are non-normal)
    - parametric : assumes Gaussian distribution (faster, less accurate)
    """
    clean = returns.dropna()
    if len(clean) == 0:
        return 0.0

    if method == "historical":
        return float(np.percentile(clean, (1 - confidence) * 100))
    elif method == "parametric":
        mu, sigma = clean.mean(), clean.std()
        return float(stats.norm.ppf(1 - confidence, mu, sigma))
    else:
        raise ValueError(f"Unknown VaR method: {method}. Use 'historical' or 'parametric'.")


def compute_cvar(
    returns: pd.Series,
    confidence: float = 0.95
) -> float:
    """
    Conditional VaR (Expected Shortfall).
    Average loss in the worst (1-confidence)% of trading days.
    More conservative and informative than plain VaR.
    Preferred by RBI and Basel III for capital adequacy.
    """
    clean = returns.dropna()
    var = compute_var(clean, confidence, method="historical")
    tail = clean[clean <= var]
    return float(tail.mean()) if len(tail) > 0 else var


def compute_sharpe(
    returns: pd.Series,
    risk_free_rate: float = 0.065  # ~RBI repo rate
) -> float:
    """
    Sharpe Ratio — annualized risk-adjusted return.
    Using RBI repo rate (~6.5%) as risk-free rate for Indian context.
    Above 1.0 = good. Above 2.0 = excellent.
    """
    clean = returns.dropna()
    daily_rf = risk_free_rate / 252
    excess = clean - daily_rf
    std = clean.std()
    if std == 0:
        return 0.0
    return float((excess.mean() / std) * np.sqrt(252))


def compute_sortino(
    returns: pd.Series,
    risk_free_rate: float = 0.065
) -> float:
    """
    Sortino Ratio — only penalizes downside volatility.
    Better metric for Indian markets which have asymmetric return profiles
    (crashes are sharp, rallies are gradual).
    """
    clean = returns.dropna()
    daily_rf = risk_free_rate / 252
    excess = clean - daily_rf
    downside_std = clean[clean < 0].std()
    if downside_std == 0:
        return 0.0
    return float((excess.mean() / downside_std) * np.sqrt(252))


def compute_max_drawdown(prices: pd.Series) -> float:
    """
    Maximum Drawdown — largest peak to trough decline in price.
    Essential for understanding worst-case loss from a peak.
    e.g., Nifty 50 fell ~38% in March 2020 (COVID crash).
    """
    clean = prices.dropna()
    rolling_peak = clean.cummax()
    drawdown = (clean - rolling_peak) / rolling_peak
    return float(drawdown.min())


def compute_volatility(
    returns: pd.Series,
    annualize: bool = True
) -> float:
    """Annualized volatility. NSE uses 252 trading days per year."""
    clean = returns.dropna()
    vol = clean.std()
    return float(vol * np.sqrt(252)) if annualize else float(vol)


def compute_beta(
    returns: pd.Series,
    benchmark_returns: pd.Series  # Should be Nifty 50 (^NSEI)
) -> float:
    """
    Beta vs Nifty 50.
    Beta > 1 = more volatile than Nifty (aggressive stock)
    Beta < 1 = less volatile than Nifty (defensive stock)
    Beta < 0 = moves opposite to Nifty (rare, potential hedge)
    """
    aligned = pd.concat([returns, benchmark_returns], axis=1).dropna()
    if len(aligned) < 30:
        return 1.0
    cov_matrix = np.cov(aligned.iloc[:, 0], aligned.iloc[:, 1])
    benchmark_var = np.var(aligned.iloc[:, 1])
    if benchmark_var == 0:
        return 1.0
    return float(cov_matrix[0][1] / benchmark_var)


def compute_calmar(
    returns: pd.Series,
    prices: pd.Series
) -> float:
    """
    Calmar Ratio — annualized return divided by max drawdown.
    Popular in hedge fund evaluation. Higher = better.
    """
    ann_return = returns.mean() * 252
    mdd = abs(compute_max_drawdown(prices))
    if mdd == 0:
        return 0.0
    return float(ann_return / mdd)


def compute_all_metrics(
    prices: pd.DataFrame,
    returns: pd.DataFrame,
    benchmark_ticker: str = "^NSEI",
    confidence: float = 0.95,
    risk_free_rate: float = 0.065
) -> pd.DataFrame:
    """
    Master function — computes all risk metrics for every asset.
    Returns clean summary DataFrame indexed by ticker.
    Benchmark is Nifty 50 by default.
    """
    # Get benchmark — handle both direct ticker and renamed columns
    benchmark_returns = None
    if benchmark_ticker in returns.columns:
        benchmark_returns = returns[benchmark_ticker]
    elif "Nifty 50" in returns.columns:
        benchmark_returns = returns["Nifty 50"]

    results = []

    for ticker in returns.columns:
        r = returns[ticker].dropna()
        p = prices[ticker].dropna()

        if len(r) < 30:
            continue

        metrics = {
            "ticker": ticker,
            "var_95": round(compute_var(r, confidence) * 100, 3),
            "cvar_95": round(compute_cvar(r, confidence) * 100, 3),
            "sharpe": round(compute_sharpe(r, risk_free_rate), 3),
            "sortino": round(compute_sortino(r, risk_free_rate), 3),
            "calmar": round(compute_calmar(r, p), 3),
            "max_drawdown_%": round(compute_max_drawdown(p) * 100, 2),
            "annualized_vol_%": round(compute_volatility(r) * 100, 2),
            "beta_vs_nifty": (
                round(compute_beta(r, benchmark_returns), 3)
                if benchmark_returns is not None and ticker != benchmark_ticker
                else 1.0
            )
        }
        results.append(metrics)

    df = pd.DataFrame(results)
    if not df.empty:
        df = df.set_index("ticker")

    return df