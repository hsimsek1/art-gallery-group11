# Week 10: executable break tests (no confirmed findings yet)

The course PDF requires a **test case that can be executed** against the anonymized assigned opposing team's version and a report with title, component, severity, description, reproduction, evidence, impact, root cause (if known), and mitigation. `test_candidate_access_control.py` is a local-only **candidate check**, not a real finding, and currently skips unless explicitly configured. It is not evidence of a vulnerability and does not stand in for the official test harness.

Use only the assigned target, approved scope, and the professor's provided harness. Capture the target commit/version, exact setup, smallest request payload/script, expected behavior based on target spec, actual output (with sanitized logs), severity rationale, and repeated reproducibility. Include a separate executable test file for each genuinely discovered break and reference that file from a completed copy of `docs/break_it_report_template.md`.

A passing check means the expected behavior happened (no break). A failed candidate check is **not automatically** a security vulnerability; investigate whether the expected response was correct and whether the resulting behavior violates a requirement. Do not submit hypothetical issues as confirmed vulnerabilities.
