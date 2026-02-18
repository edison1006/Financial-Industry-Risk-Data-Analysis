#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${PG_URL:-}" ]]; then
  echo "Missing PG_URL. Example:"
  echo "  export PG_URL='postgresql://user:pwd@localhost:5432/loan_demo'"
  exit 2
fi

python run_all.py
