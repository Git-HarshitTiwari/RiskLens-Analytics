import pandas as pd
from engine.data_fetcher import compute_returns, NIFTY_50_STOCKS, FNO_STOCKS


def test_nifty50_list_not_empty():
    assert len(NIFTY_50_STOCKS) > 0


def test_fno_stocks_subset_of_nifty50():
    for stock in FNO_STOCKS:
        assert stock in NIFTY_50_STOCKS


def test_compute_returns_shape():
    prices = pd.DataFrame({
        "RELIANCE.NS": [100, 102, 101, 105, 103],
        "TCS.NS":      [200, 198, 202, 205, 207]
    })
    returns = compute_returns(prices)
    # Log returns drop first row
    assert len(returns) == len(prices) - 1
    assert set(returns.columns) == {"RELIANCE.NS", "TCS.NS"}


def test_compute_returns_no_nulls():
    prices = pd.DataFrame({
        "INFY.NS": [1500, 1520, 1510, 1530, 1525]
    })
    returns = compute_returns(prices)
    assert returns.isnull().sum().sum() == 0