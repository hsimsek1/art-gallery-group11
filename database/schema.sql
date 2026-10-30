PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS persons (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    kind TEXT NOT NULL CHECK (kind IN ('guest', 'employee'))
);

CREATE TABLE IF NOT EXISTS rooms (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    capacity INTEGER NOT NULL CHECK (capacity > 0)
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('guest', 'employee', 'admin')),
    person_id INTEGER UNIQUE REFERENCES persons(id)
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    action TEXT NOT NULL,
    timestamp DATETIME NOT NULL,
    target TEXT,
    outcome TEXT NOT NULL DEFAULT 'accepted',
    ip TEXT
);

CREATE TABLE IF NOT EXISTS gallery_events (
    id INTEGER PRIMARY KEY,
    person_id INTEGER NOT NULL REFERENCES persons(id),
    room_id INTEGER REFERENCES rooms(id),
    event_type TEXT NOT NULL CHECK (event_type IN (
        'gallery_enter', 'gallery_leave', 'room_enter', 'room_leave'
    )),
    recorded_by INTEGER NOT NULL REFERENCES users(id),
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (
        (event_type IN ('gallery_enter', 'gallery_leave') AND room_id IS NULL) OR
        (event_type IN ('room_enter', 'room_leave') AND room_id IS NOT NULL)
    )
);

CREATE INDEX IF NOT EXISTS idx_gallery_events_person ON gallery_events(person_id, id DESC);
CREATE INDEX IF NOT EXISTS idx_gallery_events_room ON gallery_events(room_id, id DESC);

CREATE TABLE IF NOT EXISTS login_failures (
    id INTEGER PRIMARY KEY,
    username TEXT NOT NULL,
    ip TEXT NOT NULL,
    attempted_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_login_failures_username ON login_failures(username, attempted_at);
CREATE INDEX IF NOT EXISTS idx_login_failures_ip ON login_failures(ip, attempted_at);
