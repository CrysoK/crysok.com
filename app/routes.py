from datetime import date
from flask import render_template, send_file, abort, current_app
from app.logger import log


from app.blog import get_all_posts_with_cache


def calculate_age(born_str):
    if not born_str:
        raise ValueError("La variable de entorno DATE_OF_BIRTH no está configurada.")
    try:
        born = date.fromisoformat(born_str)
        today = date.today()
        age = (
            today.year - born.year - ((today.month, today.day) < (born.month, born.day))
        )
        return age
    except (ValueError, TypeError):
        raise ValueError(
            f"El formato de DATE_OF_BIRTH es incorrecto. Se esperaba 'YYYY-MM-DD', pero se recibió '{born_str}'."
        )


def register(app):
    log.info("Registering routes")

    @app.route("/")
    def home():
        dob_str = current_app.config.get("DATE_OF_BIRTH")
        age = calculate_age(dob_str)
        return render_template("home.html.j2", age=age)

    @app.route("/projects")
    def projects():
        return render_template("projects.html.j2")

    @app.route("/links")
    def links():
        return render_template("links.html.j2")

    @app.route("/blog")
    def blog():
        posts = get_all_posts_with_cache()
        return render_template("blog.html.j2", posts=posts)

    @app.route("/blog/<slug>")
    def post_detail(slug):
        posts = get_all_posts_with_cache()
        post = next((p for p in posts if p["slug"] == slug), None)
        if post is None:
            abort(404)  # O redirigir a una página de error personalizada

        # Pasar el número de la discusión para Giscus
        giscus_term = str(post["number"])

        return render_template("post.html.j2", post=post, giscus_term=giscus_term)

    @app.route("/favicon.ico")
    def favicon():
        return send_file("static/favicon/favicon.ico")

    @app.route("/ads.txt")
    def ads():
        return send_file("static/ads.txt")

    @app.route("/sitemap.xml")
    def sitemap():
        return send_file("static/sitemap.xml")

    @app.errorhandler(404)
    def page_not_found(_):
        return render_template("404.html.j2"), 404


log.debug("EOF")
