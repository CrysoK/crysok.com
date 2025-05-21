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
    # Blog
    GITHUB_API_URL = "https://api.github.com/graphql"
    GITHUB_API_TOKEN = os.getenv("GITHUB_API_TOKEN")
    GITHUB_REPO_OWNER = os.getenv("GITHUB_REPO_OWNER")
    GITHUB_REPO_NAME = os.getenv("GITHUB_REPO_NAME")
    GITHUB_BLOG_CATEGORY = os.getenv("GITHUB_BLOG_CATEGORY")
    GISCUS_REPO = f"{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}"
    GISCUS_REPO_ID = "REPO_ID_DE_GISCUS"
    DOMAIN = os.getenv("DOMAIN")  # User-Agent


log.debug("EOF")
