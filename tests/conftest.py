import plistlib
from pathlib import Path
from typing import Callable

import pytest


@pytest.fixture
def app_factory(tmp_path: Path) -> Callable[[str], Path]:
    def _create(version: str) -> Path:
        applications_dir: Path = tmp_path / "Applications"
        contents: Path = applications_dir / "Chromium.app" / "Contents"
        contents.mkdir(parents=True)

        with (contents / "Info.plist").open("wb") as f:
            plistlib.dump({"CFBundleShortVersionString": version}, f)

        return applications_dir

    return _create
