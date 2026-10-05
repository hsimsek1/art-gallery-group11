from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, database_row):
        self.id = database_row["id"]
        self.username = database_row["username"]
        self.role = database_row["role"]
