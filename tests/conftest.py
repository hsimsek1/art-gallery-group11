import pytest
from werkzeug.security import generate_password_hash
from src.backend import create_app
from src.backend.db import get_db, init_schema


@pytest.fixture
def app(tmp_path):
    app = create_app({
        'TESTING': True,
        'SECRET_KEY': 'test-secret-not-for-real-app-' * 3,
        'DATABASE': str(tmp_path / 'test.db'),
        'WTF_CSRF_ENABLED': False,
    })
    with app.app_context():
        init_schema()
        db = get_db()
        db.executescript('''
            INSERT INTO rooms (id, name, capacity) VALUES (1,'Painting Room', 1);
            INSERT INTO rooms (id, name, capacity) VALUES (2,'Sculpture Room', 2);
            INSERT INTO persons (id, name, kind) VALUES (1,'Alex','guest');
            INSERT INTO persons (id, name, kind) VALUES (2,'Sam','employee');
            INSERT INTO persons (id, name, kind) VALUES (3,'Terry','guest');
        ''')
        for name, role, person_id in [('guest11','guest',1),('employee11','employee',2),('admin11','admin',None)]:
            db.execute('INSERT INTO users (username,password_hash,role,person_id) VALUES (?,?,?,?)',
                       (name, generate_password_hash('examplePassword123!', method='scrypt'),role,person_id))
        db.commit()
    return app


@pytest.fixture
def client(app):
    return app.test_client()


def login(client, username='employee11', password='examplePassword123!'):
    return client.post('/login', data={'username': username, 'password': password})


def movement(client, event_type, person_id=1, room_id=''):
    return client.post('/events', data={
        'person_id': str(person_id), 'event_type': event_type,
        'room_id': str(room_id) if room_id != '' else '',
    })
