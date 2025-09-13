import requests
import json
from datetime import datetime

# =============================================================================
# CONFIG - Change these values
# =============================================================================
CONFIG = {
    "trigger_words": ["weather", "temperature", "rain", "snow", "windy", "cloudy", "sunny", "forecast", "temp"],
    
    "fallback_lat": 40.7128,
    "fallback_lon": -74.0060,
    "fallback_name": "New York, USA",
    
    "gps_enabled": True,
    "auto_gps": True,
    
    "tts_enabled": True,
    "tts_language": "en-US",
    "tts_text": "Weather forecast for {location}: {temp} degrees."
}


# =============================================================================
# PLUGIN FUNCTIONS
# =============================================================================

def meta():
    return {
        "name": "Weather",
        "badge": "Plugin: Weather",
        "color": "rgba(6, 182, 212, 0.8)"
    }

def can_handle(query: str):
    q = (query or "").strip().lower()
    return 1.0 if any(word in q for word in CONFIG["trigger_words"]) else 0.0

def get_used_trigger_word(query: str):
    """Extract the originally used trigger word from query"""
    if not query:
        return CONFIG["trigger_words"][0]  # Use first as fallback
    
    q = query.strip().lower()
    words = q.split()
    
    # Check each word in query against trigger words
    for word in words:
        if word in CONFIG["trigger_words"]:
            return word
    
    # Fallback to first trigger word if none found
    return CONFIG["trigger_words"][0]

def get_coords_from_query(query: str):
    """Extract GPS coordinates from query like 'weather gps:47.2692,11.4041'"""
    try:
        if 'gps:' in query.lower():
            coords_part = query.lower().split('gps:')[1].strip().split()[0]
            lat_str, lon_str = coords_part.split(',')
            lat, lon = float(lat_str), float(lon_str)
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                return lat, lon
    except:
        pass
    return None

def get_location_name(lat, lon):
    """Get city name from coordinates"""
    try:
        url = f"https://nominatim.openstreetmap.org/reverse"
        params = {'lat': lat, 'lon': lon, 'format': 'json'}
        headers = {'User-Agent': 'Weather Plugin'}
        
        response = requests.get(url, params=params, headers=headers, timeout=5)
        data = response.json()
        
        address = data.get('address', {})
        city = address.get('city') or address.get('town') or address.get('village', '')
        country = address.get('country', '')
        
        if city and country:
            return f"{city}, {country}"
        elif city:
            return city
        else:
            return f"Coordinates {lat:.2f}, {lon:.2f}"
    except:
        return f"Coordinates {lat:.2f}, {lon:.2f}"

def get_ip_location():
    """Get location from IP address"""
    try:
        response = requests.get("http://ip-api.com/json/", timeout=5)
        data = response.json()
        
        if data.get('status') == 'success':
            lat = data['lat']
            lon = data['lon']
            city = data.get('city', 'Unknown City')
            country = data.get('country', '')
            
            location_name = f"{city}, {country}" if country else city
            return lat, lon, f"{location_name} (IP-based)"
    except:
        pass
    
    # Fallback
    return CONFIG["fallback_lat"], CONFIG["fallback_lon"], CONFIG["fallback_name"]

def get_weather_data(query):
    """Get weather data for location"""
    
    # Check if GPS coordinates in query
    coords = get_coords_from_query(query)
    if coords:
        lat, lon = coords
        location_name = get_location_name(lat, lon)
        source = "GPS"
    else:
        lat, lon, location_name = get_ip_location()
        source = "IP-based" if "IP-based" in location_name else "Fallback"
    
    # Get weather from Open-Meteo API
    try:
        weather_url = "https://api.open-meteo.com/v1/forecast"
        params = {
            'latitude': lat,
            'longitude': lon,
            'current_weather': True,
            'daily': 'sunrise,sunset',
            'forecast_days': 1,
            'timezone': 'auto'
        }
        
        response = requests.get(weather_url, params=params, timeout=10)
        data = response.json()
        
        current = data['current_weather']
        temp = int(current['temperature'])
        wind_speed = current['windspeed']
        weather_code = current['weathercode']
        
        # Get sunrise/sunset
        try:
            sunrise = data['daily']['sunrise'][0].split('T')[1][:5]
            sunset = data['daily']['sunset'][0].split('T')[1][:5]
        except:
            sunrise = "06:30"
            sunset = "19:30"
        
        return {
            'temperature': temp,
            'wind_speed': wind_speed,
            'weather_code': weather_code,
            'sunrise': sunrise,
            'sunset': sunset,
            'location': location_name,
            'source': source,
            'lat': lat,
            'lon': lon
        }
        
    except Exception as e:
        print(f"Weather API error: {e}")
        # Return fallback data
        return {
            'temperature': 15,
            'wind_speed': 10,
            'weather_code': 1,
            'sunrise': "06:30",
            'sunset': "19:30",
            'location': CONFIG["fallback_name"],
            'source': "Fallback",
            'lat': CONFIG["fallback_lat"],
            'lon': CONFIG["fallback_lon"]
        }

def get_weather_description(code):
    """Convert weather code to emoji and description"""
    weather_codes = {
        0: ("☀️", "Clear sky"),
        1: ("🌤️", "Mainly clear"),
        2: ("⛅", "Partly cloudy"), 
        3: ("☁️", "Overcast"),
        45: ("🌫️", "Foggy"),
        48: ("🌫️", "Dense fog"),
        51: ("🌦️", "Light drizzle"),
        53: ("🌧️", "Drizzle"),
        55: ("🌧️", "Heavy drizzle"),
        61: ("🌧️", "Light rain"),
        63: ("🌧️", "Rain"),
        65: ("🌧️", "Heavy rain"),
        71: ("❄️", "Light snow"),
        73: ("❄️", "Snow"),
        75: ("❄️", "Heavy snow"),
        80: ("🌦️", "Rain showers"),
        81: ("🌧️", "Heavy rain showers"),
        85: ("🌨️", "Snow showers"),
        95: ("⛈️", "Thunderstorm")
    }
    return weather_codes.get(code, ("🌤️", "Unknown"))

# === CHANGED: queue() statt speak() + Dedupe, ansonsten unverändert ==========
def get_tts_script(text: str) -> str:
    safe_text = json.dumps(text)  # korrektes Escaping
    langprefs = json.dumps([CONFIG['tts_language']])
    return f"""
<script>
document.addEventListener('DOMContentLoaded', function() {{
    try {{
        if (window.TTS && (window.TTS.queue || window.TTS.speak)) {{
            var speakFn = window.TTS.queue || window.TTS.speak;
            var s = {safe_text};
            // Dedupe: gleicher Text nur einmal je Seite
            var h = 0; for (var i=0;i<s.length;i++) h = (h*31 + s.charCodeAt(i))|0;
            window.__TTS_SEEN = window.__TTS_SEEN || new Set();
            if (!window.__TTS_SEEN.has(h)) {{
                window.__TTS_SEEN.add(h);
                speakFn(s, {{ langPrefs: {langprefs} }}).catch(function(){{}});
            }}
        }}
    }} catch(e) {{}}
    // Optionales Priming beim ersten User-Tap (falls iOS blockiert)
    const enableTTS = () => {{
        try {{
            if (window.TTS && (window.TTS.queue || window.TTS.speak)) {{
                var speakFn = window.TTS.queue || window.TTS.speak;
                speakFn({safe_text}, {{ langPrefs: {langprefs} }}).catch(function(){{}});
            }}
        }} catch(e) {{}}
        document.removeEventListener('click', enableTTS);
        document.removeEventListener('touchstart', enableTTS);
    }};
    document.addEventListener('click', enableTTS, {{ once: true }});
    document.addEventListener('touchstart', enableTTS, {{ once: true }});
}});
</script>
    """

def render(query: str):
    """Main render function"""
    try:
        # Get the originally used trigger word
        original_trigger = get_used_trigger_word(query)
        
        # Get weather data
        weather = get_weather_data(query)
        emoji, condition = get_weather_description(weather['weather_code'])
        
        is_gps_query = 'gps:' in query.lower()
        current_time = datetime.now().strftime("%H:%M")
        
        # Build HTML
        html_parts = []
        
        # Main weather display
        html_parts.append(f'''
<div style="background: rgba(255,255,255,0.1); border-radius: 20px; padding: 25px; text-align: center;">
    <div style="font-size: 80px; margin-bottom: 15px;">{emoji}</div>
    <div style="font-size: 36px; font-weight: bold; margin-bottom: 10px;">{weather['temperature']}°C</div>
    <div style="font-size: 20px; color: rgba(255,255,255,0.8); margin-bottom: 15px;">{condition}</div>
    <div style="font-size: 14px; color: rgba(255,255,255,0.6);">📍 {weather['location']}</div>
    <div style="font-size: 12px; color: rgba(255,255,255,0.5); margin-top: 5px;">Source: {weather['source']}</div>
</div>
        ''')
        
        # Weather details grid
        html_parts.append(f'''
<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin: 20px 0;">
    <div style="background: rgba(255,255,255,0.1); padding: 20px; border-radius: 15px; text-align: center;">
        <div style="font-size: 24px; margin-bottom: 8px;">💨</div>
        <div style="color: rgba(255,255,255,0.8); font-size: 14px;">Wind</div>
        <div style="font-size: 18px; font-weight: bold;">{weather['wind_speed']:.0f} km/h</div>
    </div>
    <div style="background: rgba(255,255,255,0.1); padding: 20px; border-radius: 15px; text-align: center;">
        <div style="font-size: 24px; margin-bottom: 8px;">🌅</div>
        <div style="color: rgba(255,255,255,0.8); font-size: 14px;">Sun</div>
        <div style="font-size: 14px; font-weight: bold;">{weather['sunrise']} - {weather['sunset']}</div>
    </div>
</div>
        ''')
        
        # GPS button (if GPS enabled and not already GPS query)
        if CONFIG["gps_enabled"] and not is_gps_query:
            html_parts.append(f'''
<div style="text-align: center; margin: 20px 0;">
    <button id="gpsBtn" onclick="useGPS()" style="
        background: rgba(6,182,212,0.2); 
        border: 1px solid rgba(6,182,212,0.4);
        color: white; 
        padding: 12px 20px; 
        border-radius: 25px; 
        font-size: 14px; 
        cursor: pointer;
        transition: all 0.2s ease;
    ">
        📍 Use GPS Location
    </button>
</div>

<script>
function useGPS() {{
    const btn = document.getElementById('gpsBtn');
    btn.innerHTML = '📍 Getting location...';
    btn.disabled = true;
    
    if (!navigator.geolocation) {{
        btn.innerHTML = '❌ GPS not available';
        return;
    }}
    
    navigator.geolocation.getCurrentPosition(
        function(position) {{
            const lat = position.coords.latitude;
            const lon = position.coords.longitude;
            btn.innerHTML = '✅ Location found!';
            
            setTimeout(() => {{
                // Use the original trigger word that was used
                const triggerWord = '{original_trigger}';
                window.location.href = `/search?q=${{triggerWord}} gps:${{lat}},${{lon}}`;
            }}, 500);
        }},
        function(error) {{
            btn.innerHTML = '❌ GPS failed';
            btn.disabled = false;
            setTimeout(() => {{
                btn.innerHTML = '📍 Use GPS Location';
            }}, 2000);
        }},
        {{
            enableHighAccuracy: true,
            timeout: 10000,
            maximumAge: 300000
        }}
    );
}}
</script>
            ''')
        
        # === CHANGED: TTS-Text vor dem Einfügen berechnen (nur TTS-bezogen) ===
        if CONFIG["tts_enabled"]:
            tts_text = CONFIG["tts_text"].format(
                location=weather['location'].split(' (')[0],  # Remove (IP-based) suffix
                temp=weather['temperature'],
                condition=condition
            )
            html_parts.append(get_tts_script(tts_text))

        # Auto GPS script (if enabled and not GPS query)  
        if CONFIG["gps_enabled"] and CONFIG["auto_gps"] and not is_gps_query:
            html_parts.append(f'''
<script>
document.addEventListener('DOMContentLoaded', function() {{
    if (!window.location.search.includes('gps:') && navigator.geolocation) {{
        
        // Create status indicator
        const status = document.createElement('div');
        status.style.cssText = `
            position: fixed; top: 20px; right: 20px; z-index: 1000;
            background: rgba(6,182,212,0.15); border: 1px solid rgba(6,182,212,0.3);
            padding: 12px 16px; border-radius: 10px; color: white; font-size: 12px;
            backdrop-filter: blur(10px);
        `;
        status.innerHTML = '📍 Auto-detecting GPS...';
        document.body.appendChild(status);
        
        navigator.geolocation.getCurrentPosition(
            function(pos) {{
                const lat = pos.coords.latitude;
                const lon = pos.coords.longitude;
                const acc = Math.round(pos.coords.accuracy);
                
                status.innerHTML = `✅ GPS found (±${{acc}}m)`;
                
                setTimeout(() => {{
                    // FIXED: Use the original trigger word that was used
                    const triggerWord = '{original_trigger}';
                    const newQuery = `${{triggerWord}} gps:${{lat}},${{lon}}`;
                    window.location.href = `/search?q=${{encodeURIComponent(newQuery)}}`;
                }}, 0);
            }},
            function(error) {{
                status.innerHTML = '📍 Using IP location';
                setTimeout(() => status.remove(), 2000);
            }},
            {{ enableHighAccuracy: true, timeout: 8000, maximumAge: 60000 }}
        );
    }}
}});
</script>
            ''')
        
        # Footer info
        html_parts.append(f'''
<div style="text-align: center; margin-top: 20px; font-size: 11px; color: rgba(255,255,255,0.5);">
    Updated: {current_time} • Coordinates: {weather['lat']:.4f}, {weather['lon']:.4f}
</div>
        ''')
        
        # Combine all HTML
        final_html = ''.join(html_parts)
        
        return {
            "title": f"Weather for {weather['location'].split(' (')[0]}",
            "html": final_html,
            "badges": [
                f"📍 {weather['location'].split(' (')[0][:20]}",
                f"{weather['temperature']}°C",
                condition,
                weather['source']
            ],
            "items": [
                {"title": "🌡️ Temperature", "desc": f"{weather['temperature']}°C - {condition}"},
                {"title": "💨 Wind", "desc": f"{weather['wind_speed']:.0f} km/h"},
                {"title": "🌅 Sun Times", "desc": f"Rise: {weather['sunrise']}, Set: {weather['sunset']}"},
                {"title": "📍 Location", "desc": f"{weather['location']} ({weather['source']})"}
            ]
        }
        
    except Exception as e:
        return {
            "title": "Weather Error",
            "html": f'''
<div style="background: rgba(255,0,0,0.1); border-radius: 15px; padding: 20px; text-align: center;">
    <div style="font-size: 48px; margin-bottom: 10px;">❌</div>
    <div style="font-size: 18px; margin-bottom: 10px;">Weather Error</div>
    <div style="font-size: 14px; color: rgba(255,255,255,0.7);">Could not load weather data</div>
    <div style="font-size: 12px; color: rgba(255,255,255,0.5); margin-top: 10px;">Error: {str(e)[:100]}</div>
</div>
            ''',
            "badges": ["❌ Error"],
            "items": [{"title": "Status", "desc": "Failed to load weather data"}]
        }
