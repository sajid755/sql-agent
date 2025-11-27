import requests
import time
import json
import re
from langchain_ollama import ChatOllama

def get_lat_long_for_city(city: str) -> dict:
    """Get latitude and longitude for a city"""
    url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}"
    r = requests.get(url).json()

    if "results" not in r or len(r["results"]) == 0:
        return {"error": "City not found"}

    x = r["results"][0]
    return {"city": x["name"], "lat": x["latitude"], "lon": x["longitude"]}

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

# Initialize Ollama LLM (works with models that don't support native tool calling)
llm = ChatOllama(
    model="gpt-oss:120b",  # Using 120b with prompt-engineered tools
    temperature=0,
    base_url="http://192.168.2.54:11434",
)

# Prompt engineering approach - simulate tool calling
system_prompt = """You are a helpful assistant with access to these tools:

1. get_lat_long_for_city(city: str) -> Returns {"city": str, "lat": float, "lon": float}
2. get_weather_for_lat_long(lat: float, lon: float) -> Returns {"temperature": float}

IMPORTANT: To use tools, respond ONLY with valid JSON. Do not include any other text.

For a single tool call:
{"tool": "get_lat_long_for_city", "args": {"city": "Dhaka"}}

For multiple tool calls (use this when possible):
[
  {"tool": "get_lat_long_for_city", "args": {"city": "Dhaka"}},
  {"tool": "get_lat_long_for_city", "args": {"city": "Istanbul"}},
  {"tool": "get_lat_long_for_city", "args": {"city": "Sydney"}}
]

After you receive tool results, provide a natural language response to answer the user's question.

Workflow:
1. First call get_lat_long_for_city for each city
2. Then call get_weather_for_lat_long with the coordinates
3. Finally, provide a natural language summary
"""

user_query = "give me the temp of dhaka, istanbul, sydney"

messages = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": user_query}
]

start_time = time.time()

try:
    max_iterations = 5
    iteration = 0
    
    while iteration < max_iterations:
        iteration += 1
        
        # Get LLM response
        response = llm.invoke(messages)
        content = response.content.strip()
        
        # Try to extract JSON tool calls
        tool_calls = []
        
        # Look for JSON array or single JSON object
        json_match = re.search(r'(\[.*?\]|\{.*?\})', content, re.DOTALL)
        if json_match:
            try:
                parsed = json.loads(json_match.group(1))
                if isinstance(parsed, list):
                    tool_calls = parsed
                elif isinstance(parsed, dict) and "tool" in parsed:
                    tool_calls = [parsed]
            except json.JSONDecodeError:
                pass
        
        # If no tool calls found, this is the final response
        if not tool_calls:
            print(content)
            break
        
        # Execute tool calls
        tool_results = []
        for call in tool_calls:
            tool_name = call.get("tool")
            args = call.get("args", {})
            
            if tool_name == "get_lat_long_for_city":
                result = get_lat_long_for_city(**args)
            elif tool_name == "get_weather_for_lat_long":
                result = get_weather_for_lat_long(**args)
            else:
                result = {"error": f"Unknown tool: {tool_name}"}
            
            tool_results.append({"tool": tool_name, "result": result})
        
        # Add tool results to conversation
        messages.append({"role": "assistant", "content": content})
        messages.append({"role": "user", "content": f"Tool results: {json.dumps(tool_results)}"})
    
    end_time = time.time()
    response_time = end_time - start_time
    print(f"\nResponse time: {response_time:.2f}s")

except Exception as e:
    end_time = time.time()
    response_time = end_time - start_time
    print(f"Error: {type(e).__name__}: {str(e)}")
    print(f"\nFailed after: {response_time:.2f}s")
