from flask_mongoengine import MongoEngine
from flask_login import UserMixin


db = MongoEngine()

class Variant(db.DynamicDocument):
    chromosome = db.StringField()

class User(UserMixin, db.Document):
    meta = {'collection': 'user'}
    email = db.StringField(max_length=30)
    password = db.StringField()