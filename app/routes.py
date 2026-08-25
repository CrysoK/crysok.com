from datetime import date
from flask import (
    render_template,
    send_from_directory,
    abort,
    current_app,
    render_template_string,
)
from app.logger import log
from app.content import get_discussions_with_cache


def calculate_age(born_str):
    if not born_str:
        log.warning("DATE_OF_BIRTH is not set; age will be omitted.")
        return None
    try:
        born = date.fromisoformat(born_str)
        today = date.today()
        return today.year - born.year - (
            (today.month, today.day) < (born.month, born.day)
        )
    except (ValueError, TypeError):
        log.warning(
            "DATE_OF_BIRTH has an invalid format (expected YYYY-MM-DD): %s",
            born_str,
        )
        return None


def register(app):
    log.info("Registering routes")

    @app.after_request
    def add_cache_headers(response):
        content_type = response.content_type or ""
        if not content_type.startswith("text/html"):
            return response

        # Browser always revalidates HTML. CDN may reuse it briefly while
        # GitHub-backed pages refresh in the background.
        response.headers["Cache-Control"] = (
            "public, max-age=0, s-maxage=120, stale-while-revalidate=600"
        )
        response.headers["Vary"] = "Accept-Language, Cookie"
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

        return render_template(
            "home.html.j2", age=age, page=page, rendered_body=rendered_body
        )

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
            abort(404)

        giscus_term = str(post["number"])

        return render_template("post.html.j2", post=post, giscus_term=giscus_term)

    # Local fallbacks. On Vercel these paths are served from public/ by the CDN.
    @app.route("/favicon.ico")
    def favicon():
        return send_from_directory(current_app.config["PUBLIC_FOLDER"], "favicon.ico")

    @app.route("/sitemap.xml")
    def sitemap():
        return send_from_directory(current_app.config["PUBLIC_FOLDER"], "sitemap.xml")

    @app.errorhandler(404)
    def page_not_found(_):
        return render_template("404.html.j2"), 404


log.debug("EOF")
