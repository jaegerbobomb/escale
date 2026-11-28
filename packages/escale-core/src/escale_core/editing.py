"""What the editors share (S017b, S029a): local date-times and plain text fields."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from escale_core.importer import parse_datetime


def local_moment(day: str, time: str, original: object) -> datetime | None:
    """``day`` at ``time`` in the zone of ``original`` (the stored value), if valid: its
    ``timezone`` when it has one, else its UTC offset; with no stored value (a booking
    added by hand, S018), the device's offset on that day."""
    try:
        naive = datetime.strptime(f"{day.strip()} {time.strip()}", "%Y-%m-%d %H:%M")
    except ValueError:
        return None
    zone = original.get("timezone") if isinstance(original, Mapping) else None
    try:
        if isinstance(zone, str):
            return naive.replace(tzinfo=ZoneInfo(zone))
    except (ZoneInfoNotFoundError, ValueError):
        pass
    before = parse_datetime(original)
    if before is None:
        return naive.astimezone()
    return naive.replace(tzinfo=before.tzinfo)


def with_moment(moment: datetime, original: object) -> object:
    """``moment`` in the form ``original`` had: KItinerary's object, or a string."""
    if isinstance(original, Mapping):
        return {**original, "@value": moment.isoformat()}
    return moment.isoformat()


def put_text(target: dict[str, Any], key: str, value: str) -> None:
    """Set ``key`` to ``value``, or remove it when ``value`` is blank."""
    if value.strip():
        target[key] = value.strip()
    else:
        target.pop(key, None)
