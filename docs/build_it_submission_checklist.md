# Build It - Week 9 submission checklist (from course PDF, pages 5-7)

- [x] GitHub-ready source code in `src/backend/`, `src/frontend/`
- [x] `database/schema.sql`, `database/seed.sql`
- [x] README: purpose, team, tech stack, architecture, setup, roles, endpoints, tests, security, limitations
- [x] Functional and security test source under `tests/functional/`, `tests/security/`
- [x] Earlier (unchanged) Weeks 4-6 design and STRIDE threat model in `docs/design_document.pdf`
- [x] Backend route/API reference in `docs/api.md`
- [x] Deployment instructions and `docker-compose.yml`
- [x] Code for movements, occupancy, history queries, person list/creation, admin roles and audit log
- [x] Security controls: CSRF, server-side checks, SQL parameterization, template escaping, login limits
- [ ] Run `python -m pytest -q` in an environment with dependencies installed, and record results
- [ ] Run the **instructor-provided correctness oracle**; compare its expected interface contract
- [ ] Run `docker compose up --build` on a local development machine; confirm fresh setup works
- [ ] Have another student independently follow README instructions and verify reproducibility
- [ ] Push/merge to team GitHub repository (local branch `weeks7-10-build-it` was not on remote at last check), verify submitted commit SHA
- [ ] Check commit history for accidentally committed secrets/credentials (do not only scan current files)

Passing local tests does not guarantee passing the instructor's oracle or absence of vulnerabilities.
