from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
import os

import requests
import json

load_dotenv()
tavily_api_key = os.getenv("TAVILY_API_KEY")
open_weather_api_key = os.getenv("OPEN_WEATHRER_API_KEY")

mcp = FastMCP(
    "WebSearch",
    instructions="You are a web search assistant that can help with web searching tasks.",
    host="0.0.0.0",
    port=8001,
)


# 웹검색
@mcp.tool()
async def web_search(query: str, topic: str = "general", max_results: int = 3) -> str:
    """Search the web for a given query and return the results.
    Args:
        query (str): The search query.
        topic (str): The topic of the search. Must be either "news" or "general". Default is "general".
        max_results (int): The maximum number of results to return. Default is 3.
    """
    url = "https://api.tavily.com/search"

    payload = {
        "query": query,
        "topic": topic,
        "search_depth": "basic",
        "chunks_per_source": 3,
        "max_results": max_results,
        "time_range": None,
        "days": 7,
        "include_answer": True,
        "include_raw_content": False,
        "include_images": False,
        "include_image_descriptions": False,
        "include_domains": [],
        "exclude_domains": [],
    }
    headers = {
        "Authorization": f"Bearer {tavily_api_key}",
        "Content-Type": "application/json",
    }

    response = requests.request("POST", url, json=payload, headers=headers)

    return response.text


# 날씨검색
@mcp.tool()
async def weather_search(city: str) -> dict:
    """Get the current, daily weather and overview for a given city.

    Args:
        city (str): The name of the city to get the weather for.
    """

    def get_coordinates(city, api_key):
        url = f"http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={api_key}"
        response = requests.get(url)
        data = response.json()

        if not data:
            raise ValueError(f"도시 '{city}'에 대한 정보를 찾을 수 없습니다.")

        lat = data[0]["lat"]
        lon = data[0]["lon"]
        return lat, lon

    lat, lon = get_coordinates(city, open_weather_api_key)

    api = f"""https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&lang=kr&appid={open_weather_api_key}"""

    result = requests.get(api)
    data = json.loads(result.text)
    current_weather = data["current"]
    daily_weather = data["daily"]

    api = f"""https://api.openweathermap.org/data/3.0/onecall/overview?lat={lat}&lon={lon}&appid={open_weather_api_key}"""
    result = requests.get(api)
    data = json.loads(result.text)

    weather_overview = data["weather_overview"]

    return {
        "current_weather": current_weather,
        "daily_weather": daily_weather,
        "weather_overview": weather_overview,
    }


if __name__ == "__main__":
    mcp.run(transport="sse")
