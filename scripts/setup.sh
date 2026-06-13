#!/bin/sh
set -eu

if command -v python3.11 >/dev/null 2>&1; then
  PYTHON_BIN=python3.11
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN=python3
else
  PYTHON_BIN=python
fi

exec "$PYTHON_BIN" scripts/setup.py "$@"
