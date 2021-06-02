import datetime
import uuid
from flask import url_for, redirect, request
from flask_login import UserMixin, current_user
from flask_admin import Admin
from flask_admin.contrib.pymongo import ModelView
from flask_security import UserMixin
from src import mongo
import json
from . import app
from src import forms

from wtforms import form, fields
from flask_admin.contrib.pymongo import ModelView


# User admin
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
        return True

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
        mongo.db.user.insert(self.__dict__)
'''
class Role(RoleMixin):
    id = mongo.db.Column(mongo.db.Integer(), primary_key=True)
    name = mongo.db.Column(mongo.db.String(80), unique=True, nullable=False)
    description = mongo.db.Column(mongo.db.String(255))

    def __repr__(self):
        return "Role({0}-{1})".format(self.id, self.name)

    def __str__(self):
        return self.name
'''

# Customized admin views
class UserForm(form.Form):
    name = fields.StringField('Name')
    email = fields.StringField('Email')
    password = fields.StringField('Password')
    active = fields.BooleanField('Active')
    role = fields.StringField('Role')

class UserView(ModelView):

    def is_accessible(self):
        #return current_user.is_authenticated
        return current_user.role == "ROLE_ADMIN"

    def inaccessible_callback(self, name, **kwargs):
        # redirect to login page if user doesn't have access
        return redirect(url_for('login', next=request.url))

    column_list = ('_id', 'email', 'active', 'role')
    column_sortable_list = ('_id', 'email', 'active', 'role')
    form = UserForm

# Create admin
admin = Admin(app, name='VUSualizer admin', template_mode='bootstrap3')

# Add view
admin.add_view(UserView(mongo.db.user, 'User'))

