import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


# ─── Indian Market Asset Universe ─────────────────────────────────────────────

NIFTY_50_STOCKS = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
    "HINDUNILVR.NS", "ITC.NS", "SBIN.NS", "BAJFINANCE.NS", "BHARTIARTL.NS",
    "KOTAKBANK.NS", "LT.NS", "HCLTECH.NS", "AXISBANK.NS", "ASIANPAINT.NS",
    "MARUTI.NS", "SUNPHARMA.NS", "TITAN.NS", "ULTRACEMCO.NS", "WIPRO.NS",
    "NESTLEIND.NS", "POWERGRID.NS", "NTPC.NS", "TECHM.NS", "ONGC.NS",
    "BAJAJFINSV.NS", "ADANIENT.NS", "JSWSTEEL.NS", "TATASTEEL.NS", "HINDALCO.NS"
]

SECTORAL_INDICES = {
    "Nifty 50":     "^NSEI",
    "Bank Nifty":   "^NSEBANK",
    "Nifty IT":     "^CNXIT",
    "Nifty Pharma": "^CNXPHARMA",
    "Nifty Auto":   "^CNXAUTO",
    "Nifty FMCG":   "^CNXFMCG",
    "Nifty Metal":  "^CNXMETAL",
}

MARKET_INDICATORS = {
    "India VIX":  "^INDIAVIX",
    "USD/INR":    "INR=X",
    "Gold":       "GC=F",
}

# F&O eligible — high liquidity, derivatives available on NSE
FNO_STOCKS = [
    "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS",
    "BAJFINANCE.NS", "SBIN.NS", "KOTAKBANK.NS", "AXISBANK.NS", "LT.NS",
    "HCLTECH.NS", "WIPRO.NS", "TECHM.NS", "MARUTI.NS", "BAJAJFINSV.NS"
]


# ─── NSE Holidays (2024-2025) ──────────────────────────────────────────────────
# NSE is closed on these dates — we use this to validate data gaps
NSE_HOLIDAYS_2024_2025 = [
    "2024-01-26", "2024-03-25", "2024-03-29", "2024-04-14",
    "2024-04-17", "2024-04-21", "2024-05-23", "2024-06-17",
    "2024-07-17", "2024-08-15", "2024-10-02", "2024-10-14",
    "2024-11-01", "2024-11-15", "2024-11-20", "2024-12-25",
    "2025-01-26", "2025-02-26", "2025-03-14", "2025-03-31",
    "2025-04-10", "2025-04-14", "2025-04-18", "2025-05-01",
]


# ─── Core Fetch Function ───────────────────────────────────────────────────────

def fetch_price_data(
    tickers: list[str],
    period_years: int = 3,
    start_date: str = None,
    end_date: str = None,
) -> pd.DataFrame:
    """
    Fetch adjusted closing prices for NSE/BSE tickers via yfinance.
    Fetches in small batches to avoid rate limiting.
    """
    import time

    if end_date is None:
        end_date = datetime.today().strftime("%Y-%m-%d")
    if start_date is None:
        start = datetime.today() - timedelta(days=period_years * 365)
        start_date = start.strftime("%Y-%m-%d")

    print(f"  Fetching {len(tickers)} tickers from {start_date} to {end_date}...")

    # Fetch in batches of 5 to avoid rate limiting
    batch_size = 5
    all_prices = []

    for i in range(0, len(tickers), batch_size):
        batch = tickers[i:i + batch_size]
        for attempt in range(3):  # retry up to 3 times
            try:
                raw = yf.download(
                    tickers=batch,
                    start=start_date,
                    end=end_date,
                    auto_adjust=True,
                    progress=False,
                    threads=False  # more stable than threaded
                )
                if raw.empty:
                    break

                if len(batch) == 1:
                    close_data = raw["Close"] if "Close" in raw.columns else raw["Close"]
                    if isinstance(close_data, pd.DataFrame):
                        close_data.columns = [batch[0]]
                    else:
                        close_data = close_data.to_frame(name=batch[0])
                    batch_prices = close_data
                else:
                    # Multiple tickers
                    close_data = raw["Close"].copy()
                    if isinstance(close_data.columns, pd.MultiIndex):
                        # yfinance 1.3.0 returns (ticker, ticker) MultiIndex — flatten it
                        close_data.columns = [col[-1] if isinstance(col, tuple) else col
                                            for col in close_data.columns]
                    batch_prices = close_data

                all_prices.append(batch_prices)
                print(f"  ✅ Batch {i//batch_size + 1} done ({batch})")
                time.sleep(1)  # be polite to yfinance
                break

            except Exception as e:
                print(f"  ⚠️  Attempt {attempt+1} failed for batch {batch}: {e}")
                time.sleep(3)

    if not all_prices:
        raise ValueError("No valid price data returned. Check internet connection.")

    # Combine all batches
    prices = pd.concat(all_prices, axis=1)

    # Drop tickers with more than 20% missing data
    min_required = int(0.8 * len(prices))
    prices = prices.dropna(thresh=min_required, axis=1)

    if prices.empty:
        raise ValueError("All tickers failed data quality check.")

    # Forward fill then back fill
    prices = prices.ffill().bfill()
    prices = prices.dropna(how="all")

    dropped = set(tickers) - set(prices.columns)
    if dropped:
        print(f"  ⚠️  Dropped due to insufficient data: {dropped}")

    print(f"  ✅ Got clean data for {len(prices.columns)} tickers")
    return prices


def compute_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """
    Compute daily log returns.
    Log returns are standard in quant finance — they're time-additive
    and handle compounding correctly.
    """
    log_returns = np.log(prices / prices.shift(1)).dropna()
    return log_returns


# ─── Convenience Loaders ──────────────────────────────────────────────────────

def load_nifty50(period_years: int = 3) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load prices and returns for top Nifty 50 stocks."""
    prices = fetch_price_data(NIFTY_50_STOCKS, period_years=period_years)
    returns = compute_returns(prices)
    return prices, returns


def load_sectoral_indices(period_years: int = 3) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load prices and returns for NSE sectoral indices."""
    tickers = list(SECTORAL_INDICES.values())
    prices = fetch_price_data(tickers, period_years=period_years)
    # Rename columns from ticker symbols to readable names
    reverse_map = {v: k for k, v in SECTORAL_INDICES.items()}
    prices = prices.rename(columns=reverse_map)
    returns = compute_returns(prices)
    return prices, returns


def load_market_indicators(period_years: int = 3) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load India VIX, USD/INR, Gold."""
    tickers = list(MARKET_INDICATORS.values())
    prices = fetch_price_data(tickers, period_years=period_years)
    reverse_map = {v: k for k, v in MARKET_INDICATORS.items()}
    prices = prices.rename(columns=reverse_map)
    returns = compute_returns(prices)
    return prices, returns


def load_fno_stocks(period_years: int = 3) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load F&O eligible stocks."""
    prices = fetch_price_data(FNO_STOCKS, period_years=period_years)
    returns = compute_returns(prices)
    return prices, returns