import requests
import frontmatter
from markdown import markdown
from datetime import datetime
from app.config import Config
from pymdownx.emoji import to_alt


SEARCH_POSTS_QUERY = """
query ($query: String!, $limit: Int!, $after: String) {
  search(query: $query, type: DISCUSSION, first: $limit, after: $after) {
    pageInfo {
      startCursor
      hasNextPage
      endCursor
    }
    edges {
      cursor
      node {
        ... on Discussion {
          id
          url
          number # Importante para Giscus
          databaseId
          title
          body
          createdAt
          updatedAt
          category {
            name
          }
          labels(first: 10) {
            edges {
              node {
                id
                name
                description
                color
              }
            }
          }
        }
      }
    }
  }
}
"""


def slugify(text):
    import re

    text = text.lower()
    text = re.sub(
        r"[^a-z0-9\s-]", "", text
    )  # Eliminar caracteres no alfanuméricos excepto espacios y guiones
    text = re.sub(r"\s+", "-", text)  # Reemplazar espacios con guiones
    text = re.sub(r"-+", "-", text)  # Reemplazar múltiples guiones con uno solo
    return text.strip("-")


def parse_post_data(discussion_node):
    """Parsea un nodo de discusión de la API de GitHub a un formato de post."""
    try:
        # Parsear frontmatter
        fm = frontmatter.loads(discussion_node["body"])
        content_md = fm.content
        metadata = fm.metadata
    except Exception:  # Si no hay frontmatter o hay error
        content_md = discussion_node["body"]
        metadata = {}

    title = metadata.get(
        "title", discussion_node["title"]
    )  # Usar título de frontmatter si existe
    slug = metadata.get("slug") or slugify(title)
    description = metadata.get("description", "")

    # Fechas
    published_str = metadata.get("published")
    if published_str:
        published_at = datetime.strptime(str(published_str), "%Y-%m-%d")
    else:
        published_at = datetime.strptime(
            discussion_node["createdAt"], "%Y-%m-%dT%H:%M:%SZ"
        )

    updated_at = datetime.strptime(discussion_node["updatedAt"], "%Y-%m-%dT%H:%M:%SZ")

    # Etiquetas (tags y series)
    tags = []
    series = None
    for edge in discussion_node.get("labels", {}).get("edges", []):
        label_name = edge["node"]["name"]
        if label_name.startswith("tag/"):
            tags.append(label_name.split("/", 1)[1])
        elif label_name.startswith("series/"):
            series = label_name.split("/", 1)[1]
            # Podrías querer solo una serie por post, o una lista si permites múltiples

    return {
        "id": discussion_node["id"],
        "url": discussion_node["url"],
        "number": discussion_node["number"],  # Para Giscus
        "title": title,
        "slug": slug,
        "body_md": content_md,
        "body_html": markdown(
            content_md,
            extensions=[
                "tables",
                "fenced_code",  # ``` code blocks
                "footnotes",
                "attr_list",  # atributos html en markdown
                "abbr",  # abreviaturas html
                "sane_lists",  # better list parsing
                "smarty",  # convierte algunos símbolos ascii a entidades html
                "toc",  # asigna ids a títulos para crear una toc
                "pymdownx.betterem",  # mejora de smartstrong
                # "pymdownx.superfences",  # mejora fenced_code (pero rompe tables)
                "pymdownx.emoji",  # emojis a partir de ids como :smile:
                "pymdownx.tasklist",  # lista de tareas de GH
                "pymdownx.magiclink",  # beter link generation
                "gfm_admonition",  # "callouts" de GH
            ],
            extension_configs={"pymdownx.emoji": {"emoji_generator": to_alt}},
            tab_length=2,
        ),
        "description": description,
        "published_at": published_at,
        "updated_at": updated_at,
        "tags": tags,
        "series": series,
        "raw_discussion": discussion_node,  # Guardar el nodo original por si se necesita algo más
    }


def _fetch_discussions_page(limit=50, after=None):
    """Obtiene una página de discusiones."""
    headers = {
        "Authorization": f"Bearer {Config.GITHUB_API_TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": Config.DOMAIN,
    }
    query_string = f'repo:{Config.GITHUB_REPO_OWNER}/{Config.GITHUB_REPO_NAME} category:"{Config.GITHUB_BLOG_CATEGORY}" -label:state/draft'

    variables = {"query": query_string, "limit": limit, "after": after}
    response = requests.post(
        Config.GITHUB_API_URL,
        json={"query": SEARCH_POSTS_QUERY, "variables": variables},
        headers=headers,
    )
    response.raise_for_status()  # Lanza una excepción para errores HTTP
    return response.json()


def get_all_posts_recursive(limit_per_page=100):
    """Obtiene todos los posts recursivamente."""
    all_posts_data = []
    after_cursor = None
    has_next_page = True

    while has_next_page:
        try:
            data = _fetch_discussions_page(limit=limit_per_page, after=after_cursor)
        except requests.exceptions.RequestException as e:
            print(f"Error fetching discussions: {e}")
            # Podrías querer manejar esto de forma más elegante, ej., retornar posts cacheados si los hay
            return []  # O lanzar la excepción para que la app la maneje

        if "errors" in data:
            print(f"GraphQL Errors: {data['errors']}")
            # Manejar errores de GraphQL
            return []

        search_results = data.get("data", {}).get("search", {})
        if not search_results or not search_results.get("edges"):
            break  # No hay resultados o error en la estructura

        for edge in search_results["edges"]:
            if (
                edge["node"]["category"]["name"] == Config.GITHUB_BLOG_CATEGORY
            ):  # Doble check de categoría
                # Filtrar posts con etiqueta "state/draft"
                is_draft = any(
                    label["node"]["name"] == "state/draft"
                    for label in edge["node"].get("labels", {}).get("edges", [])
                )
                if not is_draft:
                    all_posts_data.append(parse_post_data(edge["node"]))

        page_info = search_results.get("pageInfo", {})
        has_next_page = page_info.get("hasNextPage", False)
        after_cursor = page_info.get("endCursor")

    # Ordenar por fecha de publicación (más reciente primero)
    all_posts_data.sort(key=lambda p: p["published_at"], reverse=True)
    return all_posts_data


# Puedes añadir una capa de caching más robusta aquí si lo deseas
# Por ejemplo, usando Flask-Caching para guardar los resultados por X minutos
_cached_posts = None
_cache_timestamp = None
CACHE_DURATION_SECONDS = 300  # 5 minutos


def get_all_posts_with_cache():
    global _cached_posts, _cache_timestamp
    now = datetime.now()

    if _cached_posts is not None and _cache_timestamp is not None:
        if (now - _cache_timestamp).total_seconds() < CACHE_DURATION_SECONDS:
            print("Returning posts from cache.")
            return _cached_posts

    print("Fetching posts from GitHub API.")
    posts = get_all_posts_recursive()
    _cached_posts = posts
    _cache_timestamp = now
    return posts
