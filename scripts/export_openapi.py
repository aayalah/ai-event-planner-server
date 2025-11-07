# scripts/export_openapi.py
import yaml
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from main import app
with open("openapi.yaml", "w") as f:
    yaml.dump(app.openapi(), f)