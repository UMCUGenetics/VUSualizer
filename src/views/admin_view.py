from flask_admin.contrib.pymongo import ModelView
from flask_login import current_user
from wtforms import form, fields
from flask import url_for, redirect, request
from src import mongo
from .. import admin


# Customized admin views, user form used in the UserView
class UserForm(form.Form):
    name = fields.StringField('Name')
    email = fields.StringField('Email')
    password = fields.StringField('Password')
    active = fields.BooleanField('Active')
    role = fields.StringField('Role')

# add UserView, where admin can change properties of users
class UserView(ModelView):

    def is_accessible(self):
        '''Only allow access to adminpages if user has an admin role. Wrapper for the Flask is_accessible function'''
        if current_user.is_authenticated:
            return current_user.role == "ROLE_ADMIN"
        else:
            return False

    def inaccessible_callback(self, name, **kwargs):
        # redirect to login page if user doesn't have access
        return redirect(url_for('login', next=request.url))

    # which properties of users are shown and editable in UserView
    column_list = ('_id', 'email', 'active', 'role')
    column_sortable_list = ('_id', 'email', 'active', 'role')
    form = UserForm


# Add view
admin.add_view(UserView(mongo.db.user, 'User'))
