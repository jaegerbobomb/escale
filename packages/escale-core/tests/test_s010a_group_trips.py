"""S010a — Group reservations into trips."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from escale_core.extraction import ExtractedReservation
from escale_core.importer import reservation_from_jsonld
from escale_core.trips import Trip, active_trip, group

scenarios("S010a.feature")

TZ = "+02:00"


def at(day: str, time: str) -> str:
    return f"2026-07-{day}T{time}:00{TZ}"


def place(kind: str, name: str, town: str) -> dict[str, Any]:
    return {
        "@type": kind,
        "name": name,
        "address": {"@type": "PostalAddress", "addressLocality": town},
    }


def train(
    ref: str, dep: tuple[str, str], arr: tuple[str, str], leave: str, reach: str
) -> dict[str, Any]:
    return {
        "@type": "TrainReservation",
        "reservationNumber": ref,
        "reservationFor": {
            "@type": "TrainTrip",
            "departureStation": place("TrainStation", *dep),
            "arrivalStation": place("TrainStation", *arr),
            "departureTime": leave,
            "arrivalTime": reach,
        },
    }


def hotel(ref: str, town: str, checkin: str, checkout: str) -> dict[str, Any]:
    return {
        "@type": "LodgingReservation",
        "reservationNumber": ref,
        "reservationFor": place("LodgingBusiness", f"Hotel {town}", town),
        "checkinTime": checkin,
        "checkoutTime": checkout,
    }


def restaurant(name: str, start: str) -> dict[str, Any]:
    return {
        "@type": "FoodEstablishmentReservation",
        "startTime": start,
        "reservationFor": place("FoodEstablishment", name, "Paris"),
    }


def concert(name: str, start: str) -> dict[str, Any]:
    return {
        "@type": "EventReservation",
        "reservationFor": {
            "@type": "Event",
            "name": name,
            "startDate": start,
            "location": place("Place", "Le Trianon", "Paris"),
        },
    }


PARIS = ("Paris Gare du Nord", "Paris")
LONDON = ("London St Pancras", "London")


def reservations(*elements: dict[str, Any]) -> list[ExtractedReservation]:
    found = [reservation_from_jsonld(e, ("doc",)) for e in elements]
    assert all(r is not None for r in found)
    return [r for r in found if r is not None]


@dataclass
class World:
    reservations: list[ExtractedReservation] = field(default_factory=list)
    trips: list[Trip] = field(default_factory=list)
    now: datetime | None = None


@pytest.fixture
def world() -> World:
    return World()


@given(
    "a train from Paris to London on 8 July, a hotel in London from 8 to 10 July, "
    "and a train back on 10 July"
)
def london_trip(world: World) -> None:
    world.reservations = reservations(
        train("T1", PARIS, LONDON, at("08", "08:01"), at("08", "09:30")),
        hotel("H1", "London", at("08", "15:00"), at("10", "11:00")),
        train("T2", LONDON, PARIS, at("10", "17:04"), at("10", "20:30")),
    )


@given("a restaurant booking at 19:30 and a concert ticket at 21:00 in Paris on the same evening")
def evening_out(world: World) -> None:
    world.reservations = reservations(
        restaurant("Le Servan", at("18", "19:30")),
        concert("Aphex Twin live", at("18", "21:00")),
    )


@given("a return train to Lyon on 1 July and a return train to Lille on 8 July")
def two_journeys(world: World) -> None:
    lyon, lille = ("Lyon Part-Dieu", "Lyon"), ("Lille Europe", "Lille")
    world.reservations = reservations(
        train("L1", PARIS, lyon, at("01", "07:00"), at("01", "09:00")),
        train("L2", lyon, PARIS, at("01", "19:00"), at("01", "21:00")),
        train("N1", PARIS, lille, at("08", "08:00"), at("08", "09:00")),
        train("N2", lille, PARIS, at("08", "18:00"), at("08", "19:00")),
    )


@given("a trip from 8 to 10 July and another from 20 to 22 July")
def two_trips(world: World) -> None:
    london_trip(world)
    world.reservations += reservations(
        train("T3", PARIS, LONDON, at("20", "08:01"), at("20", "09:30")),
        train("T4", LONDON, PARIS, at("22", "17:04"), at("22", "20:30")),
    )
    world.trips = group(world.reservations)


@when("the reservations are grouped")
def grouped(world: World) -> None:
    world.trips = group(world.reservations)


@when(parsers.parse("it is {day:d} July"))
def it_is(world: World, day: int) -> None:
    world.now = datetime.fromisoformat(f"2026-07-{day:02d}T12:00:00{TZ}")


@then(parsers.parse('they form one trip named "{name}"'))
def one_trip(world: World, name: str) -> None:
    [trip] = world.trips
    assert (trip.kind, trip.name) == ("trip", name)
    assert len(trip.reservations) == 3


@then("they form one outing")
def one_outing(world: World) -> None:
    [trip] = world.trips
    assert trip.kind == "outing"
    assert trip.name == "Le Servan + Aphex Twin live"


@then(parsers.parse('they form two trips, "{first}" and "{second}"'))
def two_trips_named(world: World, first: str, second: str) -> None:
    assert [(t.kind, t.name) for t in world.trips] == [("trip", first), ("trip", second)]


@then("the active trip is the first one")
def first_is_active(world: World) -> None:
    assert world.now is not None
    assert active_trip(world.trips, world.now) is world.trips[0]


# --- details ---


def test_reservations_are_in_time_order_inside_a_trip() -> None:
    found = reservations(
        train("T2", LONDON, PARIS, at("10", "17:04"), at("10", "20:30")),
        hotel("H1", "London", at("08", "15:00"), at("10", "11:00")),
        train("T1", PARIS, LONDON, at("08", "08:01"), at("08", "09:30")),
    )
    [trip] = group(found)
    assert [r.reference for r in trip.reservations] == ["T1", "H1", "T2"]
    assert trip.start == datetime.fromisoformat(at("08", "08:01"))
    assert trip.end == datetime.fromisoformat(at("10", "20:30"))


def test_stay_without_lodging_holds_until_the_way_back() -> None:
    """Out on Friday, back on Sunday, no hotel booked: still one trip."""
    found = reservations(
        train("A", PARIS, LONDON, at("03", "18:00"), at("03", "19:30")),
        train("B", LONDON, PARIS, at("05", "17:00"), at("05", "20:30")),
    )
    assert [t.name for t in group(found)] == ["London"]


def test_next_trip_is_active_when_none_is_in_progress() -> None:
    world = World()
    two_trips(world)
    now = datetime.fromisoformat(f"2026-07-15T12:00:00{TZ}")
    assert active_trip(world.trips, now) is world.trips[1]
    assert active_trip(world.trips, datetime.fromisoformat(f"2026-08-01T00:00:00{TZ}")) is None


def test_reservations_without_time_are_left_out() -> None:
    found = reservations(
        {"@type": "EventReservation", "reservationFor": {"@type": "Event", "name": "X"}}
    )
    assert group(found) == []
