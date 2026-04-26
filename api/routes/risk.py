import pandas as pd
import time
from fastapi import APIRouter, Depends, HTTPException, Query
from api.auth import get_current_user
from api.cache import cache_get, cache_set, make_cache_key
from api.logger import logger, log_computation_time
from engine.data_fetcher import load_nifty50, load_fno_stocks
from engine.risk_metrics import compute_all_metrics
from engine.stress_test import run_all_scenarios, run_scenario, SCENARIOS
from config.settings import settings

router = APIRouter(prefix="/risk", tags=["Risk Metrics"])


@router.get("/metrics")
def get_risk_metrics(
    period_years: int = Query(default=1, ge=1, le=5),
    universe: str = Query(default="nifty50"),
    user: dict = Depends(get_current_user)
):
    """
    Compute risk metrics for all assets.
    Protected — requires Bearer token.
    Results cached for 1 hour to avoid re-fetching.
    """
    cache_key = make_cache_key("risk_metrics", universe, period_years)
    cached = cache_get(cache_key)
    if cached:
        return cached

    start = time.time()
    try:
        if universe == "fno":
            prices, returns = load_fno_stocks(period_years=period_years)
        else:
            prices, returns = load_nifty50(period_years=period_years)

        # Fetch Nifty 50 index for beta computation
        import yfinance as yf
        nifty_prices = yf.download("^NSEI", period=f"{period_years}y",
                            interval="1d", progress=False,
                            auto_adjust=True)["Close"]
        # Flatten to Series if yfinance returns a DataFrame
        if isinstance(nifty_prices, pd.DataFrame):
            nifty_prices = nifty_prices.iloc[:, 0]
        nifty_returns = nifty_prices.pct_change().dropna()
        nifty_returns.name = "^NSEI"

        # Align and inject into returns DataFrame
        common_idx = returns.index.intersection(nifty_returns.index)
        returns_with_benchmark = returns.loc[common_idx].copy()
        returns_with_benchmark["^NSEI"] = nifty_returns.loc[common_idx]
        prices_with_benchmark = prices.loc[common_idx].copy()
        prices_with_benchmark["^NSEI"] = nifty_prices.loc[common_idx]

        metrics_df = compute_all_metrics(
            prices_with_benchmark, returns_with_benchmark,
            confidence=settings.var_confidence,
            risk_free_rate=settings.risk_free_rate
        )
        # Remove benchmark index from results — it's not a stock
        metrics_df = metrics_df.drop("^NSEI", errors="ignore")

        result = {
            "universe": universe,
            "period_years": period_years,
            "num_assets": len(metrics_df),
            "metrics": metrics_df.reset_index().to_dict(orient="records")
        }

        log_computation_time("get_risk_metrics", time.time() - start)
        cache_set(cache_key, result)
        return result

    except Exception as e:
        logger.error("Risk metrics computation failed", extra={
            "error": str(e)
        })
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stress")
def get_stress_test(
    scenario: str = Query(default="all"),
    period_years: int = Query(default=1, ge=1, le=3),
    user: dict = Depends(get_current_user)
):
    """
    Run stress test scenarios on the Nifty 50 portfolio.
    Protected — requires Bearer token.
    Available scenarios: covid_crash, global_financial_crisis,
    inr_depreciation, volatility_spike, fii_selloff, all
    """
    start = time.time()
    try:
        _, returns = load_nifty50(period_years=period_years)

        if scenario == "all":
            results = run_all_scenarios(returns)
        elif scenario in SCENARIOS:
            results = {scenario: run_scenario(returns, scenario)}
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown scenario. Choose from: "
                       f"{list(SCENARIOS.keys())} or 'all'"
            )

        log_computation_time("get_stress_test", time.time() - start)
        return {"scenarios": results}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Stress test failed", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/surface")
def get_risk_surface(
    period_years: int = Query(default=1, ge=1, le=3),
    user: dict = Depends(get_current_user)
):
    """
    Get rolling VaR surface data for 3D visualization.
    Protected — requires Bearer token.
    """
    cache_key = make_cache_key("risk_surface", period_years)
    cached = cache_get(cache_key)
    if cached:
        return cached

    start = time.time()
    try:
        from engine.portfolio import compute_risk_surface
        _, returns = load_nifty50(period_years=period_years)
        surface = compute_risk_surface(
            returns,
            window_days=settings.rolling_window_days
        )

        result = {
            "dates": [str(d.date()) for d in surface.index],
            "tickers": list(surface.columns),
            "values": surface.values.tolist(),
            "shape": list(surface.shape)
        }

        log_computation_time("get_risk_surface", time.time() - start)
        cache_set(cache_key, result, ttl=1800)
        return result

    except Exception as e:
        logger.error("Risk surface failed", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))