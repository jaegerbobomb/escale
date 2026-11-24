"""The `kitinerary-extractor` adapter: binary resolution, subprocess plumbing, real binary.

Tests marked `kitinerary` run the real extractor. They are skipped when it is not
installed, unless `ESCALE_REQUIRE_KITINERARY=1` (set in CI), where a missing binary is a
failure.
"""

from __future__ import annotations

import asyncio
import os
import stat
from pathlib import Path

import pytest

from escale_core.adapters.kitinerary_cli import (
    ExtractorError,
    ExtractorNotFoundError,
    KitineraryCli,
    find_extractor,
)
from escale_core.importer import extract

DATA = Path(__file__).parent / "data"


def _script(directory: Path, body: str, name: str = "kitinerary-extractor") -> Path:
    """A stand-in executable that runs ``body`` as a shell script."""
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / name
    path.write_text("#!/bin/sh\n" + body + "\n", encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)
    return path


# --- binary resolution ---


def test_path_comes_first(tmp_path: Path) -> None:
    on_path = _script(tmp_path / "bin", "true")
    configured = _script(tmp_path / "opt", "true")
    found = find_extractor(configured, search_path=str(tmp_path / "bin"), fallbacks=())
    assert found == on_path


def test_configured_binary_when_not_on_path(tmp_path: Path) -> None:
    configured = _script(tmp_path / "opt", "true")
    found = find_extractor(configured, search_path=str(tmp_path / "empty"), fallbacks=())
    assert found == configured


def test_distribution_location_as_last_resort(tmp_path: Path) -> None:
    distro = _script(tmp_path / "libexec" / "kf5", "true")
    found = find_extractor(None, search_path=str(tmp_path / "empty"), fallbacks=(distro,))
    assert found == distro


def test_nothing_found(tmp_path: Path) -> None:
    missing = tmp_path / "nope" / "kitinerary-extractor"
    assert find_extractor(missing, search_path=str(tmp_path), fallbacks=(missing,)) is None


def test_missing_binary_raises_a_dedicated_error(tmp_path: Path) -> None:
    cli = KitineraryCli(search_path=str(tmp_path), fallbacks=())
    with pytest.raises(ExtractorNotFoundError):
        asyncio.run(cli.extract(DATA / "no-reservation.pdf"))


# --- subprocess plumbing, with a stand-in executable ---


def test_prints_json_array(tmp_path: Path) -> None:
    binary = _script(tmp_path, """echo '[{"@type": "TrainReservation"}]'""")
    cli = KitineraryCli(binary)
    assert asyncio.run(cli.extract(DATA / "no-reservation.pdf")) == [{"@type": "TrainReservation"}]


def test_passes_the_file_as_argument(tmp_path: Path) -> None:
    binary = _script(tmp_path, """printf '[{"file": "%s"}]' "$1" """)
    cli = KitineraryCli(binary)
    ticket = DATA / "no-reservation.pdf"
    assert asyncio.run(cli.extract(ticket)) == [{"file": str(ticket)}]


def test_non_zero_exit_is_an_error(tmp_path: Path) -> None:
    binary = _script(tmp_path, "echo boom >&2; exit 3")
    with pytest.raises(ExtractorError, match="boom"):
        asyncio.run(KitineraryCli(binary).extract(DATA / "no-reservation.pdf"))


def test_output_that_is_not_a_json_array_is_an_error(tmp_path: Path) -> None:
    binary = _script(tmp_path, 'echo \'{"not": "a list"}\'')
    with pytest.raises(ExtractorError):
        asyncio.run(KitineraryCli(binary).extract(DATA / "no-reservation.pdf"))


def test_timeout_kills_the_extractor(tmp_path: Path) -> None:
    binary = _script(tmp_path, "sleep 5")
    with pytest.raises(ExtractorError, match="timed out"):
        asyncio.run(KitineraryCli(binary, timeout=0.2).extract(DATA / "no-reservation.pdf"))


def test_a_failing_extractor_is_an_error_result_not_a_crash(tmp_path: Path) -> None:
    binary = _script(tmp_path, "exit 1")
    result = asyncio.run(extract(DATA / "no-reservation.pdf", KitineraryCli(binary)))
    assert result.error is not None
    assert result.reservations == ()


# --- the real binary ---

REAL = find_extractor()
REQUIRED = os.environ.get("ESCALE_REQUIRE_KITINERARY") == "1"


@pytest.fixture
def real_cli() -> KitineraryCli:
    if REAL is None:
        if REQUIRED:
            pytest.fail("kitinerary-extractor is required (ESCALE_REQUIRE_KITINERARY=1)")
        pytest.skip("kitinerary-extractor is not installed")
    return KitineraryCli(REAL)


def test_real_train_booking(real_cli: KitineraryCli) -> None:
    result = asyncio.run(extract(DATA / "train-booking.html", real_cli))
    assert result.error is None
    [reservation] = result.reservations
    assert reservation.type == "TrainReservation"
    assert reservation.departure is not None and reservation.departure.name == "Lyon Part-Dieu"
    assert reservation.arrival is not None and reservation.arrival.name == "Paris Gare de Lyon"
    assert reservation.departure.time is not None
    assert reservation.departure.time.isoformat() == "2027-03-14T08:04:00+01:00"


def test_real_boarding_pass_pdf(real_cli: KitineraryCli) -> None:
    result = asyncio.run(extract(DATA / "iata-bcbp-demo.pdf", real_cli))
    assert result.error is None
    [reservation] = result.reservations
    assert reservation.type == "FlightReservation"
    assert reservation.departure is not None and reservation.arrival is not None
    assert (reservation.departure.name, reservation.departure.code) == ("Vienna", "VIE")
    assert (reservation.arrival.name, reservation.arrival.code) == ("Milano Malpensa", "MXP")
    assert reservation.departure.time is not None
    assert reservation.departure.time.isoformat() == "2019-09-06T15:45:00+02:00"
    assert result.document is not None
    assert result.document.mime_type == "application/pdf"


def test_real_pdf_without_reservation(real_cli: KitineraryCli) -> None:
    result = asyncio.run(extract(DATA / "no-reservation.pdf", real_cli))
    assert result.nothing_recognised
