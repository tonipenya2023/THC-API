import urllib.request

urls = [
    ("Wiki-wordmark (anterior)", "https://static.wikia.nocookie.net/thehuntergame/images/8/87/Wiki-wordmark.png/revision/latest"),
    ("Thehunter_logo (actual)", "https://static.wikia.nocookie.net/thehuntergame/images/4/48/Thehunter_logo.png/revision/latest"),
    ("THC logo Steam CDN", "https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/253710/header.jpg"),
    ("THC capsule Steam", "https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/253710/capsule_231x87.jpg"),
    ("THC logo small Steam", "https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/253710/logo.png"),
]

for name, url in urls:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        r = urllib.request.urlopen(req, timeout=5)
        ct = r.headers.get("Content-Type", "?")
        cl = r.headers.get("Content-Length", "?")
        print(f"[OK] {name}: {ct}, {cl} bytes")
    except Exception as e:
        print(f"[FALLO] {name}: {e}")
