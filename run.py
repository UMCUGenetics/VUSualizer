'''
Settings and start-script for activating the VUSualizer on the server.
'''

from src import app as application
import sys
import extra.config

# /data/vusualizer/VUSualizer, use location of VUSualizer on the serverside
sys.path.insert(0, extra.config.vusualizer_path)


class WSGIMiddleware(object):
    def __init__(self, app, prefix):
        self.app = app
        self.prefix = prefix

    def __call__(self, environ, start_response):
        environ['SCRIPT_NAME'] = self.prefix
        return self.app(environ, start_response)


# Set any url prefix (script_root) here eg. /vusualizer
application.wsgi_app = WSGIMiddleware(application.wsgi_app, "/")

if __name__ == "__main__":
    application.run()
