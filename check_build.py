import requests
from pathlib import Path

pat = Path('.git-pat').read_text().strip()
h = {'Authorization': f'token {pat}'}
d = requests.get('https://api.github.com/repos/Lynx3272/ArchiveStream-Bot/actions/runs?per_page=1', headers=h, timeout=20).json()
run = d['workflow_runs'][0]
print('run:', run['id'], run['conclusion'])
jobs = requests.get(run['jobs_url'], headers=h, timeout=20).json()
for j in jobs['jobs']:
    for s in j['steps']:
        print(' ', s['name'], '->', s['conclusion'])
    if j['conclusion'] == 'failure':
        r = requests.get(j['url'] + '/logs', headers=h, timeout=60, allow_redirects=True)
        Path('build_log.txt').write_bytes(r.content)
        print('log kaydedildi, boyut:', len(r.content))
