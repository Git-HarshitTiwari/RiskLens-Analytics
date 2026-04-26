import time
from fastapi import APIRouter, Depends, HTTPException
from api.auth import get_current_user
from api.cache import cache_get, cache_set, make_cache_key
from api.logger import logger, log_computation_time
from engine.data_fetcher import load_market_indicators, load_nifty50
from engine.india_market import (
    classify_market_regime,
    vix_asset_correlation,
    get_circuit_breaker_summary,
    flag_expiry_weeks,
    expiry_week_volatility_premium
)

router = APIRouter(prefix="/market", tags=["Market Intelligence"])


@router.get("/vix")
def get_india_vix(user: dict = Depends(get_current_user)):
    """
    India VIX current regime and recent history.
    Protected — requires Bearer token.
    """
    cache_key = make_cache_key("india_vix")
    cached = cache_get(cache_key)
    if cached:
        return cached

    start = time.time()
    try:
        prices, _ = load_market_indicators(period_years=1)

        if "India VIX" not in prices.columns:
            raise HTTPException(
                status_code=503,
                detail="India VIX data unavailable"
            )

        vix = prices["India VIX"].dropna()
        regime = classify_market_regime(vix)
        current_vix = float(vix.iloc[-1])
        current_regime = str(regime.iloc[-1])

        # Compute day-over-day VIX change
        prev_vix = float(vix.iloc[-2]) if len(vix) >= 2 else current_vix
        vix_change_pct = round(((current_vix - prev_vix) / prev_vix) * 100, 2) if prev_vix != 0 else 0.0

        result = {
            "current_vix": round(current_vix, 2),
            "current_regime": current_regime,
            "change_pct": vix_change_pct,
            "vix_history": {
                str(d.date()): round(float(v), 2)
                for d, v in vix.tail(30).items()
            },
            "regime_history": {
                str(d.date()): r
                for d, r in regime.tail(30).items()
            }
        }

        log_computation_time("get_india_vix", time.time() - start)
        cache_set(cache_key, result, ttl=1800)
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error("VIX fetch failed", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/circuits")
def get_circuit_breakers(user: dict = Depends(get_current_user)):
    """
    Circuit breaker summary for all Nifty 50 stocks.
    Protected — requires Bearer token.
    """
    cache_key = make_cache_key("circuit_breakers")
    cached = cache_get(cache_key)
    if cached:
        return cached

    start = time.time()
    try:
        _, returns = load_nifty50(period_years=1)
        summary = get_circuit_breaker_summary(returns)
        result = summary.reset_index().to_dict(orient="records")
        log_computation_time(
            "get_circuit_breakers", time.time() - start
        )
        cache_set(cache_key, result, ttl=3600)
        return {"circuit_breakers": result}
    except Exception as e:
        logger.error("Circuit breaker failed", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/expiry")
def get_expiry_premium(user: dict = Depends(get_current_user)):
    """
    F&O expiry week volatility premium for all stocks.
    Protected — requires Bearer token.
    """
    cache_key = make_cache_key("expiry_premium")
    cached = cache_get(cache_key)
    if cached:
        return cached

    start = time.time()
    try:
        _, returns = load_nifty50(period_years=1)
        flags = flag_expiry_weeks(returns)
        premium = expiry_week_volatility_premium(returns, flags)
        result = premium.reset_index().to_dict(orient="records")
        log_computation_time(
            "get_expiry_premium", time.time() - start
        )
        cache_set(cache_key, result, ttl=3600)
        return {"expiry_premium": result}
    except Exception as e:
        logger.error("Expiry premium failed", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))
    
import datetime
import pytz

@router.get("/prices")
def get_market_prices():
    """
    Proxy endpoint for live market prices.
    Fetches via yfinance server-side to avoid browser CORS issues.
    Returns latest available prices for key indices.
    Public endpoint — no auth required for navbar display.
    """
    import yfinance as yf

    symbols = {
        "nifty50": "^NSEI",
        "sensex":  "^BSESN",
        "usdinr":  "INR=X",
        "gold":    "GC=F",
    }

    prices = {}
    for key, ticker in symbols.items():
        try:
            data = yf.download(
                ticker,
                period="2d",
                interval="1d",
                progress=False,
                auto_adjust=True
            )
            if not data.empty:
                latest = float(data["Close"].iloc[-1])
                prev   = float(data["Close"].iloc[-2]) if len(data) >= 2 else latest
                change = latest - prev
                change_pct = (change / prev * 100) if prev != 0 else 0
                prices[key] = {
                    "price":      round(latest, 2),
                    "change":     round(change, 2),
                    "change_pct": round(change_pct, 2),
                    "prev_close": round(prev, 2),
                }
            else:
                prices[key] = None
        except Exception:
            prices[key] = None

    # NSE market status — IST timezone
    ist = pytz.timezone("Asia/Kolkata")
    now_ist = datetime.datetime.now(ist)
    weekday = now_ist.weekday()  # 0=Mon, 6=Sun
    hour = now_ist.hour
    minute = now_ist.minute
    time_val = hour * 60 + minute

    market_open  = 9 * 60 + 15   # 9:15 AM
    market_close = 15 * 60 + 30  # 3:30 PM

    if weekday >= 5:
        market_status = "Weekend"
    elif time_val < market_open:
        market_status = "Pre-Market"
    elif time_val <= market_close:
        market_status = "Open"
    else:
        market_status = "Closed"

    return {
        "prices":        prices,
        "market_status": market_status,
        "as_of_ist":     now_ist.strftime("%H:%M IST"),
    }