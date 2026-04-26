import pandas as pd
import numpy as np
from datetime import datetime, date


# ─── NSE Circuit Breaker Rules ─────────────────────────────────────────────────
# NSE applies these price bands on individual stocks
CIRCUIT_LIMITS = [0.02, 0.05, 0.10, 0.20]  # 2%, 5%, 10%, 20%

# NSE F&O expiry — every last Thursday of the month
# Index options expire monthly, stock options expire monthly


def detect_circuit_breakers(
    returns: pd.DataFrame,
    limit: float = 0.10
) -> pd.DataFrame:
    """
    Flag trading days where a stock hit circuit breaker limits.
    Returns a boolean DataFrame — True means circuit was hit that day.

    NSE circuit breakers:
    - Lower circuit: price fell by limit% → trading halted
    - Upper circuit: price rose by limit% → trading halted
    """
    upper_circuit = returns >= limit
    lower_circuit = returns <= -limit
    circuit_hit = upper_circuit | lower_circuit
    return circuit_hit


def get_circuit_breaker_summary(returns: pd.DataFrame) -> pd.DataFrame:
    """
    Summary of how many times each stock hit circuits.
    Useful risk signal — frequent circuit hits = high volatility/illiquidity.
    """
    circuits = detect_circuit_breakers(returns)
    summary = pd.DataFrame({
        "circuit_hits_total": circuits.sum(),
        "upper_circuits": (returns >= 0.10).sum(),
        "lower_circuits": (returns <= -0.10).sum(),
        "circuit_hit_rate_%": (circuits.sum() / len(returns) * 100).round(2)
    })
    return summary


# ─── F&O Expiry Detection ──────────────────────────────────────────────────────

def get_expiry_thursdays(
    start_date: str,
    end_date: str
) -> list[date]:
    """
    Get all NSE F&O expiry Thursdays in a date range.
    NSE monthly expiry = last Thursday of each month.
    """
    start = pd.Timestamp(start_date)
    end = pd.Timestamp(end_date)

    expiry_dates = []
    current = start

    while current <= end:
        # Get all Thursdays in the current month
        month_start = current.replace(day=1)
        month_end = (month_start + pd.offsets.MonthEnd(1))

        thursdays = pd.date_range(
            start=month_start,
            end=month_end,
            freq="W-THU"
        )

        if len(thursdays) > 0:
            last_thursday = thursdays[-1]
            if start <= last_thursday <= end:
                expiry_dates.append(last_thursday.date())

        current = month_start + pd.offsets.MonthBegin(1)

    return expiry_dates


def flag_expiry_weeks(
    returns: pd.DataFrame,
    start_date: str = None,
    end_date: str = None
) -> pd.Series:
    """
    Flag rows (trading days) that fall in an F&O expiry week.
    Returns boolean Series aligned with returns index.
    Expiry week = Monday to Thursday of expiry week.
    """
    if start_date is None:
        start_date = str(returns.index[0].date())
    if end_date is None:
        end_date = str(returns.index[-1].date())

    expiry_thursdays = get_expiry_thursdays(start_date, end_date)

    expiry_weeks = set()
    for thursday in expiry_thursdays:
        thursday_ts = pd.Timestamp(thursday)
        # Flag Mon-Thu of that week
        for i in range(4):
            day = thursday_ts - pd.Timedelta(days=3 - i)
            expiry_weeks.add(day.date())

    is_expiry_week = pd.Series(
        [d.date() in expiry_weeks for d in returns.index],
        index=returns.index,
        name="is_expiry_week"
    )
    return is_expiry_week


def expiry_week_volatility_premium(
    returns: pd.DataFrame,
    expiry_flags: pd.Series
) -> pd.DataFrame:
    """
    Compare average volatility during expiry weeks vs normal weeks.
    Quantifies the F&O expiry effect on each stock.
    """
    results = []
    for ticker in returns.columns:
        r = returns[ticker].dropna()
        expiry_mask = expiry_flags.reindex(r.index).fillna(False)

        expiry_vol = r[expiry_mask].std() * np.sqrt(252)
        normal_vol = r[~expiry_mask].std() * np.sqrt(252)
        premium = ((expiry_vol - normal_vol) / normal_vol * 100
                   if normal_vol > 0 else 0)

        results.append({
            "ticker": ticker,
            "expiry_week_vol": round(expiry_vol, 4),
            "normal_week_vol": round(normal_vol, 4),
            "expiry_premium_%": round(premium, 2)
        })

    return pd.DataFrame(results).set_index("ticker")


# ─── India VIX Analysis ────────────────────────────────────────────────────────

def classify_market_regime(vix_series: pd.Series) -> pd.Series:
    """
    Classify market stress regime based on India VIX levels.
    India VIX interpretation (similar to CBOE VIX):
    - < 15  : Low fear, calm market
    - 15-20 : Normal volatility
    - 20-25 : Elevated anxiety
    - > 25  : High fear / stress
    - > 30  : Extreme fear (crisis territory)
    """
    def classify(vix):
        if pd.isna(vix):
            return "Unknown"
        elif vix < 15:
            return "Calm"
        elif vix < 20:
            return "Normal"
        elif vix < 25:
            return "Elevated"
        elif vix < 30:
            return "High Fear"
        else:
            return "Extreme Fear"

    return vix_series.apply(classify)


def vix_asset_correlation(
    returns: pd.DataFrame,
    vix_returns: pd.Series
) -> pd.Series:
    """
    Correlation of each asset's returns with India VIX returns.
    Negative correlation = asset falls when VIX spikes (typical).
    Near-zero or positive = potential hedge / defensive asset.
    """
    correlations = {}
    for ticker in returns.columns:
        aligned = pd.concat(
            [returns[ticker], vix_returns], axis=1
        ).dropna()
        if len(aligned) > 10:
            corr = aligned.iloc[:, 0].corr(aligned.iloc[:, 1])
            correlations[ticker] = round(corr, 4)
        else:
            correlations[ticker] = None

    return pd.Series(correlations, name="vix_correlation")


# ─── INR/USD FX Impact ─────────────────────────────────────────────────────────

def fx_sensitivity(
    returns: pd.DataFrame,
    inr_returns: pd.Series
) -> pd.DataFrame:
    """
    Measure each stock's sensitivity to INR/USD moves.

    IT stocks (TCS, Infy, Wipro) earn in USD → benefit from INR weakness
    Import-heavy sectors (Oil, Auto) hurt by INR weakness

    Returns regression coefficient: positive = benefits from INR depreciation
    """
    from scipy import stats

    results = []
    for ticker in returns.columns:
        aligned = pd.concat(
            [returns[ticker], inr_returns], axis=1
        ).dropna()

        if len(aligned) > 30:
            slope, intercept, r_value, p_value, _ = stats.linregress(
                aligned.iloc[:, 1],
                aligned.iloc[:, 0]
            )
            results.append({
                "ticker": ticker,
                "fx_sensitivity": round(slope, 4),
                "r_squared": round(r_value ** 2, 4),
                "p_value": round(p_value, 4),
                "significant": p_value < 0.05
            })
        else:
            results.append({
                "ticker": ticker,
                "fx_sensitivity": None,
                "r_squared": None,
                "p_value": None,
                "significant": False
            })

    return pd.DataFrame(results).set_index("ticker")