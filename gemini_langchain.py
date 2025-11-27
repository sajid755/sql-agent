import os
import requests
import time
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import tool

load_dotenv()

@tool
def get_lat_long_for_city(city: str) -> dict:
    """Get latitude and longitude for a city"""
    url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}"
    r = requests.get(url).json()

    if "results" not in r or len(r["results"]) == 0:
        return {"error": "City not found"}

    x = r["results"][0]
    return {"city": x["name"], "lat": x["latitude"], "lon": x["longitude"]}

@tool
def get_weather_for_lat_long(lat: float, lon: float) -> dict:
    """Get current temperature for lat/lon"""
    url = "https://api.open-meteo.com/v1/forecast"
    r = requests.get(url, params={
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m"
    }).json()

    temp = r["current"]["temperature_2m"]
    return {"temperature": temp}

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=os.getenv("GOOGLE_API_KEY")
)

tools = [get_lat_long_for_city, get_weather_for_lat_long]
llm_with_tools = llm.bind_tools(tools)

messages = [
    ("system", "Always call multiple tools in parallel when possible. Never call one at a time if you can batch them."),
    ("human", "give me the temp of dhaka, istanbul, sydney")
]

start_time = time.time()
response = llm_with_tools.invoke(messages)

# Execute tool calls and collect results
while response.tool_calls:
    messages.append(response)
    for call in response.tool_calls:
        tool_fn = get_lat_long_for_city if call["name"] == "get_lat_long_for_city" else get_weather_for_lat_long
        result = tool_fn.invoke(call["args"])
        messages.append({"role": "tool", "content": str(result), "tool_call_id": call["id"]})
    response = llm_with_tools.invoke(messages)

end_time = time.time()
response_time = end_time - start_time

# Extract text from response content
if isinstance(response.content, list):
    text = response.content[0]['text'] if response.content else ""
else:
    text = response.content

print(text)
print(f"\nResponse time: {response_time:.2f}s")
