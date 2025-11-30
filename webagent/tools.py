from langchain.tools import tool
import httpx


baseurl = "http://localhost:8888/search"

@tool
async def fetch_metadata(query: str) -> dict:
    """Search the web using SearXNG.

    Args:
        query (str): The search string

    Returns:
        dict: Search results with titles, URLs, and snippets
    """
    params = {
        "q": query,
        "format": "json",
        "engines": "google,duckduckgo,bing",
        "language": "en",
        "safesearch": 0,
        "categories": "general",
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(baseurl, params=params, headers=headers)
        if response.status_code != 200:
            return {"error": f"HTTP {response.status_code}: {response.text}"}
        data = response.json()

    results = []
    for r in data.get("results", [])[:10]:
        results.append({
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "snippet": r.get("content", "")
        })

    return {"query": query, "results": results}