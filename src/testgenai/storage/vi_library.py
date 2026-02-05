from __future__ import annotations

from typing import List, Dict, Any

from testgenai.storage.db import init_db


def load_vi_library() -> List[Dict[str, Any]]:
    conn = init_db()
    rows = conn.execute("SELECT vi_id, name, path, description, parameters_json FROM labview_vis").fetchall()
    conn.close()
    return [
        {"vi_id": r[0], "name": r[1], "path": r[2], "description": r[3], "parameters_json": r[4]}
        for r in rows
    ]
