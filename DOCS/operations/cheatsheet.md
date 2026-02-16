# Cheatsheet de Operações

Breve referência com comandos, queries e playbooks para operações e triagem rápida do Equivalence Engine Service.

---

## Comandos Docker / Compose

```bash
# Inicializar todos os serviços em background
docker compose up -d

# Ver logs do serviço web
docker compose logs -f web

# Ver logs do worker
docker compose logs -f worker

# Executar migrations
docker compose exec web alembic upgrade head

# Recriar containers após mudar .env
docker compose up -d --force-recreate

# Entrar no container e abrir um shell
docker compose exec web sh

# Parar stack
docker compose down

# Parar e remover volumes
docker compose down -v
```

---

## Conexão ao Postgres

```bash
# Via Docker
docker compose exec postgres psql -U equivalence -d equivalence

# Direto (host)
psql "postgresql://equivalence:equivalence@localhost:5432/equivalence"
```

---

## Queries SQL úteis

```sql
-- API keys por tenant
SELECT api_key_id, tenant_id, role, status, created_at
FROM api_keys
ORDER BY created_at DESC
LIMIT 20;

-- Últimas avaliações (se houver tabela de audit)
SELECT * FROM audit_log ORDER BY created_at DESC LIMIT 50;

-- Versão do Alembic
SELECT * FROM alembic_version;
```

---

## Redis e RQ

```bash
# Ping Redis
redis-cli ping
# ou
docker compose exec redis redis-cli ping

# Info da fila RQ
rq info -u redis://localhost:6379/0

# Iniciar worker manualmente
rq worker -u redis://localhost:6379/0 equivalence
```

---

## Health e Métricas

```bash
# Health check
curl -sS http://localhost:8000/health | jq .

# Métricas Prometheus
curl -sS http://localhost:8000/metrics | head -n 50
```

---

## Testes e Validação

```bash
# Smoke test (script)
bash scripts/test_api.sh

# Testes unitários
pytest tests/ -v

# Teste manual de avaliação
curl -sS -X POST http://localhost:8000/v1/equivalences/evaluate \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: dev-admin-abc123' \
  -d @scripts/test_payload.json | jq .
```

---

## Playbooks curtos

### API não responde
1. `docker compose ps` — verificar se web está Up
2. `docker compose logs --tail 100 web` — ver logs
3. `curl http://localhost:8000/health` — testar

### Worker não processa jobs
1. `redis-cli ping` — Redis ok?
2. `rq info -u redis://localhost:6379/0` — fila existe?
3. Reiniciar worker: `docker compose restart worker`

### Migrations falharam
1. Verificar `DATABASE_URL`
2. `alembic current` — versão atual
3. `alembic upgrade head` — aplicar
4. Se necessário: backup e `alembic downgrade -1`

### Erro 401 na API
1. Verificar header `X-API-Key`
2. Rodar `python -m app.seed` para criar chaves
3. Verificar `API_KEY_SALT` no `.env`

---

## URLs locais

| Serviço    | URL                    |
|-----------|------------------------|
| API       | http://localhost:8000  |
| API Docs  | http://localhost:8000/docs |
| Test UI   | http://localhost:8000/test |
| Health    | http://localhost:8000/health |
| Metrics   | http://localhost:8000/metrics |
| Mock Embed| http://localhost:9001 |
| Mock LLM  | http://localhost:9002 |

---

## Onde procurar

- **Logs e compose:** `docker-compose.yml`
- **Migrations:** `alembic/versions/`
- **Scripts:** `scripts/`
- **Config:** `app/config.py`, `.env`
