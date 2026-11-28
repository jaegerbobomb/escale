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


# --- places and names (S017b, S030): KDE Itinerary's FormPlaceEditorDelegate ---

ADDRESS = {
    "street": "streetAddress",
    "postal_code": "postalCode",
    "city": "addressLocality",
    "region": "addressRegion",
}
PLACE_FIELDS = (*ADDRESS, "country", "latitude", "longitude")
"""An address as the editors show it; a prefix (``departure_``) tells two places apart."""


def _m(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def place_fields(place: object, prefix: str = "") -> dict[str, str]:
    """The address and coordinates of a schema.org place, as the editor's fields."""
    a, geo = _m(_m(place).get("address")), _m(_m(place).get("geo"))
    country = a.get("addressCountry")
    if isinstance(country, Mapping):  # a schema.org Country
        country = country.get("name")
    found = {prefix + field: _text(a.get(key)) for field, key in ADDRESS.items()}
    found[prefix + "country"] = _text(country)
    for key in ("latitude", "longitude"):
        found[prefix + key] = "" if geo.get(key) is None else str(geo[key])
    return found


def coordinates(latitude: str, longitude: str) -> tuple[float, float] | bool | None:
    """The coordinates; ``None`` when both are empty, ``False`` when they are not valid."""
    if not latitude.strip() and not longitude.strip():
        return None
    try:
        lat, lon = float(latitude), float(longitude)
    except ValueError:
        return False
    return (lat, lon) if -90 <= lat <= 90 and -180 <= lon <= 180 else False


def write_place(
    place: dict[str, Any], values: Mapping[str, str], changed: set[str], prefix: str = ""
) -> None:
    """Write the changed address and coordinate fields of ``values`` into ``place``."""
    a = dict(_m(place.get("address"))) or {"@type": "PostalAddress"}
    for field, key in (*ADDRESS.items(), ("country", "addressCountry")):
        if prefix + field in changed:
            put_text(a, key, values[prefix + field])
    if changed & {prefix + f for f in (*ADDRESS, "country")}:
        place["address"] = a
    if changed & {prefix + "latitude", prefix + "longitude"}:
        found = coordinates(values[prefix + "latitude"], values[prefix + "longitude"])
        if isinstance(found, tuple):
            place["geo"] = {"@type": "GeoCoordinates", "latitude": found[0], "longitude": found[1]}
        else:
            place.pop("geo", None)


def names(value: object) -> str:
    """``underName``: one person or several, as ``Ada, Bob``."""
    people = value if isinstance(value, list) else [value]
    return ", ".join(n for p in people if (n := _text(_m(p).get("name"))))


def put_names(raw: dict[str, Any], text: str) -> None:
    people = [{"@type": "Person", "name": n.strip()} for n in text.split(",") if n.strip()]
    if people:
        raw["underName"] = people[0] if len(people) == 1 else people
    else:
        raw.pop("underName", None)
