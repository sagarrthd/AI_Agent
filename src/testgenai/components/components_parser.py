from __future__ import annotations

from pathlib import Path
from typing import Any, Dict
import json

import pandas as pd


def load_components(path: str) -> Dict[str, Any]:
    if not path:
        return {}
    comp_path = Path(path)
    if not comp_path.exists():
        return {}
    suffix = comp_path.suffix.lower()
    if suffix == ".json":
        return json.loads(comp_path.read_text(encoding="utf-8"))
    if suffix in [".xlsx", ".xls"]:
        return {"table": pd.read_excel(comp_path).to_dict(orient="records")}
    if suffix in [".xml"]:
        return {"xml": comp_path.read_text(encoding="utf-8", errors="ignore")}
    return {"text": comp_path.read_text(encoding="utf-8", errors="ignore")}
