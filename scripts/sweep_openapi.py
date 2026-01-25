import os
import json
import re
from urllib.parse import urljoin

import requests

# load .env-ish file
ENV_PATH = os.path.join(os.path.dirname(__file__), '..', '.env')
keys = {}
base_url = os.environ.get('BASE_URL', 'http://localhost:8000')
if os.path.exists(ENV_PATH):
    with open(ENV_PATH) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                k, v = line.split('=', 1)
                keys[k.strip()] = v.strip()

api_keys = [
    keys.get('ADMIN_API_KEY'),
    keys.get('AUDITOR_API_KEY'),
    keys.get('CLIENT_API_KEY'),
]
api_keys = [k for k in api_keys if k]

report = {
    'base_url': base_url,
    'tested_at': None,
    'summary': {},
    'details': []
}

try:
    r = requests.get(urljoin(base_url, '/openapi.json'), timeout=10)
    r.raise_for_status()
    spec = r.json()
except Exception as e:
    print('Failed to fetch openapi.json:', e)
    spec = None

if spec is None:
    out = {'error': 'failed to load openapi.json'}
    print(json.dumps(out, indent=2))
    exit(2)

paths = spec.get('paths', {})
count_ok = 0
count_total = 0

for path, methods in paths.items():
    for method, meta in methods.items():
        count_total += 1
        entry = {
            'path': path,
            'method': method.upper(),
            'summary': meta.get('summary') or meta.get('description'),
            'tests': []
        }

        # skip paths with path parameters as we don't have sample ids
        if '{' in path:
            entry['skipped'] = True
            entry['skip_reason'] = 'path has parameters'
            report['details'].append(entry)
            continue

        full = urljoin(base_url, path)

        for key in api_keys:
            t = {'api_key_used': 'present' if key else 'none', 'status': None, 'status_code': None, 'body_snippet': None, 'error': None}
            headers = {}
            if key:
                headers['X-API-Key'] = key
            try:
                if method.lower() == 'get':
                    resp = requests.get(full, headers=headers, timeout=10)
                elif method.lower() == 'delete':
                    resp = requests.delete(full, headers=headers, timeout=10)
                elif method.lower() in ('post', 'put', 'patch'):
                    # try to load sensible body for known endpoints
                    if path.endswith('/v1/equivalences/evaluate') or 'evaluate' in path:
                        body_path = os.path.join(os.path.dirname(__file__), '..', 'tests', 'request_example.json')
                        try:
                            with open(body_path) as f:
                                payload = json.load(f)
                        except Exception:
                            payload = {}
                    else:
                        payload = {}
                    resp = requests.request(method.upper(), full, headers=headers, json=payload, timeout=10)
                else:
                    resp = requests.request(method.upper(), full, headers=headers, timeout=10)

                t['status_code'] = resp.status_code
                t['status'] = 'ok' if 200 <= resp.status_code < 400 else 'error'
                txt = ''
                try:
                    txt = resp.text
                except Exception:
                    txt = repr(resp.content)
                t['body_snippet'] = txt[:400]
                if 200 <= resp.status_code < 400:
                    count_ok += 1
            except Exception as e:
                t['error'] = str(e)

            entry['tests'].append(t)

        report['details'].append(entry)

report['summary'] = {'total_endpoints': count_total, 'ok_responses_count': count_ok}
report['tested_at'] = __import__('datetime').datetime.utcnow().isoformat() + 'Z'

out_path = '/tmp/openapi_sweep_report.json'
with open(out_path, 'w') as f:
    json.dump(report, f, indent=2, ensure_ascii=False)

print('Report written to', out_path)
print('Summary:', report['summary'])
