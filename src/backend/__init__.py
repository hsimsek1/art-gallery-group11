from datetime import timedelta
from pathlib import Path

import click
from flask import Flask, render_template, request
from flask_login import LoginManager, current_user
from flask_wtf.csrf import CSRFProtect
from werkzeug.exceptions import HTTPException
from werkzeug.security import generate_password_hash

from .db import audit, close_db, get_db, init_schema
from .users import User

ROOT = Path(__file__).resolve().parents[2]
login_manager = LoginManager()
csrf = CSRFProtect()


def create_app(test_config=None):
    instance = ROOT / 'instance'
    instance.mkdir(exist_ok=True)
    app = Flask(
        __name__,
        instance_path=str(instance),
        instance_relative_config=True,
        template_folder=str(ROOT / 'src/frontend/templates'),
        static_folder=str(ROOT / 'src/frontend/static'),
    )
    app.config.update(
        SECRET_KEY='',
        DATABASE=str(instance / 'week6.db'),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        SESSION_COOKIE_SECURE=False, 
        PERMANENT_SESSION_LIFETIME=timedelta(minutes=30),
        MAX_CONTENT_LENGTH=16 * 1024,
        DEBUG=False,
    )
    app.config.from_pyfile('config.py', silent=True)
    if test_config is not None:
        app.config.update(test_config)
    if not isinstance(app.config['SECRET_KEY'], str) or len(app.config['SECRET_KEY']) < 32:
        raise RuntimeError('Run tools/setup_local.py to generate a local secret key.')

    app.teardown_appcontext(close_db)
    login_manager.init_app(app)
    login_manager.login_view = 'web.login'
    csrf.init_app(app)

    @app.before_request
    def default_deny_unauthenticated():
        if request.endpoint in ('web.index', 'web.login', 'static', None):
            return None
        if not current_user.is_authenticated:
            return login_manager.unauthorized()
        return None

    @login_manager.user_loader
    def load_user(session_id):
        user_id, _, version = str(session_id).partition(':')
        if not user_id.isascii() or not user_id.isdigit() or not version.isascii() or not version.isdigit():
            return None
        if len(user_id) > 9 or len(version) > 9:
            return None
        row = get_db().execute('SELECT * FROM users WHERE id = ?', (int(user_id),)).fetchone()
        if row is None or row['session_version'] != int(version):
            return None
        return User(row)

    @app.after_request
    def harden_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Referrer-Policy'] = 'no-referrer'
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; script-src 'none'; style-src 'self'; "
            "object-src 'none'; base-uri 'self'; frame-ancestors 'none'"
        )
        if current_user.is_authenticated:
            response.headers['Cache-Control'] = 'no-store'
        return response

    @app.errorhandler(403)
    def forbidden(error):
        try:
            audit('ACCESS_DENIED', current_user.id if current_user.is_authenticated else None,
                  target=request.path, outcome='rejected')
        except Exception:
            app.logger.exception('Could not audit an access denial')
        return render_template('error.html', title='Access denied', message='Access denied.'), 403

    @app.errorhandler(404)
    def not_found(error):
        return render_template('error.html', title='Not found', message='Page not found.'), 404

    @app.errorhandler(500)
    def server_error(error):
        try:
            get_db().rollback()
        except Exception:
            pass
        return render_template('error.html', title='Error', message='A server error occurred.'), 500

    from .routes import web
    app.register_blueprint(web)

    @app.cli.command('init-db')
    def init_db_command():
        init_schema()
        click.echo('Database initialized (existing data preserved).')

    @app.cli.command('seed')
    def seed_command():
        db = get_db()
        db.executescript((ROOT / 'database/seed.sql').read_text(encoding='utf-8'))
        with db:
            for role in ('guest', 'employee', 'admin'):
                username = role + '11'
                if db.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone():
                    continue
                password = app.config.get('SEED_' + role.upper() + '_PASSWORD', '')
                if not (12 <= len(password) <= 128):
                    raise click.ClickException('Run tools/setup_local.py before seeding.')
                person_id = {'guest': 1, 'employee': 2, 'admin': None}[role]
                if person_id and db.execute('SELECT id FROM users WHERE person_id = ?', (person_id,)).fetchone():
                    person_id = None
                db.execute(
                    'INSERT INTO users (username, password_hash, role, person_id) VALUES (?, ?, ?, ?)',
                    (username, generate_password_hash(password, method='scrypt'), role, person_id),
                )
            for name, person_id in [('guest11', 1), ('employee11', 2)]:
                if not db.execute('SELECT id FROM users WHERE person_id = ?', (person_id,)).fetchone():
                    db.execute('UPDATE users SET person_id = ? WHERE username = ? AND person_id IS NULL',
                               (person_id, name))
        click.echo('Demo accounts and rooms are ready.')

    return app
