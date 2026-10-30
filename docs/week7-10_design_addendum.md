# Weeks 7-9 implemented design addendum

The earlier Weeks 4-6 design is preserved **unchanged** in `design_document.pdf`. The diagram on its pages 3-4 marks `GalleryEvents` as planned; the Week 7 implementation now realizes it and extends `AuditLogs` with `target`, `outcome`, `ip`. The primary architecture (Browser -> Flask/Jinja handlers -> SQLite) is unchanged.

## State machine

```text
outside -- gallery_enter --> gallery floor
  ^                            |   ^
  |                         room_enter | room_leave
  |                            v   |
  +---- gallery_leave ----- gallery floor <---- room
```

Precisely: outside -> gallery floor (`gallery_enter`); gallery floor -> selected room (`room_enter`, requiring capacity); selected room -> gallery floor (`room_leave`, same room); gallery floor -> outside (`gallery_leave`). The server reconstructs state from the last valid event and validates each append under `BEGIN IMMEDIATE` to prevent concurrent duplicate transitions. Any invalid change returns `409`, writing **no GalleryEvents row** and logging a rejection.

## New database relationships

- `gallery_events.person_id -> persons.id` (required)
- `gallery_events.room_id -> rooms.id` (nullable except room events)
- `gallery_events.recorded_by -> users.id` (required; server assigned)
- `users.person_id -> persons.id` (optional, unique; binds a guest account to its own event history)
- `audit_logs.user_id -> users.id` (optional)
- `login_failures` stores recent failures keyed by validated username and request IP

## Security boundaries and changes

- **Untrusted browser**: all URL query values, forms, session cookies and record IDs are validated on the server. CSRF tokens are checked before form handlers. HTML is autoescaped and CSS/JS loading restricted by Content Security Policy.
- **Role / record ownership**: guests see counts and only events tied to their account's `person_id`; staff record events and inspect people; admins manage persons, users, roles and audit log. A denied route returns 403 and records a denied audit entry.
- **Flask/SQLite**: SQL statement values are bound using `?`; the database resides outside web assets; the write transaction encloses the state check and accepted event and audit insert.
- **Local deployment**: the example uses HTTP loopback (not suitable for a public host); HTTPS and secure cookies are prerequisites for an Internet deployment.

Threats covered by the existing STRIDE model now map to implemented controls: Spoofing (authentication/login limits), Tampering (validation/CSRF/atomic events), Repudiation (audit trail), Information disclosure (ownership/Jinja/error pages), DoS (query/body limits), Elevation of privilege (role checks and allowed fields). This does **not** establish production-grade security.
