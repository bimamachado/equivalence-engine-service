# Uso e referências dos endpoints

Este documento resume os endpoints principais da aplicação, exemplos de uso (via `curl`), a ordem típica de uso e como funciona a autenticação por `X-API-Key` (quando necessária).

## Visão geral / ordem de uso recomendada

1. `/health` — checagem de saúde (sem auth).
2. `/docs` (OpenAPI/Swagger) — documentação automática da API (sem auth).
3. `/test-ui` — interface HTML simples para testar a API (sem auth).
4. `/v1/equivalences/batch` — endpoint para enviar lotes (requer `X-API-Key`).
5. `/v1/jobs/{job_id}` e `/v1/jobs/{job_id}/results` — consultar status e resultados do batch (requer `X-API-Key`).
6. `/dashboard` — UI administrativa para visualizar e rotular resultados (requer `X-API-Key` com papel `admin` ou `auditor`).
7. `/metrics` — exportação em formato Prometheus (sem auth).

## Endpoints públicos (não exigem `X-API-Key`)

Por padrão as rotas listadas abaixo são públicas e não passam pela checagem de `X-API-Key`:

- `/health`
- `/docs` (OpenAPI / Swagger UI)
- `/openapi.json`
- `/redoc`
- `/metrics`
- `/test-ui`
- `/doc` (atalho)
- `/index.html` (atalho)
- `/favicon.ico`

Qualquer outro caminho exigirá o header `X-API-Key` a menos que adicionado explicitamente à configuração.

## Autenticação: `X-API-Key`

- Propósito: identificar o `tenant` (organização/cliente) que faz a requisição e o `role` (papel) da chave para controle de acesso (por exemplo, `admin`, `auditor`, `api-client`).
- Onde é validado: o middleware usa a função `get_api_key_record` (ver `app/auth.py`) para comparar o hash da chave e checar se a chave e o tenant estão ativos.
- Formato: enviar no header HTTP `X-API-Key: <sua-chave-aqui>`.

Exemplo curl (endpoint protegido):

```
curl -i -H "X-API-Key: dev-client-123" -H "Content-Type: application/json" \
  -d '{"items": []}' \
  http://127.0.0.1:8001/v1/equivalences/batch
```

### Criação e gerenciamento de chaves

- Durante o desenvolvimento existe o script de seed `app/seed.py` que insere chaves de exemplo (veja `ADMIN_API_KEY`, `AUDITOR_API_KEY`, `CLIENT_API_KEY` via variáveis de ambiente). Você pode rodar o seed para criar chaves de teste:

```
cd /home/amachado/workspace/equivalence-engine-service
python3.13 app/seed.py
```

- Em produção você deverá criar/gerenciar entradas na tabela `ApiKey` no banco, definindo `tenant_id`, `role` e `status = 'active'` e entregar a chave secreta ao cliente. A API só armazena o hash da chave (`key_hash`).

## Descrição dos endpoints e exemplos

### /test-ui
- Tipo: HTML (template `app/templates/test_ui.html`).
- Uso: interface para testar a API manualmente no navegador.
- Exemplo: abra `http://127.0.0.1:8001/test-ui`.

### /docs e OpenAPI
- `/docs` — Swagger UI gerado pelo FastAPI. Use para explorar e testar endpoints.
- `/openapi.json` — especificação OpenAPI JSON.

### /v1/equivalences/batch (enviar lote)
- Método: POST
- Corpo: JSON com campo `items` (lista de requests individuais de avaliação). Exemplo:

```
{
  "items": [
    { "request_id": "r1", "payload": { /* ... */ } },
    { "request_id": "r2", "payload": { /* ... */ } }
  ]
}
```

Exemplo curl (requer `X-API-Key`):

```
curl -X POST http://127.0.0.1:8001/v1/equivalences/batch \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-client-123" \
  -d '{"items": [{"request_id":"r1","payload":{}}]}'
```

Resposta: `{ "job_id": "<uuid>", "status": "QUEUED", "total": N }`.

### Consultar job e resultados

- `GET /v1/jobs/{job_id}` — retorna status e progresso.
- `GET /v1/jobs/{job_id}/results` — retorna lista de itens e resultados vinculados.

Exemplo:

```
curl -i -H "X-API-Key: dev-client-123" http://127.0.0.1:8001/v1/jobs/<job_id>
curl -i -H "X-API-Key: dev-client-123" http://127.0.0.1:8001/v1/jobs/<job_id>/results
```

### /dashboard (UI administrativa)
- Tipo: HTML (Jinja templates `app/templates/list.html` e `detail.html`).
- Acesso: requer `X-API-Key` com `role` `admin` ou `auditor`.
- Rotas relevantes: `/dashboard`, `/dashboard/result/{rid}`, `/dashboard/result/{rid}/label` (POST para rotular).

Abra no navegador: `http://127.0.0.1:8001/dashboard` (use a chave `dashboard-admin` ou `dashboard-auditor` criada pelo seed para logins de teste).

### /metrics (Prometheus)
- Método: GET
- Resposta: texto com métricas no formato Prometheus.
- Exemplo:

```
curl -i http://127.0.0.1:8001/metrics
```

## Observações e recomendações

- O middleware `ApiKeyAuthMiddleware` exige `X-API-Key` para rotas não listadas como públicas. Se receber `{"detail": "Missing X-API-Key"}` isso significa que o endpoint não está em `PUBLIC_PATHS` e você deve enviar a chave.
- Use chaves com escopo/role adequados: não reutilize uma chave `api-client` para ações administrativas.
- Para testes rápidos, use `app/seed.py` para criar chaves dev (veja variáveis de ambiente `ADMIN_API_KEY`, `AUDITOR_API_KEY`, `CLIENT_API_KEY`).

Se quiser, eu crio também um `README` resumido ou exemplos prontos em `scripts/` (ex.: `scripts/example_batch.sh`) com `curl` prontos para uso. Deseja que eu adicione isso e commite para você, ou prefere commitar manualmente?
