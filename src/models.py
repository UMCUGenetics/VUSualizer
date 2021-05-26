import datetime
import uuid
from flask_login import UserMixin
from flask_admin import Admin
from flask_admin.contrib.pymongo import ModelView
from src import mongo
import json
from . import app

from wtforms import form, fields
from flask_admin.contrib.pymongo import ModelView
from flask_admin.model.fields import InlineFormField, InlineFieldList


# User admin
class InnerForm(form.Form):
    name = fields.StringField('Name')
    test = fields.StringField('Test')

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
    
    # Required for administrative interface
    def __unicode__(self):
        return self.login

    def save_to_db(self):
        mongo.db.user.insert(self.__dict__)

# Customized admin views
class UserForm(form.Form):
    name = fields.StringField('Name')
    email = fields.StringField('Email')
    password = fields.StringField('Password')

    # Inner form
    inner = InlineFormField(InnerForm)

    # Form list
    form_list = InlineFieldList(InlineFormField(InnerForm))

class UserView(ModelView):
    column_list = ('_id', 'email')
    column_sortable_list = ('_id', 'email')

    form = UserForm

# Create admin
admin = Admin(app, name='VUSualizer admin', template_mode='bootstrap3')

# Add view
admin.add_view(UserView(mongo.db.user, 'User'))

