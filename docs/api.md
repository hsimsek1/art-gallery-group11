# Secure Art Gallery - route and interface reference

**Group 11 | Weeks 7-9.** This project uses server-rendered HTML routes as its backend operations. JSON/REST is not required by the assignment: web application handlers read/write SQLite through parameterized statements. The names `logappend` and `logread` in the course PDF correspond to `POST /events` and `GET /history`/`GET /occupancy` here.

## Authorization and request rules

All routes except `GET /`, `GET /login`, `POST /login`, and static assets require authentication. Role values are `guest`, `employee`, `admin`. Roles are reloaded from SQLite for every request; form fields and cookies cannot set roles. All state-changing requests are **POST**, including logout, and require a Flask-WTF CSRF token from the corresponding HTML form. Responses are HTML; successful writes generally respond `302` to a destination page. Passwords are hashed, no plaintext passwords are stored or returned.

| Method and path | Access | Request fields / behavior | Normal / failure responses |
| --- | --- | --- | --- |
| `GET /` | Public | Redirect according to login status | `302` |
| `GET /login` | Public | Login HTML form with CSRF | `200` |
| `POST /login` | Public | `username`, `password`, `csrf_token` | `302` success; `400` malformed; `401` invalid; `429` temporary login limit |
| `POST /logout` | Signed in | `csrf_token` | `302`; `400` bad CSRF |
| `GET /dashboard` | Signed in | Gallery count and room counts | `200` |
| `GET /occupancy` | Signed in | Guest: counts; staff: person list and locations | `200` |
| `GET /persons` | Employee, Admin | List known persons and their kind | `200`; `403` others |
| `GET /events` | Employee, Admin | Form for event recording | `200`; `403` others |
| `POST /events` | Employee, Admin | `person_id` (integer), `event_type` (enum), `room_id` (required only for room moves), `csrf_token` | `302` accepted; `400` malformed; `409` invalid transition, non-existing person/room, or full room; `403` others |
| `GET /history` | Signed in | `person_id`, `room_id`, `event_type` optional; `page` default 1; `size` default 10, max 25 | `200` result; `400` invalid filter; `403` guest asking for another person's history |
| `GET /admin` | Admin | Account management panel | `200`; `403` others |
| `POST /admin/persons` | Admin | `name` (1–100 characters), `kind` (`guest` or `employee`), `csrf_token` | `302` success; `400` invalid; `403` others |
| `POST /admin/users` | Admin | `username` (1–40, alphanumeric/underscore), `password` (12–128), `role`, optional `person_id`, `csrf_token` | `302` success; `400` invalid; `409` uniqueness conflict; `403` others |
| `POST /admin/users/<user_id>/role` | Admin | `role`, `csrf_token` | `302` success; `403` own-role change or unauthorized; `404` missing; `409` last-admin demotion |
| `GET /admin/audit` | Admin | `page`, `size` with maximum 25 | `200`; `400` invalid; `403` others |

## Gallery event rules

The browser posts one of `gallery_enter`, `gallery_leave`, `room_enter`, `room_leave`. The server takes actor identity from the signed-in account, writes a timestamp, and checks the person's most recent event in a `BEGIN IMMEDIATE` SQLite transaction. A person may move from `outside` to `gallery floor` to `room`, back to `gallery floor`, and only then outside. Duplicate or out-of-order events are rejected with status `409` and **do not** create a `gallery_events` record; they create a rejected `audit_logs` entry instead. A room's count may not exceed its capacity.

## Gallery event example (with CSRF)

1. Log in with the provided local demo account via `GET /login` then `POST /login` using its CSRF token.
2. Navigate to `/events`, select a known person, choose `gallery_enter` and leave Room blank.
3. Post the form. On success the browser is redirected to `/history` and `/occupancy` reflects the new state.
4. A second `gallery_enter` for that same person yields `409`. This is an expected rejection, not a failed app execution.

## Error and privacy behavior

The app returns controlled HTML for 403/404/500. `413` means body over 16 KiB. Unauthenticated protected routes redirect to login. All guest event history is scoped to a server-linked person; a guest without a linked person receives zero events. Every database value in a query is bound with `?`, HTML is escaped by Jinja, and state writes require CSRF. Security headers include CSP, nosniff, and frame denial.

This describes the **intended implementation**; it is not a claim that the instructor's correctness oracle has passed.
