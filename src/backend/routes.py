"""Server-rendered gallery UI. All protected state changes are POST + CSRF."""
import re
import sqlite3
from functools import wraps

from flask import Blueprint, abort, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash

from .db import audit, current_locations, get_db
from .users import User

web = Blueprint('web', __name__)
ROLES = ('guest', 'employee', 'admin')
EVENT_TYPES = ('gallery_enter', 'room_enter', 'room_leave', 'gallery_leave')
PAGE_MAX = 25


def role_required(*roles):
    def decorate(func):
        @wraps(func)
        @login_required
        def wrapped(*args, **kwargs):
            if current_user.role not in roles:
                abort(403)
            return func(*args, **kwargs)
        return wrapped
    return decorate


def get_integer(value, minimum=1):
    if value is None or not re.fullmatch(r'[0-9]{1,9}', str(value)):
        abort(400)
    value = int(value)
    if value < minimum:
        abort(400)
    return value


def pagination():
    page = get_integer(request.args.get('page', '1'))
    size = get_integer(request.args.get('size', '10'))
    if size > PAGE_MAX:
        abort(400)
    return page, size


def locations_summary():
    db = get_db()
    loc = current_locations()
    rooms = [dict(room) for room in db.execute('SELECT * FROM rooms ORDER BY id')]
    for room in rooms:
        room['occupancy'] = sum(1 for spot in loc.values() if spot == room['id'])
    return loc, rooms


@web.get('/')
def index():
    return redirect(url_for('web.dashboard' if current_user.is_authenticated else 'web.login'))


@web.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    username = request.form.get('username', '').strip().lower()
    password = request.form.get('password', '')
    db = get_db()
    ip = request.remote_addr or 'unknown'
    ip_failures = db.execute(
        "SELECT COUNT(*) FROM login_failures WHERE ip = ? "
        "AND attempted_at > datetime('now', '-15 minutes')",
        (ip,),
    ).fetchone()[0]
    if ip_failures >= 20:
        audit('LOGIN_RATE_LIMITED', target='ip-limit', outcome='rejected')
        return render_template('login.html', error='Too many login attempts. Try again later.'), 429
    if not re.fullmatch(r'[a-z0-9_]{1,40}', username) or not 1 <= len(password) <= 128:
        db.execute('INSERT INTO login_failures (username, ip) VALUES (?, ?)', ('<invalid>', ip))
        db.commit()
        audit('LOGIN_FAILED', target='invalid-input', outcome='rejected')
        return render_template('login.html', error='Enter a valid username and password.'), 400
    username_failures = db.execute(
        "SELECT COUNT(*) FROM login_failures WHERE username = ? "
        "AND attempted_at > datetime('now', '-15 minutes')",
        (username,),
    ).fetchone()[0]
    if username_failures >= 5:
        audit('LOGIN_RATE_LIMITED', target=username, outcome='rejected')
        return render_template('login.html', error='Too many login attempts. Try again later.'), 429

    row = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    if row is None or not check_password_hash(row['password_hash'], password):
        db.execute('INSERT INTO login_failures (username, ip) VALUES (?, ?)', (username, ip))
        db.commit()
        audit('LOGIN_FAILED', row['id'] if row else None, target=username, outcome='rejected')
        return render_template('login.html', error='Invalid username or password.'), 401

    db.execute('DELETE FROM login_failures WHERE username = ?', (username,))
    db.commit()
    session.clear()
    login_user(User(row))
    session.permanent = True
    audit('LOGIN_SUCCESS', row['id'])
    return redirect(url_for('web.dashboard'))


@web.post('/logout')
@login_required
def logout():
    audit('LOGOUT', current_user.id)
    logout_user()
    session.clear()
    return redirect(url_for('web.login'))


@web.get('/dashboard')
@login_required
def dashboard():
    loc, rooms = locations_summary()
    return render_template('dashboard.html', rooms=rooms,
                           gallery_count=sum(spot != -1 for spot in loc.values()))


@web.get('/occupancy')
@login_required
def occupancy():
    loc, rooms = locations_summary()
    people = []
    if current_user.role in ('employee', 'admin'):
        for person in get_db().execute('SELECT id, name FROM persons ORDER BY id'):
            spot = loc.get(person['id'], -1)
            if spot != -1:
                room = next((r['name'] for r in rooms if r['id'] == spot), 'Gallery floor')
                people.append({'name': person['name'], 'place': room})
    return render_template('occupancy.html', rooms=rooms, people=people,
                           gallery_count=sum(spot != -1 for spot in loc.values()))


@web.get('/persons')
@role_required('employee', 'admin')
def persons():
    people = get_db().execute(
        'SELECT id, name, kind FROM persons ORDER BY id'
    ).fetchall()
    return render_template('persons.html', people=people)


@web.route('/events', methods=['GET', 'POST'])
@role_required('employee', 'admin')
def events():
    db = get_db()
    if request.method == 'GET':
        people = db.execute('SELECT id, name FROM persons ORDER BY name').fetchall()
        rooms = db.execute('SELECT id, name FROM rooms ORDER BY name').fetchall()
        return render_template('events.html', people=people, rooms=rooms, event_types=EVENT_TYPES)

    if set(request.form) - {'csrf_token', 'person_id', 'event_type', 'room_id'}:
        abort(400)
    person_id = get_integer(request.form.get('person_id'))
    kind = request.form.get('event_type', '')
    if kind not in EVENT_TYPES:
        abort(400)
    room_value = request.form.get('room_id', '')
    if kind in ('room_enter', 'room_leave'):
        room_id = get_integer(room_value)
    else:
        if room_value not in ('', None):
            abort(400)
        room_id = None

    target = f'person:{person_id};event:{kind};room:{room_id}'
    db.execute('BEGIN IMMEDIATE')
    person = db.execute('SELECT id FROM persons WHERE id = ?', (person_id,)).fetchone()
    room = (db.execute('SELECT id, capacity FROM rooms WHERE id = ?', (room_id,)).fetchone()
            if room_id is not None else None)
    loc = current_locations()
    before = loc.get(person_id, -1)
    valid = bool(person)
    if kind == 'gallery_enter':
        valid = valid and before == -1
    elif kind == 'gallery_leave':
        valid = valid and before == 0
    elif kind == 'room_enter':
        valid = valid and before == 0 and room is not None
        if valid:
            valid = sum(spot == room_id for spot in loc.values()) < room['capacity']
    elif kind == 'room_leave':
        valid = valid and room is not None and before == room_id
    if not valid:
        db.rollback()
        audit('GALLERY_EVENT', current_user.id, target=target, outcome='rejected')
        return render_template('error.html', title='Movement rejected',
                               message='Movement rejected: invalid state, room or capacity.'), 409

    db.execute(
        'INSERT INTO gallery_events (person_id, room_id, event_type, recorded_by) VALUES (?, ?, ?, ?)',
        (person_id, room_id, kind, current_user.id),
    )
    audit('GALLERY_EVENT', current_user.id, target=target, outcome='accepted', commit=False)
    db.commit()
    return redirect(url_for('web.history'))


@web.get('/history')
@login_required
def history():
    db = get_db()
    page, size = pagination()
    requested = request.args.get('person_id')
    person_id = get_integer(requested) if requested not in (None, '') else None
    requested_room = request.args.get('room_id')
    room_id = get_integer(requested_room) if requested_room not in (None, '') else None
    event_type = request.args.get('event_type', '')
    if event_type and event_type not in EVENT_TYPES:
        abort(400)
    if current_user.role == 'guest':
        if person_id is not None and person_id != current_user.person_id:
            abort(403)
        person_id = current_user.person_id
        if person_id is None:
            return render_template('history.html', events=[], page=page, size=size,
                                   has_next=False, person_id=None,
                                   event_type=event_type, room_id=room_id,
                                   people=[], rooms=[])
    query = """SELECT e.id, e.timestamp, e.event_type, p.name AS person_name,
                      r.name AS room_name, u.username AS recorded_by
               FROM gallery_events e
               JOIN persons p ON p.id = e.person_id
               LEFT JOIN rooms r ON r.id = e.room_id
               JOIN users u ON u.id = e.recorded_by"""
    filters, values = [], []
    if person_id is not None:
        filters.append('e.person_id = ?')
        values.append(person_id)
    if room_id is not None:
        filters.append('e.room_id = ?')
        values.append(room_id)
    if event_type:
        filters.append('e.event_type = ?')
        values.append(event_type)
    if filters:
        query += ' WHERE ' + ' AND '.join(filters)
    rows = db.execute(query + ' ORDER BY e.id DESC LIMIT ? OFFSET ?',
                      (*values, size + 1, (page - 1) * size)).fetchall()
    people = (db.execute('SELECT id, name FROM persons ORDER BY name').fetchall()
              if current_user.role != 'guest' else [])
    rooms = db.execute('SELECT id, name FROM rooms ORDER BY name').fetchall()
    return render_template('history.html', events=rows[:size], page=page,
                           has_next=len(rows) > size, person_id=person_id,
                           event_type=event_type, room_id=room_id,
                           people=people, rooms=rooms, size=size)


@web.get('/admin')
@role_required('admin')
def admin():
    db = get_db()
    users = db.execute('''SELECT u.id, u.username, u.role, u.person_id, p.name AS person_name
                          FROM users u LEFT JOIN persons p ON p.id = u.person_id ORDER BY u.id''').fetchall()
    people = db.execute('SELECT id, name FROM persons ORDER BY name').fetchall()
    return render_template('admin.html', users=users, people=people)


@web.post('/admin/persons')
@role_required('admin')
def create_person():
    if set(request.form) - {'csrf_token', 'name', 'kind'}:
        abort(400)
    name = request.form.get('name', '').strip()
    kind = request.form.get('kind', '')
    if not 1 <= len(name) <= 100 or kind not in ('guest', 'employee'):
        abort(400)
    db = get_db()
    cursor = db.execute('INSERT INTO persons (name, kind) VALUES (?, ?)',
                        (name, kind))
    audit('ADMIN_PERSON_CREATE', current_user.id,
          target=f'person:{cursor.lastrowid}', commit=False)
    db.commit()
    return redirect(url_for('web.admin'))


@web.post('/admin/users')
@role_required('admin')
def create_user():
    if set(request.form) - {'csrf_token', 'username', 'password', 'role', 'person_id'}:
        abort(400)
    username = request.form.get('username', '').strip().lower()
    password = request.form.get('password', '')
    role = request.form.get('role', '')
    person_value = request.form.get('person_id', '')
    if not re.fullmatch(r'[a-z0-9_]{1,40}', username) or not 12 <= len(password) <= 128 or role not in ROLES:
        abort(400)
    person_id = get_integer(person_value) if person_value else None
    db = get_db()
    if person_id is not None and not db.execute('SELECT id FROM persons WHERE id = ?', (person_id,)).fetchone():
        abort(400)
    try:
        db.execute(
            'INSERT INTO users (username, password_hash, role, person_id) VALUES (?, ?, ?, ?)',
            (username, generate_password_hash(password, method='scrypt'), role, person_id),
        )
        audit('ADMIN_USER_CREATE', current_user.id, target=username, commit=False)
        db.commit()
    except sqlite3.IntegrityError:
        db.rollback()
        audit('ADMIN_USER_CREATE', current_user.id, target=username, outcome='rejected')
        abort(409)
    return redirect(url_for('web.admin'))


@web.post('/admin/users/<int:user_id>/role')
@role_required('admin')
def change_role(user_id):
    if set(request.form) - {'csrf_token', 'role'}:
        abort(400)
    role = request.form.get('role', '')
    if role not in ROLES:
        abort(400)
    if user_id == current_user.id:
        abort(403) 
    db = get_db()
    target = db.execute('SELECT id, role FROM users WHERE id = ?', (user_id,)).fetchone()
    if target is None:
        abort(404)
    if target['role'] == 'admin' and role != 'admin':
        count = db.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'").fetchone()[0]
        if count <= 1:
            abort(409)
    db.execute('UPDATE users SET role = ? WHERE id = ?', (role, user_id))
    audit('ADMIN_ROLE_CHANGE', current_user.id, target=f'user:{user_id};role:{role}', commit=False)
    db.commit()
    return redirect(url_for('web.admin'))


@web.get('/admin/audit')
@role_required('admin')
def admin_audit():
    page, size = pagination()
    rows = get_db().execute('''SELECT a.id, a.timestamp, a.action, a.target, a.outcome, a.ip,
                                      u.username AS actor
                               FROM audit_logs a LEFT JOIN users u ON u.id = a.user_id
                               ORDER BY a.id DESC LIMIT ? OFFSET ?''',
                            (size + 1, (page - 1) * size)).fetchall()
    return render_template('audit.html', entries=rows[:size], page=page,
                           has_next=len(rows) > size, size=size)
