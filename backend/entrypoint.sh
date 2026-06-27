#!/usr/bin/env bash
set -euo pipefail

echo "Booting Quran Notes backend..."

# Default paths; can be overridden via env
DB_URL="${DATABASE_URL:-sqlite:///./data/quran_notes.db}"
TMP_DIR="${TMP_DIR:-./data/tmp}"

# Only ensure the sqlite file path when using sqlite
if [[ "${DB_URL}" == sqlite:* ]]; then
  sqlite_path="${DB_URL#sqlite://}"
  # Trim leading slashes for relative paths; absolute paths will be preserved
  sqlite_dir="$(dirname "${sqlite_path#//}")"
  mkdir -p "${sqlite_dir}" || true
fi

mkdir -p "${TMP_DIR}" || true

echo "Applying database migrations..."
alembic upgrade head

echo "Starting uvicorn on port ${PORT:-8000} ..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" --workers 1

