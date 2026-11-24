"""CI lints the stories (story S001): a malformed story must fail the lint step."""

from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LINTER = ROOT / "scripts" / "lint_stories.py"

STORY = textwrap.dedent(
    """\
    ---
    id: S900
    title: "Sample story"
    epic: sample
    depends_on: []
    status: proposed
    {estimate}bdd: false
    updated: "2026-11-24"
    ---

    ## User story

    > **As a** tester, **I want** a sample, **so that** the linter has input.

    ## Acceptance Criteria

    ### Scenario: Sample

    * **Given** a sample
    * **When** it is linted
    * **Then** it is checked
    """
)


def _lint(stories: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(LINTER), f"--stories-dir={stories}", "--strict"],
        capture_output=True,
        text=True,
        check=False,
    )


def test_proposed_story_without_estimate_fails_the_lint(tmp_path: Path) -> None:
    (tmp_path / "S900-sample-story.md").write_text(STORY.format(estimate=""), encoding="utf-8")

    result = _lint(tmp_path)

    assert result.returncode != 0
    assert "estimate" in result.stdout + result.stderr


def test_well_formed_story_passes_the_lint(tmp_path: Path) -> None:
    (tmp_path / "S900-sample-story.md").write_text(
        STORY.format(estimate="estimate: S\n"), encoding="utf-8"
    )

    assert _lint(tmp_path).returncode == 0


def test_repository_stories_pass_the_lint() -> None:
    result = _lint(ROOT / "stories")

    assert result.returncode == 0, result.stdout + result.stderr
