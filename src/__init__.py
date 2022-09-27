from flask import Flask
from flask_pymongo import PyMongo
from flask_admin import Admin
from flask_login import LoginManager

# flask
app = Flask(__name__)
app.config.from_pyfile("config.py")

# mongo db
mongo = PyMongo(app)

# login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = u"Please login to access this page."
login_manager.login_message_category = "warning"

# Create admin
admin = Admin(app, name='VUSualizer admin', template_mode='bootstrap3')

# ignore PEP8/flake8 warning: flask import views folder after app creation
from .views import main, auth, admin_view  # noqa: F401 E402
