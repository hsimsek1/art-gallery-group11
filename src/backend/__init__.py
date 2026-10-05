from datetime import timedelta
from pathlib import Path

import click
from flask import Flask, render_template
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash

from .db import close_db, get_db
from .users import User

ROOT = Path(__file__).resolve().parents[2]
login_manager = LoginManager()
csrf = CSRFProtect()


def create_app(test_config=None):
    """Build the app. Tests can supply settings for a temporary database."""
    instance = ROOT / "instance"
    instance.mkdir(exist_ok=True)
    app = Flask(
        __name__,
        template_folder=str(ROOT / "src/frontend/templates"),
        static_folder=str(ROOT / "src/frontend/static"),
        instance_path=str(instance),
        instance_relative_config=True,
    )
    app.config.update(
        SECRET_KEY="",
        DATABASE=str(instance / "week6.db"),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        PERMANENT_SESSION_LIFETIME=timedelta(minutes=30),
        MAX_CONTENT_LENGTH=16 * 1024,
        DEBUG=False,
    )
    app.config.from_pyfile("config.py", silent=True)
    if test_config is not None:
        app.config.update(test_config)
    if len(app.config["SECRET_KEY"]) < 32:
        raise RuntimeError("Run tools/setup_local.py to generate a local secret key.")

    app.teardown_appcontext(close_db)  
    login_manager.init_app(app)
    login_manager.login_view = "web.login"
    csrf.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        try:
            user_id = int(user_id)
        except (TypeError, ValueError):
            return None
        connection = get_db()
        result = connection.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = result.fetchone()
        if row is None:
            return None
        return User(row)

    from .routes import web
    app.register_blueprint(web)

    @app.errorhandler(403)
    def forbidden(error):
        return render_template("error.html", message="Administrator access required."), 403

    @app.cli.command("init-db")
    def init_db():
        """Create missing tables without deleting existing records."""
        connection = get_db()
        schema = (ROOT / "database/schema.sql").read_text()
        connection.executescript(schema)
        click.echo("Database initialized.")

    @app.cli.command("seed")
    def seed():
        connection = get_db()
        seed_sql = (ROOT / "database/seed.sql").read_text()
        connection.executescript(seed_sql)
        with connection:
            for role in ("guest", "employee", "admin"):
                username = role + "11"
                result = connection.execute("SELECT id FROM users WHERE username = ?", (username,))
                existing_user = result.fetchone()
                if existing_user is not None:
                    continue
                setting_name = "SEED_" + role.upper() + "_PASSWORD"
                password = app.config.get(setting_name, "")
                if len(password) < 12 or len(password) > 128:
                    raise click.ClickException("Run tools/setup_local.py before seeding.")
                password_hash = generate_password_hash(password, method="scrypt")
                connection.execute(
                    "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                    (username, password_hash, role),
                )
        click.echo("Demo accounts, persons and rooms are ready.")

    return app
