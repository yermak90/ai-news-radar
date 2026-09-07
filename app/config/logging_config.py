import logging
import sys


def configure_logging(log_level: str = "INFO") -> None:
    """Configure root logging.

    Never logs secrets (tokens/API keys) — callers must not pass them into
    log messages either.
    """
    level = getattr(logging, log_level.upper(), logging.INFO)
    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    root.addHandler(handler)

    # Quiet down noisy third-party libraries by default.
    logging.getLogger("httpx").setLevel(max(level, logging.WARNING))
    logging.getLogger("apscheduler").setLevel(max(level, logging.INFO))
