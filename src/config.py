'''
Used by __init__.py to set the MongoDB configuration for the whole app
The app can then be referenced/imported by other script using the __init__.py
'''

DEBUG = True
TESTING = True

# mongo db
SECRET_KEY = ""
MONGO_URI = "mongodb://localhost:27017/vus"

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

# gnomad settings
GNOMAD_URI_SUFFIX = '?dataset=gnomad_r2_1'