import requests
from pathlib import Path

pat = Path('.git-pat').read_text().strip()
h = {'Authorization': f'token {pat}', 'Accept': 'application/vnd.github+json'}

# string kaynagini bul
r = requests.get('https://api.github.com/search/code?q=repo:recloudstream/cloudstream+no_plugins_found',
                 headers=h, timeout=30)
for item in r.json().get('items', []):
    print(item['path'])

r2 = requests.get('https://api.github.com/search/code?q=repo:recloudstream/cloudstream+plugins_found_in_repository',
                  headers=h, timeout=30)
for item in r2.json().get('items', []):
    print(item['path'])
