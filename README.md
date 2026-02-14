# Chromium updater for macOS

![coverage-badge](https://raw.githubusercontent.com/mh-superbox/chromium-updater-mac/main/coverage-badge.svg)
[![CI](https://github.com/mh-superbox/chromium-updater-mac/actions/workflows/ci.yml/badge.svg?branch=main)][workflow-ci]
![Typing: strict][typing-strict]
![Code style: black][code-black]
![Code style: Ruff][code-ruff]

[workflow-ci]: https://github.com/superbox-dev/keba_keenergy/actions/workflows/ci.yml
[typing-strict]: https://img.shields.io/badge/typing-strict-green.svg
[code-black]: https://img.shields.io/badge/code%20style-black-black
[code-ruff]: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v1.json

This is a LaunchDaemon to automatically update [Ungoogled Chromium](https://github.com/ungoogled-software/ungoogled-chromium-macos).

## Install updater

```bash
sudo cp -f src/chromium_updater.py /usr/local/bin/chromium-updater.py
sudo cp -f src/one.superbox.chromium.updater.plist /Library/LaunchDaemons/one.superbox.chromium.updater.plist
```

## Start LaunchDaemon

```bash
sudo launchctl bootstrap system /Library/LaunchDaemons/one.superbox.chromium.updater.plist
```

## Check if LaunchDaemon is running

```bash
launchctl list | grep chromium.updater
```

## View updater logs

```bash
tail -f /var/log/chromium-updater.log
```

or use the `console.app`:

![update-chromium.png](assets/update-chromium.png)

## Stop LaunchDaemon

```bash
sudo launchctl bootout system /Library/LaunchDaemons/one.superbox.chromium.updater.plist
```
