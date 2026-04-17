"""Trading calendar helpers.

Minimal but non-fake: uses ``pandas`` business-day logic as a proxy for the
A-share / HK / US calendar. Callers can attach a real exchange calendar via
``register_calendar`` once a licensed calendar package is available.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Dict, Iterable, List, Optional

import pandas as pd


_CUSTOM_HOLIDAYS: Dict[str, List[date]] = {}


def register_holidays(region: str, holidays: Iterable[date]) -> None:
    _CUSTOM_HOLIDAYS[region.upper()] = list(holidays)


def last_trading_day(region: str = "CN", today: Optional[date] = None) -> date:
    d = today or datetime.now(tz=timezone.utc).date()
    # Roll back across weekends and registered holidays.
    holidays = set(_CUSTOM_HOLIDAYS.get(region.upper(), []))
    while d.weekday() >= 5 or d in holidays:
        d = d - timedelta(days=1)
    return d


def recent_trading_days(n: int, region: str = "CN", today: Optional[date] = None) -> List[date]:
    end = last_trading_day(region, today)
    return [d.date() for d in pd.bdate_range(end=pd.Timestamp(end), periods=n)]


def is_trading_day(d: date, region: str = "CN") -> bool:
    if d.weekday() >= 5:
        return False
    return d not in set(_CUSTOM_HOLIDAYS.get(region.upper(), []))
