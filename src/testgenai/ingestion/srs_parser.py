from __future__ import annotations

from typing import List

from pathlib import Path

from testgenai.ingestion.doc_parser import _read_text, _split_requirements


def load_srs(path: str) -> List[dict]:
    if not path:
        return []
    text = _read_text(Path(path))
    return _split_requirements(text)
