import numpy as np
import pandas as pd
from engine.risk_metrics import (
    compute_var, compute_cvar, compute_sharpe,
    compute_sortino, compute_max_drawdown, compute_volatility
)


def compute_portfolio_returns(
    returns: pd.DataFrame,
    weights: dict = None
) -> pd.Series:
    """
    Compute weighted portfolio daily returns.
    Default = equal weight across all assets.
    """
    tickers = list(returns.columns)

    if weights is None:
        w = np.array([1 / len(tickers)] * len(tickers))
    else:
        w = np.array([weights.get(t, 0.0) for t in tickers])
        total = w.sum()
        if total == 0:
            raise ValueError("Weights sum to zero.")
        w = w / total  # normalize

    port_returns = returns[tickers].dot(w)
    return port_returns


def compute_correlation_matrix(returns: pd.DataFrame) -> pd.DataFrame:
    """
    Pairwise Pearson correlation of all asset returns.
    Powers the heatmap in the dashboard.
    """
    return returns.corr().round(4)


def compute_risk_surface(
    returns: pd.DataFrame,
    window_days: int = 63  # ~1 quarter
) -> pd.DataFrame:
    """
    Rolling VaR surface — the core 3D visualization data.

    For each asset, compute rolling 95% VaR over a sliding window.
    Result: DataFrame where:
      - rows = trading dates
      - columns = asset tickers
      - values = rolling VaR (as % loss, positive number for clarity)

    This is what gets plotted on the 3D surface:
      X axis = Time
      Y axis = Assets
      Z axis = Rolling VaR magnitude
    """
    surface = {}

    for ticker in returns.columns:
        r = returns[ticker].dropna()
        rolling_var = r.rolling(window=window_days).apply(
            lambda x: abs(compute_var(
                pd.Series(x), confidence=0.95, method="historical"
            )) * 100,  # convert to positive percentage
            raw=False
        )
        surface[ticker] = rolling_var

    surface_df = pd.DataFrame(surface).dropna()
    return surface_df


def compute_portfolio_summary(
    prices: pd.DataFrame,
    returns: pd.DataFrame,
    weights: dict = None
) -> dict:
    """
    High-level portfolio KPIs for dashboard summary cards.
    All monetary context is in INR terms (Indian market).
    """
    port_returns = compute_portfolio_returns(returns, weights)
    port_prices_proxy = (1 + port_returns).cumprod() * 100  # indexed to 100

    total_return = float(
        ((prices.iloc[-1] / prices.iloc[0]) - 1).mean() * 100
    )

    return {
        "total_return_%": round(total_return, 2),
        "portfolio_var_95_%": round(compute_var(port_returns) * 100, 3),
        "portfolio_cvar_95_%": round(compute_cvar(port_returns) * 100, 3),
        "portfolio_sharpe": round(compute_sharpe(port_returns), 3),
        "portfolio_sortino": round(compute_sortino(port_returns), 3),
        "portfolio_max_drawdown_%": round(
            compute_max_drawdown(port_prices_proxy) * 100, 2
        ),
        "portfolio_annualized_vol_%": round(
            compute_volatility(port_returns) * 100, 2
        ),
        "num_assets": len(returns.columns),
        "data_start": str(returns.index[0].date()),
        "data_end": str(returns.index[-1].date()),
        "currency": "INR"
    }