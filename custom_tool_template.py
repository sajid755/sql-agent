"""
Custom Tool Template for LangChain
Works with both native tool calling and prompt-engineered approaches

Usage:
1. Define your custom tools as functions with @tool decorator
2. Choose your model type (native_tools=True/False)
3. Run the script
"""

import os
import requests
import time
import json
import re
from dotenv import load_dotenv
from langchain.tools import tool

# ============================================================================
# CONFIGURATION - MODIFY THIS SECTION
# ============================================================================

# Choose your LLM provider
PROVIDER = "ollama"  # Options: "ollama", "gemini"

# Ollama settings (if using Ollama)
OLLAMA_MODEL = "gpt-oss:20b"  # Change to your model
OLLAMA_BASE_URL = "http://192.168.2.54:11434"
NATIVE_TOOLS = True  # Set False for models that don't support native tool calling

# Gemini settings (if using Gemini)
GEMINI_MODEL = "gemini-2.5-flash"

# Your query
USER_QUERY = "give me the temp of dhaka, istanbul, sydney"

# ============================================================================
# DEFINE YOUR CUSTOM TOOLS HERE
# ============================================================================

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

# Add more custom tools here following the same pattern
# @tool
# def your_custom_tool(param1: str, param2: int) -> dict:
#     """Description of what your tool does"""
#     # Your implementation
#     return {"result": "some_value"}

# ============================================================================
# TOOL REGISTRY - Add your tools to this list
# ============================================================================

TOOLS = [get_lat_long_for_city, get_weather_for_lat_long]

# ============================================================================
# IMPLEMENTATION - No need to modify below this line
# ============================================================================

def create_tool_prompt(tools):
    """Generate system prompt for prompt-engineered tool calling"""
    tool_descriptions = []
    for i, tool in enumerate(tools, 1):
        # Get function signature and docstring
        func = tool.func if hasattr(tool, 'func') else tool
        name = func.__name__
        doc = func.__doc__ or "No description"
        tool_descriptions.append(f"{i}. {name} -> {doc.strip()}")
    
    tools_text = "\n".join(tool_descriptions)
    
    return f"""You are a helpful assistant with access to these tools:

{tools_text}

IMPORTANT: To use tools, respond ONLY with valid JSON. Do not include any other text.

For a single tool call:
{{"tool": "tool_name", "args": {{"arg1": "value1"}}}}

For multiple tool calls (use this when possible):
[
  {{"tool": "tool_name1", "args": {{"arg1": "value1"}}}},
  {{"tool": "tool_name2", "args": {{"arg1": "value1"}}}}
]

After you receive tool results, provide a natural language response to answer the user's question.
"""

def run_with_native_tools(llm, tools, query):
    """Run with native tool calling support"""
    llm_with_tools = llm.bind_tools(tools)
    
    messages = [
        ("system", "Always call multiple tools in parallel when possible."),
        ("human", query)
    ]
    
    start_time = time.time()
    
    try:
        response = llm_with_tools.invoke(messages)
        
        # Execute tool calls
        while response.tool_calls:
            messages.append(response)
            for call in response.tool_calls:
                # Find the matching tool
                tool_fn = next((t for t in tools if t.name == call["name"]), None)
                if tool_fn:
                    result = tool_fn.invoke(call["args"])
                    messages.append({"role": "tool", "content": str(result), "tool_call_id": call["id"]})
            response = llm_with_tools.invoke(messages)
        
        end_time = time.time()
        
        # Extract text from response
        if isinstance(response.content, list):
            text = response.content[0]['text'] if response.content else ""
        else:
            text = response.content
        
        print(text)
        print(f"\nResponse time: {end_time - start_time:.2f}s")
        
    except Exception as e:
        end_time = time.time()
        print(f"Error: {type(e).__name__}: {str(e)}")
        print(f"\nFailed after: {end_time - start_time:.2f}s")

def run_with_prompt_tools(llm, tools, query):
    """Run with prompt-engineered tool calling"""
    system_prompt = create_tool_prompt(tools)
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": query}
    ]
    
    start_time = time.time()
    
    try:
        max_iterations = 5
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            response = llm.invoke(messages)
            content = response.content.strip()
            
            # Try to extract JSON tool calls
            tool_calls = []
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
            
            # If no tool calls, this is the final response
            if not tool_calls:
                print(content)
                break
            
            # Execute tool calls
            tool_results = []
            for call in tool_calls:
                tool_name = call.get("tool")
                args = call.get("args", {})
                
                # Find matching tool
                tool_fn = next((t for t in tools if t.name == tool_name), None)
                if tool_fn:
                    result = tool_fn.invoke(args)
                else:
                    result = {"error": f"Unknown tool: {tool_name}"}
                
                tool_results.append({"tool": tool_name, "result": result})
            
            # Add to conversation
            messages.append({"role": "assistant", "content": content})
            messages.append({"role": "user", "content": f"Tool results: {json.dumps(tool_results)}"})
        
        end_time = time.time()
        print(f"\nResponse time: {end_time - start_time:.2f}s")
        
    except Exception as e:
        end_time = time.time()
        print(f"Error: {type(e).__name__}: {str(e)}")
        print(f"\nFailed after: {end_time - start_time:.2f}s")

def main():
    load_dotenv()
    
    # Initialize LLM based on provider
    if PROVIDER == "ollama":
        from langchain_ollama import ChatOllama
        llm = ChatOllama(
            model=OLLAMA_MODEL,
            temperature=0,
            base_url=OLLAMA_BASE_URL,
        )
        print(f"Using Ollama: {OLLAMA_MODEL}")
        
        if NATIVE_TOOLS:
            print("Mode: Native tool calling")
            run_with_native_tools(llm, TOOLS, USER_QUERY)
        else:
            print("Mode: Prompt-engineered tool calling")
            run_with_prompt_tools(llm, TOOLS, USER_QUERY)
            
    elif PROVIDER == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        llm = ChatGoogleGenerativeAI(
            model=GEMINI_MODEL,
            google_api_key=os.getenv("GOOGLE_API_KEY")
        )
        print(f"Using Gemini: {GEMINI_MODEL}")
        print("Mode: Native tool calling")
        run_with_native_tools(llm, TOOLS, USER_QUERY)
    
    else:
        print(f"Unknown provider: {PROVIDER}")

if __name__ == "__main__":
    main()
