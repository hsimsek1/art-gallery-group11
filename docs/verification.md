# Verification record (October 30, 2026)

## Checks actually performed while preparing this project

- Python `compileall` accepted all revised application and test `.py` files on October 30, 2026.
- SQLite successfully ran the revised `database/schema.sql` twice against an in-memory database, creating the six expected tables on October 30, 2026.
- Jinja2 successfully parsed all 10 revised HTML templates on October 30, 2026.
- The updated report was rendered from Markdown to a 4-page PDF and previewed.
- Existing GitHub repository was read and its Week 6 files compared with the source report.

## Checks not yet completed

- **Full pytest suite:** Flask/Flask-Login/Flask-WTF are not installed in this execution environment and installation failed due to unavailable package-index networking. Tests are written but not claimed to pass. Run `python -m pytest -q` after installing `requirements-dev.txt`.
- **Official correctness oracle:** Not provided. Must run when the course supplies it.
- **Public deployment / HTTPS:** Not performed. Local Docker instructions are provided.
- **Week 10 peer exploit results:** Assigned opposing team's code/harness not provided. No confirmed breaks claimed.
- **GitHub update:** GitHub integration returned HTTP 403 `Resource not accessible by integration` for create branch, create blob and create file. Upload/push requires working repository write authorization.

## Exact course instructions checklist
See `build_it_submission_checklist.md`, `api.md`, `week7-10_design_addendum.md`, and `tests/breakit/`. The original Weeks 4-6 design PDF was copied unchanged to `design_document.pdf`.

## October 30 final focused fixes

- Corrected `admin.html`: the administrator's **Add a person** form was accidentally inside the Jinja HTML title block; it now renders in the page body.
- Corrected the room-history assertion so it looks for an event-table cell instead of a name that can also appear in the search dropdown.
- Added a regression assertion that checks the person-creation form appears after the closing HTML head.
- The user reported their Windows pytest suite worked after the history assertion change, but the full suite could not be independently run in this review environment because Flask dependencies were unavailable. Do not represent the instructor oracle, Docker deployment, or GitHub publishing as verified.
