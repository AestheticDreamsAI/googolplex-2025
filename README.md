# GoogolPlex (2025 Edition)

A **local Siri plugin framework for iOS** – inspired by the GoogolPlex hack (2014), but stable, open and patch-proof.  
With GoogolPlex you can route Siri queries through Shortcuts & Safari redirects to your own local server and answer them with **custom Python plugins** – including UI and TTS.

---

## ✨ Features
- 🧩 **Plugin system** (`meta`, `can_handle`, `render`) – easy to extend  
- 🌍 Example plugins: **Weather**, **Web Search (SearXNG)**, **Wikipedia**, **iPhone Setup**  
- 🗣️ Text-to-Speech via `window.TTS.queue(...)` (deduplicated, iOS-friendly)  
- 📱 Seamless iPhone integration (Shortcuts + Safari redirect)  
- 🔒 100% local, privacy-friendly, no cloud dependency  

---

## 🔥 Why this is better than the original GoogolPlex (2014)

Back in 2014, the original GoogolPlex was a **hack**:  
- It hijacked Siri traffic via a proxy (Man-in-the-Middle).  
- Apple quickly patched the loophole.  
- It was closed-source, experimental, and short-lived.

This 2025 edition is **clean and sustainable**:  

✅ **No hack required** – uses official iOS features (Shortcuts + Safari Redirect).  
✅ **Patch-proof** – Apple cannot "fix" it away, since it doesn’t exploit Siri internals.  
✅ **Plugin system** – anyone can add Python plugins (`meta`, `can_handle`, `render`).  
✅ **Modern UI** – Glassmorphic design, badges, structured output.  
✅ **Text-to-Speech** – powered by `window.TTS.queue(...)`, queue-safe and iOS-friendly.  
✅ **Privacy-first** – everything runs locally, no data leaves your device/network.  
✅ **Extensible** – Weather, Web Search, Wikipedia are just examples; add your own.  

In short: instead of a proof-of-concept hack, this project is a **real open framework** for extending Siri with custom, local functionality.

---

## 📸 Demo
*(Add screenshots or GIFs here – e.g. Weather plugin, Web Search results, Siri Shortcut flow)*

---

## 🚀 Getting Started

### 1. Clone the repo
```bash
git clone https://github.com/yourname/googolplex.git
cd googolplex
````

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the server

```bash
python GoogleProxy.py
```

By default it runs at `http://localhost:5000`.

---

## 📱 iPhone Setup

To configure your iPhone, start the server and open it in Safari.

1. Visit:

   ```
   http://<your-ip>:5000
   ```
2. In the search box, type:

   ```
   setup
   ```
3. This opens the **iPhone Setup Plugin**, which guides you through the process.
   You can also go directly to:

   ```
   http://<your-ip>:5000/search?q=setup
   ```

### Method 1: Voice Control (Recommended)

1. Install the ready-made **iCloud Shortcut**.
2. Edit the shortcut and replace the server URL with your local server address (e.g. `http://192.168.1.23:8000/`).
3. Save it and say:

   * **“Hey Siri, Plex”** → Siri asks for a command.
   * Example: “weather” → Opens the Weather plugin.

### Method 2: Safari Redirect

1. Install **Redirect Web** from the App Store.
2. Create a redirect rule:

   * From: `https://www.google.com/search*`
   * To:   `http://<your-ip>:8000/search$1`
3. Now when you say *“Hey Siri, Google Plex …”* it opens Google, then Safari redirects into your server → plugin response.

---

## 📝 Writing Plugins

Plugins live in the `plugins/` directory.

A plugin must define three functions:

```python
def meta():
    return {"name": "Weather", "badge": "WEATHER"}

def can_handle(query: str) -> float:
    return 1.0 if "weather" in query.lower() else 0.0

def render(query: str):
    return {
        "title": "Weather",
        "html": "<div class='plugin-item'>☀️ 25°C – Sunny</div>",
        "badges": ["Sunny", "25°C"],
        "items": []
    }
```

That’s it! The server automatically loads all plugins from `/plugins`.

---

## 🔊 Text-to-Speech

Plugins can enqueue speech using `get_tts_script(text)`:

```python
html += get_tts_script("Weather in Zurich: 25 degrees, sunny")
```

This uses `window.TTS.queue(...)` with deduplication so the text is only spoken once.

---

## 📂 Project Structure

```
/plugins
   plugin_weather.py     # Weather plugin (Open-Meteo, TTS integration)
   plugin_searxng.py     # Web Search plugin (SearXNG)
   plugin_wikipedia.py   # Wikipedia lookup
   plugin_setup.py       # iPhone setup wizard
/GoogleProxy.py          # Main server & query dispatcher (loads all plugins)
```

---

## 🔧 Configuration

Each plugin can include its own `CONFIG` dictionary.
This allows you to adjust behavior without touching the core server.

### Weather plugin

```python
CONFIG = {
    "tts_enabled": True,
    "tts_language": "en-US",
    "units": "metric",
    "forecast_hours": 24,
    "trigger_words": ["weather", "wetter", "forecast"]
}
```

* Change `tts_language` (e.g. `"de-DE"`)
* Switch between `"metric"` and `"imperial"` units
* Extend trigger words for your language

---

### Web Search (SearXNG) plugin

```python
CONFIG = {
    "base_url": "http://192.168.1.114:8888",
    "triggers": ["web", "search", "google", "bing", "duckduckgo"],
    "max_results": 10,
    "safesearch": "1",
    "categories": "general"
}
```

* You can also override the base URL with an environment variable:

```bash
export SEARXNG_BASE_URL=http://192.168.1.114:8888
```

---

### Wikipedia plugin

```python
CONFIG = {
    "trigger_words": ["wiki", "wikipedia"],
    "language": "en"   # can be "de", "fr", ...
}
```

---

### Setup plugin

No special configuration required – it only guides you through iPhone setup.

---

👉 This means **every plugin is self-contained**:

* Config lives inside the plugin file.
* Defaults are provided.
* You can edit them directly or override via environment variables where supported.

---

## 🤝 Community

* Build your own plugins
* Share them via Pull Requests
* Example ideas: Calendar integration, Email reader, Smart Home control, Translation, Music controller

---

## 📜 License

MIT License – free to use, modify and extend.
