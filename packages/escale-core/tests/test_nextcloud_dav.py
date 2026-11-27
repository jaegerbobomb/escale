"""The Nextcloud adapter against a real server (S006a).

Runs when ``ESCALE_NEXTCLOUD_URL``, ``ESCALE_NEXTCLOUD_LOGIN`` and
``ESCALE_NEXTCLOUD_PASSWORD`` point at a Nextcloud made for tests: it creates and
deletes a "Trips" calendar and an "Escale" folder there. CI starts one in a container
and sets ``ESCALE_REQUIRE_NEXTCLOUD=1``, so a missing server fails instead of skipping.
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

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
    """An empty "Trips" calendar, if there is one, and no "Escale" folder.

    The calendar is emptied, not deleted: Nextcloud limits how many calendars an account
    creates per hour (``Too many calendars created``), and each run would create one.
    """
    dav, files = endpoints(URL, LOGIN)
    client = DAVClient(url=dav, username=LOGIN, password=PASSWORD)
    for calendar in client.principal().calendars():  # type: ignore[no-untyped-call]
        if calendar.get_display_name() == "Trips":
            for event in calendar.events():
                event.delete()
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
    current = asyncio.run(server.get_event(href))
    assert current is not None and current.etag == second
    [kept] = entries_in(current.ics)
    assert dict(kept.reservations[0].raw) == dict(hotel.raw)
    dav, _ = endpoints(URL, LOGIN)
    DAVClient(url=dav, username=LOGIN, password=PASSWORD).delete(href)
    assert asyncio.run(server.get_event(href)) is None


def test_changes_list_then_follow_the_calendar(clean: None) -> None:
    """S008b: a full listing, then only what changed, deletions included."""
    server = NextcloudDav(URL, LOGIN, PASSWORD)
    trips = asyncio.run(create_trips_calendar(server))
    first = asyncio.run(server.changes(trips.url, None))
    assert first.full and first.changed == () and first.token
    hotel = reservation_from_jsonld(
        {
            "@type": "LodgingReservation",
            "reservationNumber": "ESC-H2",
            "checkinTime": "2026-07-08T15:00:00+01:00",
            "checkoutTime": "2026-07-10T11:00:00+01:00",
            "reservationFor": {"@type": "LodgingBusiness", "name": "Hotel"},
        },
        (),
    )
    assert hotel is not None
    entry = new_entry([hotel])
    href = event_href(trips.url, entry.uid)
    etag = asyncio.run(server.put_event(href, to_ics([entry]), None))
    second = asyncio.run(server.changes(trips.url, first.token))
    assert not second.full
    assert [(e.href, e.etag) for e in second.changed] == [(href, etag)]
    assert entries_in(second.changed[0].ics)[0].uid == entry.uid
    dav, _ = endpoints(URL, LOGIN)
    DAVClient(url=dav, username=LOGIN, password=PASSWORD).delete(href)
    third = asyncio.run(server.changes(trips.url, second.token))
    assert third.removed == (href,) and third.changed == ()
    refused = asyncio.run(server.changes(trips.url, "not-a-token"))
    assert refused.full and refused.changed == ()


def test_two_devices_share_a_reservation(clean: None, tmp_path: Path) -> None:
    """S008a + S008b end to end: saved on one device, shown on the other, then gone."""
    from escale_core.account import Account
    from escale_core.extraction import Document
    from escale_core.passwords import MemoryPasswords
    from escale_core.settings import SettingsFile
    from escale_core.store import InMemoryReservationStore
    from escale_core.sync import Sync

    devices = []
    for n in range(2):
        account = Account(SettingsFile(tmp_path / f"{n}.json"), MemoryPasswords(True), NextcloudDav)
        assert asyncio.run(account.connect(URL, LOGIN, PASSWORD))
        asyncio.run(account.create_trips())
        store = InMemoryReservationStore()
        devices.append((store, Sync(store, account)))
    (first, first_sync), (second, second_sync) = devices
    hotel = reservation_from_jsonld(
        {
            "@type": "LodgingReservation",
            "reservationNumber": "ESC-H3",
            "checkinTime": "2026-07-08T15:00:00+01:00",
            "checkoutTime": "2026-07-10T11:00:00+01:00",
            "reservationFor": {"@type": "LodgingBusiness", "name": "Hotel"},
        },
        ("d",),
    )
    assert hotel is not None
    asyncio.run(first.add(Document("d", "b.pdf", "application/pdf"), [hotel]))
    assert asyncio.run(first_sync.run()).sent == 1
    assert asyncio.run(second_sync.run()).received == 1
    [shown] = asyncio.run(second.reservations())
    assert dict(shown.raw) == dict(hotel.raw)
    [href] = asyncio.run(second.events())
    dav, _ = endpoints(URL, LOGIN)
    DAVClient(url=dav, username=LOGIN, password=PASSWORD).delete(href)
    asyncio.run(second_sync.run())
    assert asyncio.run(second.reservations()) == ()
