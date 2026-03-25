#!/usr/bin/env bash
set -e

echo "==> Running tests"
pip install pytest pytest-asyncio httpx -q
pytest tests/ -v
