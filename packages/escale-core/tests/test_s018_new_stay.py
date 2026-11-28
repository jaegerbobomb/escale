"""S018 — a stay added by hand: a blank booking written by the stay editor."""

from __future__ import annotations

import time
from collections.abc import Iterator
from dataclasses import replace

import pytest

from escale_core.editing import local_moment
from escale_core.stays import edited, fields_of, new_stay, problems


@pytest.fixture
def paris(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setenv("TZ", "Europe/Paris")
    time.tzset()
    yield
    monkeypatch.undo()
    time.tzset()


def test_a_new_stay_is_blank() -> None:
    blank = new_stay()
    assert blank.type == "LodgingReservation"
    assert blank.reference is None and blank.subject_of == ()
    f = fields_of(blank)
    assert f.name == "" and f.check_in_date == ""
    assert "The name is required." in problems(f, blank)


@pytest.mark.usefixtures("paris")
def test_a_time_with_no_zone_yet_is_in_the_device_zone_on_that_day() -> None:
    summer = local_moment("2027-07-08", "15:00", None)
    winter = local_moment("2027-01-08", "15:00", None)
    assert summer is not None and summer.isoformat() == "2027-07-08T15:00:00+02:00"
    assert winter is not None and winter.isoformat() == "2027-01-08T15:00:00+01:00"


@pytest.mark.usefixtures("paris")
def test_the_editor_writes_a_whole_stay() -> None:
    blank = new_stay()
    f = replace(
        fields_of(blank),
        name="Hôtel du Nord",
        city="Paris",
        check_in_date="2027-07-08",
        check_in_time="15:00",
        check_out_date="2027-07-10",
        check_out_time="11:00",
    )
    assert problems(f, blank) == []
    stay = edited(blank, f)
    assert stay.raw == {
        "@type": "LodgingReservation",
        "reservationFor": {
            "@type": "LodgingBusiness",
            "name": "Hôtel du Nord",
            "address": {"@type": "PostalAddress", "addressLocality": "Paris"},
        },
        "checkinTime": "2027-07-08T15:00:00+02:00",
        "checkoutTime": "2027-07-10T11:00:00+02:00",
    }
