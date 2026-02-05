from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import yaml


def read_config(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_requirements(path: str) -> List[dict]:
    if not path:
        return []
    text = _read_text(Path(path))
    return _split_requirements(text)


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    suffix = path.suffix.lower()
    if suffix in [".txt", ".md"]:
        return path.read_text(encoding="utf-8")
    if suffix == ".docx":
        return _read_docx(path)
    if suffix == ".pdf":
        return _read_pdf(path)
    return path.read_text(encoding="utf-8", errors="ignore")


def _read_docx(path: Path) -> str:
    from docx import Document

    doc = Document(path)
    return "\n".join(p.text for p in doc.paragraphs)


def _read_pdf(path: Path) -> str:
    from pdfminer.high_level import extract_text

    return extract_text(str(path)) or ""


def _split_requirements(text: str) -> List[dict]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    requirements = []
    for idx, line in enumerate(lines, start=1):
        req = {
            "req_id": f"REQ-{idx:04d}",
            "title": line[:60],
            "description": line,
            "req_type": "functional",
        }
        requirements.append(req)
    return requirements
