import requests
import time
from langchain_ollama import ChatOllama
from langchain.tools import tool

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

# Initialize Ollama LLM with your server
# Using gpt-oss:20b which supports tool calling
llm = ChatOllama(
    model="qwen3:30b",
    temperature=0,
    base_url="http://192.168.2.54:11434",
)

# Bind tools to the LLM
tools = [get_lat_long_for_city, get_weather_for_lat_long]
llm_with_tools = llm.bind_tools(tools)

# Test the tool calling
messages = [
    ("system", "Always call multiple tools in parallel when possible. Never call one at a time if you can batch them."),
    ("human", "give me the temp of dhaka, istanbul, sydney")
]

start_time = time.time()

try:
    response = llm_with_tools.invoke(messages)

    # Execute tool calls and collect results
    while response.tool_calls:
        messages.append(response)
        for call in response.tool_calls:
            # Debug: show what tool is being called
            print(f"[DEBUG] Calling: {call['name']} with args: {call['args']}")
            
            tool_fn = get_lat_long_for_city if call["name"] == "get_lat_long_for_city" else get_weather_for_lat_long
            result = tool_fn.invoke(call["args"])
            messages.append({"role": "tool", "content": str(result), "tool_call_id": call["id"]})
        response = llm_with_tools.invoke(messages)

    end_time = time.time()
    response_time = end_time - start_time

    print(response.content)
    print(f"\nResponse time: {response_time:.2f}s")

except Exception as e:
    end_time = time.time()
    response_time = end_time - start_time
    print(f"Error: {type(e).__name__}: {str(e)}")
    print(f"\nFailed after: {response_time:.2f}s")
    print("\nThis model may not properly support tool calling or the tool calling sequence.")
