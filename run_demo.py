#!/usr/bin/env python3
"""
Simple demo script to run Test GenAI without optional dependencies
"""
import sys
sys.path.insert(0, 'src')

from pathlib import Path
from testgenai.ingestion.doc_parser import load_requirements, read_config
from testgenai.models.requirement import Requirement
from testgenai.rules.rule_engine import RuleEngine
from testgenai.mapping.traceability import build_trace_matrix
from testgenai.reports.stp_writer import write_stp_output

def main():
    print("="*60)
    print("TestGenAI - Simple Demo Run")
    print("="*60)
    
    # Load configuration
    print("\n[1/6] Loading configuration...")
    cfg = read_config("config.yaml")
    print(f"✓ Project: {cfg['project']['name']}")
    
    # Load requirements
    print("\n[2/6] Loading requirements...")
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
    print(f"✓ Loaded {len(requirements)} requirements")
    
    # Generate baseline tests using rule engine
    print("\n[3/6] Generating test cases using rule engine...")
    engine = RuleEngine()
    tests = engine.build_baseline_tests(requirements)
    print(f"✓ Generated {len(tests)} test cases")
    
    # Build traceability matrix
    print("\n[4/6] Building traceability matrix...")
    trace = build_trace_matrix(requirements, tests)
    print(f"✓ Mapped {len(trace)} requirements to tests")
    
    # Create output directory
    print("\n[5/6] Creating output directory...")
    out_dir = Path(cfg["outputs"]["stp_output"]).parent
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"✓ Output directory: {out_dir}")
    
    # Write Excel test plan
    print("\n[6/6] Writing Excel test plan...")
    write_stp_output(
        cfg["inputs"]["stp_template"],
        cfg["outputs"]["stp_output"],
        tests,
        trace,
        cfg["outputs"]["traceability_sheet"],
    )
    print(f"✓ Test plan written to: {cfg['outputs']['stp_output']}")
    
    print("\n" + "="*60)
    print("SUCCESS! Test plan generated successfully")
    print("="*60)
    
    print("\n📊 Summary:")
    print(f"  - Requirements processed: {len(requirements)}")
    print(f"  - Test cases generated: {len(tests)}")
    print(f"  - Output file: {cfg['outputs']['stp_output']}")
    
    print("\n📋 Sample test cases:")
    for i, test in enumerate(tests[:3], 1):
        print(f"  {i}. {test.test_id}: {test.title}")
    
    if len(tests) > 3:
        print(f"  ... and {len(tests) - 3} more")
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
