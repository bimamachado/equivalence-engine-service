# Guia de desenvolvimento: subir localmente e validar o Equivalence Engine

Este guia descreve os passos para subir a stack localmente, aplicar migrations, popular API keys e executar testes.

---

## Pré-requisitos

- Docker & Docker Compose (v2)
- Python 3.10+ (para rodar localmente sem Docker)
- `curl`, `jq` no host (úteis para inspeção)

---

## Passo a passo rápido

### 1. Preparar `.env`

Crie um arquivo `.env` na raiz (copie de `prod.env.example`):

```bash
cp prod.env.example .env
```

Variáveis mínimas para desenvolvimento:

```bash
POSTGRES_USER=equivalence
POSTGRES_PASSWORD=equivalence
POSTGRES_DB=equivalence
DATABASE_URL=postgresql+psycopg2://equivalence:equivalence@localhost:5432/equivalence
REDIS_URL=redis://localhost:6379/0
API_KEY_SALT=dev_salt_change_me

# Mocks (já sobem com docker compose)
EMBED_URL=http://localhost:9001
LLM_URL=http://localhost:9002
```

**Dentro do Docker**, use hosts `postgres` e `redis` em vez de `localhost` na `DATABASE_URL` e `REDIS_URL` se os serviços se comunicarem entre containers.

---

### 2. Subir stack com Docker

```bash
docker compose up -d
docker compose ps
```

Serviços iniciados: `web`, `worker`, `mock-embed`, `mock-llm`, `redis`, `postgres`.

---

### 3. Aplicar migrations

```bash
# Dentro do container
docker compose exec web alembic upgrade head

# Ou localmente (com venv ativado)
alembic upgrade head
```

---

### 4. Popular dados (API keys)

```bash
# Dentro do container
docker compose exec web python -m app.seed

# Ou localmente
python -m app.seed
```

Isso cria chaves de exemplo: `dev-admin-abc123`, `dev-tenant-abc123`, etc.

---

### 5. Verificar health

```bash
curl -sS http://localhost:8000/health | jq .
```

---

### 6. Testar avaliação

```bash
curl -sS -X POST http://localhost:8000/v1/equivalences/evaluate \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: dev-admin-abc123' \
  -d '{
    "request_id":"req-001",
    "origem":{"nome":"Algoritmos","carga_horaria":60,"ementa":"...","aprovado":true,"nivel":"intermediario"},
    "destino":{"nome":"Introdução a Programação","carga_horaria":60,"ementa":"...","nivel":"basico"},
    "policy":{"min_score_deferir":85},
    "taxonomy_version":"2026.01"
  }' | jq .
```

---

## Modo híbrido (infra Docker + app local)

Útil para desenvolvimento com hot-reload:

### 1. Subir só infra

```bash
docker compose up -d postgres redis mock-embed mock-llm
```

### 2. Criar venv e instalar deps

```bash
python -m venv .venv
source .venv/bin/activate  # ou .venv\Scripts\activate no Windows
pip install -r requirements.txt
```

### 3. Configurar .env para localhost

```bash
DATABASE_URL=postgresql+psycopg2://equivalence:equivalence@localhost:5432/equivalence
REDIS_URL=redis://localhost:6379/0
EMBED_URL=http://localhost:9001
LLM_URL=http://localhost:9002
```

### 4. Rodar migrations

```bash
alembic upgrade head
```

### 5. Iniciar API

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

### 6. Iniciar worker (outro terminal)

```bash
rq worker -u redis://localhost:6379/0 equivalence
```

---

## Rodar testes

```bash
pytest tests/ -v
```

---

## Troubleshooting

### Erro: "failed to resolve host 'postgres'"
- No host, use `localhost` na `DATABASE_URL` e `REDIS_URL`.
- Dentro do Docker, use `postgres` e `redis` como hosts.

### Erro: "ModuleNotFoundError: psycopg2"
```bash
pip install psycopg2-binary
```

### Worker não processa jobs
1. Verificar Redis: `redis-cli ping`
2. Verificar fila: `rq info -u redis://localhost:6379/0`
3. Iniciar worker em foreground para ver logs: `rq worker -u redis://localhost:6379/0 equivalence`

### API retorna 401
- Verificar header `X-API-Key`
- Verificar se a chave foi criada com `python -m app.seed`
- Verificar `API_KEY_SALT` (deve ser o mesmo usado no seed)

### Portas ocupadas
- Altere no `docker-compose.yml` ou use variáveis de ambiente.
- Para evitar conflito com document-validation-platform: use 8001 para API, 9012 para mock-llm.

---

## Comandos úteis

```bash
# Logs
docker compose logs -f web
docker compose logs -f worker

# Entrar no container
docker compose exec web sh

# Parar stack
docker compose down

# Parar e remover volumes
docker compose down -v
```
