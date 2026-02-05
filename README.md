TestGenAI

TestGenAI is a Python project for generating test cases, traceability, and NI TestStand XML from requirements, A2L data, and component definitions.

Quick start
- Configure inputs in config/default.yaml
- Run: testgenai --config config/default.yaml

Outputs
- Excel test plan based on the STP template
- TestStand XML sequence file
- Requirements analysis report
- High-level scenario document
- Traceability matrix

Notes
- Copilot web automation requires a signed-in browser profile
- Update selectors in llm_copilot/copilot_session.py if the Copilot UI changes
