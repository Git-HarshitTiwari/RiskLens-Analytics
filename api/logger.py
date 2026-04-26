import logging
import sys
import time
from pythonjsonlogger import jsonlogger
from functools import wraps


def setup_logger(name: str = "quant_risk") -> logging.Logger:
    """
    Creates a structured JSON logger.
    JSON logs are parseable by cloud logging services
    (AWS CloudWatch, GCP Logging, Render logs).
    """
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    # Console handler — outputs to terminal
    handler = logging.StreamHandler(sys.stdout)

    # JSON formatter — makes logs machine-readable
    formatter = jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


# Single shared logger instance — import this everywhere
logger = setup_logger()


def log_computation_time(func_name: str, duration_seconds: float, extra: dict = None):
    """Log how long a computation took — important for risk engine calls."""
    data = {
        "event": "computation_complete",
        "function": func_name,
        "duration_seconds": round(duration_seconds, 3),
    }
    if extra:
        data.update(extra)
    logger.info("Computation complete", extra=data)


def log_request(method: str, path: str, status_code: int, duration_ms: float):
    """Log every API request with timing."""
    logger.info("API request", extra={
        "event": "api_request",
        "method": method,
        "path": path,
        "status_code": status_code,
        "duration_ms": round(duration_ms, 2)
    })


def log_error(error: Exception, context: str = ""):
    """Log errors with full context."""
    logger.error("Error occurred", extra={
        "event": "error",
        "error_type": type(error).__name__,
        "error_message": str(error),
        "context": context
    })


def timed(func):
    """
    Decorator — automatically logs computation time for any function.
    Usage: @timed above any function definition.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start
        log_computation_time(func.__name__, duration)
        return result
    return wrapper