#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH="$PWD"
streamlit run streamlit_app.py --server.address 0.0.0.0 --server.port 8501