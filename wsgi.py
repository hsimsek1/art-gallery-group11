"""Gunicorn entry point; local instance/config.py must already exist."""
from src.backend import create_app

app = create_app()
