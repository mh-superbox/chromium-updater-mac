#!/usr/bin/env python3
from __future__ import annotations

import json
import logging
import plistlib
import re
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path
from typing import Any
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from http.client import HTTPResponse


logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
)


def get_latest_arm_release() -> tuple[str | None, str | None]:
    dmg_url: str | None = None

    response: HTTPResponse
    with urllib.request.urlopen(
        "https://api.github.com/repos/ungoogled-software/ungoogled-chromium-macos/releases/latest",
        timeout=15,
    ) as response:
        data: dict[str, Any] = json.load(response)

    version: str | None = data.get("tag_name")

    for asset in data["assets"]:
        name: str = asset["name"]
        if "arm64" in name and name.endswith(".dmg"):
            dmg_url = asset["browser_download_url"]

    return dmg_url, version


def get_installed_version(app_path: Path) -> str | None:
    installed_version: str | None = None

    info_plist: Path = app_path / "Contents" / "Info.plist"

    if info_plist.exists():
        with info_plist.open("rb") as f:
            plist: dict[str, Any] = plistlib.load(f)

        installed_version = plist.get("CFBundleShortVersionString") or plist.get("CFBundleVersion")

    return installed_version


def version_tuple(v: str) -> tuple[int, ...]:
    nums: list[int] = [int(x) for x in re.findall(r"\d+", v)]
    return tuple(nums[:4])


def download_dmg(url: str, target: Path) -> None:
    response: HTTPResponse

    with urllib.request.urlopen(url) as response, target.open("wb") as f:  # noqa: S310
        total_size: int = int(response.headers.get("Content-Length", 0))
        downloaded: int = 0
        chunk_size: int = 8192
        last_logged: int = 0

        logger.info("Downloading %s", target.name)

        while True:
            chunk: bytes = response.read(chunk_size)
            if not chunk:
                break

            f.write(chunk)

            downloaded += len(chunk)

            if total_size > 0:
                percent: int = int(downloaded * 100 / total_size)

                if percent >= last_logged + 5:
                    logger.info("Download progress: %d%% (%d/%d bytes)", percent, downloaded, total_size)
                    last_logged = percent

        logger.info("Downloaded to %s", target.as_posix())


def install_dmg(dmg: Path) -> None:
    mount_point: Path = Path(tempfile.mkdtemp(prefix="ungoogled-chromium-"))

    logger.info("Mounting DMG at %s", mount_point)

    subprocess.run(
        ["/usr/bin/hdiutil", "attach", "-quiet", "-nobrowse", dmg.as_posix(), "-mountpoint", mount_point.as_posix()],
        check=True,
    )

    app_dir: Path = Path("/Applications")
    source_app: Path = mount_point / "Chromium.app"
    target_app: Path = app_dir / "Chromium.app"

    try:
        if target_app.exists():
            logger.info("Removing old Chromium.app")
            subprocess.run(["/bin/rm", "-rf", target_app.as_posix()], check=True)

        logger.info("Copy new Chromium.app to /Applications")
        subprocess.run(["/bin/cp", "-R", source_app.as_posix(), target_app.as_posix()], check=True)
    finally:
        logger.info("Unmount %s", mount_point.as_posix())
        subprocess.run(["/usr/bin/hdiutil", "detach", "-quiet", mount_point.as_posix()], check=False)

        logger.info("Removing temporary DMG %s", dmg)
        subprocess.run(["/bin/rm", "-rf", dmg.as_posix(), mount_point.as_posix()], check=False)


def main() -> None:
    logger.info("Start updater for Ungoogled-Chromium")

    dmg_url, latest_version = get_latest_arm_release()

    app_path: Path = Path("/Applications/Chromium.app")
    installed_version: str | None = get_installed_version(app_path)

    logger.info("Installed version: %s", installed_version)
    logger.info("Latest version: %s", latest_version)

    if dmg_url and latest_version:
        if installed_version and version_tuple(latest_version) <= version_tuple(installed_version):
            logger.info("Already up to date 👍")
        else:
            logger.info("New version available")
            dmg_file: Path = Path(tempfile.gettempdir()) / dmg_url.split("/")[-1]
            download_dmg(dmg_url, dmg_file)
            install_dmg(dmg_file)

    sys.exit(0)


if __name__ == "__main__":
    main()
