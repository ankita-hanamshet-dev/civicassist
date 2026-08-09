#!/usr/bin/env bash
# ================================================
#  CivicAssist — Backend Startup Script (Mac/Linux)
# ================================================
set -e

# Resolve repo root (parent of this scripts/ dir)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT/backend"

echo "CivicAssist - Iniciando backend..."
echo "============================================"

# Check Python
if ! command -v python3 >/dev/null 2>&1; then
    echo "[ERROR] Python no encontrado. Instale Python 3.10+"
    exit 1
fi

# Create venv if needed
if [ ! -d "venv" ]; then
    echo "[INFO] Creando entorno virtual..."
    python3 -m venv venv
fi

# Activate
source venv/bin/activate

# Install deps
echo "[INFO] Instalando dependencias..."
pip install -q -r requirements.txt

# Warn if no API key configured
if [ ! -f ".env" ]; then
    echo "[WARN] No se encontró backend/.env — configure LLM_API_KEY (o ANTHROPIC_API_KEY)."
fi

echo "[INFO] Iniciando FastAPI en http://localhost:8000"
echo "[INFO] Documentacion: http://localhost:8000/docs"
exec python main.py
