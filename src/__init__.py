from flask import Flask
from flask_pymongo import PyMongo
from flask_admin import Admin
#from flask_mongoengine import MongoEngine
from flask_login import LoginManager

# flask
app = Flask(__name__)
app.config.from_pyfile("config.py")

# mongo db
mongo = PyMongo(app)
#db = MongoEngine()
#db.init_app(app)

# login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = u"Please login to access this page."
login_manager.login_message_category = "warning"

# Flask BCrypt will be used to salt the user password
# flask_bcrypt = Bcrypt(app)

# Create admin
admin = Admin(app, name='VUSualizer admin', template_mode='bootstrap3')


from . import *
from .views import main, auth, api, admin_view
