"""S006a — Nextcloud connection (core), on the fake server; the real one is in
``test_nextcloud_dav.py``."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

import pytest
from pytest_bdd import given, scenarios, then, when

from escale_core.adapters.fake_nextcloud import FakeNextcloud
from escale_core.nextcloud import (
    Connection,
    Problem,
    connect,
    create_trips_calendar,
    endpoints,
)

scenarios("S006a.feature")


@dataclass
class World:
    server: FakeNextcloud = field(default_factory=FakeNextcloud)
    connection: Connection | None = None


@pytest.fixture
def world() -> World:
    return World()


@given("a reachable Nextcloud server")
def reachable(world: World) -> None:
    world.server = FakeNextcloud(calendars=["Personal"])


@given('a connected account with no calendar named "Trips"')
def no_trips(world: World) -> None:
    world.server = FakeNextcloud(calendars=["Personal"])
    world.connection = asyncio.run(connect(world.server))


@given('an account without an "Escale" folder')
def no_folder(world: World) -> None:
    world.server = FakeNextcloud(calendars=["Personal"])
    assert "Escale" not in world.server.folders


@when("Escale connects with a login and a valid app password")
@when("Escale connects")
def connects(world: World) -> None:
    world.connection = asyncio.run(connect(world.server))


@when("Escale connects with a wrong app password")
def connects_wrong(world: World) -> None:
    world.server.password_ok = False
    world.connection = asyncio.run(connect(world.server))


@when("the trips calendar is created")
def create_trips(world: World) -> None:
    asyncio.run(create_trips_calendar(world.server))


@then("the user's calendars are listed")
def listed(world: World) -> None:
    assert world.connection is not None and world.connection.problem is None
    assert [c.name for c in world.connection.calendars] == ["Personal"]


@then("the result says the credentials were refused")
def refused(world: World) -> None:
    assert world.connection is not None
    assert world.connection.problem is Problem.REFUSED
    assert world.connection.calendars == ()


@then('a calendar named "Trips" exists on the server')
def trips_exists(world: World) -> None:
    assert "Trips" in [c.name for c in asyncio.run(world.server.calendars())]


@then('the folder "Escale" exists in the user\'s files')
def folder_exists(world: World) -> None:
    assert "Escale" in world.server.folders


# --- details ---


def test_unreachable_and_not_a_nextcloud_are_said() -> None:
    down = FakeNextcloud(reachable=False)
    assert asyncio.run(connect(down)).problem is Problem.UNREACHABLE
    other = FakeNextcloud(nextcloud=False)
    assert asyncio.run(connect(other)).problem is Problem.NOT_NEXTCLOUD


def test_creating_trips_twice_keeps_one_calendar() -> None:
    server = FakeNextcloud(calendars=["Personal"])
    first = asyncio.run(create_trips_calendar(server))
    second = asyncio.run(create_trips_calendar(server))
    assert first == second
    assert [c.name for c in asyncio.run(server.calendars())].count("Trips") == 1


@pytest.mark.parametrize(
    ("typed", "dav", "files"),
    [
        (
            "https://cloud.example.org",
            "https://cloud.example.org/remote.php/dav",
            "https://cloud.example.org/remote.php/dav/files/jane%20doe/",
        ),
        (
            "cloud.example.org/",
            "https://cloud.example.org/remote.php/dav",
            "https://cloud.example.org/remote.php/dav/files/jane%20doe/",
        ),
        (
            "https://example.org/nextcloud/index.php",
            "https://example.org/nextcloud/remote.php/dav",
            "https://example.org/nextcloud/remote.php/dav/files/jane%20doe/",
        ),
        (
            "http://127.0.0.1:8080",
            "http://127.0.0.1:8080/remote.php/dav",
            "http://127.0.0.1:8080/remote.php/dav/files/jane%20doe/",
        ),
    ],
)
def test_endpoints(typed: str, dav: str, files: str) -> None:
    assert endpoints(typed, "jane doe") == (dav, files)
