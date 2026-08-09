#!/usr/bin/env bash
# ================================================
#  CivicAssist — Frontend Startup Script (Mac/Linux)
# ================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT/frontend"

echo "CivicAssist - Iniciando frontend..."
echo "============================================"

# Check node
if ! command -v node >/dev/null 2>&1; then
    echo "[ERROR] Node.js no encontrado. Instale Node.js 18+"
    exit 1
fi

# Install if needed
if [ ! -d "node_modules" ]; then
    echo "[INFO] Instalando dependencias npm..."
    npm install
fi

echo "[INFO] Iniciando frontend en http://localhost:3000"
exec npm run dev
