from pathlib import Path

from testgenai.a2l.a2l_parser import load_a2l_signals
from testgenai.components.components_parser import load_components
from testgenai.ingestion.doc_parser import (
    load_requirements_from_sources,
    read_config,
)
from testgenai.ingestion.srs_parser import load_srs
from testgenai.ingestion.stp_loader import load_stp_template_schema
from testgenai.mapping.traceability import build_trace_matrix
from testgenai.models.requirement import Requirement
from testgenai.models.testcase import TestCase, TestStep
from testgenai.reports.analysis_report import write_requirements_report
from testgenai.reports.scenarios_doc import write_scenarios_doc
from testgenai.reports.stp_writer import write_stp_output
from testgenai.rules.rule_engine import RuleEngine
from testgenai.scenarios.generator import build_scenarios
from testgenai.storage.db import init_db
from testgenai.storage.step_library import load_step_library
from testgenai.storage.vi_library import load_vi_library
from testgenai.teststand.xml_builder import build_teststand_xml


def run_pipeline(config_path: str) -> None:
    cfg = read_config(config_path)

    input_cfg = cfg.get("inputs", {})
    requirement_sources = input_cfg.get("requirements_files", [])
    code_sources = input_cfg.get("code_files", [])
    if input_cfg.get("code_file"):
        code_sources.append(input_cfg["code_file"])

    req_dicts = load_requirements_from_sources(
        input_cfg.get("requirements_file", ""),
        additional_paths=[*requirement_sources, *code_sources],
    )
    requirements = [
        Requirement(
            req_id=r["req_id"],
            title=r["title"],
            description=r["description"],
            req_type=r.get("req_type", "functional"),
        )
        for r in req_dicts
    ]

    srs = load_srs(input_cfg.get("srs_file", ""))
    _ = srs
    components = load_components(input_cfg.get("components_file", ""))
    _ = components
    signals = load_a2l_signals(input_cfg.get("a2l_file", ""))

    template_schema = load_stp_template_schema(input_cfg.get("stp_template", ""))

    init_db()
    step_library = load_step_library()
    vi_library = load_vi_library()

    engine = RuleEngine()
    tests = engine.build_baseline_tests(requirements)

    if cfg.get("llm", {}).get("enabled") and cfg["llm"].get("copilot_url"):
        from testgenai.llm_copilot.copilot_session import CopilotSession
        from testgenai.llm_copilot.prompt_builder import build_prompt
        from testgenai.llm_copilot.response_parser import parse_table_response

        copilot = CopilotSession(
            cfg["llm"].get("browser_profile_path", ""),
            cfg["llm"].get("copilot_url", ""),
        )
        copilot.open()
        code_context = "\n".join(
            r["description"] for r in req_dicts if r["title"].startswith("[") and "Function behavior" in r["description"]
        )
        prompt = build_prompt(
            req_dicts,
            [s.__dict__ for s in signals],
            cfg.get("llm", {}).get("extra_user_prompt", ""),
            template_schema=template_schema,
            code_context=code_context,
        )
        response = copilot.send_prompt(
            prompt, timeout_s=cfg["llm"].get("response_timeout_s", 120)
        )
        copilot.close()
        tests.extend(_rows_to_tests(parse_table_response(response)))

    trace = build_trace_matrix(requirements, tests)

    out_dir = Path(cfg["outputs"]["stp_output"]).parent
    out_dir.mkdir(parents=True, exist_ok=True)

    scenarios = build_scenarios(requirements, signals)
    write_requirements_report(requirements, cfg["outputs"]["analysis_report"])
    write_scenarios_doc(scenarios, cfg["outputs"]["scenarios_doc"])
    write_stp_output(
        input_cfg.get("stp_template", ""),
        cfg["outputs"]["stp_output"],
        tests,
        trace,
        cfg["outputs"]["traceability_sheet"],
    )

    tree = build_teststand_xml(tests, step_library=step_library, vi_library=vi_library)
    tree.write(cfg["outputs"]["teststand_xml"], encoding="utf-8", xml_declaration=True)



def _rows_to_tests(rows: list[dict]) -> list[TestCase]:
    tests: list[TestCase] = []
    for idx, row in enumerate(rows, start=1):
        reqs = [r.strip() for r in row.get("requirements", "").split(",") if r.strip()]
        step = TestStep(
            step_id=f"LLM-STEP-{idx}",
            action=row.get("steps", ""),
            expected=row.get("expected", ""),
            requirement_ids=reqs,
        )
        tests.append(
            TestCase(
                test_id=row.get("test_id", f"LLM-TC-{idx}"),
                title=row.get("title", "LLM Test"),
                preconditions=row.get("preconditions", ""),
                steps=[step],
                requirements=reqs,
            )
        )
    return tests
