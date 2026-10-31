from flask_login import UserMixin


class User(UserMixin):
    def __init__(self, row):
        self.id = row['id']
        self.username = row['username']
        self.role = row['role']
        self.person_id = row['person_id']
        self.session_version = row['session_version']

    def get_id(self):
        return f'{self.id}:{self.session_version}'
