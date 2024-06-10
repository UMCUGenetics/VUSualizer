from flask_security import UserMixin
from src import mongo


class User(UserMixin):
    def __init__(self, email, password, role, active):
        self.id = email
        self.email = email
        self.password = password
        self.active = active
        self.role = role

    def is_authenticated(self):
        return True

    def is_active(self):
        return self.active

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.email

    def get_role(self):
        return self.role

    @classmethod
    def get(cls, email):
        data = mongo.db.user.find_one({"email": email}, {"_id": 0})
        if data is not None:
            return cls(email, data['password'], data['role'], data['active'])

    # Required for administrative interface
    def __unicode__(self):
        return self.login

    def save_to_db(self):
        mongo.db.user.insert_one(self.__dict__)
