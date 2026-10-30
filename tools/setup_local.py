"""Run once. Private configuration and randomized credentials are never committed."""
from pathlib import Path
import secrets

root = Path(__file__).resolve().parent.parent
instance = root / 'instance'
config_path = instance / 'config.py'
credentials_path = root / 'local-credentials.txt'
if config_path.exists() or credentials_path.exists() or (root / '.env').exists():
    raise SystemExit('Local configuration already exists. No files changed.')
instance.mkdir(exist_ok=True)
keys = {role: secrets.token_urlsafe(18) for role in ('ADMIN', 'EMPLOYEE', 'GUEST')}
secret_key = secrets.token_hex(32)
with config_path.open('x', encoding='utf-8') as config_file:
    config_file.write(f'SECRET_KEY = "{secret_key}"\n')
    for role, password in keys.items():
        config_file.write(f'SEED_{role}_PASSWORD = "{password}"\n')
with credentials_path.open('x', encoding='utf-8') as credentials_file:
    credentials_file.write('Group 11 LOCAL DEMO ACCOUNTS - keep private\n')
    for role, password in keys.items():
        credentials_file.write(f'{role.lower()} | {role.lower()}11 | {password}\n')
print('Created ignored instance/config.py and local-credentials.txt. Keep both private.')
