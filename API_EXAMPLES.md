# API Examples

## Headers
- `X-API-Key`: chave de API (ex.: `dev-admin-abc123`)
- `Content-Type: application/json`

## Evaluate (síncrono)
POST /v1/equivalences/evaluate

Curl example:
```bash
curl -sS -X POST http://localhost:8000/v1/equivalences/evaluate \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: dev-admin-abc123' \
  -d '{
    "request_id":"req-001",
    "origem": {"nome":"Algoritmos","carga_horaria":60,"ementa":"...","aprovado":true,"nivel":"intermediario"},
    "destino": {"nome":"Introdução a Programação","carga_horaria":60,"ementa":"...","nivel":"basico"},
    "policy": {"min_score_deferir":85},
    "taxonomy_version":"2026.01"
  }'
```

Python (requests):
```python
import requests
url='http://localhost:8000/v1/equivalences/evaluate'
headers={'X-API-Key':'dev-admin-abc123','Content-Type':'application/json'}
payload={...}
resp=requests.post(url,json=payload,headers=headers)
print(resp.status_code)
print(resp.json())
```

## Batch (assíncrono)
POST /v1/equivalences/batch
- Envia um lote de requests para serem processados por workers

Curl example:
```bash
curl -X POST http://localhost:8000/v1/equivalences/batch -H 'Content-Type: application/json' -d @batch_request.json
```

## Expected response (evaluate)
```json
{
  "request_id":"req-001",
  "decisao":"DEFERIDO",
  "score":92,
  "breakdown":{"cobertura":0.9,"cobertura_critica":1.0,"penalidade_nivel":0.0},
  "hard_rules":[],
  "justificativa_curta":"Muito semelhante.",
  "justificativa_detalhada":"..."
}
```

## Common troubleshooting
- 401/403: verifique `X-API-Key` e `API_KEY_SALT`/seed
- 5xx: ver logs do servidor e exceptions

Consulte `app/api/schemas.py` para detalhes do schema de request/response.
