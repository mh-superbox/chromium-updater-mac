#!/usr/bin/env bash

set -e

cd "$(dirname "$0")/.."

uv sync --locked --python /usr/bin/python3  --all-extras --dev
uv run pre-commit install
