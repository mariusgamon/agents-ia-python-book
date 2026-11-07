# weather_agent.py
import config

from agents import Agent, Runner, function_tool
import httpx
import asyncio

@function_tool
async def get_weather(city: str) -> dict:
    """
    Récupère la météo actuelle pour une ville.
    
    Args:
        city: Nom de la ville (ex: "Paris", "Lyon", "Bordeaux")
    
    Returns:
        Météo actuelle avec température, description, humidité
    """
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": config.OPENWEATHER_API_KEY,
        "units": "metric",
        "lang": "fr"
    }
    
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()
    
    return {
        "city": data["name"],
        "temperature": data["main"]["temp"],
        "feels_like": data["main"]["feels_like"],
        "description": data["weather"][0]["description"],
        "humidity": data["main"]["humidity"],
        "wind_kmh": round(data["wind"]["speed"] * 3.6, 1)
    }

weather_agent = Agent(
    name="WeatherAgent",
    model=config.DEFAULT_MODEL,
    instructions="""You are a weather agent. When asked about the weather in a city,
    use the get_weather tool to obtain real data.
    Present the results in a conversational and helpful way.""",
    tools=[get_weather],
)

async def main():
    cities = ["Paris", "Lyon", "Nice"]
    for city in cities:
        result = await Runner.run(
            weather_agent,
            input=f"Quelle est la météo à {city} ?"
        )
        print(f"\n{city} : {result.final_output}")

asyncio.run(main())
