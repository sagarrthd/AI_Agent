TestGenAI

TestGenAI is a Python project for generating test cases, traceability, and NI TestStand XML from requirements, A2L data, component definitions, and code artifacts.

Quick start
- Configure inputs in config/default.yaml
- Run: testgenai --config config/default.yaml

Inputs
- Requirements can be provided as TXT/MD, DOCX, PDF, XLSX.
- Additional mixed sources can be provided via `inputs.requirements_files`.
- C/C++/header files can be provided via `inputs.code_file` / `inputs.code_files`; comments, functions, and constraints are converted into requirement context.
- A2L is used both for signal extraction and LLM context.

Outputs
- Excel test plan based on the STP template (header-aware strict fill from the detected test-case header row)
- TestStand XML sequence file
- Requirements analysis report
- High-level scenario document
- Traceability matrix

Notes
- Copilot web automation requires a signed-in browser profile
- Update selectors in llm_copilot/copilot_session.py if the Copilot UI changes
