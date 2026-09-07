from datetime import UTC, datetime
from zoneinfo import ZoneInfo


def start_of_today_utc(timezone_name: str) -> datetime:
    """Midnight in the given timezone, converted to UTC (PRD rule: store UTC, display local tz)."""
    tz = ZoneInfo(timezone_name)
    now_local = datetime.now(tz)
    start_local = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
    return start_local.astimezone(UTC)


def now_in_timezone(timezone_name: str) -> datetime:
    return datetime.now(ZoneInfo(timezone_name))
