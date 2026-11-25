"""S020 — the current trip as in the mockup: structure checks (the look is validated on
screenshots)."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import flet as ft

from escale_core.importer import reservation_from_jsonld
from escale_core.trips import group
from escale_flet.demo import LONDON_TRIP, LONDON_TRIP_FULL
from escale_flet.testing import texts, walk
from escale_flet.timeline import connection, initials, trip_view

LEAVES = datetime.fromisoformat(LONDON_TRIP[0]["reservationFor"]["departureTime"])


def leg(ref: str, dep: str, arr: str, leave: str, reach: str) -> Any:
    r = reservation_from_jsonld(
        {
            "@type": "TrainReservation",
            "reservationNumber": ref,
            "reservationFor": {
                "@type": "TrainTrip",
                "departureStation": {"@type": "TrainStation", "name": dep},
                "arrivalStation": {"@type": "TrainStation", "name": arr},
                "departureTime": leave,
                "arrivalTime": reach,
            },
        },
        ("d",),
    )
    assert r is not None
    return r


def view(now: datetime = LEAVES - timedelta(minutes=40)) -> ft.Control:
    found = [reservation_from_jsonld(e, ("d",)) for e in LONDON_TRIP]
    [trip] = group([r for r in found if r])
    return trip_view(trip, now)


def tagged(control: ft.Control, key: str) -> list[Any]:
    return [c.data[key] for c in walk(control) if isinstance(c.data, dict) and key in c.data]


def test_connection_between_two_legs_at_the_same_station() -> None:
    a = leg(
        "A",
        "Paris Nord",
        "Bruxelles-Midi",
        "2026-07-08T14:25:00+02:00",
        "2026-07-08T15:47:00+02:00",
    )
    b = leg(
        "B",
        "Bruxelles-Midi",
        "Amsterdam C",
        "2026-07-08T16:07:00+02:00",
        "2026-07-08T18:52:00+02:00",
    )
    assert connection(a, b) == "Connection of 20 min at Bruxelles-Midi"


def test_no_connection_elsewhere_or_days_apart() -> None:
    a = leg(
        "A",
        "Paris Nord",
        "Bruxelles-Midi",
        "2026-07-08T14:25:00+02:00",
        "2026-07-08T15:47:00+02:00",
    )
    elsewhere = leg(
        "B", "Antwerpen", "Amsterdam C", "2026-07-08T16:07:00+02:00", "2026-07-08T18:00:00+02:00"
    )
    later = leg(
        "C",
        "Bruxelles-Midi",
        "Paris Nord",
        "2026-07-10T16:07:00+02:00",
        "2026-07-10T18:00:00+02:00",
    )
    assert connection(a, elsewhere) is None
    assert connection(a, later) is None


def test_header_has_avatars_and_traveller_count() -> None:
    shown = view()
    assert tagged(shown, "avatar") == ["Jane Doe", "Alex Martin"]
    assert "8–10 Jul 2026 · 2 travellers" in texts(shown)
    assert initials("Jane Doe") == "JD"


def test_badges_for_seat_nights_and_confirmed_stay() -> None:
    chips = tagged(view(), "chip")
    for expected in ("Platform 4", "Coach 12 · Seat 41", "2 nights", "Confirmed"):
        assert expected in chips, expected


def test_next_segment_has_the_band_others_are_in_a_boxed_list() -> None:
    shown = view()
    segments = [c for c in walk(shown) if isinstance(c.data, dict) and "segment" in c.data]
    nexts = [c for c in segments if c.data["next"]]
    assert [c.data["segment"] for c in nexts] == ["ESC-T1"]
    assert nexts[0].border is not None
    assert "NEXT · leaves in 40 min" in texts(nexts[0])


def test_an_outing_row_shows_the_street_not_the_title_again() -> None:
    found = [reservation_from_jsonld(e, ("d",)) for e in LONDON_TRIP_FULL]
    [trip] = group([r for r in found if r])
    shown = texts(trip_view(trip, LEAVES - timedelta(minutes=40)))
    assert shown.count("Dishoom Covent Garden") == 1
    assert shown.count("Tate Modern") == 1
    assert "12 Upper St Martin's Lane" in shown
    assert "Bankside" in shown


def test_an_event_elsewhere_than_its_name_shows_the_venue() -> None:
    r = reservation_from_jsonld(
        {
            "@type": "EventReservation",
            "reservationFor": {
                "@type": "Event",
                "name": "Hamlet",
                "startDate": "2026-07-09T19:30:00+01:00",
                "location": {
                    "@type": "Place",
                    "name": "Barbican Theatre",
                    "address": {"streetAddress": "Silk Street"},
                },
            },
        },
        (),
    )
    assert r is not None
    [trip] = group([r])
    assert "Barbican Theatre · Silk Street" in texts(trip_view(trip, LEAVES))
