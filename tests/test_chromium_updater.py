from __future__ import annotations

import io
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from typing import Callable
from typing import Literal
from unittest import mock
from unittest.mock import MagicMock

import pytest
from typing_extensions import Self

from src import chromium_updater


class FakeHTTPResponse:
    def __init__(self, body: bytes, headers: dict[str, str] | None = None) -> None:
        self._io: io.BytesIO = io.BytesIO(body)
        self.headers: dict[str, str] = headers or {}

    def read(self, n: int = -1) -> bytes:
        return self._io.read(n)

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args: object) -> Literal[False]:
        return False


def make_fake_urlopen(
    github_payload: dict[str, Any],
    dmg_content: bytes | None = None,
) -> Callable[[str, int], FakeHTTPResponse]:
    def fake_urlopen(url: str, timeout: int = 15) -> FakeHTTPResponse:  # noqa: ARG001
        if dmg_content is not None and url.endswith(".dmg"):
            return FakeHTTPResponse(
                dmg_content,
                headers={"Content-Length": str(len(dmg_content))},
            )
        return FakeHTTPResponse(json.dumps(github_payload).encode())

    return fake_urlopen


GITHUB_PAYLOAD: dict[str, Any] = {
    "tag_name": "145.0.7632.45-1.1",
    "assets": [
        {
            "name": "ungoogled-chromium_145.0.7632.45-1.1_arm64-macos.dmg",
            "browser_download_url": "https://github.com/ungoogled-software/ungoogled-chromium-macos/releases/download/145.0.7632.45-1.1/ungoogled-chromium_145.0.7632.45-1.1_arm64-macos.dmg",
        },
    ],
}


def test_main_full_integration(tmp_path: Path, app_factory: Callable[[str], Path]) -> None:
    dmg_content: bytes = b"DMGDATA" * 1024
    applications_dir: Path = app_factory("1.0.0")

    run_mock: MagicMock = MagicMock(return_value=SimpleNamespace(returncode=0))

    path_mock: MagicMock = MagicMock(
        side_effect=lambda p: (
            applications_dir / "Chromium.app" if str(p) == "/Applications/Chromium.app" else Path(p)
        ),
    )

    with (
        mock.patch(
            "src.chromium_updater.urllib.request.urlopen",
            side_effect=make_fake_urlopen(GITHUB_PAYLOAD, dmg_content),
        ),
        mock.patch("src.chromium_updater.Path", path_mock),
        mock.patch("src.chromium_updater.subprocess.run", run_mock),
        mock.patch(
            "src.chromium_updater.tempfile.gettempdir",
            return_value=str(tmp_path),
        ),
        mock.patch(
            "src.chromium_updater.tempfile.mkdtemp",
            return_value=str(tmp_path / "mnt"),
        ),
    ):
        with pytest.raises(SystemExit) as error:
            chromium_updater.main()

        assert error.value.code == 0

    dmg_files: list[Path] = list(tmp_path.glob("*.dmg"))

    assert len(dmg_files) == 1
    assert dmg_files[0].read_bytes() == dmg_content
    assert dmg_files[0] == tmp_path / "ungoogled-chromium_145.0.7632.45-1.1_arm64-macos.dmg"

    commands = [call.args[0] for call in run_mock.call_args_list]

    assert commands == [
        [
            "/usr/bin/hdiutil",
            "attach",
            "-quiet",
            "-nobrowse",
            f"{tmp_path.as_posix()}/ungoogled-chromium_145.0.7632.45-1.1_arm64-macos.dmg",
            "-mountpoint",
            f"{tmp_path.as_posix()}/mnt",
        ],
        ["/bin/rm", "-rf", "/Applications/Chromium.app"],
        ["/bin/cp", "-R", f"{tmp_path.as_posix()}/mnt/Chromium.app", "/Applications/Chromium.app"],
        [
            "/usr/bin/hdiutil",
            "detach",
            "-quiet",
            f"{tmp_path.as_posix()}/mnt",
        ],
        [
            "/bin/rm",
            "-rf",
            f"{tmp_path.as_posix()}/ungoogled-chromium_145.0.7632.45-1.1_arm64-macos.dmg",
            f"{tmp_path.as_posix()}/mnt",
        ],
    ]


def test_main_already_up_to_date(tmp_path: Path, app_factory: Callable[[str], Path]) -> None:
    applications_dir: Path = app_factory(GITHUB_PAYLOAD["tag_name"])

    run_mock: MagicMock = MagicMock(return_value=SimpleNamespace(returncode=0))

    path_mock: MagicMock = MagicMock(
        side_effect=lambda p: (
            applications_dir / "Chromium.app" if str(p) == "/Applications/Chromium.app" else Path(p)
        ),
    )

    with (
        mock.patch(
            "src.chromium_updater.urllib.request.urlopen",
            side_effect=make_fake_urlopen(GITHUB_PAYLOAD),
        ),
        mock.patch("src.chromium_updater.Path", path_mock),
        mock.patch("src.chromium_updater.subprocess.run", run_mock),
        mock.patch(
            "src.chromium_updater.tempfile.gettempdir",
            return_value=str(tmp_path),
        ),
        mock.patch(
            "src.chromium_updater.tempfile.mkdtemp",
            return_value=str(tmp_path / "mnt"),
        ),
    ):
        with pytest.raises(SystemExit) as error:
            chromium_updater.main()

        assert error.value.code == 0

    assert run_mock.call_args_list == []
