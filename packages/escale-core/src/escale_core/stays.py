"""What a stay's detail shows, read from its JSON-LD (S017a).

A stay is a schema.org ``LodgingReservation`` whose ``reservationFor`` is a
``LodgingBusiness``; KItinerary adds the links to manage the booking that it finds in a
confirmation (``potentialAction``, ``modifyReservationUrl``).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

from escale_core.extraction import ExtractedReservation

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
