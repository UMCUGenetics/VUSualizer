from src import app as application
import sys

# /data/vusualizer/VUSualizer
sys.path.insert(0, '/data/vusualizer/VUSualizer')


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
