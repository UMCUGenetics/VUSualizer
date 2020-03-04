import datetime
import uuid
from flask_login import UserMixin
from src import mongo


class User(UserMixin):

    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password = password
        self._id = email

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self._id

    def save_to_mongo(self):
        print(self.json())
        mongo.db.user.insert(self.json())

    @classmethod
    def get_by_email(cls, email):
        data = mongo.db.user.find_one({"email": email}, {"_id": 0})
        if data is not None:
            return cls(**data)
