# plugins/iphone_setup.py
import socket

CONFIG = {
    "trigger_words": ["iphone", "ios", "setup", "siri", "shortcut", "shortcuts", "install", "configure", "plex"],
    "server_port": 8000
}

def meta():
    return {
        "name": "iPhone Setup", 
        "badge": "iOS SETUP",
        "color": "rgba(0, 122, 255, 0.8)"
    }

def can_handle(query: str):
    q = query.lower()
    return 1.0 if any(word in q for word in CONFIG["trigger_words"]) else 0.0

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        return "localhost"

def render(query: str):
    try:
        server_ip = get_local_ip()
        server_url = f"http://{server_ip}:{CONFIG['server_port']}"
        
        html_content = f'''
        <div style="text-align: center; margin-bottom: 30px;">
            <div style="font-size: 60px; margin-bottom: 15px;">📱</div>
            <h2 style="color: var(--text-primary); margin-bottom: 10px;">iPhone Setup</h2>
            <p style="color: var(--text-secondary);">Connect your iPhone to GoogolPlex</p>
        </div>

        <div style="background: var(--glass-light); border-radius: 20px; padding: 25px; margin: 25px 0; border: 1px solid var(--glass-border-light);">
            <h3 style="color: var(--text-primary); margin-bottom: 20px;">Method 1: Voice Control (Recommended)</h3>
            
            <div style="background: var(--glass-medium); border-radius: 16px; padding: 20px; margin-bottom: 15px; border: 1px solid var(--glass-border-light);">
                <h4 style="color: var(--text-primary); margin-bottom: 15px;">Quick Install</h4>
                <p style="color: var(--text-secondary); margin-bottom: 15px;">Install the ready-made shortcut in one click:</p>
                
                <a href="https://www.icloud.com/shortcuts/dd6415bd2c9a46eaa22706966ef2f131" style="
                    background: linear-gradient(135deg, #007AFF, #0056CC);
                    color: white; 
                    padding: 14px 24px; 
                    border-radius: 16px; 
                    text-decoration: none; 
                    font-weight: 600;
                    display: inline-block;
                    box-shadow: 0 4px 15px rgba(0, 122, 255, 0.3);
                    margin-bottom: 10px;
                ">Install Plex Shortcut</a>
                
                <div style="background: var(--glass-strong); border-radius: 12px; padding: 15px; border: 1px solid var(--glass-border-light); margin-top: 15px;">
                    <p style="color: var(--text-secondary); margin-bottom: 8px; font-size: 14px;">After install:</p>
                    <p style="margin: 4px 0; color: var(--text-primary); font-size: 14px;">1. Open the shortcut</p>
                    <p style="margin: 4px 0; color: var(--text-primary); font-size: 14px;">2. Replace server URL with:</p>
                    <code style="background: var(--glass-light); padding: 4px 8px; border-radius: 6px; color: var(--text-primary); display: block; margin: 8px 0; font-size: 13px;">{server_url}/</code>
                    <p style="margin: 4px 0; color: var(--text-primary); font-size: 14px;">3. Save and test with "Hey Siri, Plex"</p>
                </div>
            </div>

            <div style="background: var(--glass-medium); border-radius: 16px; padding: 20px; border: 1px solid var(--glass-border-light);">
                <h4 style="color: var(--text-primary); margin-bottom: 15px;">Manual Setup (Alternative)</h4>
                <details style="color: var(--text-secondary);">
                    <summary style="color: var(--text-primary); cursor: pointer; margin-bottom: 10px;">Show manual instructions</summary>
                    <div style="line-height: 1.6; font-size: 14px;">
                        <p><strong>1.</strong> Open Shortcuts app on iPhone</p>
                        <p><strong>2.</strong> Create new shortcut</p>
                        <p><strong>3.</strong> Add "Text" action, set to: <code style="background: var(--glass-strong); padding: 2px 6px; border-radius: 4px;">{server_url}/</code></p>
                        <p><strong>4.</strong> Add "Ask for Input" action, prompt: <code style="background: var(--glass-strong); padding: 2px 6px; border-radius: 4px;">Command?</code></p>
                        <p><strong>5.</strong> Add "Text" action, set to: <code style="background: var(--glass-strong); padding: 2px 6px; border-radius: 4px;">search?q=</code> + Provided Input</p>
                        <p><strong>6.</strong> Add "Show Web Page" action, URL from combined text</p>
                        <p><strong>7.</strong> Name shortcut "Plex", add Siri phrase "Plex"</p>
                    </div>
                </details>
            </div>
                
            <div style="background: var(--glass-strong); border-radius: 12px; padding: 15px; border: 1px solid var(--glass-border-light); margin-top: 15px;">
                <p style="color: var(--text-primary); margin-bottom: 8px;">Usage:</p>
                <p style="margin: 4px 0; color: var(--text-primary);">"Hey Siri, Plex"</p>
                <p style="margin: 4px 0; color: var(--text-secondary);">→ "Command?"</p>
                <p style="margin: 4px 0; color: var(--text-primary);">→ "weather" / "search Python"</p>
                <p style="margin: 4px 0; color: var(--text-secondary);">→ Opens result</p>
            </div>
        </div>

        <div style="background: var(--glass-light); border-radius: 20px; padding: 25px; margin: 25px 0; border: 1px solid var(--glass-border-light);">
            <h3 style="color: var(--text-primary); margin-bottom: 20px;">Method 2: Safari Redirect</h3>
            
            <div style="background: var(--glass-medium); border-radius: 16px; padding: 20px; margin-bottom: 20px; border: 1px solid var(--glass-border-light);">
                <h4 style="color: var(--text-primary); margin-bottom: 15px;">Redirect Web Extension</h4>
                <div style="color: var(--text-secondary); line-height: 1.6; margin-bottom: 15px;">
                    <p><strong>1.</strong> Install "Redirect Web" from App Store</p>
                    <p><strong>2.</strong> Create redirect rule:</p>
                    <p><strong>3.</strong> From: <code style="background: var(--glass-strong); padding: 2px 6px; border-radius: 4px;">https://www.google.com/search*</code></p>
                    <p><strong>4.</strong> To: <code style="background: var(--glass-strong); padding: 2px 6px; border-radius: 4px;">{server_url}/search$1</code></p>
                    <p><strong>5.</strong> Enable in Safari Settings → Extensions</p>
                </div>
                
                <div style="background: var(--glass-strong); border-radius: 12px; padding: 15px; border: 1px solid var(--glass-border-light);">
                    <p style="color: var(--text-primary); margin-bottom: 8px;">Usage:</p>
                    <p style="margin: 4px 0; color: var(--text-primary);">"Hey Siri, Google Plex weather"</p>
                    <p style="margin: 4px 0; color: var(--text-secondary);">→ Siri shows Google search results</p>
                    <p style="margin: 4px 0; color: var(--text-primary);">→ Tap "Open with Google"</p>
                    <p style="margin: 4px 0; color: var(--text-secondary);">→ Extension redirects to your server</p>
                </div>
                
                <div style="background: rgba(0, 122, 255, 0.1); border: 1px solid rgba(0, 122, 255, 0.3); border-radius: 12px; padding: 12px; margin-top: 10px;">
                    <p style="color: var(--text-primary); font-size: 13px; margin: 0;">Like original 2014 GoogolPlex - hijacks Google searches</p>
                </div>
            </div>
        </div>

        <div style="background: var(--glass-light); border-radius: 16px; padding: 20px; margin: 20px 0; border: 1px solid var(--glass-border-light);">
            <h4 style="color: var(--text-primary); margin-bottom: 15px;">Server Information</h4>
            <div style="background: var(--glass-medium); border-radius: 12px; padding: 15px; border: 1px solid var(--glass-border-light);">
                <p style="color: var(--text-secondary); margin-bottom: 8px;">Your Server:</p>
                <code style="background: var(--glass-strong); padding: 8px 12px; border-radius: 8px; color: var(--text-primary); font-family: monospace; display: block;">{server_url}</code>
                <button onclick="copyToClipboard('{server_url}')" style="
                    background: var(--glass-strong); 
                    border: 1px solid var(--glass-border-light);
                    color: var(--text-primary);
                    padding: 8px 16px; 
                    border-radius: 8px; 
                    margin-top: 10px;
                    cursor: pointer;
                    font-family: inherit;
                ">Copy URL</button>
            </div>
        </div>

        <div style="background: rgba(255, 193, 7, 0.1); border: 1px solid rgba(255, 193, 7, 0.2); border-radius: 16px; padding: 20px; margin: 20px 0;">
            <h4 style="color: #FFC107; margin-bottom: 15px;">Requirements</h4>
            <ul style="color: var(--text-secondary); line-height: 1.6; margin: 0; padding-left: 20px;">
                <li>iPhone and computer on same WiFi network</li>
                <li>Server running on {server_ip}:{CONFIG['server_port']}</li>
                <li>Check firewall if connection fails</li>
            </ul>
        </div>

        <script>
        function copyToClipboard(text) {{
            if (navigator.clipboard) {{
                navigator.clipboard.writeText(text).then(function() {{
                    alert('Server URL copied!');
                }});
            }} else {{
                const textArea = document.createElement('textarea');
                textArea.value = text;
                document.body.appendChild(textArea);
                textArea.select();
                document.execCommand('copy');
                document.body.removeChild(textArea);
                alert('Server URL copied!');
            }}
        }}
        </script>
        '''

        return {
            "title": f"iPhone Setup - {server_ip}:{CONFIG['server_port']}",
            "html": html_content,
            "badges": [
                f"Server: {server_ip}",
                f"Port: {CONFIG['server_port']}",
                "iOS Ready",
                "Voice + Safari"
            ],
            "items": [
                {"title": "Voice Control", "desc": 'Say "Hey Siri, Plex" then speak your command'},
                {"title": "Safari Redirect", "desc": "Google searches redirect to your server"},
                {"title": "Server URL", "desc": f"{server_url}"},
                {"title": "Network", "desc": "iPhone and computer must be on same WiFi"}
            ]
        }

    except Exception as e:
        return {
            "title": "Setup Error",
            "html": f'''
            <div style="text-align: center; padding: 30px;">
                <div style="font-size: 48px; margin-bottom: 15px;">⚠</div>
                <h3 style="color: var(--text-primary);">Setup Error</h3>
                <p style="color: var(--text-secondary);">Could not generate setup</p>
                <code style="color: var(--text-tertiary); font-size: 12px;">{str(e)}</code>
            </div>
            ''',
            "badges": ["Error"],
            "items": []
        }