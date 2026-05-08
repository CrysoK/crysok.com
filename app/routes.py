from datetime import date
from flask import render_template, send_file, abort, current_app, render_template_string
from app.logger import log


from app.content import get_discussions_with_cache


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

    @app.after_request
    def add_cache_headers(response):
        # Cache for 5 minutes in browser and Vercel CDN
        response.headers["Cache-Control"] = "public, max-age=300, s-maxage=300"
        # Crucial for Babel: Tell CDN to separate cache by language
        response.headers["Vary"] = "Accept-Language"
        return response

    @app.route("/")
    def home():
        dob_str = current_app.config.get("DATE_OF_BIRTH")
        age = calculate_age(dob_str)
        
        pages_data = get_discussions_with_cache(
            current_app.config["GITHUB_PAGES_CATEGORY"]
        )
        page = next((p for p in pages_data if p["slug"] == "home"), None)
        
        rendered_body = {}
        if page and "body_html" in page:
            for lang, html_content in page["body_html"].items():
                rendered_body[lang] = render_template_string(html_content, age=age)

        return render_template("home.html.j2", age=age, page=page, rendered_body=rendered_body)

    @app.route("/projects")
    def projects():
        projects_data = get_discussions_with_cache(
            current_app.config["GITHUB_PROJECTS_CATEGORY"]
        )
        return render_template("projects.html.j2", projects=projects_data)

    @app.route("/projects/<slug>")
    def project_detail(slug):
        projects_data = get_discussions_with_cache(
            current_app.config["GITHUB_PROJECTS_CATEGORY"]
        )
        project = next((p for p in projects_data if p["slug"] == slug), None)
        if project is None:
            abort(404)

        giscus_term = str(project["number"])
        return render_template(
            "project_detail.html.j2", project=project, giscus_term=giscus_term
        )

    @app.route("/links")
    def links():
        pages_data = get_discussions_with_cache(
            current_app.config["GITHUB_PAGES_CATEGORY"]
        )
        page = next((p for p in pages_data if p["slug"] == "links"), None)

        return render_template("links.html.j2", page=page)

    @app.route("/blog")
    def blog():
        posts = get_discussions_with_cache(current_app.config["GITHUB_BLOG_CATEGORY"])
        return render_template("blog.html.j2", posts=posts)

    @app.route("/blog/<slug>")
    def post_detail(slug):
        posts = get_discussions_with_cache(current_app.config["GITHUB_BLOG_CATEGORY"])
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
