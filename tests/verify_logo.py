import urllib.request
html = urllib.request.urlopen('http://127.0.0.1:8080/').read().decode('utf-8')
ok = 'steamstatic.com/store_item_assets/steam/apps/253710/logo.png' in html
print(f'Logo Steam CDN: {"OK" if ok else "FALLO"}')
print(f'Texto My INFO: {"OK" if "THC - My INFO" in html else "FALLO"}')
print(f'Texto Castellano: {"OK" if "ticas de Cazador" in html else "FALLO"}')
