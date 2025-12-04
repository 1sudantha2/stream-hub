from flask import Flask, render_template, jsonify, request
import requests
import re
import threading
import os

app = Flask(__name__)

# --- 1. PLAYLIST CONFIGURATION (Lighter & Faster Lists) ---
PLAYLIST_MAP = {
    "Sri Lanka": "https://iptv-org.github.io/iptv/countries/lk.m3u",
    "Radio": "INTERNAL_RADIO",  # විශේෂ Radio අංශය
    "Music": "https://iptv-org.github.io/iptv/categories/music.m3u",
    "Kids": "https://iptv-org.github.io/iptv/categories/kids.m3u",
    "News": "https://iptv-org.github.io/iptv/categories/news.m3u",
    "Movies": "https://iptv-org.github.io/iptv/categories/movies.m3u",
    "Sports": "https://iptv-org.github.io/iptv/categories/sports.m3u",
    "Comedy": "https://iptv-org.github.io/iptv/categories/comedy.m3u",
    "Documentary": "https://iptv-org.github.io/iptv/categories/documentary.m3u"
}

# --- 2. INTERNAL RADIO CHANNELS (Syntax Corrected) ---
RADIO_CHANNELS = [
    {
        "name": "Hiru FM",
        "url": "http://radio.lotustechnologieslk.net:2020/stream/hirufmgarden",
        "logo": "https://cdn-profiles.tunein.com/s106822/images/logod.png",
        "group": "Radio"
    },
    {
        "name": "Shaa FM",
        "url": "http://radio.lotustechnologieslk.net:2020/stream/shaafmgarden",
        "logo": "https://cdn-profiles.tunein.com/s106824/images/logod.png",
        "group": "Radio"
    },
    {
        "name": "Gold FM",
        "url": "http://radio.lotustechnologieslk.net:2020/stream/goldfmgarden",
        "logo": "https://cdn-profiles.tunein.com/s13370/images/logod.png",
        "group": "Radio"
    },
    {
        "name": "Sun FM",
        "url": "http://radio.lotustechnologieslk.net:2020/stream/sunfmgarden",
        "logo": "https://cdn-profiles.tunein.com/s13374/images/logod.png",
        "group": "Radio"
    },
    {
        "name": "Sooriyan FM",
        "url": "http://radio.lotustechnologieslk.net:2020/stream/sooriyanfmgarden",
        "logo": "https://cdn-profiles.tunein.com/s15652/images/logod.png",
        "group": "Radio"
    },
    {
        "name": "Siyatha FM",
        "url": "https://srv02.onlineradio.voaplus.com/siyathafm",
        "logo": "https://cdn-profiles.tunein.com/s107779/images/logod.png",
        "group": "Radio"
    },
    {
        "name": "Y FM",
        "url": "http://s3.voscast.com:8462/;stream.mp3",
        "logo": "https://cdn-profiles.tunein.com/s86358/images/logod.png",
        "group": "Radio"
    },
    {
        "name": "Shree FM",
        "url": "https://207.148.74.192:7874/stream2.mp3",
        "logo": "https://cdn-profiles.tunein.com/s107778/images/logod.png",
        "group": "Radio"
    }
]

# --- RAM CACHE ---
PLAYLIST_CACHE = {}

def parse_m3u(url):
    try:
        response = requests.get(url, timeout=15)
        response.encoding = 'utf-8'
        lines = response.text.split('\n')
        channels = []
        
        current_name = None
        current_logo = None
        current_group = "Others" 
        
        for line in lines:
            line = line.strip()
            if line.startswith('#EXTINF'):
                logo_match = re.search(r'tvg-logo="([^"]+)"', line)
                current_logo = logo_match.group(1) if logo_match else None
                group_match = re.search(r'group-title="([^"]+)"', line)
                current_group = group_match.group(1).strip() if group_match else "Others"
                parts = line.split(',')
                current_name = parts[-1].strip() if len(parts) > 1 else "Unknown Channel"
            
            elif line.startswith('http') and current_name:
                channels.append({
                    'name': current_name,
                    'logo': current_logo,
                    'group': current_group,
                    'url': line
                })
                current_name = None 
                
        return channels
    except Exception as e:
        print(f"Error parsing {url}: {e}")
        return []

def preload_playlists():
    print("🚀 Pre-loading playlists...")
    for name, url in PLAYLIST_MAP.items():
        if name == "Radio": continue 
        if name not in PLAYLIST_CACHE:
            try:
                data = parse_m3u(url)
                PLAYLIST_CACHE[name] = data
                print(f"✅ Cached: {name} ({len(data)} channels)")
            except:
                pass
    print("✨ Ready!")

# Start background loading
threading.Thread(target=preload_playlists).start()

# ----------------- API ENDPOINTS -----------------

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/playlists')
def get_playlist_names():
    return jsonify(list(PLAYLIST_MAP.keys()))

@app.route('/api/channels')
def get_channels():
    # Default playlist is Sri Lanka
    playlist_name = request.args.get('playlist', 'Sri Lanka')
    
    # 1. Handle Radio Request
    if playlist_name == "Radio":
        return jsonify(RADIO_CHANNELS)
    
    # 2. Handle Cached TV Lists
    if playlist_name in PLAYLIST_CACHE and PLAYLIST_CACHE[playlist_name]:
        return jsonify(PLAYLIST_CACHE[playlist_name])
    
    # 3. Fallback: Download if not cached
    url = PLAYLIST_MAP.get(playlist_name)
    if not url: return jsonify([]), 404
    
    data = parse_m3u(url)
    PLAYLIST_CACHE[playlist_name] = data
    return jsonify(data)

if __name__ == '__main__':
    # RENDER DEPLOYMENT CONFIG
    # Cloud එකේ Port එක ගන්නවා, නැත්නම් 5000 පාවිච්චි කරනවා
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
