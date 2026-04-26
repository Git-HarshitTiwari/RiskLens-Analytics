import pandas as pd
import numpy as np
from engine.risk_metrics import compute_var, compute_cvar


# ── Historical Scenario Parameters ────────────────────────────────────────────
# Based on real Indian market crash events

SCENARIOS = {
    "covid_crash": {
        "name": "COVID-19 Market Crash (Mar 2020)",
        "description": "Nifty fell ~38% in 40 days. "
                       "Worst single-month fall in NSE history.",
        "market_return": -0.38,
        "volatility_multiplier": 3.5,
        "duration_days": 40,
    },
    "global_financial_crisis": {
        "name": "Global Financial Crisis (2008)",
        "description": "Nifty fell ~60% peak to trough. "
                       "FII outflows, credit freeze.",
        "market_return": -0.60,
        "volatility_multiplier": 4.0,
        "duration_days": 365,
    },
    "inr_depreciation": {
        "name": "INR Depreciation Shock",
        "description": "Sharp INR/USD move of 15%. "
                       "Impacts import-heavy sectors.",
        "market_return": -0.12,
        "volatility_multiplier": 1.8,
        "duration_days": 90,
        "inr_shock": -0.15,
    },
    "volatility_spike": {
        "name": "Volatility Spike (VIX > 35)",
        "description": "India VIX spikes above 35. "
                       "Options premiums explode, liquidity dries up.",
        "market_return": -0.15,
        "volatility_multiplier": 2.5,
        "duration_days": 20,
    },
    "fii_selloff": {
        "name": "FII Mass Selloff",
        "description": "Foreign institutions exit India "
                       "aggressively. Rupee under pressure.",
        "market_return": -0.20,
        "volatility_multiplier": 2.0,
        "duration_days": 60,
    },
}


def run_scenario(
    returns: pd.DataFrame,
    scenario_key: str,
    weights: dict = None
) -> dict:
    """
    Simulate how the portfolio would perform under a stress scenario.
    Uses historical volatility scaled by scenario multiplier.
    """
    if scenario_key not in SCENARIOS:
        raise ValueError(
            f"Unknown scenario: {scenario_key}. "
            f"Available: {list(SCENARIOS.keys())}"
        )

    scenario = SCENARIOS[scenario_key]
    tickers = list(returns.columns)

    # Equal weights if none provided
    if weights is None:
        w = np.array([1 / len(tickers)] * len(tickers))
    else:
        w = np.array([weights.get(t, 0.0) for t in tickers])
        w = w / w.sum()

    # Portfolio returns
    port_returns = returns[tickers].dot(w)

    # Scale volatility by scenario multiplier
    scaled_vol = port_returns.std() * scenario["volatility_multiplier"]

    # Simulate stressed returns using Monte Carlo
    np.random.seed(42)
    n_days = scenario["duration_days"]
    daily_market_drift = scenario["market_return"] / n_days

    simulated = np.random.normal(
        loc=daily_market_drift,
        scale=scaled_vol,
        size=n_days
    )
    simulated_series = pd.Series(simulated)

    # Compute stressed metrics
    stressed_var = compute_var(simulated_series, confidence=0.95)
    stressed_cvar = compute_cvar(simulated_series, confidence=0.95)
    cumulative_return = float(np.prod(1 + simulated) - 1)
    max_single_day_loss = float(simulated.min())

    # Compare to normal VaR
    normal_var = compute_var(port_returns, confidence=0.95)

    return {
        "scenario": scenario["name"],
        "description": scenario["description"],
        "duration_days": n_days,
        "assumed_market_return_%": round(
            scenario["market_return"] * 100, 1
        ),
        "volatility_multiplier": scenario["volatility_multiplier"],
        "stressed_var_95_%": round(stressed_var * 100, 3),
        "stressed_cvar_95_%": round(stressed_cvar * 100, 3),
        "normal_var_95_%": round(normal_var * 100, 3),
        "var_deterioration_%": round(
            (stressed_var - normal_var) * 100, 3
        ),
        "simulated_cumulative_return_%": round(
            cumulative_return * 100, 2
        ),
        "worst_single_day_%": round(
            max_single_day_loss * 100, 2
        ),
    }


def run_all_scenarios(
    returns: pd.DataFrame,
    weights: dict = None
) -> dict:
    """Run all stress scenarios and return combined results."""
    results = {}
    for key in SCENARIOS:
        try:
            results[key] = run_scenario(returns, key, weights)
        except Exception as e:
            results[key] = {"error": str(e)}
    return results