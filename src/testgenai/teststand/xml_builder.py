from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from typing import List, Dict, Any

from testgenai.models.testcase import TestCase


def build_teststand_xml(
    testcases: List[TestCase],
    step_library: List[Dict[str, Any]] | None = None,
    vi_library: List[Dict[str, Any]] | None = None,
) -> ET.ElementTree:
    root = ET.Element("TestStandSequenceFile")
    _add_type_definitions(root, step_library or [], vi_library or [])
    _add_variable_section(root, testcases)
    _add_step_templates(root, step_library or [])
    seq = ET.SubElement(root, "Sequence", {"Name": "MainSequence"})
    _add_sequence_variables(seq, testcases)

    for tc in testcases:
        step = ET.SubElement(seq, "Step", {"Name": tc.title, "Type": "Action"})
        if tc.preconditions:
            ET.SubElement(step, "Preconditions").text = tc.preconditions
        _add_requirements(step, tc.requirements)

        for s in tc.steps:
            action = ET.SubElement(step, "Action")
            ET.SubElement(action, "Description").text = s.action
            ET.SubElement(action, "Expected").text = s.expected
            _add_requirements(action, s.requirement_ids)
            _add_template_ref(action, step_library or [], s.action)
            _add_vi_call(action, vi_library or [], s.action)

    return ET.ElementTree(root)


def _add_variable_section(root: ET.Element, testcases: List[TestCase]) -> None:
    vars_node = ET.SubElement(root, "Variables")
    req_ids = sorted({req for tc in testcases for req in tc.requirements})
    for req_id in req_ids:
        var = ET.SubElement(vars_node, "Variable", {"Name": req_id, "Type": "String"})
        var.text = req_id


def _add_sequence_variables(seq: ET.Element, testcases: List[TestCase]) -> None:
    vars_node = ET.SubElement(seq, "Variables")
    ET.SubElement(vars_node, "Variable", {"Name": "CurrentTestId", "Type": "String"})
    ET.SubElement(vars_node, "Variable", {"Name": "CurrentRequirementIds", "Type": "String"})
    ET.SubElement(vars_node, "Variable", {"Name": "TotalTests", "Type": "Number"}).text = str(
        len(testcases)
    )


def _add_step_templates(root: ET.Element, step_library: List[Dict[str, Any]]) -> None:
    if not step_library:
        return
    templates = ET.SubElement(root, "StepTemplates")
    for entry in step_library:
        template = ET.SubElement(templates, "Template", {"Name": entry.get("name", "")})
        ET.SubElement(template, "Description").text = entry.get("description", "")
        _add_parameters(template, entry.get("parameters_json", ""))


def _add_type_definitions(
    root: ET.Element,
    step_library: List[Dict[str, Any]],
    vi_library: List[Dict[str, Any]],
) -> None:
    type_defs = ET.SubElement(root, "TypeDefinitions")
    ET.SubElement(type_defs, "TypeDefinition", {"Name": "String", "Kind": "Scalar"})
    ET.SubElement(type_defs, "TypeDefinition", {"Name": "Number", "Kind": "Scalar"})
    _add_custom_param_types(type_defs, step_library)
    _add_custom_param_types(type_defs, vi_library)


def _add_custom_param_types(type_defs: ET.Element, library: List[Dict[str, Any]]) -> None:
    seen: set[str] = set()
    for entry in library:
        params = _load_params(entry.get("parameters_json", ""))
        if not isinstance(params, dict):
            continue
        for key in params.keys():
            type_name = f"Param_{key}"
            if type_name in seen:
                continue
            seen.add(type_name)
            ET.SubElement(type_defs, "TypeDefinition", {"Name": type_name, "Kind": "Scalar"})


def _add_template_ref(parent: ET.Element, step_library: List[Dict[str, Any]], action: str) -> None:
    match = _match_library(action, step_library)
    if match:
        ET.SubElement(parent, "TemplateRef", {"Name": match.get("name", "")})


def _add_vi_call(parent: ET.Element, vi_library: List[Dict[str, Any]], action: str) -> None:
    match = _match_library(action, vi_library)
    if not match:
        return
    call = ET.SubElement(parent, "CallVI", {"Name": match.get("name", "")})
    ET.SubElement(call, "Path").text = match.get("path", "")
    _add_parameters(call, match.get("parameters_json", ""))


def _add_requirements(parent: ET.Element, req_ids: List[str]) -> None:
    if not req_ids:
        return
    reqs = ET.SubElement(parent, "Requirements")
    for req_id in req_ids:
        ET.SubElement(reqs, "Requirement", {"ID": req_id})


def _add_parameters(parent: ET.Element, params_json: str) -> None:
    params = _load_params(params_json)
    if not isinstance(params, dict):
        return
    params_node = ET.SubElement(parent, "Parameters")
    if isinstance(params, dict):
        for key, value in params.items():
            param = ET.SubElement(params_node, "Parameter", {"Name": str(key)})
            param.text = str(value)


def _load_params(params_json: str) -> Any:
    if not params_json:
        return None
    try:
        return json.loads(params_json)
    except json.JSONDecodeError:
        return None


def _match_library(action: str, library: List[Dict[str, Any]]) -> Dict[str, Any] | None:
    text = action.lower()
    for entry in library:
        name = str(entry.get("name", ""))
        if name and name.lower() in text:
            return entry
    return None
