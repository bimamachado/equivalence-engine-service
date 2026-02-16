# Equivalence Engine — Guia completo (Macro → Micro)

Este documento detalha a arquitetura e o uso do projeto do macro (visão geral) ao micro (endpoints, exemplos e comandos), incluindo variáveis de ambiente, como subir os serviços, como rodar workers, migrar o banco e exemplos de requisições.

**Arquitetura (Macro)**

- Web/API: fornece endpoints HTTP para avaliar equivalências e operações administrativas. Código principal em [app/main.py](app/main.py#L1).
- Engine: regras, scoring e justificativas em [app/engine](app/engine).
- Mapper: integração com serviços de embeddings/LLM ou mappers de fallback em [app/mapper](app/mapper).
- Queue / Workers: processamento assíncrono de batch jobs via RQ (Redis) e workers em [app/worker.py](app/worker.py#L1).
- Storage: Postgres para auditoria e persistência (`DATABASE_URL`) e Redis para cache/fila (`REDIS_URL`).
- Migrations: Alembic (alembic/).

Componentes principais e onde olhar (micro):

- Configurações: [app/config.py](app/config.py#L1-L20) — carrega `DATABASE_URL`, `REDIS_URL`, `API_KEY_SALT`, etc.
- Conexão DB: [app/db.py](app/db.py#L1-L20) — `engine = create_engine(settings.DATABASE_URL, ...)`.
- Redis client: [app/redis_client.py](app/redis_client.py#L1-L20).
- Seed de dados (chaves de API de exemplo): [app/seed.py](app/seed.py#L1-L60).
- Rotas API: [app/api/routes.py](app/api/routes.py#L1-L200) — endpoints síncronos e criação de jobs batch.
- Batch API: [app/api/batch_routes.py](app/api/batch_routes.py#L1-L200) — enfileira jobs para processamento assíncrono.
- Worker (RQ): [docker-compose.prod.yml](docker-compose.prod.yml#L50-L56) mostra como executar `rq worker` dentro de um container; localmente use `rq worker -u <REDIS_URL> <QUEUE_NAME>`.

Variáveis de ambiente importantes

- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` — credenciais do Postgres.
- `DATABASE_URL` — string de conexão usada pela app.
- `REDIS_URL` — URL do Redis.
- `RQ_QUEUE_NAME` — nome da fila RQ (padrão: `equivalence`).
- `API_KEY_SALT` — salt para hashing de API keys. Usado em [app/security.py](app/security.py#L1-L12).
- `TENANT_API_KEY`, `ADMIN_API_KEY`, `AUDITOR_API_KEY`, `CLIENT_API_KEY` — definidos pelo `app/seed.py` para dados dev.
- `EMBED_URL`, `EMBED_API_KEY`, `LLM_URL`, `LLM_API_KEY` — endpoints e chaves para mappers externos (veja [app/mapper/clients.py](app/mapper/clients.py#L1-L80)).

Exemplo `.env` (desenvolvimento)

```dotenv
POSTGRES_USER=equivalence
POSTGRES_PASSWORD=dev-equivalence-pass
POSTGRES_DB=equivalence
DATABASE_URL=postgresql+psycopg2://equivalence:dev-equivalence-pass@127.0.0.1:5433/equivalence
REDIS_URL=redis://127.0.0.1:6380/0
RQ_QUEUE_NAME=equivalence

API_KEY_SALT=change-this-to-a-long-random-string
TENANT_API_KEY=dev-tenant-abc123
ADMIN_API_KEY=dev-admin-123
AUDITOR_API_KEY=dev-auditor-123
CLIENT_API_KEY=dev-client-123

EMBED_URL=http://localhost:9001
EMBED_API_KEY=
LLM_URL=http://localhost:9002
LLM_API_KEY=
```

Como subir tudo (dev)

1) Docker Compose (recomendado):

```bash
docker compose build --pull
docker compose up -d
```

O `docker-compose.yml` inicia `web`, `mock-embed`, `mock-llm`, `redis` e `postgres` (veja [docker-compose.yml](docker-compose.yml#L1-L80)).

2) Manual (venv):

```bash
python -m venv .venv
source .venv/bin/activate   # ou .\.venv\Scripts\Activate.ps1 no Windows
pip install -r requirements.txt
# garanta que .env está configurado
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

Rodando o worker (dev)

- Local (host expõe Redis):

```bash
pip install -r requirements.txt
rq worker -u redis://localhost:6380/0 equivalence
```

- Em Docker (exemplo de serviço no compose prod): veja `docker-compose.prod.yml` que executa `rq worker -u ${REDIS_URL} ${RQ_QUEUE_NAME}`.

Popular dados (seed)

```bash
# a seed usa variáveis: TENANT_API_KEY, ADMIN_API_KEY, AUDITOR_API_KEY, CLIENT_API_KEY
python -m app.seed
```

API — macro → micro (endpoints e exemplos)

1) Endpoint principal: `POST /v1/equivalences/evaluate`
- Rola a lógica completa: valida entrada -> mapear (mapper: embeddings/LLM ou stub) -> aplicar regras duras -> scoring -> justificar -> persistir/auditar (opcional).
- Implementação em [app/api/routes.py](app/api/routes.py#L1-L200) e `app/engine`.

Exemplo mínimo (curl):

```bash
curl -sS -X POST http://127.0.0.1:8001/v1/equivalences/evaluate \
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

Exemplo em Python (requests):

```python
import requests
url='http://localhost:8100/v1/equivalences/evaluate'
headers={'X-API-Key':'dev-admin-123','Content-Type':'application/json'}
payload={
  'request_id':'req-001',
  'origem':{'nome':'Algoritmos','carga_horaria':60,'ementa':'...','aprovado':True,'nivel':'intermediario'},
  'destino':{'nome':'Introdução a Programação','carga_horaria':60,'ementa':'...','nivel':'basico'},
  'policy':{'min_score_deferir':85},
  'taxonomy_version':'2026.01'
}
resp=requests.post(url,json=payload,headers=headers)
print(resp.status_code, resp.json())
```

Resposta esperada: objeto `EvaluateResponse` com `decisao`, `score`, `breakdown`, `hard_rules`, `justificativa_*`, `evidence` (se ativo), etc. Consulte `app/api/schemas.py`.

2) Batch processing (macro):
- Enfileire muitos itens no endpoint batch ou diretamente em `Queue.enqueue` (veja [app/api/batch_routes.py](app/api/batch_routes.py#L1-L200)).
- Worker consome e chama `app.worker.process_job_item`.

Exemplo de enfileiramento (curl):

```bash
curl -X POST http://127.0.0.1:8001/v1/equivalences/batch -H 'Content-Type: application/json' -d @batch_request.json
```

3) Admin / Reprocess / DLQ
- Endpoints administrativos e de DLQ estão em [app/admin_routes.py](app/admin_routes.py#L1-L200) e [app/rq_hooks.py](app/rq_hooks.py#L1-L200).

Mapeadores e fallback (micro)

- `app/mapper` contém implementações de mappers: `stub_mapper.py` (útil para dev), `openai_mapper.py` (exemplo), `embedding_llm_mapper.py` (uso real com embeddings + LLM). Configure via `EMBED_URL`/`EMBED_API_KEY` e `LLM_URL`/`LLM_API_KEY`.
- Se o mapper principal falhar, `fallback_mapper` pode fornecer resultados degradados (veja `app/mapper/fallback_mapper.py`). O engine marca `degraded_mode` quando isso acontece.

Observabilidade e readiness

- Verificações de readiness ocorrem em [app/readiness.py](app/readiness.py#L1-L80) e verificam conexões ao Postgres e Redis.
- Métricas e logs: ver [app/metrics.py](app/metrics.py) e [app/logging_setup.py](app/logging_setup.py).

Dicas de produção

- Use um secret manager para `POSTGRES_PASSWORD`, `DATABASE_URL`, `API_KEY_SALT`.
- Troque `API_KEY_SALT` por uma string forte e rotacione se necessário.
- Escale workers conforme a demanda da fila RQ e monitore latência CPU/memória.
- Mantenha backups do Postgres e estratégias para persistência do volume `pgdata` (veja `docker-compose.prod.yml`).

Troubleshooting rápido

- Erro de conexão DB: verifique `DATABASE_URL` e se o container Postgres está up (`docker compose ps`).
- Worker não processa jobs: verifique `redis` (`redis-cli ping`) e que a fila correta está sendo observada (`rq info -u <REDIS_URL>`).
- Mapper externo não responde: teste `EMBED_URL`/`LLM_URL` com `curl`.

Próximos passos que eu posso fazer

- Mesclar este conteúdo no `README.md` principal ou criar `README.env.md` no repo (posso criar o arquivo se você autorizar).
- Adicionar exemplos de request/response completos (JSON) e scripts de integração.

---

Arquivo criado: `README.full.md`. Se quiser que eu integre este conteúdo ao `README.md` principal, diga se prefere que eu substitua um bloco específico ou que eu adicione um link para `README.full.md` no topo do `README.md`.
