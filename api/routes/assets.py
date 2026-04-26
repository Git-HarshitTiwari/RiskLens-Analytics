from fastapi import APIRouter
from engine.data_fetcher import (
    NIFTY_50_STOCKS, SECTORAL_INDICES,
    MARKET_INDICATORS, FNO_STOCKS
)

router = APIRouter(prefix="/assets", tags=["Assets"])


@router.get("/")
def list_all_assets():
    """List all available assets in the platform."""
    return {
        "nifty_50_stocks": NIFTY_50_STOCKS,
        "sectoral_indices": SECTORAL_INDICES,
        "market_indicators": MARKET_INDICATORS,
        "fno_stocks": FNO_STOCKS,
        "total_stocks": len(NIFTY_50_STOCKS),
    }


@router.get("/nifty50")
def list_nifty50():
    """List Nifty 50 stock tickers."""
    return {
        "tickers": NIFTY_50_STOCKS,
        "count": len(NIFTY_50_STOCKS)
    }


@router.get("/fno")
def list_fno():
    """List F&O eligible stock tickers."""
    return {
        "tickers": FNO_STOCKS,
        "count": len(FNO_STOCKS)
    }


@router.get("/indices")
def list_indices():
    """List available sectoral indices."""
    return {
        "indices": SECTORAL_INDICES,
        "count": len(SECTORAL_INDICES)
    }