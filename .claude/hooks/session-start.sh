#!/usr/bin/env bash
# Prepares a remote Claude Code session (module `claude-code`). Idempotent.
set -euo pipefail
[ "${CLAUDE_CODE_REMOTE:-}" = "true" ] || exit 0
cd "${CLAUDE_PROJECT_DIR:-$(pwd)}"
if [ -f pyproject.toml ] && command -v uv >/dev/null 2>&1; then
  uv sync --all-packages >/dev/null
fi
