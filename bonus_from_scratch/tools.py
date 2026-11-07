import httpx
import ast
import operator


def get_weather(city: str) -> str:
    """Récupère la météo via Open-Meteo (gratuit, sans clé)."""
    # Geocoding
    geo = httpx.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": city, "count": 1, "language": "fr"},
        timeout=10.0,
    ).json()

    if not geo.get("results"):
        return f"Ville introuvable : {city}"

    loc  = geo["results"][0]
    lat, lon = loc["latitude"], loc["longitude"]

    # Météo
    meteo = httpx.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude":          lat,
            "longitude":         lon,
            "current_weather":   True,
            "wind_speed_unit":   "kmh",
        },
        timeout=10.0,
    ).json()

    cw = meteo["current_weather"]
    return (
        f"Météo à {city} : {cw['temperature']}°C, "
        f"vent {cw['windspeed']} km/h."
    )


def calculate(expression: str) -> str:
    """Évalue une expression mathématique de façon sécurisée.

    Restrictions :
    - seules les constantes int/float sont acceptées (pas de strings, listes, etc.)
    - seules les 6 opérations listées dans SAFE_OPS sont autorisées
    - tout le reste lève ValueError avec un message explicite
    """
    SAFE_OPS = {
        ast.Add: operator.add, ast.Sub: operator.sub,
        ast.Mult: operator.mul, ast.Div: operator.truediv,
        ast.Pow: operator.pow, ast.USub: operator.neg,
    }

    def _eval(node):
        if isinstance(node, ast.Constant):
            # On filtre explicitement : seuls les nombres sont acceptés.
            # Sans ce check, "calculate(\"hello\")" passerait silencieusement.
            if isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
                return node.value
            raise ValueError(f"Constante non autorisée : {type(node.value).__name__}")
        if isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type not in SAFE_OPS:
                raise ValueError(f"Opération non autorisée : {op_type.__name__}")
            return SAFE_OPS[op_type](_eval(node.left), _eval(node.right))
        if isinstance(node, ast.UnaryOp):
            op_type = type(node.op)
            if op_type not in SAFE_OPS:
                raise ValueError(f"Opération unaire non autorisée : {op_type.__name__}")
            return SAFE_OPS[op_type](_eval(node.operand))
        raise ValueError(f"Expression non autorisée : {type(node).__name__}")

    try:
        result = _eval(ast.parse(expression, mode="eval").body)
        return f"{expression} = {result}"
    except Exception as e:
        return f"Erreur de calcul : {e}"


def search_web_snippets(query: str, n: int = 3) -> str:
    """Recherche des snippets web via l'API publique DuckDuckGo Instant Answer (sans clé).

    Attention : ce n'est pas une vraie API de news. DuckDuckGo Instant Answer
    retourne des RelatedTopics (snippets encyclopédiques type Wikipedia), pas
    forcément des actualités récentes — parfois rien du tout.

    Pour de la veille pro, utilisez une API de recherche/news fiable
    (Tavily, Brave Search, NewsAPI...) ou un flux RSS contrôlé.
    """
    try:
        r = httpx.get(
            "https://api.duckduckgo.com/",
            params={"q": query, "format": "json", "no_html": 1},
            timeout=10.0,
        ).json()
        topics = r.get("RelatedTopics", [])[:n]
        if not topics:
            return f"Aucun résultat pour : {query}"
        return "\n".join(
            f"- {t['Text']}" for t in topics if "Text" in t
        )
    except Exception as e:
        return f"Erreur recherche : {e}"
