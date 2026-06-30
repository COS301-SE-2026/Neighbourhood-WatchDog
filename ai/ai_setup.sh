#!/bin/bash
# Neighbourhood WatchDog - AI Service One-Time Setup Script
# Run this once after cloning the repo on a new machine
# 

set -e

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SYMLINK=~/watchdog

echo "============================================"
echo "  Neighbourhood WatchDog - AI Setup"
echo "============================================"

#  Step 1: Create symlink (avoids spaces-in-path PyTorch crash)
echo ""
echo "[1/5] Creating symlink ~/watchdog -> $REPO_DIR"
if [[ -L "$SYMLINK" ]]; then
    echo "      Symlink already exists — skipping"
else
    ln -s "$REPO_DIR" "$SYMLINK"
    echo "      Done: ~/watchdog -> $REPO_DIR"
fi

#  Step 2: Python venv
echo ""
echo "[2/5] Setting up Python virtual environment"
cd ~/watchdog/ai

if [[ -d ".venv" ]]; then
    echo "      .venv already exists — skipping creation"
else
    python3 -m venv .venv
    echo "      .venv created"
fi

source .venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
echo "      Python dependencies installed"

#  Step 3: Download model weights 
echo ""
echo "[3/5] Downloading model weights"

WEIGHTS_DIR=~/watchdog/ai/pipeline/models/weights
mkdir -p "$WEIGHTS_DIR"

if [[ -f "$WEIGHTS_DIR/best.pt" ]]; then
    echo "      best.pt already exists — skipping"
else
    echo "      Downloading threat detection model from HuggingFace..."
    python3 - << 'PYEOF'
from huggingface_hub import hf_hub_download
import os
path = hf_hub_download(
    repo_id="Subh775/Threat-Detection-YOLOv8n",
    filename="weights/best.pt",
    local_dir=os.path.expanduser("~/watchdog/ai/pipeline/models/weights/")
)
print(f"      Downloaded to: {path}")
PYEOF
fi

if [[ -f "$WEIGHTS_DIR/yolov8n.pt" ]]; then
    echo "      yolov8n.pt already exists — skipping"
else
    echo "      Downloading YOLOv8n (person detection) from Ultralytics..."
    python3 -c "from ultralytics import YOLO; YOLO('yolov8n.pt')" 2>/dev/null
    # Move to weights dir if downloaded to current dir
    [[ -f "yolov8n.pt" ]] && mv yolov8n.pt "$WEIGHTS_DIR/"
    echo "      Done"
fi

#  Step 4: Patch deep_sort_realtime for Python 3.12 
echo ""
echo "[4/5] Patching deep_sort_realtime for Python 3.12 compatibility"

python3 - << 'PYEOF'
import re, os

filepath = os.path.expanduser(
    "~/watchdog/ai/.venv/lib/python3.12/site-packages/deep_sort_realtime/embedder/embedder_pytorch.py"
)

if not os.path.exists(filepath):
    print("      File not found — skipping patch (may be a different Python version)")
    exit(0)

with open(filepath) as f:
    content = f.read()

if "pkg_resources" not in content:
    print("      Already patched — skipping")
    exit(0)

content = content.replace("import pkg_resources", "import os as _os")
content = content.replace("from setuptools import pkg_resources", "import os as _os")
content = re.sub(
    r'pkg_resources\.resource_filename\(["\']deep_sort_realtime["\'],\s*',
    '_os.path.join(_os.path.dirname(_os.path.dirname(__file__)), ',
    content
)

with open(filepath, "w") as f:
    f.write(content)

print("      Patched successfully")
PYEOF

#  Step 5: Frontend dependencies 
echo ""
echo "[5/5] Installing frontend dependencies"
cd ~/watchdog/frontend

if [[ -d "node_modules" ]]; then
    echo "      node_modules already exists — skipping"
else
    npm install --silent
    echo "      Done"
fi

#  Done 
echo ""
echo "  Setup complete!"
echo ""
echo "  To start the project, run these in"
echo "  separate terminals:"
echo ""
echo "  Terminal 1 (infrastructure):"
echo "    cd ~/watchdog"
echo "    docker compose up postgres backend mediamtx"
echo ""
echo "  Terminal 2 (AI service):"
echo "    cd ~/watchdog/ai"
echo "    source .venv/bin/activate"
echo "    export MKL_THREADING_LAYER=GNU"
echo "    export BACKEND_URL=http://localhost:8000"
echo "    uvicorn app:app --host 0.0.0.0 --port 8001"
echo ""
echo "  Terminal 3 (frontend):"
echo "    cd ~/watchdog/frontend"
echo "    npm run dev"
echo ""
echo "  Then open: http://localhost:3000"
