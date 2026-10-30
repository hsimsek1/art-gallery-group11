from concurrent.futures import ThreadPoolExecutor
from src.backend.db import get_db
from tests.conftest import login, movement


def test_invalid_sequence_is_409_and_unchanged(client, app):
    login(client)
    assert movement(client, 'room_enter', room_id=1).status_code == 409
    assert movement(client, 'gallery_leave').status_code == 409
    assert movement(client, 'gallery_enter').status_code == 302
    assert movement(client, 'gallery_enter').status_code == 409
    assert movement(client, 'room_enter', room_id=999).status_code == 409
    assert movement(client, 'room_enter', room_id=1).status_code == 302
    assert movement(client, 'room_leave', room_id=2).status_code == 409
    assert movement(client, 'gallery_leave').status_code == 409
    with app.app_context():
        db = get_db()
        assert db.execute('SELECT COUNT(*) FROM gallery_events').fetchone()[0] == 2
        assert db.execute("SELECT COUNT(*) FROM audit_logs WHERE action='GALLERY_EVENT' AND outcome='rejected'").fetchone()[0] == 6


def test_capacity_enforced(client, app):
    login(client)
    movement(client, 'gallery_enter', person_id=1)
    movement(client, 'gallery_enter', person_id=2)
    assert movement(client, 'room_enter', person_id=1, room_id=1).status_code == 302
    assert movement(client, 'room_enter', person_id=2, room_id=1).status_code == 409


def test_request_validation_and_parameterization(client):
    login(client)
    assert client.post('/events', data={'person_id': '1 OR 1=1', 'event_type':'gallery_enter', 'room_id':''}).status_code == 400
    assert client.post('/events', data={'person_id':'1','event_type':'gallery_enter','room_id':'','role':'admin'}).status_code == 400
    assert client.get('/history?person_id=1%20OR%201=1').status_code == 400
    assert client.get('/history?page=0').status_code == 400
    assert client.get('/history?size=26').status_code == 400
    assert client.get('/history?size=25').status_code == 200
    assert client.get('/admin/audit').status_code == 403


def test_xss_is_escaped_on_history(client, app):
    login(client)
    with app.app_context():
        db = get_db()
        db.execute('UPDATE persons SET name = ? WHERE id = ?', ('<script>alert(1)</script>',1))
        db.commit()
    movement(client, 'gallery_enter', person_id=1)
    body = client.get('/history').data
    assert b'<script>alert(1)</script>' not in body
    assert b'&lt;script&gt;' in body
    response = client.get('/dashboard')
    assert b"script-src 'none'" in response.headers['Content-Security-Policy'].encode()
    assert response.headers['X-Content-Type-Options'] == 'nosniff'


def test_denied_403_and_admin_changes_audited(client, app):
    login(client, 'guest11')
    assert client.get('/admin').status_code == 403
    with app.app_context():
        row = get_db().execute("SELECT action, outcome, ip FROM audit_logs WHERE action='ACCESS_DENIED'").fetchone()
        assert row['outcome'] == 'rejected'
        assert row['ip'] is not None


def test_rate_limit_and_same_bad_credential_message(client):
    unknown = client.post('/login', data={'username':'nobody', 'password':'bad'})
    known = client.post('/login', data={'username':'employee11', 'password':'bad'})
    assert unknown.status_code == known.status_code == 401
    assert b'Invalid username or password.' in unknown.data
    assert b'Invalid username or password.' in known.data
    for _ in range(4):
        client.post('/login', data={'username':'employee11', 'password':'bad'})
    assert client.post('/login', data={'username':'employee11', 'password':'examplePassword123!'}).status_code == 429


def test_csrf_on_state_changes(app):
    app.config['WTF_CSRF_ENABLED'] = True
    client = app.test_client()
    assert client.post('/login', data={'username':'admin11','password':'examplePassword123!'}).status_code == 400
    token_html = client.get('/login').data.decode()
    import re
    token = re.search(r'name="csrf_token" value="([^"]+)"', token_html).group(1)
    assert client.post('/login', data={'username':'admin11', 'password':'examplePassword123!',
                                        'csrf_token':token}).status_code == 302
    assert client.post('/admin/users', data={'username':'bad', 'password':'testPassword123!',
                                            'role':'guest'}).status_code == 400
    assert client.get('/logout').status_code == 405


def test_concurrent_duplicate_movements_only_one_accepted(app):
    """Different sessions race on the same person; BEGIN IMMEDIATE serializes writers."""
    def send_one(_):
        with app.test_client() as client:
            login(client)
            return movement(client, 'gallery_enter', person_id=1).status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        statuses = list(pool.map(send_one, range(2)))
    assert sorted(statuses) == [302, 409]
    with app.app_context():
        assert get_db().execute('SELECT COUNT(*) FROM gallery_events').fetchone()[0] == 1


def test_size_limit(client):
    login(client)
    response = client.post('/events', data={'person_id':'1', 'event_type':'gallery_enter',
                                           'room_id':'', 'padding':'x' * 20000})
    assert response.status_code == 413


def test_person_endpoints_access_control_and_validation(client, app):
    assert client.get('/persons').status_code == 302
    login(client, 'guest11')
    assert client.get('/persons').status_code == 403
    assert client.post('/admin/persons', data={'name':'Unauthorized', 'kind':'guest'}).status_code == 403
    client.post('/logout')
    login(client, 'admin11')
    assert client.post('/admin/persons', data={'name':'', 'kind':'guest'}).status_code == 400
    assert client.post('/admin/persons', data={'name':'Good', 'kind':'superuser'}).status_code == 400
    assert client.post('/admin/persons', data={'name':'Good', 'kind':'guest', 'role':'admin'}).status_code == 400
    with app.app_context():
        assert get_db().execute("SELECT COUNT(*) FROM persons WHERE name IN ('Good','Unauthorized')").fetchone()[0] == 0


def test_session_cookie_and_expiration_configuration(client, app):
    from datetime import timedelta
    assert app.config['SESSION_COOKIE_HTTPONLY'] is True
    assert app.config['SESSION_COOKIE_SAMESITE'] == 'Lax'
    assert app.config['PERMANENT_SESSION_LIFETIME'] == timedelta(minutes=30)
    response = login(client)
    cookie = response.headers.get('Set-Cookie', '')
    assert 'HttpOnly' in cookie and 'SameSite=Lax' in cookie
    assert client.post('/logout').status_code == 302
    assert client.get('/admin').status_code == 302


def test_user_entered_person_name_escaped(client):
    login(client, 'admin11')
    assert client.post('/admin/persons', data={
        'name': '<img src=x onerror=alert(1)>', 'kind': 'guest'
    }).status_code == 302
    response = client.get('/persons')
    assert b'<img src=x onerror=alert(1)>' not in response.data
    assert b'&lt;img' in response.data
