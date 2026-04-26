import time
from fastapi import APIRouter, Depends, HTTPException, Query
from api.auth import get_current_user
from api.cache import cache_get, cache_set, make_cache_key
from api.logger import logger, log_computation_time
from engine.data_fetcher import load_nifty50
from engine.portfolio import (
    compute_portfolio_summary,
    compute_correlation_matrix,
    compute_portfolio_returns
)
from engine.benchmark import (
    fetch_benchmark,
    compare_portfolio_to_benchmark
)

router = APIRouter(prefix="/portfolio", tags=["Portfolio"])


@router.get("/summary")
def get_portfolio_summary(
    period_years: int = Query(default=1, ge=1, le=5),
    user: dict = Depends(get_current_user)
):
    """
    Portfolio-level KPIs — return, VaR, Sharpe, drawdown etc.
    Protected — requires Bearer token.
    """
    cache_key = make_cache_key("portfolio_summary", period_years)
    cached = cache_get(cache_key)
    if cached:
        return cached

    start = time.time()
    try:
        prices, returns = load_nifty50(period_years=period_years)
        summary = compute_portfolio_summary(prices, returns)
        log_computation_time("get_portfolio_summary", time.time() - start)
        cache_set(cache_key, summary)
        return summary
    except Exception as e:
        logger.error("Portfolio summary failed", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/correlation")
def get_correlation_matrix(
    period_years: int = Query(default=1, ge=1, le=5),
    user: dict = Depends(get_current_user)
):
    """
    Pairwise correlation matrix for all Nifty 50 stocks.
    Powers the heatmap in the dashboard.
    Protected — requires Bearer token.
    """
    cache_key = make_cache_key("correlation", period_years)
    cached = cache_get(cache_key)
    if cached:
        return cached

    start = time.time()
    try:
        _, returns = load_nifty50(period_years=period_years)
        corr = compute_correlation_matrix(returns)
        result = {
            "tickers": list(corr.columns),
            "matrix": corr.values.tolist()
        }
        log_computation_time(
            "get_correlation_matrix", time.time() - start
        )
        cache_set(cache_key, result)
        return result
    except Exception as e:
        logger.error("Correlation failed", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/benchmark")
def get_benchmark_comparison(
    benchmark: str = Query(default="Nifty 50"),
    period_years: int = Query(default=1, ge=1, le=5),
    user: dict = Depends(get_current_user)
):
    """
    Compare portfolio performance against Nifty 50 or sectoral index.
    Returns alpha, beta, tracking error, information ratio.
    Protected — requires Bearer token.
    """
    start = time.time()
    try:
        _, port_returns = load_nifty50(period_years=period_years)
        _, bench_returns = fetch_benchmark(benchmark, period_years)

        port_series = compute_portfolio_returns(port_returns)
        bench_series = bench_returns.iloc[:, 0]

        result = compare_portfolio_to_benchmark(
            port_series, bench_series, benchmark
        )
        log_computation_time(
            "get_benchmark_comparison", time.time() - start
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Benchmark comparison failed", extra={
            "error": str(e)
        })
        raise HTTPException(status_code=500, detail=str(e))