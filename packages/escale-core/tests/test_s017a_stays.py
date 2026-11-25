"""S017a — what a stay's detail shows (core part)."""

from __future__ import annotations

from typing import Any

import pytest

from escale_core.importer import reservation_from_jsonld
from escale_core.stays import address, cancelled, contact, manage_link


def stay(**extra: Any) -> Any:
    place = {
        "@type": "LodgingBusiness",
        "name": "Hotel Test",
        "address": {
            "@type": "PostalAddress",
            "streetAddress": "1 Test Street",
            "postalCode": "WC1V 7BD",
            "addressLocality": "London",
            "addressRegion": "England",
            "addressCountry": "GB",
        },
        "telephone": "+44 20 7946 0000",
        "email": "desk@example.com",
        "url": "https://example.com/hotel",
    }
    element = {"@type": "LodgingReservation", "reservationFor": place, **extra}
    r = reservation_from_jsonld(element, ())
    assert r is not None
    return r


def test_address_is_one_line_from_street_to_country() -> None:
    assert address(stay()) == "1 Test Street, WC1V 7BD London, England, GB"


def test_address_with_a_country_object() -> None:
    r = stay()
    r.raw["reservationFor"]["address"] = {
        "addressLocality": "Paris",
        "addressCountry": {"@type": "Country", "name": "France"},
    }
    assert address(r) == "Paris, France"


def test_contact() -> None:
    c = contact(stay())
    assert (c.telephone, c.email, c.website) == (
        "+44 20 7946 0000",
        "desk@example.com",
        "https://example.com/hotel",
    )


@pytest.mark.parametrize(
    ("extra", "expected"),
    [
        (
            {
                "potentialAction": {
                    "@type": "UpdateAction",
                    "target": "https://secure.booking.com/x",
                }
            },
            ("Booking.com", "https://secure.booking.com/x"),
        ),
        (
            {
                "potentialAction": [
                    {"@type": "CancelAction", "target": "https://www.airbnb.fr/cancel"},
                    {
                        "@type": "ViewAction",
                        "target": {"urlTemplate": "https://www.airbnb.fr/trips/1"},
                    },
                ]
            },
            ("Airbnb", "https://www.airbnb.fr/trips/1"),
        ),
        (
            {"modifyReservationUrl": "https://hotel.example.org/manage"},
            ("hotel.example.org", "https://hotel.example.org/manage"),
        ),
        (
            {"url": "https://www.booking.com/mybooking"},
            ("Booking.com", "https://www.booking.com/mybooking"),
        ),
        ({"url": "javascript:alert(1)"}, None),
        ({}, None),
    ],
    ids=["update-action", "view-action-template", "modify-url", "url", "not-http", "none"],
)
def test_manage_link(extra: dict[str, Any], expected: tuple[str, str] | None) -> None:
    link = manage_link(stay(**extra))
    assert (None if link is None else (link.site, link.url)) == expected


def test_cancelled() -> None:
    assert cancelled(stay(reservationStatus="http://schema.org/ReservationCancelled"))
    assert not cancelled(stay(reservationStatus="http://schema.org/ReservationConfirmed"))
    assert not cancelled(stay())
