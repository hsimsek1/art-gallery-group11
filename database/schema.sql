PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('guest', 'employee', 'admin'))
);

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

CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    action TEXT NOT NULL,
    timestamp DATETIME NOT NULL
);
