"""The Nextcloud adapter against a real server (S006a).

Runs when ``ESCALE_NEXTCLOUD_URL``, ``ESCALE_NEXTCLOUD_LOGIN`` and
``ESCALE_NEXTCLOUD_PASSWORD`` point at a Nextcloud made for tests: it creates and
deletes a "Trips" calendar and an "Escale" folder there. CI starts one in a container
and sets ``ESCALE_REQUIRE_NEXTCLOUD=1``, so a missing server fails instead of skipping.
"""

from __future__ import annotations

import asyncio
import os

import pytest
from caldav.davclient import DAVClient

from escale_core.adapters.nextcloud_dav import NextcloudDav
from escale_core.ical_mapping import entries_in, new_entry, to_ics
from escale_core.importer import reservation_from_jsonld
from escale_core.nextcloud import (
    EventChanged,
    Problem,
    connect,
    create_trips_calendar,
    endpoints,
    event_href,
)

URL = os.environ.get("ESCALE_NEXTCLOUD_URL", "")
LOGIN = os.environ.get("ESCALE_NEXTCLOUD_LOGIN", "")
PASSWORD = os.environ.get("ESCALE_NEXTCLOUD_PASSWORD", "")

if not (URL and LOGIN and PASSWORD):
    if os.environ.get("ESCALE_REQUIRE_NEXTCLOUD") == "1":
        raise RuntimeError("ESCALE_NEXTCLOUD_URL, _LOGIN and _PASSWORD are required")
    pytest.skip("no Nextcloud to test against", allow_module_level=True)


@pytest.fixture
def clean() -> None:
    """No "Trips" calendar and no "Escale" folder before the test."""
    dav, files = endpoints(URL, LOGIN)
    client = DAVClient(url=dav, username=LOGIN, password=PASSWORD)
    for calendar in client.principal().calendars():  # type: ignore[no-untyped-call]
        if calendar.get_display_name() == "Trips":
            calendar.delete()
    client.delete(files + "Escale/")


def test_connect_lists_calendars_and_prepares_the_folder(clean: None) -> None:
    server = NextcloudDav(URL, LOGIN, PASSWORD)
    connection = asyncio.run(connect(server))
    assert connection.problem is None
    assert connection.calendars, "a new Nextcloud account has a Personal calendar"
    assert asyncio.run(server.folder_exists("Escale"))


def test_wrong_password_is_refused() -> None:
    connection = asyncio.run(connect(NextcloudDav(URL, LOGIN, PASSWORD + "-wrong")))
    assert connection.problem is Problem.REFUSED


def test_unreachable_server() -> None:
    connection = asyncio.run(connect(NextcloudDav("http://127.0.0.1:9", LOGIN, PASSWORD)))
    assert connection.problem is Problem.UNREACHABLE


def test_not_a_nextcloud() -> None:
    connection = asyncio.run(connect(NextcloudDav(URL + "/nope", LOGIN, PASSWORD)))
    assert connection.problem is Problem.NOT_NEXTCLOUD


def test_create_trips_calendar(clean: None) -> None:
    server = NextcloudDav(URL, LOGIN, PASSWORD)
    created = asyncio.run(create_trips_calendar(server))
    again = asyncio.run(create_trips_calendar(server))
    names = [c.name for c in asyncio.run(server.calendars())]
    assert created.name == "Trips" and again.url == created.url
    assert names.count("Trips") == 1


def test_put_event_creates_then_updates_and_refuses_a_stale_etag(clean: None) -> None:
    """S008a: the event Escale writes, as the server keeps it."""
    server = NextcloudDav(URL, LOGIN, PASSWORD)
    trips = asyncio.run(create_trips_calendar(server))
    hotel = reservation_from_jsonld(
        {
            "@type": "LodgingReservation",
            "reservationNumber": "ESC-H1",
            "checkinTime": "2026-07-08T15:00:00+01:00",
            "checkoutTime": "2026-07-10T11:00:00+01:00",
            "reservationFor": {"@type": "LodgingBusiness", "name": 'Hotel; "A", B'},
        },
        (),
    )
    assert hotel is not None
    entry = new_entry([hotel])
    href = event_href(trips.url, entry.uid)
    first = asyncio.run(server.put_event(href, to_ics([entry]), None))
    assert first
    with pytest.raises(EventChanged):
        asyncio.run(server.put_event(href, to_ics([entry]), None))  # already there
    second = asyncio.run(server.put_event(href, to_ics([entry]), first))
    assert second
    with pytest.raises(EventChanged):
        asyncio.run(server.put_event(href, to_ics([entry]), '"stale"'))
    dav, _ = endpoints(URL, LOGIN)
    body = DAVClient(url=dav, username=LOGIN, password=PASSWORD).request(href).raw
    [kept] = entries_in(body)
    assert dict(kept.reservations[0].raw) == dict(hotel.raw)
