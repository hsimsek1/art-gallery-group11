import sqlite3

from flask import current_app, g

def get_db():
    if "db" not in g:
        database_path = current_app.config["DATABASE"]
        connection = sqlite3.connect(database_path)
        connection.row_factory = sqlite3.Row  # Read columns by name, such as row["id"].
        connection.execute("PRAGMA foreign_keys=ON")
        g.db = connection
    return g.db


def close_db(error=None):
    connection = g.pop("db", None)
    if connection is not None:
        connection.close()


def record_auth(action, user_id=None):
    connection = get_db()
    connection.execute(
        "INSERT INTO audit_logs (user_id, action, timestamp) VALUES (?, ?, CURRENT_TIMESTAMP)",
        (user_id, action),
    )
    connection.commit() 
