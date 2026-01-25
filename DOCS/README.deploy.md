# Deploy / Produção

Este documento amplia o processo de deploy e contém exemplos práticos para preparar infraestrutura, banco, chaves e executar o deploy com `docker-compose`.

Sumário rápido
- Gerenciamento de segredos
- Preparar Postgres/Redis
- Migrations e seed
- Geração e rotação de `API_KEY`s
- Subir containers (dev / prod)
- Checklist e troubleshooting

1) Variáveis sensíveis e segredos
- Guarde segredos em um secret manager (AWS Secrets Manager, Azure Key Vault, HashiCorp Vault, etc.).
- Variáveis mínimas necessárias:
  - `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`
  - `DATABASE_URL` (ex: `postgresql+psycopg2://user:pass@postgres:5432/db`)
  - `REDIS_URL` (ex: `redis://redis:6379/0`)
  - `API_KEY_SALT` (use `openssl rand -hex 32`)
  - `ADMIN_API_KEY`, `AUDITOR_API_KEY`, `CLIENT_API_KEY` (apenas para dev — em prod gere chaves seguras)
  - `LLM_API_KEY`, `EMBED_API_KEY` (opcional, se usar provedores externos)

2) Preparar Postgres e Redis
- Em ambientes com Docker Compose (produção simples) use volumes para persistência:
  - `docker-compose.prod.yml` já referencia volumes para Postgres.
- Exemplo rápido de deploy local (compose):

```bash
# exportar segredos (preferível: colocar em arquivo .env NÃO comitado ou injetar via secret manager)
export POSTGRES_PASSWORD="<secure>"
export POSTGRES_USER="equivalence"
export POSTGRES_DB="equivalence"
export DATABASE_URL="postgresql+psycopg2://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}"
export REDIS_URL="redis://redis:6379/0"
export API_KEY_SALT="$(openssl rand -hex 32)"

# subir infra básica (Postgres, Redis, mocks)
docker compose -f docker-compose.yml up -d --build
```

3) Migrations (Alembic)
- Sempre aplique migrations antes de iniciar a API em produção:

```bash
# exemplo: rodar dentro do container `web` (torna o comando idempotente para CI)
docker-compose exec web bash -lc "alembic upgrade head"
```

- Em CI/CD, coloque `alembic upgrade head` em um passo controlado (antes do rollout).

4) Seed / dados iniciais (API keys, tenant, taxonomy)
- Para ambiente de desenvolvimento ou staging use o script de seed seguro:

```bash
# executar dentro do container web
docker-compose exec web bash -lc "python scripts/seed_safe.py"
```

- O script cria tenants de exemplo e chaves dev (ver `scripts/seed_safe.py`). Em produção, crie chaves via processo administrativo ou import seguro.

5) Geração e rotação de `API_KEY`s
- Regras recomendadas:
  - gere chaves longas imprevisíveis (ex: 32+ bytes base64)
  - armazene apenas o hash (`API_KEY_SALT` + hashing forte, p.ex. HMAC-SHA256) no DB
  - forneça mecanismo de rotação: revogar a chave antiga, inserir nova, notificar consumidores

- Exemplo rápido (gera uma chave no host):
```bash
python - <<'PY'
import secrets
print(secrets.token_urlsafe(48))
PY
```

6) Subir a API (dev vs prod)
- Dev (rápido):
```bash
docker compose up -d --build
# aplica migrations e seed
docker-compose exec web bash -lc "alembic upgrade head && python scripts/seed_safe.py"
```

- Prod (compose prod):
```bash
export $(cat prod.env | xargs)
docker compose -f docker-compose.prod.yml up -d --build
# em seguida, executar migrations em um job controlado
docker-compose -f docker-compose.prod.yml exec web bash -lc "alembic upgrade head"
```

7) Health-checks e verificação pós-deploy
- Endpoints úteis:
  - `/health` — status da API
  - `/ready` — readiness (DB/Redis)

Exemplo:
```bash
curl -I http://localhost:8000/health
curl -s http://localhost:8000/ready
```

8) Observabilidade
- Exponha métricas (Prometheus) e logs estruturados.
- Alerta recomendado: filas RQ com jobs atrasados, conexões DB falhando, tempo de resposta alto.

9) Backups e rollbacks
- Backup rápido:
```bash
docker exec -t <postgres-container> pg_dumpall -c -U ${POSTGRES_USER} > dump_$(date +%F).sql
```
- Rollback de migrations requer planejamento (algumas migrations não são facilmente reversíveis). Teste rollback em staging.

10) CI / CD recomendações
- Em pipelines:
  - Build da imagem
  - Rodar testes unitários (sem serviços externos)
  - Subir ambiente de integração (Postgres/Redis/mocks)
  - Rodar `alembic upgrade head` e testes de integração
  - Se passar, promover imagem e executar rollout controlado

11) Troubleshooting rápido
- Erro de conexão com Postgres: verifique `DATABASE_URL` e se o serviço Postgres está no mesmo network do `web`.
- Erro MultipleResultsFound / duplicidade de `api_keys`: verifique registros duplicados e aplique migration de constraint (já presente no projeto).
- Worker não processa jobs: verifique se `worker` está em execução e conectado ao mesmo Redis do `web`.

12) Checklist rápido antes do primeiro deploy
- [ ] Segredos armazenados e referenciados pelo orquestrador
- [ ] Volumes/PVC configurados para Postgres
- [ ] `alembic upgrade head` executado com sucesso
- [ ] Seed carregado (quando necessário)
- [ ] Workers configurados e testados
- [ ] Monitoramento/alertas ativos

Se quiser, posso:
- adicionar um exemplo de `prod.env` seguro (modelo sem valores sensíveis), ou
- criar um playbook passo-a-passo para um deploy em Kubernetes (manifests/helm).

---

Histórico: documento original com recomendações básicas expandido para incluir comandos práticos, exemplos e checklist.

