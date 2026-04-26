from sqlalchemy import (
    Column, String, Float, DateTime, Integer,
    create_engine, text
)
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
from config.settings import settings

Base = declarative_base()


class RiskMetricRecord(Base):
    """
    Stores computed risk metrics for each asset.
    Every time the risk engine runs, results are persisted here.
    This means the dashboard can load historical computations
    instantly without recomputing from scratch.
    """
    __tablename__ = "risk_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(30), nullable=False, index=True)
    computed_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Core risk metrics
    var_95 = Column(Float)
    cvar_95 = Column(Float)
    sharpe = Column(Float)
    sortino = Column(Float)
    calmar = Column(Float)
    max_drawdown = Column(Float)
    annualized_vol = Column(Float)
    beta_vs_nifty = Column(Float)

    # Metadata
    period_years = Column(Integer, default=1)
    data_start = Column(String(20))
    data_end = Column(String(20))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "ticker": self.ticker,
            "computed_at": str(self.computed_at),
            "var_95": self.var_95,
            "cvar_95": self.cvar_95,
            "sharpe": self.sharpe,
            "sortino": self.sortino,
            "calmar": self.calmar,
            "max_drawdown": self.max_drawdown,
            "annualized_vol": self.annualized_vol,
            "beta_vs_nifty": self.beta_vs_nifty,
            "period_years": self.period_years,
            "data_start": self.data_start,
            "data_end": self.data_end,
        }


class PortfolioSnapshotRecord(Base):
    """
    Stores portfolio-level summary snapshots.
    Useful for tracking how portfolio risk evolves over time.
    """
    __tablename__ = "portfolio_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    computed_at = Column(DateTime, default=datetime.utcnow, index=True)

    total_return = Column(Float)
    portfolio_var = Column(Float)
    portfolio_cvar = Column(Float)
    portfolio_sharpe = Column(Float)
    portfolio_sortino = Column(Float)
    portfolio_max_drawdown = Column(Float)
    portfolio_vol = Column(Float)
    num_assets = Column(Integer)
    data_start = Column(String(20))
    data_end = Column(String(20))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "computed_at": str(self.computed_at),
            "total_return": self.total_return,
            "portfolio_var": self.portfolio_var,
            "portfolio_cvar": self.portfolio_cvar,
            "portfolio_sharpe": self.portfolio_sharpe,
            "portfolio_sortino": self.portfolio_sortino,
            "portfolio_max_drawdown": self.portfolio_max_drawdown,
            "portfolio_vol": self.portfolio_vol,
            "num_assets": self.num_assets,
            "data_start": self.data_start,
            "data_end": self.data_end,
        }


# ── Database Connection ────────────────────────────────────────────────────────

def get_engine():
    """Create SQLAlchemy engine from settings."""
    return create_engine(
        settings.database_url,
        pool_pre_ping=True,       # verify connection before using
        pool_size=5,
        max_overflow=10
    )


def get_session():
    """Get a database session — used in API routes."""
    engine = get_engine()
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def init_db():
    """
    Create all tables if they don't exist.
    Called once on app startup.
    Safe to call multiple times — won't recreate existing tables.
    """
    engine = get_engine()
    Base.metadata.create_all(bind=engine)


def check_db_connection() -> bool:
    """Health check — verify DB is reachable."""
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False