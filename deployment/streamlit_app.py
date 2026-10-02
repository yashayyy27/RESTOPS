"""Public-only entry point; ignores local dataset/database environment overrides."""

import os
from pathlib import Path
import runpy

os.environ["RESTOPS_MODE"] = "public"
root = Path(__file__).resolve().parents[1]
runpy.run_path(str(root / "streamlit_app.py"), run_name="__main__")
