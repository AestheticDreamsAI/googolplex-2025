# plugins/web_search.py
# SearXNG als Plugin (statt im Server)
# - Triggert auf "web", "search", "suche", "google", "bing", "duckduckgo"
# - Fallback-Score (0.05) damit es greift, wenn kein anderes Plugin matcht
# - Nutzt das UI-Design des Hosts (Glass-Styles)

from __future__ import annotations
import html, os, requests
from urllib.parse import urlencode

CONFIG = {
    "base_url": "http://192.168.1.114:8888",
    "triggers": ["web", "search", "suche", "google", "bing", "duckduckgo"],
    "max_results": 50,
    "safesearch": "1",
    "categories": "general",
}

def meta():
    return {
        "name": "Web Search",
        "badge": "SEARXNG",
        "color": "var(--glass-medium)",
    }

def can_handle(query: str):
    q = (query or "").strip().lower()
    if not q:
        return 0.0
    # starke Treffer: explizite Trigger am Anfang
    if any(q.startswith(t + " ") for t in CONFIG["triggers"]):
        return 0.9
    # schwächer: Trigger irgendwo
    if any(t in q for t in CONFIG["triggers"]):
        return 0.4
    # Fallback-Score, damit Websuche greift, wenn sonst nichts matched
    return 0.05

def _strip_trigger(q: str) -> str:
    q = (q or "").strip()
    parts = q.split(None, 1)
    if parts and parts[0].lower() in CONFIG["triggers"]:
        return parts[1] if len(parts) > 1 else ""
    return q

def _search_searxng(query: str):
    data = {
        "q": query,
        "format": "json",
        "safesearch": CONFIG["safesearch"],
        "categories": CONFIG["categories"],
    }
    UA_SAFARI = ("Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) "
                 "AppleWebKit/605.1.15 (KHTML, like Gecko) "
                 "Version/17.5 Mobile/15E148 Safari/604.1")

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "User-Agent": UA_SAFARI,
        "Origin": CONFIG["base_url"],
        "Referer": f"{CONFIG['base_url']}/",
    }

    s = requests.Session()
    s.headers.update(headers)
    # bevorzugt: POST
    r = s.post(f"{CONFIG['base_url']}/search", data=data, timeout=10, allow_redirects=False)
    if r.status_code == 403:
        r = s.get(f"{CONFIG['base_url']}/search", params=data, timeout=10, allow_redirects=False)
    r.raise_for_status()
    payload = r.json()

    results = payload.get("results", [])
    out = []
    for i, res in enumerate(results[: CONFIG["max_results"]], 1):
        title = res.get("title") or "No Title"
        url = res.get("url") or "#"
        content = res.get("content", res.get("pretty_url", "")) or ""
        if len(content) > 200:
            content = content[:200] + "..."
        engine = res.get("engine", "unknown")
        domain = ""
        try:
            domain = url.split("/")[2]
        except Exception:
            domain = url
        out.append({
            "pos": i,
            "title": title,
            "url": url,
            "snippet": content,
            "engine": engine,
            "domain": domain,
        })
    engines = sorted({r.get("engine","") for r in results if r.get("engine")})
    return out, engines, len(results)

def render(query: str):
    q = _strip_trigger(query)
    if not q:
        return {
            "title": "Web Search",
            "html": '<div class="plugin-item"><p>Gib einen Suchbegriff an, z. B. <code>web quantum dots</code>.</p></div>',
            "badges": ["SEARXNG"],
            "items": [],
        }

    try:
        results, engines, total = _search_searxng(q)
    except Exception as e:
        return {
            "title": f'Web Search – Error',
            "html": f'<div class="error-message"><h4>SearXNG Fehler</h4><p>{html.escape(str(e))}</p></div>',
            "badges": ["Error"],
            "items": [],
        }

    # Stats-Bar
    engines_html = ''.join([f'<span class="engine-tag">{html.escape(x)}</span>' for x in engines])
    stats_html = f'''
    <div class="stats-bar">
      <div class="stat-item"><span class="stat-value">{total}</span> results</div>
      <div class="stat-item">Search engines: <div class="engines-list">{engines_html}</div></div>
    </div>
    '''

    # Result-Liste (Glass)
    lst = []
    for r in results:
        lst.append(f'''
        <div class="search-result">
          <div class="result-header">
            <div class="result-position">{r["pos"]}</div>
            <div class="result-title">
              <h4><a href="{html.escape(r["url"])}" target="_blank">{html.escape(r["title"])}</a></h4>
              <div class="result-url">{html.escape(r["domain"])}</div>
            </div>
          </div>
          <div class="result-content">{html.escape(r["snippet"])}</div>
          <div class="result-meta"><span class="result-engine">{html.escape(r["engine"])}</span></div>
        </div>
        ''')

    results_html = stats_html + '<div class="search-results">' + ''.join(lst) + '</div>'

    return {
        "title": f'Web Search: "{q}"',
        "html": results_html,
        "badges": ["SEARXNG"],
        "items": [],
    }
