# scripts/export_openapi.py
from main import app
import yaml
with open("openapi.yaml", "w") as f:
    yaml.dump(app.openapi(), f)