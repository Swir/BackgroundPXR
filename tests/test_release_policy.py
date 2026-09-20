from __future__ import annotations

import pytest

from tools.release_policy import (
    ReleasePolicyError,
    validate_final_release_version,
    validate_public_release_readiness,
)


@pytest.mark.parametrize("version", ["1.0.0", "1.2.3", "2.0.0"])
def test_final_1_plus_versions_are_publishable(version: str) -> None:
    parsed = validate_final_release_version(version)
    assert parsed[0] >= 1


@pytest.mark.parametrize(
    "version",
    [
        "0.4.0",
        "1.0.0rc1",
        "1.0.0-rc.1",
        "1.0.0-beta",
        "v1.0.0",
        "1.0",
        " 1.0.0",
    ],
)
def test_nonfinal_or_pre_1_versions_are_rejected(version: str) -> None:
    with pytest.raises(ReleasePolicyError):
        validate_final_release_version(version)


def _roadmap(*, completed: int) -> str:
    items = [
        f"- [{'x' if index <= completed else ' '}] acceptance item {index}"
        for index in range(1, 11)
    ]
    return "\n".join(items) + "\n"


def test_1_0_publication_requires_first_nine_items_and_final_notes() -> None:
    parsed = validate_public_release_readiness(
        "1.0.0",
        roadmap_text=_roadmap(completed=9),
        release_notes_text="# BackgroundPXR 1.0.0 — Final\n",
    )
    assert parsed == (1, 0, 0)


def test_1_0_publication_rejects_open_item_nine() -> None:
    with pytest.raises(ReleasePolicyError, match="item 9 is still unchecked"):
        validate_public_release_readiness(
            "1.0.0",
            roadmap_text=_roadmap(completed=8),
            release_notes_text="# BackgroundPXR 1.0.0 — Final\n",
        )


def test_1_0_publication_keeps_publish_smoke_item_open_until_after_release() -> None:
    with pytest.raises(ReleasePolicyError, match="item 10 includes publication"):
        validate_public_release_readiness(
            "1.0.0",
            roadmap_text=_roadmap(completed=10),
            release_notes_text="# BackgroundPXR 1.0.0 — Final\n",
        )


def test_1_0_publication_requires_exact_final_release_notes_heading() -> None:
    with pytest.raises(ReleasePolicyError, match="does not contain"):
        validate_public_release_readiness(
            "1.0.0",
            roadmap_text=_roadmap(completed=9),
            release_notes_text="# BackgroundPXR 1.0.0rc1 — Candidate\n",
        )


@pytest.mark.parametrize("missing", ["roadmap", "notes"])
def test_1_0_publication_requires_repository_evidence(missing: str) -> None:
    kwargs = {
        "roadmap_text": _roadmap(completed=9),
        "release_notes_text": "# BackgroundPXR 1.0.0 — Final\n",
    }
    if missing == "roadmap":
        kwargs["roadmap_text"] = None
    else:
        kwargs["release_notes_text"] = None

    with pytest.raises(ReleasePolicyError, match="evidence is required"):
        validate_public_release_readiness("1.0.0", **kwargs)
