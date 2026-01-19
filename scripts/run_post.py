#!/usr/bin/env python3
import json,urllib.request,urllib.error

url = 'http://localhost:8000/v1/equivalences/evaluate'
headers = {'Content-Type': 'application/json', 'X-API-Key': 'dev-admin-123'}
payload = {
    'request_id': 'req-001',
    'origem': {'nome': 'Algoritmos', 'carga_horaria': 60, 'ementa': '...', 'aprovado': True, 'nivel': 'intermediario'},
    'destino': {'nome': 'Introducao a Programacao', 'carga_horaria': 60, 'ementa': '...', 'nivel': 'basico'},
    'policy': {'min_score_deferir': 85},
    'taxonomy_version': '2026.01'
}

data = json.dumps(payload).encode('utf-8')
req = urllib.request.Request(url, data=data, headers=headers, method='POST')
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        body = r.read().decode('utf-8')
        print(body)
        print('\nHTTP_CODE:%d' % r.getcode())
except urllib.error.HTTPError as e:
    try:
        err_body = e.read().decode('utf-8')
    except Exception:
        err_body = str(e)
    print(err_body)
    print('\nHTTP_CODE:%d' % e.code)
except Exception as e:
    import traceback
    traceback.print_exc()
    print('\nHTTP_CODE:0')
