# Secure Art Gallery Web Application

**BIBIFI Group 11 - Huseyin Simsek and Gustavo Pepe**

Kent State CS 4/53401, Secure Programming, Fall 2026

[GitHub repository](https://github.com/hsimsek1/secure-art-gallery-group11)

## Current milestone: Weeks 4-6

This version contains the team requirements, secure design, and a small working backend and database. Log in to view rooms loaded from SQLite. An administrator-only page demonstrates authorization. This satisfies the Week 6 demonstration: **Browser -> Flask -> SQLite with authentication**.

## Technology and structure

The application has three direct package dependencies: Flask, Flask-Login and Flask-WTF.

| Part | Choice |
| --- | --- |
| Language | Python 3.12 |
| Web application | Flask |
| Database | SQLite, using Python's built-in sqlite3 module |
| Pages | Jinja (included with Flask), HTML and CSS |
| Password hashing | Werkzeug scrypt (included with Flask) |
| Authentication | Flask-Login |
| Form protection | Flask-WTF CSRF |
| Tests | pytest, development only |

There is no ORM, separate database server, JavaScript framework or separate configuration-loading library. Database values use ? placeholders; browser input is never inserted into SQL strings. The connection handling follows [Flask's SQLite pattern](https://flask.palletsprojects.com/en/stable/patterns/sqlite3/).

- `src/backend/`: application setup, SQLite connections, login-user object and routes.
- `src/frontend/`: login, room list and administrator demonstration templates.
- `database/`: schema and fictional seed records.
- `docs/`: requirements/design PDFs, editable Markdown and three SVG diagrams.
- `tests/functional/` and `tests/security/`: 14 milestone tests.
- `tools/`: a one-time script to generate local credentials.

There are four tables: Users, Persons, Rooms and a small AuditLogs table for login/logout activity. Persons are seeded reference records only. Sessions use Flask signed cookies, so no session table is needed.

## Reading the code

Start with these files in order:

1. `database/schema.sql`: the four tables, their columns, and their constraints.
2. `src/backend/routes.py`: what happens when someone opens a page or submits the login form.
3. `src/backend/db.py`: opening a connection, closing it, and saving an authentication log entry.
4. `src/backend/users.py`: an ordinary class holding a logged-in user's ID, username and role.
5. `src/backend/__init__.py`: connecting the Flask parts, reading local settings, and registering database commands.
6. `src/frontend/templates/`: HTML pages with small Jinja conditions and loops.

The login function follows a straight sequence: read the form, validate it, find the account with a parameterized query, check the password hash, and start the session. The dashboard reads room rows and passes them to an HTML template.

A few Flask conventions are worth learning: `create_app()` builds the application; a `Blueprint` groups page routes; `@login_required` redirects visitors who have not logged in; `g` holds a database connection for the current request. Comments explain these where they are used. Configuration comes from the private `instance/config.py` file; tests supply temporary settings.

`tools/setup_local.py` creates random passwords, writes Flask's settings file, and writes the account list you use to log in. Each password has its own variable, and the two file writes show exactly what is saved. The `secrets` module generates secure random values; `"x"` opens a new file without overwriting an existing one.

## Installation and database setup

Install Python 3.12, then open PowerShell in the repository:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe tools/setup_local.py
.\.venv\Scripts\python.exe -m flask --app src.backend init-db
.\.venv\Scripts\python.exe -m flask --app src.backend seed
```

The setup script writes a local secret and three random passwords to ignored `instance/config.py`, which Flask loads directly. It will not overwrite existing configuration. **If this workspace already has `instance/config.py` and `local-credentials.txt`, skip that script.** Initialization and seeding can be repeated without deleting existing records.

This simplified version uses ignored `instance/week6.db`. Any older `instance/gallery.db` remains untouched and is not used by this version. The existing workspace's credentials have been preserved in `instance/config.py`; its old .env is archived privately as `instance/legacy.env`. When updating a different old checkout, copy its four existing secret/password settings into `instance/config.py` using `config.example.py` as the format, and keep its credentials file.

Reference data includes two fictional persons and Painting Room (capacity 10) and Sculpture Room (capacity 5).

For macOS/Linux, use `python3.12 -m venv .venv` and replace `.\.venv\Scripts\python.exe` with `.venv/bin/python`.

## Run and log in

```powershell
.\.venv\Scripts\python.exe -m flask --app src.backend run --host=127.0.0.1 --port=5000
```

Open http://127.0.0.1:5000. Stop the server with Ctrl+C. Read your passwords in the local, ignored `local-credentials.txt`.

| Account | Role | Current access |
| --- | --- | --- |
| guest11 | User/Guest | Login, room list and logout |
| employee11 | Employee | Login, room list and logout |
| admin11 | Administrator | The same access plus the administrator page |

Employees have their own role, but the Week 6 room-list permissions match Guest permissions. Account management is not included. Accounts are created by the seed command, with Werkzeug scrypt password hashes stored in the database.

## Routes and authorization

| Method / path | Access | Purpose |
| --- | --- | --- |
| GET / | Public | Redirect to login or dashboard |
| GET, POST /login | Public | Display login form and authenticate |
| POST /logout | Logged-in user | End the current session |
| GET /dashboard | Logged-in user | Read and display room records |
| GET /admin | Administrator | Demonstrate the server-side role check |

These Flask routes are the backend; a separate REST API is not required. `login_required` protects the pages. The administrator route checks the role loaded from the database and returns 403 for Guest and Employee accounts. Hiding a navigation link is not the authorization control.

## Basic security

Passwords are salted and hashed. Sessions use a local signing secret, HttpOnly/SameSite cookies and a 30-minute lifetime. Login and logout forms require CSRF tokens. Login fields are validated, queries use sqlite3 parameter binding, and Jinja escapes output. Request bodies are limited to 16 KiB.

The small authentication log stores action, time and an optional user ID, never passwords or tokens. There is no audit browser. Secrets, credentials, databases and virtual environments are excluded from Git. This is a local HTTP demonstration with debugging off; it is not a production deployment or a complete security assessment.

## Tests and demonstration

Install the development dependencies when running tests:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
```

The tests use temporary databases and cover login for all three roles, invalid passwords, login protection, logout, password hashing, administrator access/denial, initialization, repeatable seed data, schema constraints, input validation and CSRF. GitHub Actions installs requirements-dev.txt on Python 3.12 and runs the same command. `pytest.ini` uses pytest's default temporary-directory behavior.

To demonstrate Week 6: initialize and seed the database, log in as Employee, view the seeded rooms, open `/admin` to see access denied, log out, then log in as Administrator and open `/admin` successfully.

## Requirements and design

- [Team and requirements](docs/phase1_requirements.pdf): concise project scope, stack, roles, functional/security requirements and security goals.
- [Design document](docs/design_document.pdf): architecture, DFD, trust boundaries, ERD and six STRIDE threats.
- Matching `.md` files are the editable report sources; `docs/diagrams/` contains the SVG diagrams.

The scope follows **F26_BIBIFI_Project.pdf, pages 4-5**. Full gallery events, occupancy, history, persons/account management and state validation belong to the later application milestone and are absent here. Docker appears in the overall repository layout on page 7, but it is omitted from this Weeks 4-6 version because it is not required by that milestone's implementation checklist.

`database/schema.sql` is the single schema definition used by `init-db`. No export or ORM model synchronization is needed. The finished PDFs and editable Markdown/SVG files are included directly; there is no report-generation script to install or maintain. If you change a report, update its Markdown source and export a matching PDF with your Markdown editor, then check the layout.
