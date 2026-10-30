# Phase 2 / Build It: final submission instructions

Source: `F26_BIBIFI_Project-2.pdf`, section 5 (Week 9), section 6 (repository structure). The course PDF does NOT state a Canvas-specific file upload format or define a separate PDF report for Phase 2. Check the Canvas assignment page before the 11:59 PM deadline.

## Required in the submitted repository

- `README.md`: purpose, team, stack, architecture, setup, roles, routes, tests, security, limitations.
- `src/backend/` and `src/frontend/`: web UI, backend logic, security controls.
- `database/schema.sql`, `database/seed.sql`: persistent relational database.
- `tests/functional/`, `tests/security/`: test source.
- `docs/design_document.pdf`: prior Weeks 4–6 secure design and STRIDE threat model (not rewritten).
- `docs/api.md`: backend route documentation.
- `docker-compose.yml`, `Dockerfile`, README deployment section: reproducibility.

The extra Week 7–10 report PDF is supplemental; the course PDF does not require a separate Phase 2 report PDF. The Week 10 Break It report is a distinct deliverable requiring the anonymized opponent and executable vulnerabilities; templates are not actual findings.

## On your Windows PowerShell computer

From the project root:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m flask --app src.backend init-db
.\.venv\Scripts\python.exe -m flask --app src.backend seed
.\.venv\Scripts\python.exe -m flask --app src.backend run --host=127.0.0.1 --port=5678
```

Use a browser to log in as an administrator and employee, record a person entering and leaving the gallery and a room, confirm counts and history, and check forbidden guest actions. Stop Flask with Ctrl+C.

```powershell
git status --short
git diff --check
git check-ignore instance/config.py local-credentials.txt
git add .
git diff --cached --name-only
git diff --cached --check
git commit -m "Complete Build It Weeks 7-9"
git push -u origin weeks7-10-build-it
```

**Before committing:** The staged file list must not include `.venv/`, `instance/`, `local-credentials.txt`, real databases, passwords, or API keys. If it does, stop and unstage those items. Do not commit generated credentials. Verify the pushed branch exists at `https://github.com/hsimsek1/art-gallery-group11/tree/weeks7-10-build-it`. The main branch remains on Week 6 until merged, so if grading expects a default-branch GitHub link, merge your changes or provide the direct branch/commit link as Canvas specifies.

If the instructor provided correctness oracle scripts, run them as directed and record results. Otherwise note they were unavailable; local pytest does not substitute for the oracle.

## Canvas

1. Open **Project Phase 2** on Canvas and read its required submission type. The PDF itself does not say whether Canvas needs a URL, ZIP, report, or several fields.
2. Submit the required GitHub URL (prefer the updated branch or merged `main`), and any ZIP/report requested by Canvas. Don't assume uploading a ZIP is always required.
3. Verify the link is accessible and points to the updated implementation, not the original Week 6 `main` branch.
4. Confirm Canvas displays **Submitted** and an appropriate timestamp before 11:59 PM.

## Week 10 (separate)

The course PDF specifically requires real executable peer vulnerability tests, with title, affected endpoint, severity, attack explanation, steps, evidence, impact, root cause if known, and recommended mitigation. The skeleton in `tests/breakit/` is only a starting point and does not earn validated-break credit by itself.
