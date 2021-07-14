'''
Settings and start-script for activating the VUSualizer on the server.
Use this run.py on the serverside. change name of run_dwergeik.py to run.py
The original run.py is for using VUSualizer locally
'''

from src import app as application
import sys

# /data/vusualizer/VUSualizer, use location of VUSualizer on the serverside
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
