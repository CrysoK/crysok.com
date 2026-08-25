from flask import Flask, request, current_app, g
from flask_babel import Babel, gettext as _, lazy_gettext as _l, format_date  # noqa
from app.config import Config
from app import routes
from app.logger import log


babel = Babel()


def create_app(config=Config):
    log.info("Creating app")

    app = Flask(
        __name__,
        static_folder=config.STATIC_FOLDER,
        static_url_path="/static",
        template_folder=config.TEMPLATES_FOLDER,
    )
    app.config.from_object(config)

    # Routing
    routes.register(app)

    log.info("Registering Babel")
    babel.init_app(app, locale_selector=get_locale)

    app.jinja_env.globals['format_date'] = format_date

    return app


def get_locale():
    log.debug("Getting locale")
    langs = current_app.config["LANGUAGES"]
    lang = request.cookies.get("lang")
    if lang not in langs:
        lang = request.accept_languages.best_match(langs)
        if lang is None:
            lang = current_app.config["BABEL_DEFAULT_LOCALE"]
        # Do not Set-Cookie here: it forces CDN BYPASS. The language switcher
        # writes the cookie from the client when the user picks a language.

    g.lang = lang
    return lang


log.debug("EOF")
