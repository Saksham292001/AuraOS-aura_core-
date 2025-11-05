# src/aura_core/apprentices/web_researcher.py
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import trafilatura
import traceback
from typing import List, Dict, Union

def _fetch_static_html(url: str) -> str:
    """Fetches HTML using requests (fast, no JS)."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
    }
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    return response.text

def _fetch_dynamic_html(url: str) -> str:
    """Fetches HTML using a headless browser (slower, runs JS)."""
    print(f"--- Web Researcher: Rendering JavaScript for {url} ---")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(url, wait_until='networkidle', timeout=15000)
            content = page.content()
        except Exception as e:
            print(f"--- Web Researcher: Playwright failed, falling back to initial content. Reason: {e} ---")
            content = page.content() # Get content even if network doesn't idle
        finally:
            browser.close()
    return content

def _extract_article_text(html: str) -> str:
    """Uses trafilatura to extract main article text, removing boilerplate."""
    # include_links=True can be useful
    text = trafilatura.extract(html, include_comments=False, include_tables=False)
    if not text:
        print("--- Web Researcher Warning: trafilatura failed to find article. Falling back to full text. ---")
        return _extract_full_text(html)
    return text

def _extract_full_text(html: str) -> str:
    """Uses BeautifulSoup to get all visible text (original method)."""
    soup = BeautifulSoup(html, 'html.parser')
    for script_or_style in soup(["script", "style", "nav", "footer", "aside"]):
        script_or_style.decompose()
    return ' '.join(t.strip() for t in soup.stripped_strings)

def _extract_with_selector(html: str, selector: str, extract_mode: str) -> Union[str, List[str]]:
    """Uses BeautifulSoup and a CSS selector to get specific content."""
    soup = BeautifulSoup(html, 'html.parser')
    elements = soup.select(selector)
    if not elements:
        return f"Warning: No elements found matching selector '{selector}'."
    
    if extract_mode == "links":
        return [el.get('href', '') for el in elements if el.get('href')]
    elif extract_mode == "images":
        return [el.get('src', '') for el in elements if el.get('src')]
    else: # Default to "text"
        return [" ".join(el.stripped_strings) for el in elements]

def run(payload):
    """Fetches and parses text content from a URL with advanced options."""
    url = payload.get("url")
    if not url:
        return "Error: Missing 'url' in payload."

    render_js = payload.get("render_js", False)
    # Mode: "article" (default), "full_text"
    extract_mode = payload.get("mode", "article").lower()
    # Selector: "table.data", "#main_content p", etc.
    selector = payload.get("selector")
    
    try:
        # Step 1: Fetch HTML
        if render_js:
            html = _fetch_dynamic_html(url)
        else:
            html = _fetch_static_html(url)
            
        if not html:
            return "Error: Failed to fetch any HTML content."

        # Step 2: Extract Content
        if selector:
            # Specific element scraping (e.g., get links, images, or text from elements)
            print(f"--- Web Researcher: Extracting with selector '{selector}' ---")
            return _extract_with_selector(html, selector, extract_mode)
            
        elif extract_mode == "article":
            # Intelligent article extraction
            print("--- Web Researcher: Extracting main article content ---")
            return _extract_article_text(html)
            
        elif extract_mode == "full_text":
            # Simple "get all text"
            print("--- Web Researcher: Extracting all text (full_text mode) ---")
            return _extract_full_text(html)
        
        else:
            return f"Error: Unknown extract mode '{extract_mode}'. Use 'article', 'full_text', or 'selector'."

    except Exception as e:
        traceback.print_exc()
        return f"Error: Failed to process URL {url}. Reason: {e}"