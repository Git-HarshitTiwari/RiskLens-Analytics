import io
import csv
import time
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from api.auth import get_current_user
from api.logger import logger, log_computation_time
from engine.data_fetcher import load_nifty50
from engine.risk_metrics import compute_all_metrics
from engine.portfolio import compute_portfolio_summary
from config.settings import settings

router = APIRouter(prefix="/export", tags=["Export"])


@router.get("/csv/metrics")
def export_metrics_csv(
    period_years: int = 1,
    user: dict = Depends(get_current_user)
):
    """
    Export risk metrics as CSV file.
    Protected — requires Bearer token.
    """
    start = time.time()
    try:
        prices, returns = load_nifty50(period_years=period_years)
        metrics = compute_all_metrics(
            prices, returns,
            confidence=settings.var_confidence,
            risk_free_rate=settings.risk_free_rate
        )

        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            "Ticker", "VaR 95%", "CVaR 95%", "Sharpe",
            "Sortino", "Calmar", "Max Drawdown %",
            "Annualized Vol %", "Beta vs Nifty"
        ])

        # Rows
        for ticker, row in metrics.iterrows():
            writer.writerow([
                ticker,
                row.get("var_95", ""),
                row.get("cvar_95", ""),
                row.get("sharpe", ""),
                row.get("sortino", ""),
                row.get("calmar", ""),
                row.get("max_drawdown_%", ""),
                row.get("annualized_vol_%", ""),
                row.get("beta_vs_nifty", ""),
            ])

        output.seek(0)
        log_computation_time("export_metrics_csv", time.time() - start)

        return StreamingResponse(
            io.BytesIO(output.getvalue().encode()),
            media_type="text/csv",
            headers={
                "Content-Disposition":
                    "attachment; filename=nifty50_risk_metrics.csv"
            }
        )

    except Exception as e:
        logger.error("CSV export failed", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/csv/portfolio")
def export_portfolio_csv(
    period_years: int = 1,
    user: dict = Depends(get_current_user)
):
    """Export portfolio summary as CSV."""
    try:
        prices, returns = load_nifty50(period_years=period_years)
        summary = compute_portfolio_summary(prices, returns)

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Metric", "Value"])
        for k, v in summary.items():
            writer.writerow([k, v])

        output.seek(0)

        return StreamingResponse(
            io.BytesIO(output.getvalue().encode()),
            media_type="text/csv",
            headers={
                "Content-Disposition":
                    "attachment; filename=portfolio_summary.csv"
            }
        )
    except Exception as e:
        logger.error("Portfolio CSV export failed", extra={
            "error": str(e)
        })
        raise HTTPException(status_code=500, detail=str(e))