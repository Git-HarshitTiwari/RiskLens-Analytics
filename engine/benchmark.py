import pandas as pd
import numpy as np
from engine.data_fetcher import fetch_price_data, compute_returns
from engine.risk_metrics import (
    compute_sharpe, compute_max_drawdown,
    compute_volatility, compute_var
)


BENCHMARKS = {
    "Nifty 50":   "^NSEI",
    "Bank Nifty": "^NSEBANK",
    "Nifty IT":   "^CNXIT",
}


def fetch_benchmark(
    benchmark_name: str = "Nifty 50",
    period_years: int = 1
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Fetch prices and returns for a benchmark index."""
    ticker = BENCHMARKS.get(benchmark_name)
    if not ticker:
        raise ValueError(
            f"Unknown benchmark: {benchmark_name}. "
            f"Choose from: {list(BENCHMARKS.keys())}"
        )
    prices = fetch_price_data([ticker], period_years=period_years)
    prices = prices.rename(columns={ticker: benchmark_name})
    returns = compute_returns(prices)
    return prices, returns


def compare_portfolio_to_benchmark(
    portfolio_returns: pd.Series,
    benchmark_returns: pd.Series,
    benchmark_name: str = "Nifty 50",
    risk_free_rate: float = 0.065
) -> dict:
    """
    Compare portfolio performance against a benchmark.
    Computes alpha, beta, tracking error, information ratio.
    These are standard metrics used by fund managers in India.
    """
    # Align both series on same dates
    aligned = pd.concat(
        [portfolio_returns, benchmark_returns], axis=1
    ).dropna()
    aligned.columns = ["portfolio", "benchmark"]

    port = aligned["portfolio"]
    bench = aligned["benchmark"]

    # Beta — portfolio sensitivity to benchmark
    cov_matrix = np.cov(port, bench)
    bench_var = np.var(bench)
    beta = float(cov_matrix[0][1] / bench_var) if bench_var != 0 else 1.0

    # Alpha — excess return over what beta predicts (annualized)
    daily_rf = risk_free_rate / 252
    alpha = float(
        (port.mean() - daily_rf - beta * (bench.mean() - daily_rf)) * 252
    )

    # Tracking error — volatility of return difference
    active_returns = port - bench
    tracking_error = float(active_returns.std() * np.sqrt(252))

    # Information ratio — active return per unit of tracking error
    information_ratio = float(
        (active_returns.mean() * 252) / tracking_error
    ) if tracking_error != 0 else 0.0

    # Individual metrics
    port_sharpe = compute_sharpe(port, risk_free_rate)
    bench_sharpe = compute_sharpe(bench, risk_free_rate)

    port_vol = compute_volatility(port)
    bench_vol = compute_volatility(bench)

    port_return = float(port.mean() * 252 * 100)
    bench_return = float(bench.mean() * 252 * 100)

    return {
        "benchmark_name": benchmark_name,
        "portfolio_annualized_return_%": round(port_return, 2),
        "benchmark_annualized_return_%": round(bench_return, 2),
        "excess_return_%": round(port_return - bench_return, 2),
        "portfolio_sharpe": round(port_sharpe, 3),
        "benchmark_sharpe": round(bench_sharpe, 3),
        "portfolio_volatility_%": round(port_vol * 100, 2),
        "benchmark_volatility_%": round(bench_vol * 100, 2),
        "alpha": round(alpha * 100, 3),
        "beta": round(beta, 3),
        "tracking_error_%": round(tracking_error * 100, 2),
        "information_ratio": round(information_ratio, 3),
    }