# GoogleProxy.py – PURE GLASSMORPHISM DESIGN + Plugin-System + SearXNG Integration
# Run:  pip install fastapi uvicorn requests
# Start: python3 GoogleProxy.py

from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
from typing import Optional
from urllib.parse import urlencode
from datetime import datetime
import html, os, importlib.util, requests
import os
import time

# Global state für file tracking
PLUGIN_MTIMES = {}
LAST_CHECK = 0
CHECK_INTERVAL = 2.0  # Sekunden zwischen checks

APP_TITLE = "GoogolPlex Siri"
APP_VERSION = "3.2.0"
PLUGIN_DIR = os.path.join(os.path.dirname(__file__), "plugins")

SEARXNG_BASE_URL = "" #Or Local Instanz

app = FastAPI(title=APP_TITLE, version=APP_VERSION)

def load_plugins():
    mods = []
    if not os.path.isdir(PLUGIN_DIR): 
        return mods
    print("Loading Plugins...");
    for fname in os.listdir(PLUGIN_DIR):
        if not fname.endswith(".py") or fname.startswith("_"):
            continue
        path = os.path.join(PLUGIN_DIR, fname)
        name = f"plugin_{os.path.splitext(fname)[0]}"
        print(f"[PLUGIN] {name}")
        spec = importlib.util.spec_from_file_location(name, path)
        if not spec or not spec.loader: 
            continue
        mod = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(mod)  # type: ignore
            if all(hasattr(mod, fn) for fn in ("meta","can_handle","render")):
                mods.append(mod)
        except Exception as e:
            print(f"[PLUGIN] failed to load {fname}: {e}")
    return mods

PLUGINS = load_plugins()

def check_plugin_changes():
    """Prüft ob sich Plugin-Dateien geändert haben"""
    global PLUGIN_MTIMES, LAST_CHECK
    
    now = time.time()
    if now - LAST_CHECK < CHECK_INTERVAL:
        return False
    
    LAST_CHECK = now
    print(f"[DEBUG] Checking for plugin changes...") # Debug-Zeile hinzufügen
    
    if not os.path.isdir(PLUGIN_DIR):
        print(f"[DEBUG] Plugin dir not found: {PLUGIN_DIR}") # Debug
        return False
    
    current_mtimes = {}
    for fname in os.listdir(PLUGIN_DIR):
        if fname.endswith(".py") and not fname.startswith("_"):
            path = os.path.join(PLUGIN_DIR, fname)
            try:
                mtime = os.path.getmtime(path)
                current_mtimes[fname] = mtime
                print(f"[DEBUG] Found plugin: {fname} (mtime: {mtime})") # Debug
            except OSError as e:
                print(f"[DEBUG] Error reading {fname}: {e}") # Debug
                continue
    
    # First run - save current state
    if not PLUGIN_MTIMES:
        print(f"[DEBUG] First run, saving {len(current_mtimes)} plugin states") # Debug
        PLUGIN_MTIMES = current_mtimes
        return False
    
    # Check for changes
    if current_mtimes != PLUGIN_MTIMES:
        print(f"[DEBUG] Changes detected: {current_mtimes} vs {PLUGIN_MTIMES}") # Debug
        PLUGIN_MTIMES = current_mtimes
        return True
    
    print(f"[DEBUG] No changes detected") # Debug
    return False

def reload_plugins_if_needed():
    """Lädt Plugins neu wenn sich was geändert hat"""
    global PLUGINS
    
    if check_plugin_changes():
        print(f"[RELOAD] Plugin changes detected - reloading...")
        try:
            PLUGINS = load_plugins()
            print(f"[RELOAD] Successfully reloaded {len(PLUGINS)} plugins")
        except Exception as e:
            print(f"[RELOAD] Error reloading plugins: {e}")

def pick_plugin(query: str):
    reload_plugins_if_needed()  # <-- Diese Zeile hinzufügen
    
    q = (query or "").strip().lower()
    best = (0.0, None)
    for m in PLUGINS:
        try:
            s = m.can_handle(q)
            if isinstance(s, bool): s = 1.0 if s else 0.0
            s = float(s or 0.0)
        except Exception:
            s = 0.0
        if s > best[0]:
            best = (s, m)
    return best[1]

def search_searxng(query: str):
    """SearXNG via POST /search (q=...) – with browser headers + fallback."""
    data = {
        "q": query,
        "format": "json",
        "safesearch": "1",
        "categories": "general",
    }

    UA_SAFARI = ("Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) "
                 "AppleWebKit/605.1.15 (KHTML, like Gecko) "
                 "Version/17.5 Mobile/15E148 Safari/604.1")
    base = SEARXNG_BASE_URL.rstrip("/")
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "User-Agent": UA_SAFARI,
        "Origin": f"{base}",
        "Referer": f"{base}/",
    }

    try:
        s = requests.Session()
        s.headers.update(headers)

        # 1) POST (recommended by your instance)
        r = s.post(f"{base}/search", data=data, timeout=10, allow_redirects=False)

        # 403 → Try fallback (some proxies only accept GET)
        if r.status_code == 403:
            r = s.get(f"{base}/search", params=data, timeout=10, allow_redirects=False)

        r.raise_for_status()
        payload = r.json()

        results = payload.get("results", [])
        formatted = []
        for i, res in enumerate(results[:10], 1):
            title = res.get("title", "No Title")
            url = res.get("url", "#")
            content = res.get("content", res.get("pretty_url", "")) or ""
            if len(content) > 200:
                content = content[:200] + "..."
            engine = res.get("engine", "unknown")
            domain = url.split("/")[2] if url and len(url.split("/")) > 2 else url
            formatted.append({
                "position": i,
                "title": title,
                "url": url,
                "content": content,
                "engine": engine,
                "domain": domain or "",
            })

        return {
            "success": True,
            "results": formatted,
            "total_results": len(results),
            "query": query,
            "engines": sorted({r.get("engine", "") for r in results if r.get("engine")}),
        }
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": f"Connection error to SearXNG: {e}", "results": [], "total_results": 0}
    except Exception as e:
        return {"success": False, "error": f"Unknown error: {e}", "results": [], "total_results": 0}


HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <meta name="color-scheme" content="dark">
  <title>GoogolPlex | Better Than Siri</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }
    
    :root {
      /* Pure Glass Morphism - Only White/Transparent */
      --glass-light: rgba(255, 255, 255, 0.06);
      --glass-medium: rgba(255, 255, 255, 0.10);
      --glass-strong: rgba(255, 255, 255, 0.15);
      --glass-stronger: rgba(255, 255, 255, 0.20);
      
      --glass-border-light: rgba(255, 255, 255, 0.12);
      --glass-border-medium: rgba(255, 255, 255, 0.18);
      --glass-border-strong: rgba(255, 255, 255, 0.25);
      
      --glass-hover: rgba(255, 255, 255, 0.12);
      --glass-active: rgba(255, 255, 255, 0.18);
      
      /* Text Colors */
      --text-primary: rgba(255, 255, 255, 0.95);
      --text-secondary: rgba(255, 255, 255, 0.80);
      --text-tertiary: rgba(255, 255, 255, 0.65);
      --text-muted: rgba(255, 255, 255, 0.45);
      --text-very-muted: rgba(255, 255, 255, 0.30);
    }
    
    body {
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
      background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%);
      background-attachment: fixed;
      color: var(--text-primary);
      min-height: 100vh;
      padding: env(safe-area-inset-top, 20px) env(safe-area-inset-right, 20px) env(safe-area-inset-bottom, 20px) env(safe-area-inset-left, 20px);
      line-height: 1.5;
      overflow-x: hidden;
    }
    
    body::before {
      content: '';
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background-image: 
        radial-gradient(circle at 20% 20%, rgba(255, 255, 255, 0.05) 0%, transparent 50%),
        radial-gradient(circle at 80% 80%, rgba(255, 255, 255, 0.03) 0%, transparent 50%),
        radial-gradient(circle at 40% 60%, rgba(255, 255, 255, 0.02) 0%, transparent 50%);
      pointer-events: none;
      z-index: -1;
    }
    
    .container {
      max-width: 430px;
      margin: 0 auto;
      padding-top: 40px;
      position: relative;
      z-index: 1;
    }
    
    /* Pure White Header */
    .header {
      text-align: center;
      margin-bottom: 40px;
    }
    
    .header h1 {
      color: white;
      font-size: 36px;
      font-weight: 800;
      letter-spacing: -1px;
      margin-bottom: 8px;
    }
    
    .header h1::after {
      content: '';
      position: absolute;
      bottom: -6px;
      left: 50%;
      transform: translateX(-50%);
      width: 60px;
      height: 2px;
      background: rgba(255, 255, 255, 0.4);
      border-radius: 2px;
    }
    
    .header p {
      font-size: 16px;
      color: var(--text-secondary);
      font-weight: 500;
    }
    
    /* Pure Glass Search Bar */
    .search-container {
      margin-bottom: 30px;
    }
    
    .search-bar {
      display: flex;
      background: var(--glass-medium);
      backdrop-filter: blur(24px) saturate(180%);
      -webkit-backdrop-filter: blur(24px) saturate(180%);
      border-radius: 28px;
      padding: 6px;
      align-items: center;
      border: 1px solid var(--glass-border-light);
      box-shadow: 
        0 8px 32px rgba(0, 0, 0, 0.4),
        0 2px 8px rgba(0, 0, 0, 0.2),
        inset 0 1px 0 rgba(255, 255, 255, 0.1);
      transition: all 0.3s ease;
    }
    
    .search-bar:hover {
      border-color: var(--glass-border-medium);
      box-shadow: 
        0 12px 40px rgba(0, 0, 0, 0.5),
        0 4px 12px rgba(0, 0, 0, 0.3),
        inset 0 1px 0 rgba(255, 255, 255, 0.15);
    }
    
    .search-bar:focus-within {
      border-color: var(--glass-border-strong);
      box-shadow: 
        0 12px 40px rgba(0, 0, 0, 0.5),
        0 4px 12px rgba(0, 0, 0, 0.3),
        inset 0 1px 0 rgba(255, 255, 255, 0.2);
    }
    
    .search-bar input {
      flex: 1;
      background: transparent;
      border: none;
      outline: none;
      padding: 16px 24px;
      font-size: 17px;
      color: var(--text-primary);
      font-weight: 500;
      font-family: inherit;
    }
    
    .search-bar input::placeholder {
      color: var(--text-tertiary);
      font-weight: 400;
    }
    
    /* Pure Glass Search Button */
    .search-btn {
      background: var(--glass-strong);
      border: 1px solid var(--glass-border-medium);
      border-radius: 50%;
      width: 48px;
      height: 48px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      font-size: 18px;
      cursor: pointer;
      transition: all 0.3s ease;
      backdrop-filter: blur(12px);
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
    }
    
    .search-btn:hover {
      transform: scale(1.05);
      background: var(--glass-stronger);
      border-color: var(--glass-border-strong);
      box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
    }
    
    .search-btn:active {
      transform: scale(0.98);
    }
    
    /* Pure Glass Result Panel */
    .result-panel {
      background: var(--glass-medium);
      backdrop-filter: blur(24px) saturate(180%);
      -webkit-backdrop-filter: blur(24px) saturate(180%);
      border-radius: 24px;
      border: 1px solid var(--glass-border-light);
      overflow: hidden;
      margin-bottom: 30px;
      box-shadow: 
        0 20px 60px rgba(0, 0, 0, 0.4),
        0 8px 24px rgba(0, 0, 0, 0.2),
        inset 0 1px 0 rgba(255, 255, 255, 0.1);
      transition: all 0.3s ease;
    }
    
    .result-panel:hover {
      transform: translateY(-2px);
      box-shadow: 
        0 24px 80px rgba(0, 0, 0, 0.5),
        0 12px 32px rgba(0, 0, 0, 0.3),
        inset 0 1px 0 rgba(255, 255, 255, 0.15);
    }
    
    .panel-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 24px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
      background: var(--glass-light);
    }
    
    .panel-header h2 {
      font-size: 20px;
      font-weight: 600;
      color: var(--text-primary);
    }
    
    .badge {
      padding: 8px 16px;
      border-radius: 20px;
      font-size: 11px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 1px;
      background: var(--glass-strong);
      border: 1px solid var(--glass-border-medium);
      backdrop-filter: blur(8px);
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
      color: var(--text-primary);
    }
    
    .panel-content {
      padding: 24px;
    }
    
    .query-display {
      background: var(--glass-strong);
      border: 1px solid var(--glass-border-medium);
      border-radius: 16px;
      padding: 16px 20px;
      font-size: 14px;
      color: var(--text-secondary);
      margin-bottom: 24px;
      font-style: italic;
      font-weight: 500;
      backdrop-filter: blur(8px);
    }
    
    .result-text {
      font-size: 16px;
      color: var(--text-primary);
      margin-bottom: 24px;
      line-height: 1.6;
    }
    
    .result-text h3 {
      font-size: 18px;
      font-weight: 600;
      margin-bottom: 16px;
      color: var(--text-primary);
    }
    
    /* Search Results */
    .search-results {
      margin-top: 24px;
    }
    
    .stats-bar {
      background: var(--glass-light);
      border-radius: 16px;
      padding: 20px;
      margin-bottom: 24px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 16px;
      border: 1px solid var(--glass-border-light);
      backdrop-filter: blur(12px);
    }
    
    .stat-item {
      font-size: 14px;
      color: var(--text-secondary);
    }
    
    .stat-value {
      font-weight: 600;
      color: var(--text-primary);
    }
    
    .engines-list {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }
    
    .engine-tag {
      background: var(--glass-medium);
      color: var(--text-primary);
      padding: 6px 12px;
      border-radius: 12px;
      font-size: 11px;
      font-weight: 500;
      border: 1px solid var(--glass-border-light);
      backdrop-filter: blur(6px);
    }
    
    .search-result {
      background: var(--glass-light);
      border-radius: 20px;
      padding: 24px;
      margin-bottom: 16px;
      border: 1px solid var(--glass-border-light);
      transition: all 0.3s ease;
      backdrop-filter: blur(12px);
    }
    
    .search-result:hover {
      background: var(--glass-hover);
      transform: translateY(-2px);
      box-shadow: 0 12px 32px rgba(0, 0, 0, 0.3);
      border-color: var(--glass-border-medium);
    }
    
    .result-header {
      display: flex;
      align-items: flex-start;
      margin-bottom: 16px;
    }
    
    .result-position {
      background: var(--glass-strong);
      color: var(--text-primary);
      border-radius: 50%;
      width: 32px;
      height: 32px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 13px;
      font-weight: 600;
      margin-right: 16px;
      flex-shrink: 0;
      border: 1px solid var(--glass-border-light);
      backdrop-filter: blur(8px);
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    }
    
    .result-title {
      flex: 1;
    }
    
    .result-title h4 {
      font-size: 18px;
      font-weight: 600;
      color: var(--text-primary);
      margin-bottom: 6px;
      line-height: 1.4;
    }
    
    .result-title a {
      color: var(--text-primary);
      text-decoration: none;
      transition: color 0.2s ease;
    }
    
    .result-title a:hover {
      color: var(--text-secondary);
      text-decoration: underline;
    }
    
    .result-url {
      font-size: 13px;
      color: var(--text-tertiary);
      margin-bottom: 12px;
      font-family: 'SF Mono', Monaco, monospace;
      word-break: break-all;
    }
    
    .result-content {
      font-size: 14px;
      color: var(--text-secondary);
      line-height: 1.6;
      margin-bottom: 12px;
    }
    
    .result-meta {
      display: flex;
      gap: 12px;
      font-size: 11px;
      color: var(--text-muted);
    }
    
    .result-engine {
      background: var(--glass-light);
      padding: 4px 10px;
      border-radius: 12px;
      backdrop-filter: blur(8px);
    }
    
    /* Plugin Badges - Pure Glass */
    .plugin-badges {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      margin: 20px 0;
    }
    
    .plugin-badge {
      background: var(--glass-medium);
      border: 1px solid var(--glass-border-light);
      padding: 8px 16px;
      border-radius: 20px;
      font-size: 12px;
      font-weight: 500;
      backdrop-filter: blur(12px);
      transition: all 0.2s ease;
      color: var(--text-primary);
    }
    
    .plugin-badge:hover {
      background: var(--glass-hover);
      transform: translateY(-1px);
    }
    
    /* Plugin Items */
    .plugin-items {
      margin-top: 24px;
    }
    
    .plugin-item {
      background: var(--glass-light);
      border: 1px solid var(--glass-border-light);
      padding: 20px;
      border-radius: 16px;
      margin-bottom: 16px;
      backdrop-filter: blur(12px);
      transition: all 0.2s ease;
    }
    
    .plugin-item:hover {
      background: var(--glass-hover);
      transform: translateY(-1px);
    }
    
    .plugin-item h4 {
      font-size: 16px;
      font-weight: 600;
      color: var(--text-primary);
      margin-bottom: 8px;
    }
    
    .plugin-item p {
      font-size: 14px;
      color: var(--text-secondary);
      line-height: 1.5;
    }
    
    /* Error Messages - Pure Glass */
    .error-message {
      background: var(--glass-medium);
      border: 1px solid var(--glass-border-medium);
      border-radius: 16px;
      padding: 24px;
      margin: 24px 0;
      color: var(--text-secondary);
      backdrop-filter: blur(12px);
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
    }
    
    .error-message h4 {
      color: var(--text-primary);
      margin-bottom: 12px;
      font-size: 16px;
      font-weight: 600;
    }
    
    /* Pure Glass Action Buttons */
    .action-buttons {
      display: flex;
      flex-direction: column;
      gap: 16px;
      margin-bottom: 32px;
    }
    
    .btn {
      background: var(--glass-strong);
      backdrop-filter: blur(24px) saturate(180%);
      -webkit-backdrop-filter: blur(24px) saturate(180%);
      border: 1px solid var(--glass-border-medium);
      border-radius: 20px;
      padding: 18px 24px;
      color: var(--text-primary);
      font-size: 16px;
      font-weight: 500;
      text-align: center;
      text-decoration: none;
      transition: all 0.3s ease;
      cursor: pointer;
      font-family: inherit;
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
    }
    
    .btn:hover {
      background: var(--glass-active);
      transform: translateY(-2px);
      box-shadow: 0 12px 32px rgba(0, 0, 0, 0.3);
      border-color: var(--glass-border-strong);
    }
    
    .btn:active {
      transform: translateY(0);
    }
    
    .btn-secondary {
      background: var(--glass-medium);
      border-color: var(--glass-border-light);
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25);
    }
    
    .btn-secondary:hover {
      background: var(--glass-active);
      border-color: var(--glass-border-strong);
      box-shadow: 0 12px 32px rgba(0, 0, 0, 0.35);
    }
    
    /* Bottom Text */
    .bottom-text {
      text-align: center;
      color: var(--text-tertiary);
      font-size: 14px;
      margin-bottom: 32px;
      line-height: 1.6;
      padding: 24px;
      background: var(--glass-light);
      border-radius: 16px;
      border: 1px solid var(--glass-border-light);
      backdrop-filter: blur(12px);
    }
    
    /* Footer */
    .footer {
      text-align: center;
      color: var(--text-muted);
      font-size: 12px;
      padding: 24px;
      border-top: 1px solid rgba(255, 255, 255, 0.08);
      margin-top: 48px;
    }
    
    .footer a {
      color: var(--text-secondary);
      text-decoration: none;
      font-weight: 500;
      transition: color 0.2s ease;
    }
    
    .footer a:hover {
      color: var(--text-primary);
    }
    
    /* Responsive */
    @media (max-width: 480px) {
      body {
        padding: 16px;
      }
      
      .container {
        padding-top: 24px;
      }
      
      .header h1 {
        font-size: 32px;
      }
      
      .search-bar input {
        font-size: 16px;
        padding: 14px 20px;
      }
      
      .stats-bar {
        flex-direction: column;
        align-items: flex-start;
      }
      
      .panel-content, .panel-header {
        padding: 20px;
      }
    }
    
    /* Accessibility & Performance */
    @media (prefers-reduced-motion: reduce) {
      * {
        animation-duration: 0.01ms !important;
        transition-duration: 0.01ms !important;
      }
    }
    
    @media (prefers-contrast: high) {
      :root {
        --glass-light: rgba(255, 255, 255, 0.15);
        --glass-medium: rgba(255, 255, 255, 0.20);
        --glass-strong: rgba(255, 255, 255, 0.25);
        --glass-border-light: rgba(255, 255, 255, 0.25);
        --glass-border-medium: rgba(255, 255, 255, 0.35);
        --glass-border-strong: rgba(255, 255, 255, 0.45);
      }
    }
    
    /* Hide/Show States */
    [hidden] {
      display: none !important;
    }
    
    /* Smooth Animations */
    @keyframes fadeInUp {
      from {
        opacity: 0;
        transform: translateY(20px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }
    
    .result-panel, .plugin-item, .search-result {
      animation: fadeInUp 0.6s ease-out;
    }
  </style>
</head>
<body>
  <div class="container">
    <!-- Header -->
    <div class="header">
      <h1>GoogolPlex</h1>
      <p>Better Than Siri - Unlimited Possibilities</p>
    </div>
    
    <!-- Search -->
    <div class="search-container">
      <form class="search-bar" action="/search" method="get">
        <input name="q" value="[[QUERY_ESC]]" placeholder="[[SEARCH_PLACEHOLDER]]" autofocus>
        <button type="submit" class="search-btn">🔍</button>
      </form>
    </div>

    <!-- Result Panel -->
    <div class="result-panel" [[RESULT_HIDDEN_ATTR]]>
      <div class="panel-header">
        <h2>[[TITLE_ESC]]</h2>
        <span class="badge" style="background: [[BADGE_COLOR]];">[[BADGE_TEXT_ESC]]</span>
      </div>
      <div class="panel-content">
        <div class="query-display">[[QUERY_LEDE]]</div>
        <div class="result-text">
          <h3>Search Result:</h3>
          [[CONTENT_HTML]]
        </div>
        
        <!-- Search Results -->
        [[SEARCH_RESULTS_HTML]]
        
        <!-- Plugin System Integration -->
        <div style="margin-top: 20px;">[[EXTRA_BADGES]]</div>
        <div>[[EXTRA_ITEMS]]</div>
      </div>
    </div>
  </div>
  
    
    <!-- Action Buttons -->
    <div class="action-buttons">
      <a href="/" class="btn">🆕 New Search</a>
    </div>
    
  
  <!-- Footer -->
  <div class="footer">
    © [[YEAR]] • GoogolPlex Proxy • Runs locally•  
  </div>

<script>
/* ==== Global TTS for iOS (Priming + Voices + Overlay + Queue) ==== */
(function () {
  if (!("speechSynthesis" in window)) {
    window.TTS = { supported:false, speak:()=>Promise.reject("No TTS"), queue:()=>{}, cancel:()=>{} };
    return;
  }

  const S = window.speechSynthesis;
  const isiOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
  const state = {
    voices: [],
    ready: false,
    primed: !isiOS,
    pending: [],
    defaults: { rate: 1.0, pitch: 1.0, langPrefs: ["en-US","en-GB","de-DE","de-CH","de-AT","de"] },
    overlay: null,
  };

  function refreshVoices() {
    const v = S.getVoices() || [];
    if (v.length) { state.voices = v; state.ready = true; }
  }
  refreshVoices();
  if (!state.ready) S.onvoiceschanged = refreshVoices;

  function ensureOverlay() {
    if (state.overlay || !isiOS || state.primed) return;
    const o = document.createElement("div");
    o.id = "ttsUnlockOverlay";
    o.style.cssText = "position:fixed;inset:0;display:flex;align-items:center;justify-content:center;"
      + "background:rgba(0,0,0,.6);backdrop-filter:blur(8px);z-index:99999;opacity:0;";
    o.innerHTML = `
      <div style="background:var(--glass-strong);backdrop-filter:blur(24px);color:white;padding:24px 28px;border-radius:20px;
                  box-shadow:0 20px 60px rgba(0,0,0,.4);text-align:center;max-width:320px;border:1px solid var(--glass-border-medium);">
        <div style="font-size:20px;font-weight:700;margin-bottom:8px;">Enable Speech Output</div>
        <div style="font-size:14px;opacity:.8;margin-bottom:16px;">Tap below to unlock iPhone voice output.</div>
        <button id="ttsUnlockBtn" style="background:var(--glass-strong);color:white;padding:12px 20px;border:1px solid var(--glass-border-medium);border-radius:16px;font-weight:600;cursor:pointer;backdrop-filter:blur(12px);">
          ▶️ Activate Speech
        </button>
      </div>`;
    document.body.appendChild(o);
    state.overlay = o;

    const btn = o.querySelector("#ttsUnlockBtn");
    const activate = async () => {
      try {
        if (window.audioManager && typeof window.audioManager.stop === "function") {
          try { window.audioManager.stop(); } catch (_) {}
        }
        const u = new SpeechSynthesisUtterance(".");
        u.volume = 0.001; u.rate = 2.0;
        u.onstart = () => { try { S.cancel(); } catch(_){} };
        S.speak(u);

        for (let i=0;i<8 && !state.ready;i++) {
          await new Promise(r => setTimeout(r, 125));
          refreshVoices();
        }
        state.primed = true;
      } finally {
        if (state.overlay) {
          state.overlay.remove();
          state.overlay = null;
        }
        drainQueue();
      }
    };
    btn.addEventListener("click", activate, { once: true });
    const passThrough = async () => { await activate(); document.removeEventListener("pointerdown", passThrough); };
    document.addEventListener("pointerdown", passThrough, { once: true });
  }

  function pickVoice(opts = {}) {
    const wanted = opts.langPrefs || state.defaults.langPrefs;
    for (const pref of wanted) {
      const m = state.voices.find(x => x.lang === pref);
      if (m) return m;
    }
    const def = state.voices.find(x => x.default);
    return def || state.voices[0] || null;
  }

  async function _speakNow(text, options = {}) {
    const t = (text || "").toString().trim();
    if (!t) return;
    if (!state.ready) {
      for (let i=0;i<8 && !state.ready;i++) {
        await new Promise(r => setTimeout(r, 125));
        refreshVoices();
      }
    }
    S.cancel();
    const u = new SpeechSynthesisUtterance(t);
    let v = null;
    if (options.voiceName) v = state.voices.find(x => x.name === options.voiceName) || null;
    if (!v) v = pickVoice(options);
    if (v) u.voice = v;
    u.lang = (v && v.lang) || (options.langPrefs && options.langPrefs[0]) || (navigator.language || "en-US");
    u.rate  = Number(options.rate  ?? state.defaults.rate);
    u.pitch = Number(options.pitch ?? state.defaults.pitch);
    return new Promise((resolve, reject) => {
      u.onend   = () => resolve();
      u.onerror = e  => reject(e.error || "tts-error");
      try { S.speak(u); } catch (e) { reject(e); }
    });
  }

  async function speak(text, options = {}) {
    if (!state.primed && isiOS) {
      state.pending.push({ text, options });
      ensureOverlay();
      return Promise.resolve();
    }
    return _speakNow(text, options);
  }

  function queue(text, options = {}) {
    state.pending.push({ text, options });
    if (state.primed || !isiOS) drainQueue();
    else ensureOverlay();
  }

  async function drainQueue() {
    const items = state.pending.slice();
    state.pending.length = 0;
    for (const it of items) {
      try { await _speakNow(it.text, it.options); } catch (_) {}
    }
  }

  function cancel(){ S.cancel(); }

  window.TTS = {
    supported: true,
    speak,
    queue,
    cancel,
    getVoices: () => state.voices.slice(),
    setDefaults(cfg = {}) { Object.assign(state.defaults, cfg); }
  };
})();
</script>

</body>
</html>
"""

def render_page(query: str, searxng_results=None):
    # pick plugin
    mod = pick_plugin(query)
    if mod:
        meta = mod.meta()
        res = mod.render(query)
        title = res.get("title","Result")
        html_block = res.get("html","")
        badges = res.get("badges", [])
        items = res.get("items", [])
        badge_text = meta.get("badge","Plugin")
        badge_color = "var(--glass-strong)"
        hide_info_cards = ""
    elif searxng_results:
        # Show SearXNG results
        if searxng_results['success']:
            title = f'SearXNG Search Results for "{query}"'
            html_block = f"<p>Found: <strong>{searxng_results['total_results']} results</strong> from SearXNG</p>"
            badge_text = "SEARXNG"
            badge_color = "var(--glass-medium)"
            hide_info_cards = "hidden"
        else:
            title = f'Search Error for "{query}"'
            html_block = f'<div class="error-message"><h4>Error in SearXNG Search</h4><p>{searxng_results["error"]}</p></div>'
            badge_text = "ERROR"
            badge_color = "var(--glass-stronger)"
            hide_info_cards = "hidden"
        badges, items = [], []
    else:
        title = 'Search Result for "{}"'.format(html.escape(query or "")) if query else "GoogolPlex"
        html_block = "<p>Here is the relevant information I found for you:</p>" if query else "<p>Ask me something ...</p>"
        badges, items = [], []
        badge_text = "SMART ASSISTANT"
        badge_color = "var(--glass-medium)"
        hide_info_cards = ""

    def render_badges(badges):
        if not badges:
            return ""
        glass_levels = ['var(--glass-medium)', 'var(--glass-strong)', 'var(--glass-light)', 'var(--glass-stronger)']
        out = []
        for i, b in enumerate(badges):
            glass_bg = glass_levels[i % len(glass_levels)]
            out.append(f'<span class="plugin-badge" style="background: {glass_bg}; color: var(--text-primary); border: 1px solid var(--glass-border-light);">{html.escape(str(b))}</span>')
        return f'<div class="plugin-badges">{"".join(out)}</div>' if out else ""

    def render_items(items):
        if not items:
            return ""
        out = []
        for it in items:
            t = html.escape(str(it.get("title","Item")))
            d = html.escape(str(it.get("desc","")))
            out.append(f'<div class="plugin-item"><h4>{t}</h4><p>{d}</p></div>')
        return f'<div class="plugin-items">{"".join(out)}</div>' if out else ""

    def render_search_results(searxng_results):
        if not searxng_results or not searxng_results['success'] or not searxng_results['results']:
            return ""
        
        html_parts = []
        
        # Stats Bar
        engines_html = ''.join([f'<span class="engine-tag">{engine}</span>' for engine in searxng_results.get('engines', [])])
        stats_html = f'''
        <div class="stats-bar">
            <div class="stat-item">
                <span class="stat-value">{searxng_results['total_results']}</span> results found
            </div>
            <div class="stat-item">
                Search engines: <div class="engines-list">{engines_html}</div>
            </div>
        </div>
        '''
        html_parts.append(stats_html)
        
        # Search Results
        results_html = '<div class="search-results">'
        for result in searxng_results['results']:
            result_html = f'''
            <div class="search-result">
                <div class="result-header">
                    <div class="result-position">{result['position']}</div>
                    <div class="result-title">
                        <h4><a href="{html.escape(result['url'])}" target="_blank">{html.escape(result['title'])}</a></h4>
                        <div class="result-url">{html.escape(result['domain'])}</div>
                    </div>
                </div>
                <div class="result-content">{html.escape(result['content'])}</div>
                <div class="result-meta">
                    <span class="result-engine">{html.escape(result['engine'])}</span>
                </div>
            </div>
            '''
            results_html += result_html
        
        results_html += '</div>'
        html_parts.append(results_html)
        
        return ''.join(html_parts)

    doc = HTML
    doc = doc.replace("[[QUERY_ESC]]", html.escape(query or ""))
    doc = doc.replace("[[TITLE_ESC]]", html.escape(title))
    doc = doc.replace("[[CONTENT_HTML]]", html_block)
    doc = doc.replace("[[BADGE_TEXT_ESC]]", html.escape(badge_text))
    doc = doc.replace("[[BADGE_COLOR]]", badge_color)
    doc = doc.replace("[[EXTRA_BADGES]]", render_badges(badges))
    doc = doc.replace("[[EXTRA_ITEMS]]", render_items(items))
    doc = doc.replace("[[SEARCH_RESULTS_HTML]]", render_search_results(searxng_results))
    doc = doc.replace("[[HIDE_INFO_CARDS]]", hide_info_cards)

    doc = doc.replace("[[SEARXNG_URL]]", f"/searxng?q={urlencode({'q': query})}" if query else f"/searxng")
    doc = doc.replace("[[YEAR]]", str(datetime.now().year))
    
    if query:
        doc = doc.replace("[[RESULT_HIDDEN_ATTR]]", "")
        doc = doc.replace("[[QUERY_LEDE]]", '"{}"'.format(html.escape(query)))
        doc = doc.replace("[[SEARCH_PLACEHOLDER]]", "Start new search...")
    else:
        doc = doc.replace("[[RESULT_HIDDEN_ATTR]]", "hidden")
        doc = doc.replace("[[QUERY_LEDE]]", "")
        doc = doc.replace("[[SEARCH_PLACEHOLDER]]", "Search or command ...")
        
    return HTMLResponse(doc)

@app.get("/", response_class=HTMLResponse)
def index():
    return render_page(query="")

@app.get("/search", response_class=HTMLResponse)
def search(
    q: Optional[str] = Query(None),
    as_q: Optional[str] = Query(None),
    engine: str = Query("plugins"),
):
    effective_q = (as_q or q or "").strip()
    
    if engine == "searxng" and effective_q:
        # mit Trigger-Präfix, damit web_search.py sicher matched
        return render_page(query=f"web {effective_q}")

    
    # If no query provided, show homepage
    if not effective_q:
        return render_page(query="")
    
    # Try to find a matching plugin first
    mod = pick_plugin(effective_q)
    if mod:
        # Plugin found, use it
        return render_page(query=effective_q)
    else:
        # No plugin found, fall back to SearXNG automatically
        results = search_searxng(effective_q)
        return render_page(query=effective_q, searxng_results=results)

from urllib.parse import unquote_plus
from typing import Optional
from fastapi import Request, Query

def normalize_query(raw: str) -> str:
    if not raw:
        return ""
    s = raw.strip()
    if s.lower().startswith("q%3d"):     # q%3Dfoo  -> q=foo
        s = unquote_plus(s)
    if s.lower().startswith("q="):       # q=foo    -> foo
        s = s[2:]
    return s.strip()

@app.get("/searxng", response_class=HTMLResponse)
def searxng_endpoint(
    request: Request,
    q: Optional[str] = Query(None),
    query: Optional[str] = Query(None),
):
    # accept q OR query and normalize
    raw = q if (q not in (None, "")) else (query or "")
    q_norm = normalize_query(raw)

    if not q_norm:
        return render_page(query="")

    results = search_searxng(q_norm)
    return render_page(query=q_norm, searxng_results=results)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False, proxy_headers=True, forwarded_allow_ips="*")
