#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

if [[ ! -x ./.venv/bin/python ]]; then
  echo "Virtual environment not found at .venv/bin/python" >&2
  exit 1
fi

exec ./.venv/bin/python src/main.py "$@"
