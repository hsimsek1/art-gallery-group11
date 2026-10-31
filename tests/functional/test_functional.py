import sqlite3
from src.backend.db import get_db, init_schema
from tests.conftest import login, movement


def test_seed_and_init_idempotent(app):
    with app.app_context():
        init_schema()
        db = get_db()
        assert db.execute('SELECT COUNT(*) FROM persons').fetchone()[0] == 3
        assert db.execute('SELECT COUNT(*) FROM rooms').fetchone()[0] == 2
        assert db.execute('SELECT COUNT(*) FROM users').fetchone()[0] == 3


def test_login_and_roles(client):
    assert client.get('/dashboard').status_code == 302
    assert login(client).status_code == 302
    assert b'Gallery dashboard' in client.get('/dashboard').data
    assert client.get('/admin').status_code == 403
    assert client.post('/logout').status_code == 302
    assert client.get('/dashboard').status_code == 302
    assert login(client, 'admin11').status_code == 302
    assert client.get('/admin').status_code == 200


def test_movement_lifecycle_and_occupancy(client, app):
    login(client)
    assert movement(client, 'gallery_enter').status_code == 302
    assert b'Current occupancy: 1' in client.get('/dashboard').data
    assert movement(client, 'room_enter', room_id=1).status_code == 302
    assert b'Alex' in client.get('/occupancy').data
    assert movement(client, 'room_leave', room_id=1).status_code == 302
    assert movement(client, 'gallery_leave').status_code == 302
    assert b'Current occupancy: 0' in client.get('/dashboard').data
    with app.app_context():
        assert get_db().execute('SELECT COUNT(*) FROM gallery_events').fetchone()[0] == 4


def test_guest_history_only_their_person(client):
    login(client)
    movement(client, 'gallery_enter', person_id=1)
    movement(client, 'gallery_enter', person_id=2)
    client.post('/logout')
    login(client, 'guest11')
    html = client.get('/history').data
    assert b'Alex' in html
    assert b'Sam' not in html
    assert client.get('/history?person_id=2').status_code == 403
    assert client.get('/events').status_code == 403
    assert client.get('/occupancy').status_code == 200
    assert b'Sam' not in client.get('/occupancy').data


def test_admin_can_create_and_change_role(client, app):
    login(client, 'admin11')
    admin_page = client.get('/admin').data
    assert b'action="/admin/persons"' in admin_page.split(b'</head>')[1]
    resp = client.post('/admin/users', data={'username':'viewer','password':'secureDemoPassword123!',
                   'role':'guest','person_id':'3'})
    assert resp.status_code == 302
    with app.app_context():
        db = get_db()
        user = db.execute("SELECT id, password_hash FROM users WHERE username='viewer'").fetchone()
        assert user['password_hash'] != 'secureDemoPassword123!'
        user_id = user['id']
        own_id = db.execute("SELECT id FROM users WHERE username='admin11'").fetchone()['id']
    assert client.post(f'/admin/users/{user_id}/role', data={'role':'employee'}).status_code == 302
    assert client.post(f'/admin/users/{own_id}/role', data={'role':'guest'}).status_code == 403
    with app.app_context():
        assert get_db().execute('SELECT role FROM users WHERE id = ?', (user_id,)).fetchone()[0] == 'employee'


def test_existing_week6_database_upgrades(tmp_path):
    from src.backend import create_app
    db_path = tmp_path / 'old.db'
    db = sqlite3.connect(db_path)
    db.executescript('''
      CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password_hash TEXT, role TEXT);
      CREATE TABLE persons (id INTEGER PRIMARY KEY, name TEXT, kind TEXT);
      CREATE TABLE rooms (id INTEGER PRIMARY KEY, name TEXT, capacity INTEGER);
      CREATE TABLE audit_logs (id INTEGER PRIMARY KEY, user_id INTEGER, action TEXT, timestamp DATETIME);
      INSERT INTO users VALUES (1,'keepme','oldhash','guest');
      INSERT INTO persons VALUES (1,'Existing','guest');
      INSERT INTO audit_logs (user_id, action,timestamp) VALUES (1,'LOGIN_SUCCESS',CURRENT_TIMESTAMP);
    ''')
    db.close()
    app = create_app({'SECRET_KEY':'unit-test-only-key-'*4,'DATABASE':str(db_path)})
    with app.app_context():
        init_schema()
        init_schema()
        connection = get_db()
        assert connection.execute('SELECT username FROM users').fetchone()[0] == 'keepme'
        assert connection.execute('SELECT action FROM audit_logs').fetchone()[0] == 'LOGIN_SUCCESS'
        assert connection.execute('SELECT COUNT(*) FROM gallery_events').fetchone()[0] == 0
        assert 'person_id' in [r['name'] for r in connection.execute('PRAGMA table_info(users)')]


def test_person_management_and_history_queries(client, app):
    login(client, 'admin11')
    response = client.post('/admin/persons', data={'name': 'New Visitor', 'kind': 'guest'})
    assert response.status_code == 302
    with app.app_context():
        db = get_db()
        person_id = db.execute('SELECT id FROM persons WHERE name = ?', ('New Visitor',)).fetchone()[0]
    assert b'New Visitor' in client.get('/persons').data
    assert movement(client, 'gallery_enter', person_id=person_id).status_code == 302
    assert movement(client, 'room_enter', person_id=person_id, room_id=2).status_code == 302
    assert b'New Visitor' in client.get('/history?room_id=2&event_type=room_enter').data
    assert b'<td>New Visitor</td>' not in client.get('/history?room_id=1&event_type=room_enter').data
    assert client.get('/history?event_type=unknown').status_code == 400
    assert client.get('/history?room_id=2%20OR%201=1').status_code == 400
