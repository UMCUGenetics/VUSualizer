import datetime
import uuid
from flask_login import UserMixin
from src import mongo
import json


class User(UserMixin):
    def __init__(self, email, password):
        self.id = email
        self.email = email
        self.password = password

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.email

    @classmethod
    def get(cls, email):
        data = mongo.db.user.find_one({"email": email}, {"_id": 0})
        if data is not None:
            return cls(email, data['password'])
            # return cls(**data)

    def save_to_db(self):
        mongo.db.user.insert(self.__dict__)
