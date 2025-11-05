# src/aura_core/apprentices/web_searcher.py
from ddgs import DDGS
import traceback
from typing import List, Dict, Union

def run(payload) -> Union[List[Dict[str, str]], str]:
    """
    Performs a web search and returns a list of rich results
    (title, URL, snippet).
    """
    query = payload.get("query")
    if not query:
        return "Error: Missing 'query' in payload."

    num_results = int(payload.get("num_results", 3))
    region = payload.get("region", "wt-wt") # Default: World-wide
    # Timelimit: "d" (day), "w" (week), "m" (month), "y" (year)
    timelimit = payload.get("timelimit") 

    try:
        print(f"--- Web Searcher: Searching for top {num_results} result(s) for '{query}' ---")
        
        with DDGS() as ddgs:
            # ddgs.text returns a list of dictionaries
            results = list(ddgs.text(
                query,
                region=region,
                safesearch='moderate',
                timelimit=timelimit,
                max_results=num_results
            ))

        if not results:
            return f"Error: No search results found for '{query}'."

        # Return the list of rich result dictionaries
        # Format: [{"title": "...", "href": "...", "body": "..."}, ...]
        return results

    except Exception as e:
        traceback.print_exc()
        return f"Error: Failed during web search. Reason: {e}"