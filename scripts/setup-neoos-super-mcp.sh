#!/usr/bin/env bash
# NeoOS Super MCP: Debian/PRoot setup, install, and verification.
# Safe defaults: no arbitrary shell execution, no project deletion, no automatic cleanup.
set -Eeuo pipefail

PROJECT_HOME="${HOME}/neoos-super-mcp"
ZIP_CANDIDATES=(
  "/storage/emulated/0/Download/neoos-super-mcp.zip"
  "/sdcard/Download/neoos-super-mcp.zip"
  "${HOME}/storage/shared/Download/neoos-super-mcp.zip"
  "${HOME}/neoos-super-mcp.zip"
)

say() { printf '\n[NeoOS Super MCP] %s\n' "$*"; }
die() { printf '\n[오류] %s\n' "$*" >&2; exit 1; }

find_project() {
  if [[ -f "${PROJECT_HOME}/pyproject.toml" ]]; then
    printf '%s\n' "${PROJECT_HOME}"
    return 0
  fi
  if [[ -f "${PROJECT_HOME}/neoos-super-mcp/pyproject.toml" ]]; then
    printf '%s\n' "${PROJECT_HOME}/neoos-super-mcp"
    return 0
  fi
  find "$PROJECT_HOME" -maxdepth 4 -type f -name pyproject.toml -print -quit 2>/dev/null \
    | sed 's|/pyproject.toml$||'
}

say "Checking Debian/Python environment"
if ! command -v python3 >/dev/null 2>&1; then
  die "python3 not found. In Debian run: apt update && apt install -y python3 python3-venv python3-pip unzip"
fi
python3 --version
if ! python3 -m venv --help >/dev/null 2>&1; then
  die "Python venv unavailable. In Debian run: apt install -y python3-venv"
fi

PROJECT="$(find_project || true)"
if [[ -z "${PROJECT}" || ! -f "${PROJECT}/pyproject.toml" ]]; then
  ZIP_PATH=""
  for candidate in "${ZIP_CANDIDATES[@]}"; do
    if [[ -f "$candidate" ]]; then ZIP_PATH="$candidate"; break; fi
  done
  [[ -n "$ZIP_PATH" ]] || die "Project not found. Put neoos-super-mcp.zip in Android Download or extract the project under ~/neoos-super-mcp."
  command -v unzip >/dev/null 2>&1 || die "unzip missing. Run: apt install -y unzip"
  TMP_DIR="$(mktemp -d "${HOME}/.neoos-super-mcp-extract.XXXXXX")"
  trap 'rm -rf "$TMP_DIR"' EXIT
  say "Extracting project archive from $ZIP_PATH"
  unzip -q "$ZIP_PATH" -d "$TMP_DIR"
  PROJECT_FILE="$(find "$TMP_DIR" -maxdepth 5 -type f -name pyproject.toml -print -quit)"
  [[ -n "$PROJECT_FILE" ]] || die "ZIP extracted, but pyproject.toml was not found. Check that this is the NeoOS Super MCP archive."
  PROJECT="$(dirname "$PROJECT_FILE")"
  mkdir -p "$PROJECT_HOME"
  # Copy only when canonical project is absent; do not overwrite an existing project.
  if [[ "$PROJECT" != "$PROJECT_HOME" && ! -f "$PROJECT_HOME/pyproject.toml" ]]; then
    cp -a "$PROJECT/." "$PROJECT_HOME/"
    PROJECT="$PROJECT_HOME"
  fi
fi

[[ -f "${PROJECT}/pyproject.toml" ]] || die "Could not resolve project directory."
say "Project: $PROJECT"
cd "$PROJECT"

if [[ ! -x .venv/bin/python ]]; then
  say "Creating Python virtual environment"
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate

say "Installing project dependencies (optional Ruff lint package is intentionally skipped)"
python -m pip install --upgrade pip
python -m pip install -e .
python -m pip install 'pytest>=8,<9'

say "Running unit tests"
pytest -q

say "Running MCP protocol smoke test"
python scripts/protocol_smoke.py

say "SUCCESS: installation and both test stages passed."
printf 'Project: %s\n' "$PROJECT"
printf 'Activate later with: source "%s/.venv/bin/activate"\n' "$PROJECT"
