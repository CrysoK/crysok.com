import os
from app.logger import log


class Config:
    # Flask
    TEMPLATES_FOLDER = "templates"
    STATIC_FOLDER = "static"
    SECRET_KEY = os.environ.get("FLASK_SECRET", "flask-secret-key")
    LANGUAGES = ["en", "es"]
    # Flask-Babel
    BABEL_DEFAULT_LOCALE = "en"
    BABEL_TRANSLATION_DIRECTORIES = "i18n"
    # Babel
    BABEL_CLI_CONFIG = "app/babel.cfg"
    BABEL_CLI_I18N_DIR = "app/i18n"
    # Flask-Jinja2
    jinja_options = {
        "comment_start_string": "<!--",
        "comment_end_string": "-->",
    }


log.debug("EOF")
