from flask_mongoengine import MongoEngine
from flask_login import UserMixin
from wtforms.validators import InputRequired
from pymongo import MongoClient

# db = MongoEngine()

db = MongoClient('localhost', 27017)


class Variant(db.DynamicDocument):
    name = db.StringField()
    chromosome = db.StringField()
    tags = db.ListField(db.ReferenceField('Tag'))

    # Required for administrative interface
    def __unicode__(self):
        return self.name


class User(UserMixin, db.Document):
    meta = {'collection': 'user'}
    name = db.StringField()
    email = db.StringField()
    password = db.StringField()
    tags = db.ListField(db.ReferenceField('Tag'))

    # date_joined, enabled, last_login,

    def __unicode__(self):
        return self.name


class Post(db.Document):
    author = db.ReferenceField(User)
    text = db.StringField(validators=[InputRequired(message=u'Missing title.')])

    def __unicode__(self):
        return self.author


class Tag(db.Document):
    name = db.StringField(max_length=10)

    def __unicode__(self):
        return self.name
