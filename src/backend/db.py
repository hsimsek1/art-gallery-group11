"""Small SQLite helpers. All SQL values are bound with ? placeholders."""
import sqlite3
from flask import current_app, g, request


def get_db():
    if 'db' not in g:
        db = sqlite3.connect(current_app.config['DATABASE'], timeout=10)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        db.execute('PRAGMA busy_timeout=10000')
        g.db = db
    return g.db


def close_db(error=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def audit(action, user_id=None, target=None, outcome='accepted', commit=True):
    """Caller may set commit=False when logging inside an existing transaction."""
    db = get_db()
    db.execute(
        'INSERT INTO audit_logs (user_id, action, timestamp, target, outcome, ip) '
        'VALUES (?, ?, CURRENT_TIMESTAMP, ?, ?, ?)',
        (user_id, action, target, outcome, request.remote_addr if request else None),
    )
    if commit:
        db.commit()


def init_schema():
    """Create the new tables and upgrade a Week 6 DB without deleting its data."""
    from pathlib import Path
    root = Path(__file__).resolve().parents[2]
    db = get_db()

    for table, columns in {
        'users': {'person_id': 'INTEGER REFERENCES persons(id)'},
        'audit_logs': {
            'target': 'TEXT',
            'outcome': "TEXT NOT NULL DEFAULT 'accepted'",
            'ip': 'TEXT',
        },
    }.items():
        present = {row['name'] for row in db.execute(f'PRAGMA table_info({table})')}
        if present:
            for column, definition in columns.items():
                if column not in present:
                    db.execute(f'ALTER TABLE {table} ADD COLUMN {column} {definition}')
    db.commit()
    db.executescript((root / 'database/schema.sql').read_text(encoding='utf-8'))
    db.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_users_person_id ON users(person_id)')
    db.commit()


def current_locations():
    """Return {person_id: room_id|0|-1} based on accepted event ordering.

    -1 means outside; 0 means inside gallery but not inside a room.
    No cached state table can drift from the event history.
    """
    latest = get_db().execute('''
        SELECT e.person_id, e.room_id, e.event_type
        FROM gallery_events e
        JOIN (SELECT person_id, MAX(id) AS last_id FROM gallery_events GROUP BY person_id) x
          ON x.last_id = e.id
    ''').fetchall()
    locations = {}
    for event in latest:
        kind = event['event_type']
        locations[event['person_id']] = (
            -1 if kind == 'gallery_leave' else
            event['room_id'] if kind == 'room_enter' else 0
        )
    return locations


def record_auth(action, user_id=None):
    audit(action, user_id)
