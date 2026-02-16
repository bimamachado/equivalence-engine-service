# Manual de Operação e Incidentes

## Equivalence Engine Service

Este manual descreve como operar o sistema no dia a dia, monitorar saúde e performance, identificar incidentes e agir em cada tipo de falha.

---

## 1. Objetivo

- Como **operar o sistema no dia a dia**
- Como **monitorar saúde e performance**
- Como **identificar e classificar incidentes**
- Como **agir em cada tipo de falha**
- O que **NÃO fazer** em situações críticas

---

## 2. Componentes críticos

1. **Web/API** — endpoints HTTP (evaluate, batch, admin)
2. **Worker RQ** — processamento assíncrono de jobs
3. **PostgreSQL** — persistência (tenants, api_keys, auditoria)
4. **Redis** — fila RQ e cache
5. **Mappers** — embeddings e LLM (externos ou mocks)

---

## 3. Princípios operacionais

### 3.1 Auditoria
- Avaliações e decisões devem ser auditáveis
- Nunca alterar registros de auditoria manualmente

### 3.2 Desacoplamento
- Consumidores (ex.: document-validation-platform) não devem ser bloqueados por falha interna
- Respostas síncronas devem ser rápidas; batch é assíncrono

---

## 4. Checklist diário (início do dia)

1. **Verificar containers**
```bash
docker compose ps
```

2. **Verificar health da API**
```bash
curl -sS http://localhost:8000/health
```

3. **Verificar Redis**
```bash
redis-cli ping
```

4. **Verificar fila RQ**
```bash
rq info -u redis://localhost:6379/0
```
- Jobs failed? Jobs queued crescendo?

---

## 5. Classificação de incidentes

| Nível | Descrição            |
|-------|----------------------|
| SEV-1 | API indisponível     |
| SEV-2 | Processamento parado (worker down, Redis down) |
| SEV-3 | Lentidão ou backlog  |
| SEV-4 | Erro isolado         |

---

## 6. Incidentes comuns e resposta

### INCIDENTE 1 — API fora do ar (SEV-1)

**Sintoma:** `curl /health` falha

**Ação:**
1. `docker compose ps` — container web está Up?
2. `docker compose logs --tail 200 web` — ver erro
3. Verificar Postgres e Redis
4. Reiniciar: `docker compose restart web`

---

### INCIDENTE 2 — Worker não processa jobs (SEV-2)

**Sintoma:** Jobs na fila RQ não são consumidos

**Diagnóstico:**
- Redis disponível? `redis-cli ping`
- Worker rodando? `docker compose ps worker`
- Logs do worker: `docker compose logs --tail 200 worker`

**Ação:**
1. Reiniciar worker: `docker compose restart worker`
2. Se Redis estiver down, subir Redis primeiro

---

### INCIDENTE 3 — Mapper externo não responde (SEV-3)

**Sintoma:** Avaliações falham com timeout ou erro de conexão

**Diagnóstico:**
- `EMBED_URL` e `LLM_URL` configurados?
- Testar: `curl http://localhost:9001/health` (mock embed)
- Verificar fallback mapper (modo degradado)

**Ação:**
1. Usar mocks locais para dev
2. Verificar credenciais e rede para serviços reais
3. Fallback mapper deve ativar automaticamente

---

### INCIDENTE 4 — Migrations falharam

**Sintoma:** API ou worker não sobem por erro de schema

**Ação:**
1. Ver logs: `docker compose logs migrate`
2. Verificar `alembic_version`
3. Backup antes de corrigir
4. Rodar manualmente: `alembic upgrade head`

---

## 7. Rotinas de manutenção

### Reiniciar um serviço
```bash
docker compose restart web
docker compose restart worker
```

### Rebuild total
```bash
docker compose up -d --build
```

### Reset completo (dev)
```bash
docker compose down -v
docker compose up -d --build
```

---

## 8. Backup & Restore

**Backup Postgres:**
```bash
docker compose exec postgres pg_dump -U equivalence equivalence -Fc -f /tmp/equiv_backup.dump
docker compose cp $(docker compose ps -q postgres):/tmp/equiv_backup.dump ./backup.dump
```

**Restore:**
```bash
docker compose exec -T postgres pg_restore -U equivalence -d equivalence --clean /tmp/backup.dump
```

---

## 9. O que NÃO fazer

❌ Alterar registros de auditoria manualmente  
❌ Apagar dados sem backup  
❌ Compartilhar API Keys  
❌ Logar PII (dados pessoais)  
❌ Rodar migrations em produção sem backup  

---

## 10. Links úteis

- Cheatsheet: [docs/operations/cheatsheet.md](../operations/cheatsheet.md)
- Incident response: [docs/runbooks/incident_response.md](incident_response.md)
- Deploy: [docs/deploy.md](../deploy.md)
