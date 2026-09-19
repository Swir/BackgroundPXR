from __future__ import annotations

import pytest

from tools.release_policy import ReleasePolicyError, validate_final_release_version


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
