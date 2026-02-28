import re
import requests
import frontmatter
from markdown import markdown
from datetime import datetime
from app.config import Config
from pymdownx.emoji import to_alt


SEARCH_DISCUSSIONS_QUERY = """
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


def extract_first_image(markdown_text):
    """Extrae la primera URL de imagen de un texto en Markdown o HTML."""
    # Buscar formato Markdown: ![alt text](https://url-de-la-imagen.png "title")
    md_match = re.search(r"!\[.*?\]\(([^)\s]+).*?\)", markdown_text)
    if md_match:
        return md_match.group(1)

    # Buscar formato HTML: <img src="https://url-de-la-imagen.png" ...>
    html_match = re.search(
        r'<img[^>]+src=["\']([^"\']+)["\']', markdown_text, re.IGNORECASE
    )
    if html_match:
        return html_match.group(1)

    return None


def split_bilingual_content(markdown_text):
    """Separa el contenido en inglés y español. Si no hay etiquetas, devuelve lo mismo para ambos."""
    # Buscar si existe la etiqueta de separación
    first_tag_match = re.search(r"<!--\s*(ES|EN)\s*-->", markdown_text, re.IGNORECASE)

    # Si no hay etiquetas, asumimos que el texto es válido para ambos idiomas (retrocompatibilidad)
    if not first_tag_match:
        return markdown_text, markdown_text

    # Extraer todo lo que esté ANTES de la primera etiqueta (ej. una imagen de portada compartida)
    common_header = markdown_text[: first_tag_match.start()].strip()

    es_match = re.search(
        r"<!--\s*ES\s*-->(.*?)(?=<!--\s*EN\s*-->|$)",
        markdown_text,
        re.DOTALL | re.IGNORECASE,
    )
    en_match = re.search(
        r"<!--\s*EN\s*-->(.*?)(?=<!--\s*ES\s*-->|$)",
        markdown_text,
        re.DOTALL | re.IGNORECASE,
    )

    content_es = es_match.group(1).strip() if es_match else ""
    content_en = en_match.group(1).strip() if en_match else ""

    # Unir el encabezado común (imagen) con el contenido específico de cada idioma
    if common_header:
        content_es = f"{common_header}\n\n{content_es}"
        content_en = f"{common_header}\n\n{content_en}"

    return content_es, content_en


def parse_discussion_node(discussion_node):
    """Parsea un nodo de discusión de la API de GitHub a un formato de post."""
    try:
        # Parsear frontmatter
        fm = frontmatter.loads(discussion_node["body"])
        content_md = fm.content
        metadata = fm.metadata
    except Exception:  # Si no hay frontmatter o hay error
        content_md = discussion_node["body"]
        metadata = {}

    # Fallback al título/descripción base si no existe la versión traducida
    base_title = metadata.get("title", discussion_node["title"])
    title = {
        "es": metadata.get("title_es", base_title),
        "en": metadata.get("title_en", base_title),
    }
    base_desc = metadata.get("description", "")
    description = {
        "es": metadata.get("description_es", base_desc),
        "en": metadata.get("description_en", base_desc),
    }
    slug = metadata.get("slug") or slugify(base_title)
    tabs = int(str(metadata.get("tabs", 2)))

    # Prioridad: 1. Frontmatter -> 2. Primera imagen del Markdown -> 3. None
    cover_image = metadata.get("image") or extract_first_image(content_md)

    body_md_es, body_md_en = split_bilingual_content(content_md)

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

    extensions = [
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
        "pymdownx.tilde",  # soporte para tachado (~~strikethrough~~)
        "gfm_admonition",  # "callouts" de GH
    ]
    extension_configs = {
        "pymdownx.emoji": {"emoji_generator": to_alt},
        "pymdownx.tilde": {"subscript": False},
    }

    return {
        "id": discussion_node["id"],
        "url": discussion_node["url"],
        "number": discussion_node["number"],  # Para Giscus
        "title": title,
        "slug": slug,
        "cover_image": cover_image,
        "body_md": {
            "es": body_md_es,
            "en": body_md_en,
        },
        "body_html": {
            "es": markdown(
                body_md_es,
                extensions=extensions,
                extension_configs=extension_configs,
                tab_length=tabs,
            ),
            "en": markdown(
                body_md_en,
                extensions=extensions,
                extension_configs=extension_configs,
                tab_length=tabs,
            ),
        },
        "description": description,
        "published_at": published_at,
        "updated_at": updated_at,
        "tags": tags,
        "series": series,
        "raw_discussion": discussion_node,  # Guardar el nodo original por si se necesita algo más
        "meta": metadata,
    }


def _fetch_discussions_page(category_name, limit=50, after=None):
    """Obtiene una página de discusiones para una categoría específica."""
    headers = {
        "Authorization": f"Bearer {Config.GITHUB_API_TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": Config.DOMAIN,
    }
    query_string = f'repo:{Config.GITHUB_REPO_OWNER}/{Config.GITHUB_REPO_NAME} category:"{category_name}" -label:state/draft'

    variables = {"query": query_string, "limit": limit, "after": after}
    response = requests.post(
        Config.GITHUB_API_URL,
        json={"query": SEARCH_DISCUSSIONS_QUERY, "variables": variables},
        headers=headers,
    )
    response.raise_for_status()  # Lanza una excepción para errores HTTP
    return response.json()


def get_all_discussions_recursive(category_name, limit_per_page=100):
    """Obtiene todas las discusiones recursivamente para una categoría."""
    all_items_data = []
    after_cursor = None
    has_next_page = True

    while has_next_page:
        try:
            data = _fetch_discussions_page(
                category_name, limit=limit_per_page, after=after_cursor
            )
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
            if edge["node"]["category"]["name"] == category_name:  # Doble check
                # Filtrar posts con etiqueta "state/draft"
                is_draft = any(
                    label["node"]["name"] == "state/draft"
                    for label in edge["node"].get("labels", {}).get("edges", [])
                )
                if not is_draft:
                    all_items_data.append(parse_discussion_node(edge["node"]))

        page_info = search_results.get("pageInfo", {})
        has_next_page = page_info.get("hasNextPage", False)
        after_cursor = page_info.get("endCursor")

    # 1. Ordenamos por fecha de publicación (más reciente primero, como respaldo)
    all_items_data.sort(key=lambda p: p["published_at"], reverse=True)
    # 2. Ordenamos por el campo 'order' del frontmatter (1 es el primero).
    # Si un post no tiene 'order', se le asigna 9999 para que vaya al final.
    all_items_data.sort(key=lambda p: p["meta"].get("order", 9999))
    return all_items_data


# Sistema de caché para múltiples categorías
_caches = {}
CACHE_DURATION_SECONDS = 300  # 5 minutos


def get_discussions_with_cache(category_name):
    global _caches
    now = datetime.now()

    if category_name in _caches:
        cached_data, timestamp = _caches[category_name]
        if (now - timestamp).total_seconds() < CACHE_DURATION_SECONDS:
            print(f"Returning {category_name} from cache.")
            return cached_data

    print(f"Fetching {category_name} from GitHub API.")
    discussions = get_all_discussions_recursive(category_name)
    _caches[category_name] = (discussions, now)
    return discussions
