from flask import Flask, make_response
from flask_debugtoolbar import DebugToolbarExtension
from flask_admin import Admin

# from pymongo import MongoClient

from models import *
from views import *  # index, variant, export, register, login, logout, account

# client = MongoClient('localhost', 27017)
# mydb = client.vus
# mycollection = mydb.variant

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

app.add_url_rule('/register', view_func=register, methods=["GET", "POST"])
app.add_url_rule('/login', view_func=login, methods=["GET", "POST"])
app.add_url_rule('/logout', view_func=logout)
app.add_url_rule('/account', view_func=account)

app.add_url_rule('/variants', view_func=variants)
app.add_url_rule('/variant/<id>', view_func=variant)

app.add_url_rule('/patients', view_func=patients)
app.add_url_rule('/patient/<id>', view_func=patient)

app.add_url_rule('/genes', view_func=genes)
app.add_url_rule('/gene/<id>', view_func=gene)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return User.objects(pk=user_id).first()


@app.errorhandler(404)
def notfound(e):
    return make_response(render_template("404.html"))


if __name__ == "__main__":
    admin = Admin(app, 'VUSualizer')
    admin.add_view(UserView(User))
    admin.add_view(VariantView(Variant))
    # admin.add_view(PostView(Post))

    app.run(debug=True)
