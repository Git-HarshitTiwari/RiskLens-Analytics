import numpy as np
import pandas as pd
import pytest
from engine.risk_metrics import (
    compute_var, compute_cvar, compute_sharpe,
    compute_sortino, compute_max_drawdown, compute_volatility, compute_beta
)


@pytest.fixture
def sample_returns():
    np.random.seed(42)
    return pd.Series(np.random.normal(0.0005, 0.015, 500))


@pytest.fixture
def sample_prices():
    np.random.seed(42)
    r = np.random.normal(0.0005, 0.015, 500)
    return pd.Series(100 * np.exp(np.cumsum(r)))


@pytest.fixture
def benchmark_returns():
    np.random.seed(99)
    return pd.Series(np.random.normal(0.0004, 0.012, 500))


def test_var_is_negative(sample_returns):
    assert compute_var(sample_returns) < 0


def test_cvar_worse_than_var(sample_returns):
    var = compute_var(sample_returns)
    cvar = compute_cvar(sample_returns)
    assert cvar <= var


def test_var_99_worse_than_var_95(sample_returns):
    var_95 = compute_var(sample_returns, confidence=0.95)
    var_99 = compute_var(sample_returns, confidence=0.99)
    assert var_99 <= var_95


def test_sharpe_is_float(sample_returns):
    result = compute_sharpe(sample_returns)
    assert isinstance(result, float)


def test_sortino_is_float(sample_returns):
    result = compute_sortino(sample_returns)
    assert isinstance(result, float)


def test_max_drawdown_negative(sample_prices):
    dd = compute_max_drawdown(sample_prices)
    assert dd < 0


def test_volatility_positive(sample_returns):
    vol = compute_volatility(sample_returns)
    assert vol > 0


def test_beta_is_float(sample_returns, benchmark_returns):
    beta = compute_beta(sample_returns, benchmark_returns)
    assert isinstance(beta, float)


def test_var_invalid_method(sample_returns):
    with pytest.raises(ValueError):
        compute_var(sample_returns, method="montecarlo_fake")