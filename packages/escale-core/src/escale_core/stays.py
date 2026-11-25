"""What a stay's detail shows, read from its JSON-LD (S017a).

The editor's fields, their validation and how they are written back are here too
(S017b). A stay is a schema.org ``LodgingReservation`` whose ``reservationFor`` is a
``LodgingBusiness``; KItinerary adds the links to manage the booking that it finds in a
confirmation (``potentialAction``, ``modifyReservationUrl``).
"""

from __future__ import annotations

import copy
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from urllib.parse import urlparse
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from escale_core.extraction import ExtractedReservation
from escale_core.importer import parse_datetime, reservation_from_jsonld

_SITES = {"booking.com": "Booking.com", "airbnb": "Airbnb"}
"""Known booking sites: a host ending in the key, or with the key as one of its labels."""


@dataclass(frozen=True)
class Contact:
    telephone: str | None
    email: str | None
    website: str | None


@dataclass(frozen=True)
class ManageLink:
    site: str
    url: str


def _m(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _place(r: ExtractedReservation) -> Mapping[str, Any]:
    return _m(r.raw.get("reservationFor"))


def address(r: ExtractedReservation) -> str | None:
    """``1 Test Street, WC1V 7BD London, England, GB``: street to country, what is known."""
    a = _m(_place(r).get("address"))
    country = a.get("addressCountry")
    town = " ".join(t for t in (_text(a.get("postalCode")), _text(a.get("addressLocality"))) if t)
    parts = [
        _text(a.get("streetAddress")),
        town or None,
        _text(a.get("addressRegion")),
        _text(_m(country).get("name")) if isinstance(country, Mapping) else _text(country),
    ]
    return ", ".join(p for p in parts if p) or None


def contact(r: ExtractedReservation) -> Contact:
    place = _place(r)
    return Contact(
        telephone=_text(place.get("telephone")),
        email=_text(place.get("email")),
        website=_web(place.get("url")),
    )


def cancelled(r: ExtractedReservation) -> bool:
    status = r.raw.get("reservationStatus")
    return isinstance(status, str) and status.endswith("ReservationCancelled")


def _web(value: object) -> str | None:
    """``value`` if it is an http(s) link: nothing else is opened from imported data."""
    url = _text(value)
    if url is None or urlparse(url).scheme not in ("http", "https"):
        return None
    return url


def _target(action: Mapping[str, Any]) -> str | None:
    target = action.get("target")
    if isinstance(target, Mapping):
        target = target.get("urlTemplate")
    return _web(target)


def _site(url: str) -> str:
    host = (urlparse(url).hostname or "").removeprefix("www.")
    for key, name in _SITES.items():
        if host == key or host.endswith("." + key) or key in host.split("."):
            return name
    return host


def manage_link(r: ExtractedReservation) -> ManageLink | None:
    """Where the booking can be managed: an update or view action, else the booking's URL."""
    raw_actions = r.raw.get("potentialAction")
    actions = raw_actions if isinstance(raw_actions, list) else [raw_actions]
    by_type = {_m(a).get("@type"): _target(_m(a)) for a in actions}
    for url in (
        by_type.get("UpdateAction"),
        _web(r.raw.get("modifyReservationUrl")),
        by_type.get("ViewAction"),
        _web(r.raw.get("url")),
    ):
        if url:
            return ManageLink(_site(url), url)
    return None


# --- editing (S017b) ---


@dataclass(frozen=True)
class StayFields:
    """What the stay editor shows, as text: the fields of KDE Itinerary's ``HotelEditor``."""

    name: str = ""
    street: str = ""
    postal_code: str = ""
    city: str = ""
    region: str = ""
    country: str = ""
    latitude: str = ""
    longitude: str = ""
    check_in_date: str = ""
    """``YYYY-MM-DD``, in the place's own time."""
    check_in_time: str = ""
    """``HH:MM``."""
    check_out_date: str = ""
    check_out_time: str = ""
    description: str = ""
    telephone: str = ""
    email: str = ""
    website: str = ""
    reference: str = ""
    under_name: str = ""


_ADDRESS = {
    "street": "streetAddress",
    "postal_code": "postalCode",
    "city": "addressLocality",
    "region": "addressRegion",
}
_CONTACT = {"telephone": "telephone", "email": "email", "website": "url"}


def _names(value: object) -> str:
    people = value if isinstance(value, list) else [value]
    return ", ".join(n for p in people if (n := _text(_m(p).get("name"))))


def _country(value: object) -> str:
    return (_text(_m(value).get("name")) if isinstance(value, Mapping) else _text(value)) or ""


def fields_of(r: ExtractedReservation) -> StayFields:
    place = _place(r)
    a = _m(place.get("address"))
    geo = _m(place.get("geo"))
    start, end = (parse_datetime(r.raw.get(k)) for k in ("checkinTime", "checkoutTime"))
    return StayFields(
        name=_text(place.get("name")) or "",
        **{field: _text(a.get(key)) or "" for field, key in _ADDRESS.items()},
        country=_country(a.get("addressCountry")),
        latitude="" if geo.get("latitude") is None else str(geo["latitude"]),
        longitude="" if geo.get("longitude") is None else str(geo["longitude"]),
        check_in_date=f"{start:%Y-%m-%d}" if start else "",
        check_in_time=f"{start:%H:%M}" if start else "",
        check_out_date=f"{end:%Y-%m-%d}" if end else "",
        check_out_time=f"{end:%H:%M}" if end else "",
        description=_text(r.raw.get("lodgingUnitDescription")) or "",
        **{field: _text(place.get(key)) or "" for field, key in _CONTACT.items()},
        reference=r.reference or "",
        under_name=_names(r.raw.get("underName")),
    )


def _moment(day: str, time: str, original: object) -> datetime | None:
    """``day`` at ``time`` in the zone of ``original`` (the stored value), if valid."""
    try:
        naive = datetime.strptime(f"{day.strip()} {time.strip()}", "%Y-%m-%d %H:%M")
    except ValueError:
        return None
    zone = _m(original).get("timezone")
    try:
        if isinstance(zone, str):
            return naive.replace(tzinfo=ZoneInfo(zone))
    except (ZoneInfoNotFoundError, ValueError):
        pass
    before = parse_datetime(original)
    return naive.replace(tzinfo=before.tzinfo if before else None)


def _coordinates(f: StayFields) -> tuple[float, float] | bool | None:
    """The coordinates; ``None`` when both are empty, ``False`` when they are not valid."""
    if not f.latitude.strip() and not f.longitude.strip():
        return None
    try:
        lat, lon = float(f.latitude), float(f.longitude)
    except ValueError:
        return False
    return (lat, lon) if -90 <= lat <= 90 and -180 <= lon <= 180 else False


def problems(f: StayFields, r: ExtractedReservation | None = None) -> list[str]:
    """Why the stay cannot be saved, as in KDE Itinerary; empty when it can."""
    raw = r.raw if r is not None else {}
    found = [] if f.name.strip() else ["The name is required."]
    ends = []
    for label, day, time, key in (
        ("check-in", f.check_in_date, f.check_in_time, "checkinTime"),
        ("check-out", f.check_out_date, f.check_out_time, "checkoutTime"),
    ):
        when = _moment(day, time, raw.get(key))
        if not day.strip() or not time.strip():
            found.append(f"The {label} is required.")
        elif when is None:
            found.append(f"The {label} is not a valid date and time.")
        ends.append(when)
    start, end = ends
    if start and end and (start.tzinfo is None) != (end.tzinfo is None):
        start, end = (
            start.replace(tzinfo=start.tzinfo or end.tzinfo),
            end.replace(tzinfo=end.tzinfo or start.tzinfo),
        )
    if start and end and end <= start:
        found.append("The check-out must be after the check-in.")
    if _coordinates(f) is False:
        found.append("The coordinates are not valid.")
    return found


def _when(moment: datetime, original: object) -> object:
    if isinstance(original, Mapping):
        return {**original, "@value": moment.isoformat()}
    return moment.isoformat()


def _put(target: dict[str, Any], key: str, value: str) -> None:
    if value.strip():
        target[key] = value.strip()
    else:
        target.pop(key, None)


def edited(r: ExtractedReservation, f: StayFields) -> ExtractedReservation:
    """``r`` with the editor's fields written into its JSON-LD; untouched fields stay as
    they were. Call only when ``problems(f, r)`` is empty."""
    before = fields_of(r)
    raw = copy.deepcopy(dict(r.raw))
    place = dict(_m(raw.get("reservationFor"))) or {"@type": "LodgingBusiness"}
    a = dict(_m(place.get("address"))) or {"@type": "PostalAddress"}
    changed = {k for k, v in vars(f).items() if v != getattr(before, k)}
    if "name" in changed:
        _put(place, "name", f.name)
    for field, key in _ADDRESS.items():
        if field in changed:
            _put(a, key, getattr(f, field))
    if "country" in changed:
        _put(a, "addressCountry", f.country)
    if changed & {*_ADDRESS, "country"}:
        place["address"] = a
    if changed & {"latitude", "longitude"}:
        coordinates = _coordinates(f)
        if isinstance(coordinates, tuple):
            place["geo"] = {
                "@type": "GeoCoordinates",
                "latitude": coordinates[0],
                "longitude": coordinates[1],
            }
        else:
            place.pop("geo", None)
    for field, key in _CONTACT.items():
        if field in changed:
            _put(place, key, getattr(f, field))
    raw["reservationFor"] = place
    for key, day, time in (
        ("checkinTime", "check_in_date", "check_in_time"),
        ("checkoutTime", "check_out_date", "check_out_time"),
    ):
        if changed & {day, time}:
            moment = _moment(getattr(f, day), getattr(f, time), raw.get(key))
            if moment is not None:
                raw[key] = _when(moment, raw.get(key))
    if "description" in changed:
        _put(raw, "lodgingUnitDescription", f.description)
    if "reference" in changed:
        _put(raw, "reservationNumber", f.reference)
    if "under_name" in changed:
        people = [
            {"@type": "Person", "name": n.strip()} for n in f.under_name.split(",") if n.strip()
        ]
        if people:
            raw["underName"] = people[0] if len(people) == 1 else people
        else:
            raw.pop("underName", None)
    new = reservation_from_jsonld(raw, r.subject_of)
    assert new is not None
    return new
