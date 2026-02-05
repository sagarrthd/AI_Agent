from __future__ import annotations

from typing import List, Dict, Any

from testgenai.storage.db import init_db


def load_step_library() -> List[Dict[str, Any]]:
    conn = init_db()
    rows = conn.execute("SELECT step_id, name, description, parameters_json FROM teststand_steps").fetchall()
    conn.close()
    return [
        {"step_id": r[0], "name": r[1], "description": r[2], "parameters_json": r[3]}
        for r in rows
    ]
