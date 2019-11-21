from flask import Flask
from flask_mongoengine import MongoEngine, Document
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import Email, Length, InputRequired
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_debugtoolbar import DebugToolbarExtension

from models import db, User
from views import * #index, variant, export, register, login, logout, account

app = Flask(__name__)
app.config.from_object(__name__)
app.config['TESTING'] = True
app.config['SECRET_KEY'] = 'vusualyzerrrrrrrr'
app.config['MONGODB_SETTINGS'] = {
    'db': 'vus',
    'host': 'mongodb://localhost:27017/vus'
}
app.debug = True
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config['DEBUG_TB_PANELS'] = (
    'flask_debugtoolbar.panels.versions.VersionDebugPanel',
    'flask_debugtoolbar.panels.timer.TimerDebugPanel',
    'flask_debugtoolbar.panels.headers.HeaderDebugPanel',
    'flask_debugtoolbar.panels.request_vars.RequestVarsDebugPanel',
    'flask_debugtoolbar.panels.template.TemplateDebugPanel',
    'flask_debugtoolbar.panels.logger.LoggingPanel',
    'flask_mongoengine.panels.MongoDebugPanel'
)

db.init_app(app)

DebugToolbarExtension(app)

app.add_url_rule('/', view_func=index)
app.add_url_rule('/home', view_func=index)
app.add_url_rule('/variant', view_func=variant)
app.add_url_rule('/register', view_func=register, methods=["GET", "POST"])
app.add_url_rule('/login', view_func=login, methods=["GET", "POST"])
app.add_url_rule('/logout', view_func=logout)
app.add_url_rule('/account', view_func=account)
app.add_url_rule('/variants', view_func=variants)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.objects(pk=user_id).first()



if __name__ == "__main__":
    app.run(debug=True)