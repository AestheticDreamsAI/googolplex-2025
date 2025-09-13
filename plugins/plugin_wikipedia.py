# plugin_wikipedia.py
# Wikipedia summaries with CONFIG: default_lang, triggers, user_agent
import requests, html, urllib.parse

CONFIG = {
    "default_lang": "de",   # "de" or "en" default if detection is unsure
    "triggers": ["wiki","wikipedia","wer ist","was ist","who is","what is"],
    "user_agent": "GoogProx-Wiki/1.0 (contact: you@example.com)",
}

def meta():
    return {"name": "Wikipedia", "badge": "WIKI", "color": "rgba(33,150,243,0.28)"}

def can_handle(q: str):
    ql = (q or "").lower()
    return any(t in ql for t in CONFIG.get("triggers", []))

def _guess_lang(text: str):
    t = (text or "").lower()
    # naive detection: umlauts → de, english prompts → en
    if any(w in t for w in [" wer ist", " was ist", "de:", "de-wiki", "dewiki"]) or any(ch in t for ch in "äöüß"):
        return "de"
    if any(w in t for w in [" who is", " what is", "en:", "en-wiki", "enwiki"]):
        return "en"
    return CONFIG.get("default_lang", "en")

def _extract_term(query: str):
    q = (query or "").strip()
    ql = q.lower()
    for lead in ["wikipedia ", "wiki ", "wer ist ", "was ist ", "who is ", "what is "]:
        if ql.startswith(lead):
            return q[len(lead):].strip(" ?!")
    return q.strip(" ?!")

def render(query: str):
    term = _extract_term(query)
    lang = _guess_lang(query)
    base = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/"
    title = urllib.parse.quote(term.replace(" ", "_"))
    url = base + title
    try:
        r = requests.get(url, timeout=6, headers={"User-Agent": CONFIG.get("user_agent")})
        if r.status_code == 404:
            raise ValueError("Not found")
        r.raise_for_status()
        data = r.json()
        extract = data.get("extract") or ("Keine Zusammenfassung gefunden." if lang=="de" else "No summary available.")
        page_url = data.get("content_urls", {}).get("desktop", {}).get("page", f"https://{lang}.wikipedia.org/wiki/{title}")
        thumb = data.get("thumbnail", {}).get("source")
        h = f'<p>{html.escape(extract)}</p>'
        if thumb:
            h = f'<div style="display:flex;gap:12px;align-items:flex-start"><img src="{html.escape(thumb)}" style="max-width:120px;border-radius:8px"/>{h}</div>'
        h += f'<p><a href="{html.escape(page_url)}" target="_blank">↗ Wikipedia öffnen</a></p>'
        return {"title": f"Wikipedia: {html.escape(term)}", "html": h, "badges": [lang.upper()], "items": []}
    except Exception as e:
        return {"title": f"Wikipedia: {html.escape(term)}", "html": f"<p>❌ Fehler: {html.escape(str(e))}</p>", "badges": ["Error"], "items": []}
