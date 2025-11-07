# scripts/export_openapi.py
import yaml
from main import app

with open("openapi.yaml", "w") as f:
    yaml.dump(app.openapi(), f)