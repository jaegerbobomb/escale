"""S035 — the "My trips" list: sections, filter and search."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pytest
from pytest_bdd import given, scenarios, then, when

from escale_core.extraction import ExtractedReservation
from escale_core.importer import reservation_from_jsonld
from escale_core.trips import Trip, browse, group, matches

scenarios("S035.feature")

NOW = datetime.fromisoformat("2026-07-01T12:00:00+02:00")


def _r(element: dict[str, Any]) -> ExtractedReservation:
    r = reservation_from_jsonld(element, ())
    assert r is not None
    return r


def stay(ref: str, town: str, checkin: str, checkout: str) -> ExtractedReservation:
    return _r(
        {
            "@type": "LodgingReservation",
            "reservationNumber": ref,
            "reservationFor": {
                "@type": "LodgingBusiness",
                "name": f"Hotel {town}",
                "address": {"@type": "PostalAddress", "addressLocality": town},
            },
            "checkinTime": f"{checkin}T15:00:00+02:00",
            "checkoutTime": f"{checkout}T11:00:00+02:00",
        }
    )


def dinner(name: str, day: str) -> ExtractedReservation:
    return _r(
        {
            "@type": "FoodEstablishmentReservation",
            "reservationFor": {"@type": "Restaurant", "name": name},
            "startTime": f"{day}T19:30:00+02:00",
        }
    )


@pytest.fixture
def world() -> dict[str, Any]:
    return {}


@given("two trips and one outing")
def two_and_one(world: dict[str, Any]) -> None:
    world["trips"] = group(
        [
            stay("L1", "Lisbon", "2026-08-22", "2026-08-24"),
            dinner("Chez Paul", "2026-07-18"),
            stay("B1", "Berlin", "2026-09-15", "2026-09-18"),
        ]
    )


@given('a trip holding the booking reference "QX7RTB"')
def with_reference(world: dict[str, Any]) -> None:
    world["trips"] = group(
        [
            stay("QX7RTB", "Lisbon", "2026-08-22", "2026-08-24"),
            stay("B1", "Berlin", "2026-09-15", "2026-09-18"),
        ]
    )


@when('the user chooses "Outings"')
def outings(world: dict[str, Any]) -> None:
    world["listed"] = browse(world["trips"], NOW, kind="outing")


@when('the user searches "QX7RTB"')
def search(world: dict[str, Any]) -> None:
    world["listed"] = browse(world["trips"], NOW, query="QX7RTB")


def names(listed: list[tuple[str, list[Trip]]]) -> list[str]:
    return [t.name for _, trips in listed for t in trips]


@then("only the outing is listed")
def only_outing(world: dict[str, Any]) -> None:
    assert names(world["listed"]) == ["Chez Paul"]


@then("the trip holding it is listed")
def holding_listed(world: dict[str, Any]) -> None:
    assert names(world["listed"]) == ["Lisbon"]


# --- details ---


def test_upcoming_first_then_past_by_year_most_recent_first() -> None:
    trips = group(
        [
            stay("P1", "Geneva", "2026-03-06", "2026-03-08"),
            stay("P2", "Barcelona", "2025-01-05", "2025-01-09"),
            stay("P3", "Rome", "2025-10-01", "2025-10-04"),
            stay("U2", "Berlin", "2026-09-15", "2026-09-18"),
            stay("U1", "Lisbon", "2026-08-22", "2026-08-24"),
        ]
    )
    listed = browse(trips, NOW)
    assert [title for title, _ in listed] == ["Upcoming", "2026", "2025"]
    assert names(listed) == ["Lisbon", "Berlin", "Geneva", "Rome", "Barcelona"]


def test_a_trip_in_progress_is_upcoming() -> None:
    [now_trip] = group([stay("N1", "Porto", "2026-06-30", "2026-07-02")])
    assert browse([now_trip], NOW) == [("Upcoming", [now_trip])]


def test_trips_only() -> None:
    trips = group(
        [stay("L1", "Lisbon", "2026-08-22", "2026-08-24"), dinner("Chez Paul", "2026-07-18")]
    )
    assert names(browse(trips, NOW, kind="trip")) == ["Lisbon"]


@pytest.mark.parametrize("query", ["lisbon", "LISBON", "Hotel Lis", "l1", "  lisbon "])
def test_search_names_places_and_references_ignoring_case(query: str) -> None:
    [trip] = group([stay("L1", "Lisbon", "2026-08-22", "2026-08-24")])
    assert matches(trip, query)


def test_search_misses() -> None:
    [trip] = group([stay("L1", "Lisbon", "2026-08-22", "2026-08-24")])
    assert not matches(trip, "berlin")


def test_an_empty_search_matches_everything() -> None:
    [trip] = group([stay("L1", "Lisbon", "2026-08-22", "2026-08-24")])
    assert matches(trip, "")


def test_nothing_matches_no_section() -> None:
    trips = group([stay("L1", "Lisbon", "2026-08-22", "2026-08-24")])
    assert browse(trips, NOW, query="zzz") == []
