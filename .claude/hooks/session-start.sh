#!/bin/bash
# SessionStart hook: prepare the astrology engine for Claude Code web sessions.
# Installs the package editable with dev extras so `python -m interpreter.predict`
# and `python -m pytest` work out of the box. Idempotent; web-only.
set -euo pipefail

# Only run in the remote (Claude Code on the web) environment.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "${CLAUDE_PROJECT_DIR:-.}"

# Editable install with dev extras (skyfield, numpy, pytest). pip skips
# already-satisfied deps, so this is fast on a cached container.
python -m pip install --quiet --root-user-action=ignore --upgrade pip >/dev/null 2>&1 || true
python -m pip install --quiet --root-user-action=ignore -e ".[dev]"

echo "[session-start] advance-astrology engine ready (skyfield, numpy, pytest installed)."
