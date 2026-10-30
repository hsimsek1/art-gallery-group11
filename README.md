# Secure Art Gallery — BIBIFI Group 11

**Huseyin Simsek and Gustavo Pepe · Kent State University · Secure Programming · Fall 2026**

This Flask + SQLite app implements the Weeks **7–9 Build It** continuation of the Weeks 4–6 design. It keeps people, login accounts, rooms, event history and a security audit log. **Week 10 Break It** is a separate peer assessment: a report template and test plan are in `docs/`, but no peer vulnerabilities are claimed without the assigned opponent's code and test harness.

## Milestones

| Week | Implementation / deliverable |
| --- | --- |
| 4–6 | Existing Flask, SQLite, authentication, roles, initial schema and threat model preserved |
| 7 | Movement form, gallery/room entry and exit, derived occupancy, bounded history, 409 invalid-state responses, atomic event writes |
| 8 | Record ownership, authorization checks, capacity limits, login rate limit, CSRF, SQL parameters, autoescaping, secure response headers, richer audit logs |
| 9 | Regression tests, legacy DB migration, documentation, local deployment configuration and CI workflow |
| 10 | Peer-code assessment plan and executable-case **template**, pending actual opponent code and course harness |

## Architecture

The required **Browser -> Web Application -> Backend/API -> Database** is implemented by a browser rendering Jinja HTML, Flask web handlers performing backend operations (`/events`, `/history`, `/admin`, etc.), and persistent SQLite tables. A separate JSON REST service is not necessary because the Flask endpoints are the backend. Event append and state read correspond to the PDF's `logappend` and `logread` concepts. The exact route contract is in `docs/api.md`.

## Tech stack

Python 3.12, Flask, Flask-Login, Flask-WTF CSRF, Werkzeug scrypt, SQLite via built-in `sqlite3`, and Jinja/HTML/CSS. Tests use `pytest`. No external database, ORM or JS framework is required.

## Run on Windows (PowerShell)

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe tools/setup_local.py
.\.venv\Scripts\python.exe -m flask --app src.backend init-db
.\.venv\Scripts\python.exe -m flask --app src.backend seed
.\.venv\Scripts\python.exe -m flask --app src.backend run --host=127.0.0.1 --port=5678
```

Open **http://127.0.0.1:5678**. Read the *ignored, local-only* `local-credentials.txt` for your randomly generated demo passwords. Never commit `instance/`, a database or credentials. If a local `instance/config.py` already exists from Week 6, **skip the setup script**. If `local-credentials.txt` is missing, inspect the three `SEED_*_PASSWORD` settings in `instance/config.py` **on your own computer only**; never paste them into chats or commit them. Those settings only match accounts seeded with those passwords; changing a config value does not reset an existing account password. Running `init-db` upgrades the existing `instance/week6.db` in place without deleting existing accounts, persons, rooms or logs; back up that database before upgrading. Running `seed` again preserves existing data.

macOS/Linux: use `python3.12 -m venv .venv`, `.venv/bin/python` in place of the PowerShell Python executable.

To test:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

GitHub Actions runs the same suite for pushes and pull requests. Local test dependencies are listed in `requirements-dev.txt`.

## Local container deployment (Week 9)

From a checkout where `tools/setup_local.py`, `init-db` and `seed` have already been run, install Docker Engine and run:

```bash
docker compose up --build
```

Open http://127.0.0.1:5678. Compose binds only loopback, uses Gunicorn inside the container, and mounts the ignored local `instance/` folder for secrets/database. This is a **local deployment only**. Before making a public deployment, set `SESSION_COOKIE_SECURE = True` in private config and provide HTTPS at a trusted reverse proxy; audit logging, backups, resource limits, secret handling, and production hardening are still required. SQLite is suitable for a small classroom demo, not necessarily a production service.

## Routes and permissions

| Method and path | Guest | Employee | Admin |
| --- | --- | --- | --- |
| `GET /dashboard` | Room counts | Room counts | Room counts |
| `GET /occupancy` | Room counts only | Counts + person names | Counts + person names |
| `GET /history` | **Own linked person only** | Query/filter events | Query/filter events |
| `GET /persons` | Forbidden | View tracked people | View tracked people |
| `POST /admin/persons` | Forbidden | Forbidden | Add a tracked person |
| `GET /events` and `POST /events` | Forbidden | Record movements | Record movements |
| `GET /admin` | Forbidden | Forbidden | View accounts |
| `POST /admin/users` | Forbidden | Forbidden | Create a hashed-password account |
| `POST /admin/users/<id>/role` | Forbidden | Forbidden | Change another account's role |
| `GET /admin/audit` | Forbidden | Forbidden | Paginated action log |
| `GET/POST /login`, `POST /logout` | Login/logout | Login/logout | Login/logout |

Only a signed-in employee or administrator may post a movement. Accepted event types: `gallery_enter`, `gallery_leave`, `room_enter`, `room_leave`. Gallery enter requires being outside; room enter requires being inside gallery but not another room; room leave requires matching room; gallery leave requires being in the gallery but outside rooms. Full rooms reject further entry. Invalid state or invalid/missing person/room -> HTTP **409** with a rejected audit entry. Malformed fields -> HTTP **400**. Write transactions use `BEGIN IMMEDIATE` to serialize the check and insert. Current position is always reconstructed from each person's latest accepted event, not a potentially stale location cache.

Events are immutable in the UI. Server, not the browser, sets `recorded_by` and timestamp. All output is escaped in Jinja; SQL values use bound `?` placeholders; signed sessions, CSRF, no-store headers, content security policy, error handling, generic login errors, audit metadata and a 15-minute login-attempt limit provide defense in depth. These are meaningful controls but **not proof of production-grade security**.

## Database upgrade and privacy

`database/schema.sql` defines `users`, `persons`, `rooms`, `gallery_events`, `audit_logs`, and `login_failures`. The `init-db` command adds new columns to legacy Week 6 users/audit tables and creates new tables/indexes. `guest11` links to Demo Guest Alex and `employee11` to Demo Employee Sam when those person IDs are not already assigned to someone else; an unlinked guest sees **no** history. Room names and counts may be viewed by every signed-in account, but the full occupancy name list requires staff privileges.

## Week 9 evidence and Week 10 limitation

Review `tests/functional/test_functional.py`, `tests/security/test_security.py`, `.github/workflows/tests.yml`, and `docs/weeks7-10_report.md`, `docs/api.md`, `docs/design_document.pdf`. The tests exercise role restrictions, state transitions, capacity, 409 rejection, row-level history access, invalid data, login lockout, SQLi inputs, XSS escaping, CSRF, request size, migration and a concurrent duplicate movement. The course-provided correctness oracle was **not included with the materials supplied here**, so it has not been run or represented as passed. Obtain it from the course and run it against this project before submitting.

Week 10 requires the **assigned opponent’s code/harness** and actual reproducible exploits. Do not submit hypothetical findings as real breaks. Use `docs/break_it_report_template.md` for each real case, and follow the authorized test scope in the course directions.

## Required hand-in map (course PDF section 5)

- Repository/source: this project, including `src/`, `database/`, and `README.md`.
- Tests: `tests/functional/` and `tests/security/`.
- Weeks 4–6 design document and STRIDE threat model: `docs/design_document.pdf` (unchanged copy of the team's earlier report).
- API/route documentation: `docs/api.md`.
- Deployment: this README and `docker-compose.yml` (local-only).
- Week 10: `docs/break_it_report_template.md` is a blank report; `tests/breakit/` is a test skeleton, **not** confirmed findings.

The required Week 9 official correctness oracle is supplied by the instructor and is **not included** with this package.
