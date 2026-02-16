# Deploy / Subida do Equivalence Engine Service

Este documento descreve como subir a aplicação em diferentes modos:

- **Com Docker (recomendado)**: stack completa via Docker Compose
- **Híbrido**: infra via Docker + app rodando local
- **Sem Docker**: tudo local (exige provisionar dependências manualmente)

---

## 1. Pré-requisitos

### Para subir com Docker

- Docker Desktop (ou Docker Engine) + Docker Compose v2
- Portas livres (defaults):
  - API: `8000`
  - Postgres: `5432`
  - Redis: `6379`
  - Mock Embed: `9001`
  - Mock LLM: `9002`

### Para subir sem Docker

- Python 3.10+
- PostgreSQL 16+
- Redis 7+
- (Opcional) virtualenv/venv

---

## 2. Variáveis de ambiente (.env)

Crie `.env` na raiz (copie de `prod.env.example`). Exemplo mínimo para **Docker**:

```bash
POSTGRES_USER=equivalence
POSTGRES_PASSWORD=equivalence
POSTGRES_DB=equivalence
DATABASE_URL=postgresql+psycopg2://equivalence:equivalence@postgres:5432/equivalence
REDIS_URL=redis://redis:6379/0
API_KEY_SALT=change-me-to-a-long-random-string

# Mappers (stubs em dev)
EMBED_URL=http://mock-embed:9001
LLM_URL=http://mock-llm:9002
```

Para **rodar no host** (modo híbrido), use `localhost`:

```bash
DATABASE_URL=postgresql+psycopg2://equivalence:equivalence@localhost:5433/equivalence
REDIS_URL=redis://localhost:6380/0
EMBED_URL=http://localhost:9101
LLM_URL=http://localhost:9102
```

---

## 3. Subir com Docker (stack completa)

### 3.1 Build + up

```bash
docker compose up -d --build
docker compose ps
```

### 3.2 Migrations

```bash
docker compose exec web alembic upgrade head
```

### 3.3 Seed (API keys)

```bash
docker compose exec web python -m app.seed
```

### 3.4 Validar

```bash
curl -sS http://localhost:8100/health
curl -sS http://localhost:8100/docs
```

---

## 4. Modo híbrido (infra Docker + app local)

### 4.1 Subir só infra

```bash
docker compose up -d postgres redis mock-embed mock-llm
```

### 4.2 Venv e deps

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 4.3 Migrations (host = localhost)

```bash
export DATABASE_URL=postgresql+psycopg2://equivalence:equivalence@localhost:5433/equivalence
alembic upgrade head
```

### 4.4 Iniciar API

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

### 4.5 Iniciar worker (outro terminal)

```bash
rq worker -u redis://localhost:6380/0 equivalence
```

---

## 5. Produção — recomendações

### Secrets
- Não versionar `.env` em repos públicos
- Usar Vault, AWS Secrets Manager ou similar
- `API_KEY_SALT`, credenciais DB e Redis em secrets manager

### Migrations em produção
1. Backup completo do banco
2. Testar migration em staging
3. Janela de manutenção comunicada
4. Executar `alembic upgrade head`
5. Validar smoke tests
6. Plano de rollback documentado

### Alta disponibilidade
- Postgres: réplica/standby, backups contínuos
- Redis: Sentinel/cluster
- API: múltiplas réplicas atrás de load balancer
- Workers: escalar horizontalmente conforme fila

### Health / Readiness
- Liveness: `GET /health`
- Readiness: verificar DB e Redis em `/health` (se implementado)

### Monitoring
- Expor `/metrics` (Prometheus)
- Alertas: latência alta, taxa de erro, fila RQ crescendo

---

## 6. Parar a stack

```bash
docker compose down
```

Com remoção de volumes (cuidado: apaga dados):

```bash
docker compose down -v
```

---

## 7. Troubleshooting

### Portas ocupadas
- Altere no `docker-compose.yml` ou use variáveis
- Conflito com document-validation-platform: use 8001 para API, 9012 para mock-llm

### Erro "failed to resolve host 'postgres'"
- No host use `localhost`; dentro do Docker use `postgres`

### Erro "ModuleNotFoundError: psycopg2"
```bash
pip install psycopg2-binary
```

### Worker não processa
- Verificar Redis: `redis-cli ping`
- Verificar fila: `rq info -u redis://localhost:6379/0`
- Reiniciar worker: `docker compose restart worker`
