from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd


def load_stp_template(path: str) -> Optional[pd.DataFrame]:
    if not path:
        return None
    stp_path = Path(path)
    if not stp_path.exists():
        return None
    return pd.read_excel(stp_path)
