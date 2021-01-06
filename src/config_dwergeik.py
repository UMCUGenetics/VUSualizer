DEBUG = True
TESTING = True

#APPLICATION_ROOT = "/vusualizer"
#SERVER_NAME = "dwergeik.op.umcutrecht.nl/"

# mongo db
SECRET_KEY = "vusualyzerrrrrrrr"
MONGO_URI = "mongodb://%s:%s@localhost/vusualizer" % ("vusualizer", "bla")
#"mongodb://localhost:27017/vus"

# debug bar
DEBUG_TB_INTERCEPT_REDIRECTS = False
DEBUG_TB_PANELS = (
    'flask_debugtoolbar.panels.versions.VersionDebugPanel',
    'flask_debugtoolbar.panels.timer.TimerDebugPanel',
    'flask_debugtoolbar.panels.headers.HeaderDebugPanel',
    'flask_debugtoolbar.panels.request_vars.RequestVarsDebugPanel',
    'flask_debugtoolbar.panels.template.TemplateDebugPanel',
    'flask_debugtoolbar.panels.logger.LoggingPanel',
    'flask_mongoengine.panels.MongoDebugPanel'
)

# REMEMBER_COOKIE_DURATION = timedelta(seconds=20)
