"""
Timezone utilities for the application
Uses Australia/Sydney timezone by default
"""
from datetime import datetime
from zoneinfo import ZoneInfo
from app.core.config import settings


def get_timezone() -> ZoneInfo:
    """Get the configured timezone"""
    return ZoneInfo(settings.TIMEZONE)


def now() -> datetime:
    """Get current datetime in the configured timezone (Australia/Sydney)"""
    return datetime.now(get_timezone())


def now_naive() -> datetime:
    """
    Get current datetime in the configured timezone as a naive datetime.
    Useful for database columns that don't store timezone info.
    """
    return datetime.now(get_timezone()).replace(tzinfo=None)


def utc_to_local(utc_dt: datetime) -> datetime:
    """Convert UTC datetime to local timezone"""
    if utc_dt is None:
        return None
    if utc_dt.tzinfo is None:
        utc_dt = utc_dt.replace(tzinfo=ZoneInfo("UTC"))
    return utc_dt.astimezone(get_timezone())


def local_to_utc(local_dt: datetime) -> datetime:
    """Convert local datetime to UTC"""
    if local_dt is None:
        return None
    if local_dt.tzinfo is None:
        local_dt = local_dt.replace(tzinfo=get_timezone())
    return local_dt.astimezone(ZoneInfo("UTC"))
