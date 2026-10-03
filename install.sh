#!/usr/bin/env bash
# install.sh — one-command ISHA installer (Linux/macOS).
#
#   bash install.sh
#
# Creates .venv/, installs the wheel (or falls back to the source tree),
# copies .env.example to .env. Afterwards:  source .venv/bin/activate && isha doctor
set -euo pipefail
cd "$(dirname "$0")"

REPO="$(pwd)"
VENV="$REPO/.venv"
WHEEL="$(ls -1t "$REPO"/dist/isha_fix-*.whl 2>/dev/null | head -n1 || true)"

echo "ISHA installer (repo: $REPO)"

if ! command -v python3 >/dev/null; then
  echo "python3 not found on PATH" >&2; exit 1
fi
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)' \
  || { echo "Python 3.10+ required" >&2; exit 1; }

if [ ! -d "$VENV" ]; then
  echo "Creating .venv ..."
  python3 -m venv "$VENV"
fi
PY="$VENV/bin/python"

echo "Installing ISHA + dependencies (first run downloads a few hundred MB; torch/CUDA via docling are the bulk) ..."
"$PY" -m pip install --upgrade pip >/dev/null
if [ -n "$WHEEL" ]; then
  echo "Installing wheel: $WHEEL"
  "$PY" -m pip install "$WHEEL"
else
  echo "No wheel in dist/ — installing from source tree"
  "$PY" -m pip install "$REPO"
fi

if [ ! -f "$REPO/.env" ]; then
  cp "$REPO/.env.example" "$REPO/.env"
  echo "Created .env from .env.example — add your GROQ_API_KEY / GOOGLE_API_KEY"
fi

"$VENV/bin/isha" --help >/dev/null

echo
echo "Done. Next steps:"
echo "  $REPO/.env  -> add your API keys"
echo "  source $VENV/bin/activate && isha doctor"
echo "  isha fix --repo <path-or-url> --issue '...' --apply"
