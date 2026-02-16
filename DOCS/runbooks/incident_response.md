# Runbook — Resposta a Incidentes

Este runbook orienta a resposta a incidentes no Equivalence Engine Service com foco em:

- restaurar serviço (mitigar impacto)
- preservar evidências (auditoria)
- identificar causa raiz (RCA)

---

## 1. Classificação do incidente

- **P0**: API fora do ar ou nenhuma avaliação processa.
- **P1**: processamento degradado (worker down, backlog crescendo).
- **P2**: falha parcial (ex.: batch falhando, síncrono ok).
- **P3**: bug/alerta sem impacto imediato.

---

## 2. Checklist inicial (primeiros 10 minutos)

### 1) Confirmar sintomas

- API responde?
```bash
curl -sS http://localhost:8000/health | cat
```

- Stack Docker saudável?
```bash
docker compose ps
```

### 2) Coletar contexto

- O que mudou? (deploy, migrations, env, secrets)
- Qual tenant/endpoint afetado?
- Início do problema (timestamp)

### 3) Definir mitigação rápida

- Se API down: reiniciar container `web`
- Se worker down: reiniciar `worker`, verificar Redis
- Se DB down: priorizar restauração do Postgres

---

## 3. Playbooks por sintoma

### 3.1 API fora do ar

**Sinais:** `curl /health` falha, container `web` reiniciando

**Ações:**
1. Ver logs: `docker compose logs --tail=200 web`
2. Checar dependências: `docker compose ps postgres redis`
3. Corrigir `.env` se necessário e subir: `docker compose up -d --build web`

---

### 3.2 Avaliações síncronas falham (timeout/500)

**Sinais:** `POST /v1/equivalences/evaluate` retorna erro

**Diagnóstico:**
1. Logs do web: `docker compose logs --tail=200 web`
2. Mapper (EMBED_URL, LLM_URL) respondendo?
3. Postgres conectado?

**Mitigação:**
- Se mapper externo down: usar mocks ou fallback mapper
- Se DB down: restaurar Postgres

---

### 3.3 Jobs batch não processam

**Sinais:** Jobs enfileirados mas não executam

**Diagnóstico:**
1. Redis: `redis-cli ping`
2. Fila RQ: `rq info -u redis://localhost:6379/0`
3. Worker: `docker compose logs --tail=200 worker`

**Mitigação:**
- Reiniciar worker: `docker compose restart worker`
- Verificar DLQ (jobs failed) e reprocessar se necessário

---

### 3.4 Erros de migrations / schema

**Sinais:** migrate falha, serviços não sobem

**Ações:**
1. Ver logs: `docker compose logs migrate`
2. Rodar migrations manualmente: `alembic upgrade head`
3. Não forçar app com schema incompleto
4. Se necessário: restaurar backup e reaplicar

---

### 3.5 Problemas de conexão (DB/Redis)

**Sinais:** "connection refused", "could not connect"

**Diagnóstico:**
- `DATABASE_URL` e `REDIS_URL` corretos?
- Dentro do Docker: usar hosts `postgres` e `redis`
- No host: usar `localhost`

**Mitigação:**
- Verificar rede Docker
- Reiniciar postgres/redis: `docker compose restart postgres redis`

---

## 4. Comunicação e registro

Durante o incidente, registrar:

- impacto (quantos consumidores, quantas avaliações)
- janela temporal
- comandos executados
- mitigação aplicada

Após estabilizar:

- abrir RCA com causa raiz, correção e ações preventivas

---

## 5. Pós-incidente (RCA)

Checklist de RCA:

- Qual foi o gatilho? (deploy, config, carga, dependência externa)
- Por que o alerta não pegou antes? (observabilidade)
- Como prevenir?
  - dashboards/alerts
  - timeouts/retry
  - testes de integração

---

## 6. Comandos úteis

```bash
# Health-checks rápidos
curl -sS http://localhost:8000/health | jq .
curl -sS http://localhost:8000/metrics | head -n 20
docker compose ps

# Redis e RQ
redis-cli ping
rq info -u redis://localhost:6379/0

# Reiniciar serviços
docker compose restart web worker
```

---

## 7. Links

- Runbook geral: [docs/runbooks/operations.md](operations.md)
- Cheatsheet: [docs/operations/cheatsheet.md](../operations/cheatsheet.md)
- Deploy: [docs/deploy.md](../deploy.md)
