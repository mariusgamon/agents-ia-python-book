# tools/weather.py
import config
import httpx
from agents import function_tool


async def fetch_weather(city: str) -> dict:
    """
    Récupère la météo actuelle pour une ville.

    Args:
        city: Nom de la ville (ex: "Paris", "Lyon", "Bordeaux")

    Returns:
        Météo actuelle avec température, description, humidité,
        ou un dict {"error": ...} si le service ne répond pas.
    """
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"q": city, "appid": config.OPENWEATHER_API_KEY, "units": "metric", "lang": "fr"}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
    except httpx.TimeoutException:
        return {"error": f"Timeout : le service météo ne répond pas pour {city}"}
    except httpx.HTTPStatusError as e:
        return {"error": f"Erreur HTTP {e.response.status_code} pour {city}"}

    return {
        "city": data["name"],
        "temperature": data["main"]["temp"],
        "feels_like": data["main"]["feels_like"],
        "description": data["weather"][0]["description"],
        "humidity": data["main"]["humidity"],
        "wind_kmh": round(data["wind"]["speed"] * 3.6, 1),
    }


# La même fonction, exposée à l'agent comme outil (même nom qu'au Jour 2)
get_weather = function_tool(fetch_weather, name_override="get_weather")
