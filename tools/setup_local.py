from pathlib import Path
import secrets

root = Path(__file__).resolve().parent.parent
instance = root / "instance"
config_path = instance / "config.py"
credentials_path = root / "local-credentials.txt"

if config_path.exists() or credentials_path.exists() or (root / ".env").exists():
    raise SystemExit("Local configuration already exists. No files changed.")

instance.mkdir(exist_ok=True)

secret_key = secrets.token_hex(32)
admin_password = secrets.token_urlsafe(18)
employee_password = secrets.token_urlsafe(18)
guest_password = secrets.token_urlsafe(18)

with config_path.open("x", encoding="utf-8") as config_file:
    config_file.write(f'''SECRET_KEY = "{secret_key}"
SEED_ADMIN_PASSWORD = "{admin_password}"
SEED_EMPLOYEE_PASSWORD = "{employee_password}"
SEED_GUEST_PASSWORD = "{guest_password}"
''')

with credentials_path.open("x", encoding="utf-8") as credentials_file:
    credentials_file.write(f'''Group 11 LOCAL DEMO ACCOUNTS - never upload this file
admin | admin11 | {admin_password}
employee | employee11 | {employee_password}
guest | guest11 | {guest_password}
''')

print("Created ignored instance/config.py and local-credentials.txt. Keep both private.")
