#!/usr/bin/env bash
# setup.sh — First-time setup for OPERATOR-QI
set -euo pipefail

echo "==> OPERATOR-QI setup"

# Copy .env if missing
if [ ! -f .env ]; then
    cp .env.example .env
    echo "  ✓ .env created from .env.example"
fi

# Install backend deps
if command -v python3 &>/dev/null; then
    echo "  → Installing backend dependencies..."
    cd backend && pip install -e ".[dev]" -q && cd ..
    echo "  ✓ Backend deps installed"
fi

# Install frontend deps
if command -v node &>/dev/null; then
    echo "  → Installing frontend dependencies..."
    cd frontend && npm install -q && cd ..
    echo "  ✓ Frontend deps installed"
fi

echo ""
echo "  All done! Run 'make up' to start the services."
