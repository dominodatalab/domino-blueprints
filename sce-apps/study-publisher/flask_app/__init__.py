"""Study Publisher Flask application factory."""
import os
import secrets
from flask import Flask


class ReverseProxied:
    """WSGI middleware for Domino's reverse proxy.

    Uses DOMINO_RUN_HOST_PATH env var as the authoritative script-name source.
    Falls back to HTTP_X_SCRIPT_NAME header only when the env var is absent,
    as the header alone can be spoofed or absent depending on proxy config.
    """

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        # Authoritative source: env var set by Domino at app launch
        script_name = os.environ.get('DOMINO_RUN_HOST_PATH', '').rstrip('/')

        # Fallback to proxy header when env var not set (e.g. local dev)
        if not script_name:
            script_name = environ.get('HTTP_X_SCRIPT_NAME', '').rstrip('/')

        if script_name:
            environ['SCRIPT_NAME'] = script_name
            path_info = environ.get('PATH_INFO', '')
            # Strip prefix if the proxy hasn't already done so
            if path_info.startswith(script_name):
                environ['PATH_INFO'] = path_info[len(script_name):] or '/'

        scheme = environ.get('HTTP_X_SCHEME', '')
        if scheme:
            environ['wsgi.url_scheme'] = scheme

        forwarded_host = environ.get('HTTP_X_FORWARDED_HOST', '')
        if forwarded_host:
            environ['HTTP_HOST'] = forwarded_host

        return self.app(environ, start_response)


def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')

    # A stable secret key must be provided via env var in production so
    # sessions survive app restarts. A random fallback is safe for dev only.
    app.secret_key = os.environ.get('FLASK_SECRET_KEY', secrets.token_hex(32))

    app.wsgi_app = ReverseProxied(app.wsgi_app)

    from .routes import main  # noqa: PLC0415
    app.register_blueprint(main)

    return app
