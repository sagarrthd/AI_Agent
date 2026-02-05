from pathlib import Path
from testgenai.ingestion.doc_parser import load_requirements
from testgenai.ingestion.stp_loader import load_stp_template
from testgenai.a2l.a2l_parser import load_a2l_signals
from testgenai.components.components_parser import load_components
from testgenai.rules.rule_engine import RuleEngine
from testgenai.models.requirement import Requirement
from testgenai.mapping.traceability import build_trace_matrix
from testgenai.reports.stp_writer import write_stp_output
from testgenai.llm_copilot.copilot_session import CopilotSession
from testgenai.llm_copilot.prompt_builder import build_prompt
from testgenai.llm_copilot.response_parser import parse_table_response
from testgenai.models.testcase import TestCase, TestStep
from testgenai.teststand.xml_builder import build_teststand_xml
from testgenai.reports.analysis_report import write_requirements_report
from testgenai.reports.scenarios_doc import write_scenarios_doc
from testgenai.scenarios.generator import build_scenarios
from testgenai.storage.db import init_db
from testgenai.storage.step_library import load_step_library
from testgenai.storage.vi_library import load_vi_library
from testgenai.ingestion.srs_parser import load_srs
from testgenai.ingestion.doc_parser import read_config


def run_pipeline(config_path: str) -> None:
    cfg = read_config(config_path)

    req_dicts = load_requirements(cfg["inputs"]["requirements_file"])
    requirements = [
        Requirement(
            req_id=r["req_id"],
            title=r["title"],
            description=r["description"],
            req_type=r.get("req_type", "functional"),
        )
        for r in req_dicts
    ]
    srs = load_srs(cfg["inputs"]["srs_file"])
    _ = srs
    components = load_components(cfg["inputs"]["components_file"])
    _ = components
    signals = load_a2l_signals(cfg["inputs"]["a2l_file"])
    _ = signals

    stp_template = load_stp_template(cfg["inputs"]["stp_template"])
    _ = stp_template

    init_db()
    step_library = load_step_library()
    vi_library = load_vi_library()

    engine = RuleEngine()
    tests = engine.build_baseline_tests(requirements)

    if cfg.get("llm", {}).get("enabled") and cfg["llm"].get("copilot_url"):
        copilot = CopilotSession(
            cfg["llm"].get("browser_profile_path", ""),
            cfg["llm"].get("copilot_url", ""),
        )
        copilot.open()
        prompt = build_prompt(req_dicts, [s.__dict__ for s in signals], "")
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
        cfg["inputs"]["stp_template"],
        cfg["outputs"]["stp_output"],
        tests,
        trace,
        cfg["outputs"]["traceability_sheet"],
    )

    tree = build_teststand_xml(tests, step_library=step_library, vi_library=vi_library)
    tree.write(cfg["outputs"]["teststand_xml"], encoding="utf-8", xml_declaration=True)

    _ = trace


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
