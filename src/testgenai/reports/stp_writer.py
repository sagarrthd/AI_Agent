from __future__ import annotations

from copy import copy
from pathlib import Path
from typing import Dict, List, Tuple

import openpyxl

from testgenai.models.testcase import TestCase


_FIELD_KEYWORDS = {
    "test_id": ["test id", "id", "case id", "identifier", "test_id"],
    "title": ["title", "summary", "test name", "case name", "test title"],
    "description": ["description", "objective", "purpose", "test scenario"],
    "preconditions": ["preconditions", "pre-requisites", "setup", "pinned", "pin state"],
    "steps": ["steps", "actions", "procedure", "test steps", "step description", "debugger action"],
    "expected": ["expected", "expected result", "expected behavior", "writes expected"],
    "requirements": ["requirement", "req id", "traceability", "ref"],
}


def write_stp_output(
    template_path: str,
    output_path: str,
    tests: List[TestCase],
    trace_matrix: Dict[str, List[str]],
    trace_sheet_name: str,
) -> None:
    if not template_path or not Path(template_path).exists():
        raise FileNotFoundError(f"Template file not found: {template_path}")

    wb = openpyxl.load_workbook(template_path)

    target_sheet, header_row, header_map = _find_test_sheet(wb)
    _fill_test_sheet(target_sheet, tests, header_row, header_map)

    if trace_sheet_name:
        trace_sheet = wb[trace_sheet_name] if trace_sheet_name in wb.sheetnames else wb.create_sheet(trace_sheet_name)
        _fill_trace_sheet(trace_sheet, trace_matrix)

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    wb.save(output)


def _find_test_sheet(workbook: openpyxl.Workbook) -> Tuple[openpyxl.worksheet.worksheet.Worksheet, int, Dict[str, int]]:
    for sheet_name in workbook.sheetnames:
        sheet = workbook[sheet_name]
        for row_idx in range(1, min(sheet.max_row, 50) + 1):
            row_values = [str(c.value).strip().lower() if c.value else "" for c in sheet[row_idx]]
            if _looks_like_header(row_values):
                return sheet, row_idx, _build_header_map(row_values)

    return workbook.active, 1, {}


def _looks_like_header(row_values: List[str]) -> bool:
    has_id = any("test id" in v or "case id" in v for v in row_values)
    has_body = any("step" in v for v in row_values) or any("title" in v for v in row_values)
    return has_id and has_body


def _build_header_map(row_values: List[str]) -> Dict[str, int]:
    header_map: Dict[str, int] = {}
    for col_idx, cell_value in enumerate(row_values, 1):
        for field, keywords in _FIELD_KEYWORDS.items():
            if field in header_map:
                continue
            if any(k in cell_value for k in keywords):
                header_map[field] = col_idx
    return header_map


def _fill_test_sheet(sheet, tests: List[TestCase], header_row: int, header_map: Dict[str, int]) -> None:
    if not header_map:
        header_map = {
            "test_id": 1,
            "title": 2,
            "description": 3,
            "preconditions": 4,
            "steps": 5,
            "expected": 6,
            "requirements": 7,
        }

    start_row = header_row + 1
    _clear_existing_rows(sheet, start_row, header_map)

    template_style_row = _resolve_style_row(sheet, start_row)

    for offset, test in enumerate(tests):
        row = start_row + offset
        steps_text = "\n".join(f"{i + 1}. {s.action}" for i, s in enumerate(test.steps))
        expected_text = "\n".join(f"{i + 1}. {s.expected}" for i, s in enumerate(test.steps))

        values = {
            "test_id": test.test_id,
            "title": test.title,
            "description": test.title,
            "preconditions": test.preconditions,
            "steps": steps_text,
            "expected": expected_text,
            "requirements": ", ".join(test.requirements),
        }

        for field, col in header_map.items():
            cell = sheet.cell(row=row, column=col)
            cell.value = values.get(field, "")
            _copy_cell_style(sheet, template_style_row, row, col)


def _clear_existing_rows(sheet, start_row: int, header_map: Dict[str, int]) -> None:
    for row in range(start_row, sheet.max_row + 1):
        if not any(sheet.cell(row=row, column=col).value for col in header_map.values()):
            continue
        for col in header_map.values():
            sheet.cell(row=row, column=col).value = None


def _resolve_style_row(sheet, start_row: int) -> int:
    for row in range(start_row, min(sheet.max_row, start_row + 10) + 1):
        if any(sheet.cell(row=row, column=col).has_style for col in range(1, sheet.max_column + 1)):
            return row
    return max(start_row - 1, 1)


def _copy_cell_style(sheet, src_row: int, dst_row: int, col: int) -> None:
    src = sheet.cell(row=src_row, column=col)
    dst = sheet.cell(row=dst_row, column=col)
    if src.has_style:
        dst._style = copy(src._style)
    if src.number_format:
        dst.number_format = src.number_format
    if src.alignment:
        dst.alignment = copy(src.alignment)


def _fill_trace_sheet(sheet, trace_matrix: Dict[str, List[str]]) -> None:
    sheet.delete_rows(1, sheet.max_row)
    sheet.cell(row=1, column=1, value="Requirement ID")
    sheet.cell(row=1, column=2, value="Test Cases")

    for row_idx, (req, tests) in enumerate(trace_matrix.items(), start=2):
        sheet.cell(row=row_idx, column=1, value=req)
        sheet.cell(row=row_idx, column=2, value=", ".join(tests))
