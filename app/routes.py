from flask import render_template, send_file
from app.logger import log


def register(app):
    log.info("Registering routes")

    @app.route("/")
    def home():
        return render_template("home.html.j2")

    @app.route("/projects")
    def projects():
        return render_template("projects.html.j2")

    @app.route("/links")
    def links():
        return render_template("links.html.j2")

    @app.route("/blog")
    def blog():
        return render_template("blog.html.j2")

    @app.route("/cv")
    def cv():
        return render_template("cv.html.j2")

    @app.route("/favicon.ico")
    def favicon():
        return send_file("static/favicon/favicon.ico")

    @app.errorhandler(404)
    def page_not_found(_):
        return render_template("404.html.j2"), 404


log.debug("EOF")
