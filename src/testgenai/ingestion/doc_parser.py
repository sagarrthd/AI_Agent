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
    if suffix == ".xlsx":
        return _read_xlsx(path)
    return path.read_text(encoding="utf-8", errors="ignore")


def _read_xlsx(path: Path) -> str:
    try:
        import pandas as pd
    except ImportError:
        print(f"Warning: Skipping '{path.name}' - pandas library is not installed.")
        return ""
    except Exception as e:
        print(f"Warning: Failed to read '{path.name}' - {e}")
        return ""

    try:
        df = pd.read_excel(path)
        # Convert all content to string and join with newlines
        text_content = []
        for col in df.columns:
            # Add column header as context
            text_content.append(str(col))
            # Add all non-null values in the column
            text_content.extend(df[col].dropna().astype(str).tolist())
        return "\n".join(text_content)
    except Exception as e:
        print(f"Warning: Failed to parse '{path.name}' as Excel - {e}")
        return ""


def _read_docx(path: Path) -> str:
    try:
        from docx import Document
    except ImportError:
        print(f"Warning: Skipping '{path.name}' - python-docx library is not installed.")
        return ""
    except Exception as e:
        print(f"Warning: Failed to read '{path.name}' - {e}")
        return ""

    doc = Document(path)
    return "\n".join(p.text for p in doc.paragraphs)


def _read_pdf(path: Path) -> str:
    try:
        from pdfminer.high_level import extract_text
    except ImportError:
        print(f"Warning: Skipping '{path.name}' - pdfminer.six library is not installed.")
        return ""
    except Exception as e:
        print(f"Warning: Failed to read '{path.name}' - {e}")
        return ""

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
