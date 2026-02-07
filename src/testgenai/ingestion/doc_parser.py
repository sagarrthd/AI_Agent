from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, Iterable, List

import yaml


def read_config(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_requirements(path: str) -> List[dict]:
    if not path:
        return []
    text = _read_text(Path(path))
    return _split_requirements(text)


def load_requirements_from_sources(
    primary_path: str,
    additional_paths: Iterable[str] | None = None,
) -> List[dict]:
    """Load requirements from one or many mixed-format sources.

    Supported types include text/markdown, docx, pdf, xlsx and source artifacts
    such as C/C++/header/A2L files.
    """
    paths: list[str] = [primary_path] if primary_path else []
    if additional_paths:
        paths.extend([p for p in additional_paths if p])

    merged: list[dict] = []
    for source in paths:
        text = _read_text(Path(source))
        if not text.strip():
            continue
        merged.extend(_split_requirements(text, source_name=Path(source).name))

    return _renumber_requirements(merged)


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    suffix = path.suffix.lower()
    if suffix in [".txt", ".md", ".a2l"]:
        return path.read_text(encoding="utf-8", errors="ignore")
    if suffix == ".docx":
        return _read_docx(path)
    if suffix == ".pdf":
        return _read_pdf(path)
    if suffix in {".xlsx", ".xlsm", ".xls"}:
        return _read_xlsx(path)
    if suffix in {".c", ".h", ".hpp", ".cpp"}:
        return _read_c_like(path)
    return path.read_text(encoding="utf-8", errors="ignore")


def _read_xlsx(path: Path) -> str:
    try:
        import pandas as pd
    except ImportError:
        print(f"Warning: Skipping '{path.name}' - pandas library is not installed.")
        return ""

    try:
        df = pd.read_excel(path)
        text_content = []
        for col in df.columns:
            text_content.append(str(col))
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

    doc = Document(path)
    return "\n".join(p.text for p in doc.paragraphs)


def _read_pdf(path: Path) -> str:
    try:
        from pdfminer.high_level import extract_text
    except ImportError:
        print(f"Warning: Skipping '{path.name}' - pdfminer.six library is not installed.")
        return ""

    return extract_text(str(path)) or ""


def _read_c_like(path: Path) -> str:
    content = path.read_text(encoding="utf-8", errors="ignore")
    lines: list[str] = []

    comment_matches = re.findall(r"//\s*(.+)", content)
    block_matches = re.findall(r"/\*(.*?)\*/", content, flags=re.DOTALL)
    lines.extend(comment_matches)
    for block in block_matches:
        lines.extend([seg.strip(" *") for seg in block.splitlines() if seg.strip(" *")])

    signature_matches = re.findall(
        r"^\s*[A-Za-z_][\w\s\*]+\s+([A-Za-z_]\w*)\s*\(([^;{}]*)\)\s*\{",
        content,
        flags=re.MULTILINE,
    )
    for fn_name, params in signature_matches:
        param_text = " ".join(params.split())
        lines.append(f"Function behavior: {fn_name}({param_text})")

    define_matches = re.findall(r"^\s*#define\s+([A-Za-z_]\w*)\s+(.+)$", content, flags=re.MULTILINE)
    for key, value in define_matches:
        lines.append(f"Constraint: {key} = {value.strip()}")

    return "\n".join(lines)


def _split_requirements(text: str, source_name: str = "") -> List[dict]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    requirements = []

    req_pattern = re.compile(r"^(REQ[-_ ]?\d+)[:\-\s]+(.+)$", re.IGNORECASE)

    for idx, line in enumerate(lines, start=1):
        match = req_pattern.match(line)
        if match:
            req_id = match.group(1).upper().replace(" ", "-").replace("_", "-")
            description = match.group(2).strip()
        else:
            req_id = f"REQ-{idx:04d}"
            description = line

        title = description[:60]
        if source_name:
            title = f"[{source_name}] {title}"[:60]

        requirements.append(
            {
                "req_id": req_id,
                "title": title,
                "description": description,
                "req_type": "functional",
            }
        )
    return requirements


def _renumber_requirements(requirements: List[dict]) -> List[dict]:
    """Ensure IDs are unique and deterministic after multi-file merge."""
    used: set[str] = set()
    for idx, req in enumerate(requirements, start=1):
        req_id = req.get("req_id") or f"REQ-{idx:04d}"
        if req_id in used:
            req_id = f"REQ-{idx:04d}"
        req["req_id"] = req_id
        used.add(req_id)
    return requirements
